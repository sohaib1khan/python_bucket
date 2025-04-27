# System Monitoring Dashboard

A comprehensive system monitoring dashboard that provides real-time information about your system's performance and resource usage.

## Features

- **System Overview**: CPU usage, memory usage, and system information
- **Process Management**: View and manage running processes
- **Network Monitoring**: Real-time network traffic visualization and connection tracking
- **Disk Analysis**: Disk usage statistics, I/O monitoring, and directory size analysis
- **Temperature & Battery**: Monitor system temperature and battery status (if available)
- **System Logging**: Track system events and resource usage warnings

## Installation & Setup

### Automatic Setup (Linux/macOS)

Use the included setup script to automatically create a virtual environment and install dependencies:

1. Make the setup script executable:
   ```bash
   chmod +x setup.sh
   ```

2. Run the setup script:
   ```bash
   ./setup.sh
   ```

The script will:
- Check if a virtual environment exists and create one if needed
- Activate the virtual environment
- Install the required dependencies
- Offer to run the application immediately

### Manual Setup

1. Make sure you have Python 3.7+ installed
2. Create a virtual environment and activate it:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

After setup, you can run the application with:
```bash
python system_dashboard.py
```

If you've closed your terminal, first activate the virtual environment:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## Creating a Portable Application

You can create a standalone executable using PyInstaller:

1. Install PyInstaller in your virtual environment:
   ```bash
   pip install pyinstaller
   ```

2. Create a single-file executable:
   ```bash
   pyinstaller --onefile --windowed --name="SystemMonitor" system_dashboard.py
   ```

For a more customized build:

```bash
pyinstaller --onefile --windowed --icon=app_icon.ico --name="SystemMonitor" --hidden-import=matplotlib --hidden-import=tkinter system_dashboard.py
```

The executable will be created in the `dist` directory and can be run on systems with similar OS versions without needing Python installed.

### Advanced PyInstaller Usage

For more control over the build process:

1. Generate a spec file:
   ```bash
   pyi-makespec --onefile --windowed system_dashboard.py
   ```

2. Edit the spec file to include any additional resources

3. Build from the spec file:
   ```bash
   pyinstaller system_dashboard.spec
   ```

## Project Structure

- `system_dashboard.py` - The main application
- `requirements.txt` - Required Python packages
- `setup.sh` - Setup script for automatic installation and environment setup
- `README.md` - This file

## Tabs

The dashboard includes multiple tabs for different monitoring purposes:

1. **Overview**: General system information with CPU and memory graphs
2. **Processes**: List of running processes with the ability to view details or terminate them
3. **Network**: Network traffic monitoring and active connection listing
4. **Disk**: Disk usage, I/O statistics, and directory size analysis

## Requirements

- Python 3.7+
- psutil
- matplotlib
- tkinter (usually included with Python)

## Platform Compatibility

- Works on Windows, macOS, and Linux
- Some features like CPU temperature may be limited on certain platforms
- Administrator/root privileges may be required for certain features

## Troubleshooting

If you encounter issues with tkinter, make sure it's installed on your system:

- Ubuntu/Debian: `sudo apt-get install python3-tk`
- Fedora: `sudo dnf install python3-tkinter`
- Arch Linux: `sudo pacman -S tk`
- macOS (with Homebrew): `brew install python-tk`
- Windows: Tkinter is included with standard Python installations