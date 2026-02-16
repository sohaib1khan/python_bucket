# UniFi Network Dashboard

A **simple, interactive** UniFi network dashboard that allows users to **fetch** connected devices, view **live network activity**, and manage UniFi Controller access with a **GUI interface**.

## Requirements
Ensure you have the following installed before running the application:

- **Python** (Version 3.x)
- **pip** (Python package manager)

Required Python dependencies:

```
requests
PyQt6
keyring
pyinstaller
```

## Setup & Installation
1. **Be in the directory** where the project files (`main.py`, `build.sh`, `requirements.txt`) are located.
2. **Install required dependencies** by running:

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:

   ```bash
   python main.py
   ```

## Features
- **Fetch Connected Devices** → Displays all devices connected to the UniFi network.
- **View Live Network Traffic** → See top bandwidth-consuming devices.
- **Secure Credential Storage** → Uses `keyring` for safe authentication.
- **Dark-Themed UI** → Eye-friendly interface with status indicators.
- **Footer Status Updates** → Shows live feedback during operations.

## Building an Executable
To package the application into an executable:

```bash
bash build.sh
```

This will generate a standalone executable that does **not** require Python to run.

## Notes
- The script will prompt for **UniFi Controller IP** on first launch.
- Login credentials are stored securely using `keyring`.
- **Clearing output triggers an animation** for better user experience.

Enjoy managing your **UniFi Network** efficiently! 🚀

