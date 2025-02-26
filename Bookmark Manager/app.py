import sys
import json
import os
import csv
import webbrowser
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget,
    QLineEdit, QLabel, QHBoxLayout, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt


def get_config_path():
    """Returns the correct path to config.json, whether running from source or as an executable."""
    if getattr(sys, 'frozen', False):  # Running as PyInstaller bundled app
        base_path = os.path.dirname(sys.executable)  # Use the directory of the executable
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, "config.json")


CONFIG_FILE = get_config_path()


class BookmarkManager(QWidget):
    def __init__(self):
        super().__init__()

        # Layouts
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Category Input and Button
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("New Category Name")
        self.layout.addWidget(self.category_input)

        self.add_category_button = QPushButton("Add Category")
        self.add_category_button.clicked.connect(self.add_category)
        self.layout.addWidget(self.add_category_button)
        
        self.delete_category_button = QPushButton("Delete Category")
        self.delete_category_button.clicked.connect(self.delete_category)
        self.layout.addWidget(self.delete_category_button)

        self.setWindowTitle("Bookmark Manager")
        self.setGeometry(100, 100, 600, 500)

        self.config = self.load_config()

        # Theme Switch Button
        self.theme_button = QPushButton("Switch Theme")
        self.theme_button.clicked.connect(self.switch_theme)
        self.layout.addWidget(self.theme_button)

        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search bookmarks...")
        self.search_input.textChanged.connect(self.filter_bookmarks)
        self.layout.addWidget(self.search_input)

        # Category List
        self.category_label = QLabel("Categories:")
        self.layout.addWidget(self.category_label)

        self.category_list = QListWidget()
        self.layout.addWidget(self.category_list)
        self.category_list.itemClicked.connect(self.load_bookmarks)

        # Bookmark List
        self.bookmark_label = QLabel("Bookmarks:")
        self.layout.addWidget(self.bookmark_label)

        self.bookmark_list = QListWidget()
        self.layout.addWidget(self.bookmark_list)
        self.bookmark_list.itemDoubleClicked.connect(self.open_bookmark)

        # Input Fields
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Bookmark Name")
        self.layout.addWidget(self.name_input)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Bookmark URL")
        self.layout.addWidget(self.url_input)

        # Buttons Layout
        button_layout = QHBoxLayout()
        self.layout.addLayout(button_layout)

        self.add_button = QPushButton("Add Bookmark")
        self.add_button.clicked.connect(self.add_bookmark)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit Bookmark")
        self.edit_button.clicked.connect(self.edit_bookmark)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete Bookmark")
        self.delete_button.clicked.connect(self.delete_bookmark)
        button_layout.addWidget(self.delete_button)

        self.export_button = QPushButton("Export Bookmarks")
        self.export_button.clicked.connect(self.export_bookmarks)
        button_layout.addWidget(self.export_button)

        self.import_button = QPushButton("Import Bookmarks")
        self.import_button.clicked.connect(self.import_bookmarks)
        button_layout.addWidget(self.import_button)

        # Load categories on start
        self.load_categories()
        self.apply_theme()

    def delete_category(self):
        """Delete the selected category."""
        selected_category = self.category_list.currentItem()
        if selected_category:
            category = selected_category.text()
            del self.config["categories"][category]
            self.save_config(self.config)
            self.load_categories()
            self.bookmark_list.clear()  # Clear bookmark list if category is deleted


    def load_config(self):
        """Load config file or create default one."""
        if not os.path.exists(CONFIG_FILE):
            default_config = {"categories": {}, "settings": {"theme": "dark"}}
            self.save_config(default_config)
            return default_config
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)

    def save_config(self, config):
        """Save changes to config file."""
        with open(CONFIG_FILE, "w") as file:
            json.dump(config, file, indent=4)

    def load_categories(self):
        """Load categories into the category list."""
        self.category_list.clear()
        self.category_list.addItems(self.config["categories"].keys())

    def add_category(self):
        """Add a new category."""
        category_name = self.category_input.text().strip()
        if category_name and category_name not in self.config["categories"]:
            self.config["categories"][category_name] = []
            self.save_config(self.config)
            self.load_categories()
            self.category_input.clear()


    def load_bookmarks(self):
        """Load bookmarks when a category is selected."""
        self.bookmark_list.clear()
        selected_category = self.category_list.currentItem().text()
        bookmarks = self.config["categories"].get(selected_category, [])

        for bm in bookmarks:
            self.bookmark_list.addItem(f"{bm['name']} - {bm['url']}")

    def add_bookmark(self):
        """Add a new bookmark or update an existing one."""
        selected_category = self.category_list.currentItem()
        selected_bookmark = self.bookmark_list.currentItem()

        if selected_category:
            category = selected_category.text()
            name = self.name_input.text().strip()
            url = self.url_input.text().strip()

            if name and url:
                bookmarks = self.config["categories"].get(category, [])

                # If editing an existing bookmark, update it
                if selected_bookmark:
                    old_name = selected_bookmark.text().split(" - ")[0]
                    for bm in bookmarks:
                        if bm["name"] == old_name:
                            bm["name"] = name
                            bm["url"] = url
                            break
                else:
                    # Otherwise, add a new bookmark
                    bookmarks.append({"name": name, "url": url})

                self.config["categories"][category] = bookmarks
                self.save_config(self.config)
                self.load_bookmarks()
                self.name_input.clear()
                self.url_input.clear()


    def delete_bookmark(self):
        """Delete the selected bookmark."""
        selected_category = self.category_list.currentItem()
        selected_bookmark = self.bookmark_list.currentItem()

        if selected_category and selected_bookmark:
            category = selected_category.text()
            bookmark_name = selected_bookmark.text().split(" - ")[0]

            self.config["categories"][category] = [
                bm for bm in self.config["categories"][category] if bm["name"] != bookmark_name
            ]
            if not self.config["categories"][category]:  # Remove category if empty
                del self.config["categories"][category]

            self.save_config(self.config)
            self.load_bookmarks()
            self.load_categories()
    
    def edit_bookmark(self):
        """Load selected bookmark data into input fields for editing."""
        selected_bookmark = self.bookmark_list.currentItem()
        if selected_bookmark:
            name, url = selected_bookmark.text().split(" - ")
            self.name_input.setText(name)
            self.url_input.setText(url)


    def open_bookmark(self):
        """Open the selected bookmark in the default web browser."""
        selected_bookmark = self.bookmark_list.currentItem()
        if selected_bookmark:
            url = selected_bookmark.text().split(" - ")[1]
            webbrowser.open(url)

    def switch_theme(self):
        """Switch between light and dark themes."""
        current_theme = self.config["settings"].get("theme", "dark")
        new_theme = "light" if current_theme == "dark" else "dark"
        self.config["settings"]["theme"] = new_theme
        self.save_config(self.config)
        self.apply_theme()

    def apply_theme(self):
        """Apply theme settings to the UI."""
        theme = self.config["settings"].get("theme", "dark")

        if theme == "dark":
            self.setStyleSheet("background-color: #2E2E2E; color: white;")
            button_style = """
                QPushButton {
                    background-color: #555;
                    color: white;
                    border: 1px solid #777;
                    padding: 8px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #777;
                }
                QPushButton:pressed {
                    background-color: #444;
                }
            """
        else:
            self.setStyleSheet("background-color: white; color: black;")
            button_style = """
                QPushButton {
                    background-color: #f0f0f0;
                    color: black;
                    border: 1px solid #ccc;
                    padding: 8px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #ddd;
                }
                QPushButton:pressed {
                    background-color: #bbb;
                }
            """

        # Apply styles to all buttons
        self.theme_button.setStyleSheet(button_style)
        self.add_category_button.setStyleSheet(button_style)
        self.delete_category_button.setStyleSheet(button_style)
        self.add_button.setStyleSheet(button_style)
        self.edit_button.setStyleSheet(button_style)
        self.delete_button.setStyleSheet(button_style)
        self.export_button.setStyleSheet(button_style)
        self.import_button.setStyleSheet(button_style)


    def filter_bookmarks(self):
        """Filter bookmarks based on search input."""
        query = self.search_input.text().lower()
        self.bookmark_list.clear()

        selected_category = self.category_list.currentItem()
        if selected_category:
            category = selected_category.text()
            bookmarks = self.config["categories"].get(category, [])

            for bm in bookmarks:
                if query in bm['name'].lower() or query in bm['url'].lower():
                    self.bookmark_list.addItem(f"{bm['name']} - {bm['url']}")

    def export_bookmarks(self):
        """Export bookmarks to a JSON file."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Bookmarks", "", "JSON Files (*.json)")
        if file_path:
            with open(file_path, "w") as file:
                json.dump(self.config["categories"], file, indent=4)
            QMessageBox.information(self, "Export", "Bookmarks exported successfully!")

    def import_bookmarks(self):
        """Import bookmarks from a JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Bookmarks", "", "JSON Files (*.json)")
        if file_path:
            with open(file_path, "r") as file:
                self.config["categories"].update(json.load(file))
            self.save_config(self.config)
            self.load_categories()
            QMessageBox.information(self, "Import", "Bookmarks imported successfully!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BookmarkManager()
    window.show()
    sys.exit(app.exec())
