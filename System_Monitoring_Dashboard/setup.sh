#!/bin/bash

# Variables for easy customization
VENV_NAME="venv"
REQUIREMENTS_FILE="requirements.txt"
PYTHON_CMD="python3"
APP_SCRIPT="system_dashboard.py"

# ANSI color codes for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Display header
echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}    System Dashboard Setup Script   ${NC}"
echo -e "${BLUE}====================================${NC}"

# Check if Python is installed
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo -e "${RED}Error: $PYTHON_CMD is not installed. Please install Python first.${NC}"
    exit 1
fi

# Display Python version
echo -e "${BLUE}Using:${NC} $($PYTHON_CMD --version)"

# Check if venv folder exists
if [ -d "$VENV_NAME" ]; then
    echo -e "${GREEN}Virtual environment exists. Activating...${NC}"
else
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    $PYTHON_CMD -m venv $VENV_NAME
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment. Please install venv package.${NC}"
        echo -e "${YELLOW}Try: sudo apt-get install python3-venv (Ubuntu/Debian)${NC}"
        echo -e "${YELLOW}Try: sudo dnf install python3-virtualenv (Fedora)${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Virtual environment created successfully.${NC}"
fi

# Activate virtual environment
source $VENV_NAME/bin/activate

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to activate virtual environment.${NC}"
    exit 1
fi

echo -e "${GREEN}Virtual environment activated.${NC}"
echo -e "${BLUE}Using Python:${NC} $(python --version)"

# Check if requirements file exists
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo -e "${RED}Error: $REQUIREMENTS_FILE not found.${NC}"
    echo -e "${YELLOW}Please make sure it exists in the current directory.${NC}"
    deactivate
    exit 1
fi

# Install requirements
echo -e "${YELLOW}Installing requirements from $REQUIREMENTS_FILE...${NC}"
pip install -r $REQUIREMENTS_FILE

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install requirements.${NC}"
    deactivate
    exit 1
fi

echo -e "${GREEN}Requirements installed successfully.${NC}"

# Check if the app script exists
if [ ! -f "$APP_SCRIPT" ]; then
    echo -e "${YELLOW}Warning: $APP_SCRIPT not found.${NC}"
    echo -e "${YELLOW}Setup completed, but application script is missing.${NC}"
else
    echo -e "${GREEN}Setup completed successfully!${NC}"
    echo -e "${BLUE}You can now run the application with:${NC}"
    echo -e "    ${YELLOW}python $APP_SCRIPT${NC}"
fi

# Ask if the user wants to run the app now
if [ -f "$APP_SCRIPT" ]; then
    echo -e "${BLUE}Do you want to run the application now? (y/n)${NC}"
    read -r answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Starting application...${NC}"
        python $APP_SCRIPT
    else
        echo -e "${BLUE}You can run the application later with:${NC}"
        echo -e "    ${YELLOW}source $VENV_NAME/bin/activate${NC}"
        echo -e "    ${YELLOW}python $APP_SCRIPT${NC}"
    fi
fi

# Note: The script doesn't deactivate the virtual environment at the end
# so the user can run commands in the activated environment