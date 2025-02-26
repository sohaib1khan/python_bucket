#!/bin/bash

set -e  # Exit script on error

# --- Step 1: Detect Python & Pip ---
if command -v python3 &>/dev/null; then
    PYTHON=python3
    PIP=pip3
elif command -v python &>/dev/null; then
    PYTHON=python
    PIP=pip
else
    echo "Python is not installed. Please install Python and try again."
    exit 1
fi

echo "Using: $PYTHON ($PIP)"

# --- Step 2: Install Required Packages ---
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found in the current directory!"
    exit 1
fi

echo "Installing required Python packages..."
$PIP install --user -r requirements.txt
$PIP install pyqt6

# --- Step 3: Set up Virtual Environment ---
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

echo "Virtual environment activated!"

# --- Step 4: Install PyInstaller ---
echo "Installing PyInstaller..."
pip install pyinstaller

# --- Step 5: Bundle the App with PyInstaller ---
echo "Bundling the application into an executable..."
pyinstaller --onefile --name=bookmark_manager --add-data "config.json:config.json" --hidden-import=app main.py

# --- Step 6: Clean up Unnecessary Files ---
echo "Cleaning up unnecessary files..."
deactivate  # Deactivate virtual environment
rm -rf build venv __pycache__
rm -rf bookmark_manager.spec  # Remove PyInstaller spec file

# --- Step 7: Provide User Instructions ---
echo -e "\n✅ Build complete! You can now run the app:"
echo -e "   ./dist/bookmark_manager"
echo -e "\nTo move the app to a more accessible location, run:"
echo -e "   mv dist/bookmark_manager /usr/local/bin/"

exit 0
