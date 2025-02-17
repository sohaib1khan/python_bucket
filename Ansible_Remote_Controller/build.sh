#!/bin/bash

# Enable error handling
set -e

# Define project name
APP_NAME="AnsibleRemoteController"

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Detect package manager
if command_exists apt; then
    PKG_MANAGER="apt"
    INSTALL_CMD="sudo apt install -y"
elif command_exists dnf; then
    PKG_MANAGER="dnf"
    INSTALL_CMD="sudo dnf install -y"
elif command_exists yum; then
    PKG_MANAGER="yum"
    INSTALL_CMD="sudo yum install -y"
else
    echo "❌ Unsupported Linux distribution. Exiting."
    exit 1
fi

# Ensure system is updated (Only once at the start)
if [[ "$PKG_MANAGER" == "apt" ]]; then
    echo "🔄 Updating package list..."
    sudo apt update && sudo apt upgrade -y
fi

# Function to check system requirements
check_requirements() {
    echo "🔍 Checking system requirements..."
    MISSING_REQUIREMENTS=()

    if ! command_exists python3; then
        MISSING_REQUIREMENTS+=("Python3")
    fi
    if ! command_exists pip3; then
        MISSING_REQUIREMENTS+=("Pip")
    fi
    if ! python3 -m venv --help &> /dev/null; then
        MISSING_REQUIREMENTS+=("Python Virtual Environment (venv)")
    fi
    if ! command_exists pyinstaller; then
        MISSING_REQUIREMENTS+=("PyInstaller")
    fi
    if ! python3 -c "import PyQt6" &> /dev/null; then
        MISSING_REQUIREMENTS+=("PyQt6 (installed via pip)")
    fi

    if [ ${#MISSING_REQUIREMENTS[@]} -eq 0 ]; then
        echo "✅ All requirements are met!"
    else
        echo "⚠️ The following dependencies are missing:"
        for req in "${MISSING_REQUIREMENTS[@]}"; do
            echo "   - $req"
        done
    fi
}

# Run requirements check before installing anything
check_requirements

# Install required system dependencies
echo "🔧 Installing system dependencies..."
$INSTALL_CMD python3 python3-pip python3-venv ansible

# Ensure virtual environment is set up correctly
if [ ! -d "venv" ]; then
    echo "⚙️ Creating a virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip inside the virtual environment
echo "🔄 Upgrading pip inside virtual environment..."
pip install --upgrade pip

# Install dependencies inside the virtual environment
echo "📦 Installing dependencies from requirements.txt..."
pip install -r requirements.txt


# Install PyQt6 system-wide if missing (ONLY via pip)
if ! python3 -c "import PyQt6" &> /dev/null; then
    echo "⚠️ PyQt6 is missing! Installing it globally via pip..."
    sudo pip3 install PyQt6
fi

# Activate or create a virtual environment
if [ -d "venv" ]; then
    echo "✅ Virtual environment found. Activating..."
    source venv/bin/activate
else
    echo "⚙️  Creating a virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Ensure requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found! Creating one with required dependencies..."
    echo -e "PyQt6\npyinstaller" > requirements.txt
fi

# Install dependencies inside the virtual environment
echo "📦 Installing dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# Ensure PyQt6 is installed inside the virtual environment
if ! python3 -c "import PyQt6" &> /dev/null; then
    echo "⚠️ PyQt6 is missing! Installing it inside the virtual environment..."
    pip install PyQt6
fi

# Install PyInstaller if missing
if ! command_exists pyinstaller; then
    echo "⚠️ PyInstaller is not installed! Installing..."
    pip install pyinstaller
fi

# Build the executable using PyInstaller
echo "🚀 Building $APP_NAME..."
pyinstaller --onefile --name "$APP_NAME" --windowed --noconsole \
  --hidden-import=PyYAML \
  --hidden-import=PyQt6.sip \
  --hidden-import=PyQt6.QtWidgets \
  --hidden-import=PyQt6.QtGui \
  --hidden-import=PyQt6.QtCore \
  main.py


# Deactivate virtual environment
deactivate

# Move the built executable to the Build directory
echo "📂 Moving the executable to Build directory..."
mv dist/"$APP_NAME" .

# Cleanup unnecessary files
echo "🧹 Cleaning up unnecessary files..."
rm -rf build dist "$APP_NAME".spec

echo "✅ Build complete! The '$APP_NAME' executable is ready to use."
