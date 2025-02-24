from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import feedparser
import requests
import hashlib
from bs4 import BeautifulSoup

app = Flask(__name__)

# SQLite Database Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feeds.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model
class Feed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(300), unique=True, nullable=False)
    last_hash = db.Column(db.String(64), nullable=True)

# Create database
with app.app_context():
    db.create_all()


# Database Model for Saved Articles
class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    content_html = db.Column(db.Text, nullable=False)
    saved_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# Create tables
with app.app_context():
    db.create_all()


# ✅ **Scraper Function - Returns HTML Output**
def scrape_website(url):
    """Scrapes metadata and full article content from a webpage."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()
    except requests.Timeout:
        return {"error": "⚠️ Timeout: The site took too long to respond."}
    except requests.RequestException as e:
        return {"error": f"❌ Unable to fetch the page: {e}"}

    soup = BeautifulSoup(response.text, "html.parser")

    # ✅ Extract Title
    title = soup.title.string.strip() if soup.title else "No Title Found"

    # ✅ Extract Meta Description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    description = meta_desc["content"].strip() if meta_desc and "content" in meta_desc.attrs else "No Description Available"

    # ✅ Extract OpenGraph Image
    og_image = soup.find("meta", property="og:image")
    image_url = og_image["content"].strip() if og_image and "content" in og_image.attrs else ""

    # ✅ Extract Last Modified Date
    last_modified_date = None
    for tag in [
        {"name": "last-modified"},
        {"property": "article:modified_time"},
        {"itemprop": "dateModified"},
        {"name": "date"},
        {"property": "og:updated_time"},
        {"name": "dcterms.modified"},
    ]:
        last_modified = soup.find("meta", attrs=tag)
        if last_modified and "content" in last_modified.attrs:
            last_modified_date = last_modified["content"].strip()
            break

    last_modified_date = last_modified_date or "No Last Modified Date Found"

    # ✅ Extract Readable Content (FULL ARTICLE in HTML format)
    content_html = ""

    # **🔍 TRY MULTIPLE CONTENT LOCATIONS**
    for selector in ["article", "div.content", "div#main", "section", "div.post-body"]:
        found_element = soup.select_one(selector)
        if found_element:
            content_html = str(found_element)
            break

    # **🔍 Fallback to Collecting All Paragraphs**
    if not content_html:
        paragraphs = soup.find_all("p")
        content_html = "".join(str(p) for p in paragraphs) if paragraphs else "<p>No readable content found.</p>"

    # ✅ Compute Hash for Change Detection
    page_hash = hashlib.md5(content_html.encode()).hexdigest() if content_html else "no_content"

    # ✅ Return FULL HTML Content
    return {
        "title": title,
        "description": description,
        "image_url": image_url,
        "last_modified": last_modified_date,
        "hash": page_hash,
        "content_html": f"<h2>{title}</h2><p><strong>{description}</strong></p>{content_html}"
    }



# ✅ **Fetch RSS Content**
def fetch_rss_content(url):
    """Attempt to fetch RSS content from a URL"""
    print(f"🔎 Checking {url} for RSS feed...")

    feed = feedparser.parse(url)

    if feed.bozo == 0 and "entries" in feed:
        print(f"✅ RSS feed found! Displaying articles from {url}")
        return [{"title": entry.title, "link": entry.link} for entry in feed.entries[:5]]

    print(f"❌ No valid RSS feed found at {url}. Falling back to scraping...")
    return None

# ✅ **Fetch Articles for a Feed**
@app.route('/fetch_articles/<int:feed_id>')
def fetch_articles(feed_id):
    feed = Feed.query.get(feed_id)
    if not feed:
        return jsonify({"error": "Feed not found"}), 404

    print(f"🔎 Checking {feed.url} for RSS feed...")

    # ✅ Step 1: Try fetching RSS content first
    articles = fetch_rss_content(feed.url)
    if articles:
        return jsonify({"articles": articles})

    # ✅ Step 2: If RSS fails, attempt full page scraping
    print(f"❌ No valid RSS detected. Scraping full metadata for {feed.url}...")

    page_info = scrape_website(feed.url)

    # ✅ Ensure scraped content is structured properly
    if "content_html" in page_info:
        if feed.last_hash and feed.last_hash != page_info["hash"]:
            page_info["update"] = "This page has been updated!"
        else:
            page_info["update"] = "No recent updates."

        feed.last_hash = page_info["hash"]
        db.session.commit()

        return jsonify({"articles": [{
    "title": page_info["title"],
    "url": feed.url,  # ✅ Ensure URL is included in JSON
    "content_html": page_info["content_html"],
    "update": page_info.get("update", "No recent updates.")
}]})


    return jsonify({"error": "Failed to retrieve content from site."})


# ✅ **Home Page**
@app.route('/')
def index():
    feeds = Feed.query.all()
    return render_template('index.html', feeds=feeds)

# ✅ **Add Feed**
@app.route('/add_feed', methods=['POST'])
def add_feed():
    name = request.form['name']
    url = request.form['url']

    if not name or not url:
        return jsonify({"error": "Name and URL cannot be empty"}), 400

    if Feed.query.filter_by(url=url).first():
        return jsonify({"error": "Feed already exists"}), 400

    new_feed = Feed(name=name, url=url)
    db.session.add(new_feed)
    db.session.commit()

    return jsonify({"message": "Feed added successfully!"})

@app.route('/update_feed/<int:feed_id>', methods=['POST'])
def update_feed(feed_id):
    feed = Feed.query.get(feed_id)
    if not feed:
        return jsonify({"error": "Feed not found"}), 404

    new_name = request.form['name']
    new_url = request.form['url']

    if not new_name or not new_url:
        return jsonify({"error": "Name and URL cannot be empty"}), 400

    feed.name = new_name
    feed.url = new_url
    db.session.commit()

    return jsonify({"message": "Feed updated successfully!"})

@app.route('/save_article', methods=['POST'])
def save_article():
    data = request.json  # Use JSON data instead of form
    print("Received Data:", data)  # ✅ Debug Incoming Data

    title = data.get('title')
    url = data.get('url')
    content_html = data.get('content_html')

    if not title or not url or not content_html:
        return jsonify({"error": "Missing data. Cannot save article."}), 400

    new_article = Article(title=title, url=url, content_html=content_html)
    db.session.add(new_article)
    db.session.commit()

    return jsonify({"message": "Article saved successfully!"})


@app.route('/load_articles')
def load_articles():
    articles = Article.query.order_by(Article.saved_at.desc()).all()
    return jsonify({
        "articles": [
            {"title": a.title, "url": a.url, "content_html": a.content_html, "saved_at": a.saved_at.strftime("%Y-%m-%d %H:%M")}
            for a in articles
        ]
    })



# ✅ **Delete Feed**
@app.route('/delete_feed/<int:feed_id>', methods=['DELETE'])
def delete_feed(feed_id):
    feed = Feed.query.get(feed_id)
    if not feed:
        return jsonify({"error": "Feed not found"}), 404

    db.session.delete(feed)
    db.session.commit()
    return jsonify({"message": "Feed deleted successfully!"})


if __name__ == '__main__':
    app.run(debug=True)
