# 🎱 Magic 8 Ball - Desktop App

## 📌 Overview

The **Magic 8 Ball** is a fun, interactive desktop application that answers your questions with randomized responses, just like the classic Magic 8 Ball toy!

This app is built using **Python and PyQt6** and includes **animations, sound effects, and a visually appealing UI** to make the experience more immersive.

---

## 🚀 Features

- 🎭 **Animated 8 Ball** that shakes before revealing an answer.
- 🎶 **Sound Effects** for an immersive experience.
- 🔄 **Randomized Responses** with colorful text.
- 🌙 **Dark-Themed UI** for a comfortable experience.
- ✅ **Standalone Executable** support for Windows & Linux.

---

## 🛠️ Installation

### 1️⃣ Install Dependencies

First, install Python (if not already installed), then install the required dependencies:

```bash
pip install -r requirements.txt
```

### 2️⃣ Run the Application

Simply execute the script using:

```bash
python main.py
```

---

## 📦 Building Executable

You can package the app as a standalone executable using **PyInstaller**.

### **Build App**

```bash
pyinstaller --onefile --noconsole --name=8ballgame --add-data "magic8ball.png:." --add-data "magic8sound.mp3:." main.py
```

The generated app file will be in the `dist/` folder.

---

## 🎨 Assets & Resources

This app includes:

- 🎨 `magic8ball.png` - The Magic 8 Ball image.
- 🎵 `magic8sound.mp3` - Sound effect for revealing an answer.
- 📝 `main.py` - The main application script.
- 📜 `requirements.txt` - Required dependencies for the app.

---

