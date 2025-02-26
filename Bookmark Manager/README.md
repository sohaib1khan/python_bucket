# Bookmark Manager

## Overview

The **Bookmark Manager** is a simple desktop application that allows users to organize their bookmarks efficiently. It provides an intuitive interface for managing bookmarks by categories, enabling easy access, editing, and searching. The application is built using **Python (PyQt6)** and can be run as a standalone executable.

## Features

- **Categorized Bookmarks**: Organize bookmarks under different categories.
- **CRUD Operations**: Add, edit, and delete bookmarks.
- **Search Functionality**: Quickly search for bookmarks.
- **Import/Export Bookmarks**: Save and load bookmarks from JSON files.
- **Theme Switching**: Toggle between light and dark themes.
- **Standalone Executable**: No need to install Python to run the application.

## Folder Structure

```
/bookmark_manager
│── app.py                  # Main Application File
│── main.py                 # Entry Point
│── config.json             # Stores Categories & Bookmarks
│── requirements.txt        # Python Dependencies
│── build.sh                # Script to Build Executable
│── dist/                   # Folder where Executable is Created
│── venv/                   # Virtual Environment (Optional)
│── __pycache__/            # Python Cache (Ignored)
```

## Running the Application

### Running from Source (Requires Python)

#### Step 1: Install Dependencies

Ensure Python and pip are installed, then run:

```bash
pip install -r requirements.txt
```

#### Step 2: Run the Application

```bash
python main.py
```

### Running the Compiled Executable (No Python Required)

#### Step 1: Build the Executable

If you haven't built it yet, run:

```bash
chmod +x build.sh
./build.sh
```

#### Step 2: Run the Application

After building, the executable will be inside `dist/`:

```bash
./dist/bookmark_manager
```

#### Optional: Move Executable to Global Location

To run it from anywhere:

```bash
sudo mv dist/bookmark_manager /usr/local/bin/
bookmark_manager
```

## Configuration and Customization

### Modifying the UI

- The user interface is built with **PyQt6**.
- UI layouts and elements are defined in `main.py`.
- Theme settings are managed in `apply_theme()`.

### Managing Bookmarks

- Bookmarks and categories are stored in **config.json**.
- To reset the application, delete `config.json` and restart.

## Troubleshooting

### Application Doesn't Launch?

Run:

```bash
./dist/bookmark_manager
```

If you see errors regarding `config.json`, ensure it exists in the executable directory.

### Permission Issues on Linux?

Run:

```bash
chmod +x dist/bookmark_manager
```

### Missing `config.json`?

Create a new `config.json` file:

```json
{
    "categories": {
        "Work": [],
        "Personal": []
    },
    "settings": {
        "theme": "dark"
    }
}
```

This document provides clear instructions on using, configuring, and troubleshooting the application.

