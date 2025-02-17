#!/bin/bash

# Enable error handling
set -e

# Define project name
APP_NAME="CommandManager"

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

# Ask user for mode (Dry-Run or Direct Install)
echo "⚙️  Select an option:"
echo "1️⃣  Dry Run (Check requirements only)"
echo "2️⃣  Direct Install & Build"
read -p "Enter your choice (1 or 2): " USER_CHOICE

if [[ "$USER_CHOICE" == "1" ]]; then
    DRY_RUN=true
    echo "🔍 Running in Dry-Run mode..."
elif [[ "$USER_CHOICE" == "2" ]]; then
    DRY_RUN=false
    echo "📦 Running full installation & build..."
else
    echo "❌ Invalid option. Exiting."
    exit 1
fi

# Ensure system is updated (Only once at the start)
if [[ "$PKG_MANAGER" == "apt" && "$DRY_RUN" == false ]]; then
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

    if [ ${#MISSING_REQUIREMENTS[@]} -eq 0 ]; then
        echo "✅ All requirements are met!"
    else
        echo "⚠️ The following dependencies are missing:"
        for req in "${MISSING_REQUIREMENTS[@]}"; do
            echo "   - $req"
        done

        if $DRY_RUN; then
            echo "💡 Run the script again and select 'Direct Install' to install missing dependencies."
            exit 0
        fi
    fi
}

# Run requirements check before installing anything
check_requirements

# Install dependencies if not in dry-run mode
install_dependency() {
    local package="$1"
    local install_name="$2"

    if ! command_exists "$package"; then
        read -p "Do you want to install $install_name? (y/n): " INSTALL_CONFIRM
        if [[ "$INSTALL_CONFIRM" =~ ^[Yy]$ ]]; then
            echo "🔧 Installing $install_name..."
            $INSTALL_CMD "$install_name"  # ✅ Only install, no update
        else
            echo "❌ $install_name is required. Exiting."
            exit 1
        fi
    fi
}

if ! $DRY_RUN; then
    install_dependency python3 "Python3"
    install_dependency pip3 "python3-pip"
    install_dependency "python3-venv" "python3-venv"

    # Activate or create a virtual environment
    if [ -d "venv" ]; then
        echo "✅ Virtual environment found. Activating..."
        source venv/bin/activate
    else
        echo "⚙️  Creating a virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
    fi

    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        echo "❌ requirements.txt not found! Exiting."
        exit 1
    fi

    # Install dependencies
    echo "📦 Installing dependencies from requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt

    # Install PyInstaller if missing
    if ! command_exists pyinstaller; then
        echo "⚠️ PyInstaller is not installed!"
        read -p "Do you want to install PyInstaller? (y/n): " INSTALL_PYINSTALLER
        if [[ "$INSTALL_PYINSTALLER" =~ ^[Yy]$ ]]; then
            echo "🔧 Installing PyInstaller..."
            pip install pyinstaller
        else
            echo "❌ PyInstaller is required. Exiting."
            exit 1
        fi
    fi

    # Build the executable using PyInstaller
    echo "🚀 Building $APP_NAME..."
    pyinstaller --onefile --name "$APP_NAME" --windowed main.py

    # Deactivate virtual environment
    deactivate

    # Move the built executable to the Build directory
    echo "📂 Moving the executable to Build directory..."
    mv dist/"$APP_NAME" .

    # Cleanup unnecessary files
    echo "🧹 Cleaning up unnecessary files..."
    rm -rf build dist "$APP_NAME".spec

    echo "✅ Build complete! You can find '$APP_NAME' in the Build directory."
fi
