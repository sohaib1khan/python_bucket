import sys
import requests
import json
import random
import keyring  # Import keyring to manage credentials
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, QLineEdit, QInputDialog)
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QTextCursor
from PyQt6.QtCore import QTimer, Qt  # ✅ Import Qt

SERVICE_NAME = "UniFiDashboard"  # Unique identifier for keyring

# UniFi Controller Details
UNIFI_HOST = "https://192.168.1.1:8443" # Change to your UniFi Controller IP
SITE = "default"  # Change if needed
VERIFY_SSL = False  # Set to True if using valid SSL certs

requests.packages.urllib3.disable_warnings()

class UniFiDashboard(QWidget):
 
    # 🛠️ Add a constructor to initialize the class
    def __init__(self):
        super().__init__()
        self.username = ""
        self.password = ""
        self.session = None  # Stores the session after login
        self.initUI()  # 🛠️ Add this line to initialize the UI properly
 
    # 🛠️ Add the update_header method to update the header label
    def update_header(self):
        """ Updates the header with the UniFi Controller connection status. """
        if self.session:
            self.header_label.setText(f"Connected to UniFi at {UNIFI_HOST}")
            self.header_label.setStyleSheet("color: #00ff00;")  # Green when connected
        else:
            self.header_label.setText("UniFi Controller: Not Connected")
            self.header_label.setStyleSheet("color: red;")  # Red when not connected


    # 🛠️ Add the initUI method to initialize the UI
    def initUI(self):
        self.setWindowTitle("UniFi Network Dashboard")
        self.setGeometry(100, 100, 700, 500)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

        layout = QVBoxLayout()

        self.header_label = QLabel("UniFi Controller: Not Connected", self)
        self.header_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.header_label.setStyleSheet("color: #00ff00;")
        layout.addWidget(self.header_label)

        self.update_header() 


        self.device_output = QTextEdit(self)
        self.device_output.setReadOnly(True)
        self.device_output.setStyleSheet("background-color: black; color: white; font-size: 14px;")
        layout.addWidget(self.device_output)


        self.fetch_button = QPushButton("Fetch Devices", self)
        self.fetch_button.setStyleSheet("background-color: #007acc; color: white; font-size: 14px;")
        self.fetch_button.clicked.connect(self.fetch_devices)
        layout.addWidget(self.fetch_button)

        self.live_button = QPushButton("View Live Network", self)
        self.live_button.setStyleSheet("background-color: #d9534f; color: white; font-size: 14px;")
        self.live_button.clicked.connect(self.view_live_network)
        layout.addWidget(self.live_button)

        self.clear_button = QPushButton("Clear Output", self)
        self.clear_button.setStyleSheet("background-color: #666; color: white; font-size: 14px;")
        self.clear_button.clicked.connect(self.clear_output)
        layout.addWidget(self.clear_button)

        # 🛠️ Add a footer label
        self.footer_label = QLabel("📡 UniFi Network Dashboard | Status: Idle", self)
        self.footer_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.footer_label.setStyleSheet("color: lightgray;")
        layout.addWidget(self.footer_label, alignment=Qt.AlignmentFlag.AlignCenter)


        self.setLayout(layout)

        # 🛠️ Start an idle animation when the output is empty
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self.animate_idle)
        self.idle_timer.start(1000)  # Runs every 1 second


    # 🛠️ Add the prompt_credentials method to retrieve stored credentials
    def prompt_credentials(self):
        """Retrieves stored credentials if available, otherwise prompts the user."""
        stored_username = keyring.get_password(SERVICE_NAME, "username")
        stored_password = keyring.get_password(SERVICE_NAME, "password")

        if stored_username and stored_password:
            self.username = stored_username
            self.password = stored_password
            return True  # Use cached credentials

        # Prompt the user if no stored credentials exist
        self.username, ok = QInputDialog.getText(self, "Login", "Enter UniFi Username:")
        if not ok:
            return False

        self.password, ok = QInputDialog.getText(self, "Login", "Enter UniFi Password:", QLineEdit.EchoMode.Password)
        if not ok:
            return False

        # Save credentials securely
        keyring.set_password(SERVICE_NAME, "username", self.username)
        keyring.set_password(SERVICE_NAME, "password", self.password)

        return True

    
    def animate_idle(self):
        """Show subtle animation when idle."""
        if self.device_output.toPlainText().strip() == "":  # If output is empty
            idle_texts = ["🟢 Waiting.", "🟢 Waiting..", "🟢 Waiting..."]
            self.device_output.setText(random.choice(idle_texts))  # Randomly choose an animation




    # 🛠️ Add the login method to authenticate with the UniFi Controller
    def login(self):
        # If we already have a session, reuse it
        if self.session:
            return self.session
        
        if not self.username or not self.password:  # Only prompt if no credentials exist
            if not self.prompt_credentials():
                return None


        session = requests.Session()
        login_payload = {"username": self.username, "password": self.password}
        login_url = f"{UNIFI_HOST}/api/login"

        response = session.post(login_url, json=login_payload, verify=VERIFY_SSL)
        if response.status_code == 200:
            self.session = session  # Store session for future use
            self.update_header()  # 🛠️ Update header after successful login
            self.footer_label.setText("✅ Login successful. Ready to fetch devices.")
            return session

        else:
            self.session = None
            self.footer_label.setText("❌ Login failed. Check credentials.")
            return None


    def fetch_devices(self):
        session = self.login()
        if not self.session:
            self.session = self.login()
        if not self.session:
            self.device_output.setText("Failed to login. Check credentials.")
            return


        devices_url = f"{UNIFI_HOST}/api/s/{SITE}/stat/sta"
        response = session.get(devices_url, verify=VERIFY_SSL)

        if response.status_code == 200:
            devices = response.json()["data"]
            self.device_output.clear()
            cursor = self.device_output.textCursor()
            
            for device in devices:
                color = QColor(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                fmt = QTextCharFormat()
                fmt.setForeground(color)
                cursor.setCharFormat(fmt)
                cursor.insertText(f"Device: {device.get('hostname', 'Unknown')}\n")
                cursor.insertText(f"  MAC Address: {device['mac']}\n")
                cursor.insertText(f"  IP Address: {device.get('ip', 'N/A')}\n")
                cursor.insertText(f"  Connected to: {device.get('essid', 'Wired')}\n")
                cursor.insertText(f"  Signal Strength: {device.get('signal', 'N/A')} dBm\n")
                cursor.insertText(f"  Device Type: {device.get('oui', 'Unknown')}\n")
                cursor.insertText("=" * 40 + "\n")
        else:
            self.device_output.setText("Failed to retrieve devices.")
            self.footer_label.setText("❌ Device fetch failed. Check login or network.")


    def view_live_network(self):
        """Fetch and display the top 5 devices consuming the most bandwidth."""
        if not self.session:
            self.session = self.login()
        if not self.session:
            self.device_output.setText("Failed to login. Check credentials.")
            return

        devices_url = f"{UNIFI_HOST}/api/s/{SITE}/stat/sta"
        response = self.session.get(devices_url, verify=VERIFY_SSL)

        devices = []  # Initialize devices variable
        if response.status_code == 200:
            devices = response.json()["data"]
            self.footer_label.setText(f"✅ {len(devices)} devices fetched successfully.")

            # Sort devices by total data usage (download + upload)
            sorted_devices = sorted(devices, key=lambda x: x.get("tx_bytes", 0) + x.get("rx_bytes", 0), reverse=True)

            self.device_output.clear()
            cursor = self.device_output.textCursor()

            top_devices = sorted_devices[:5]  # Get the top 5 bandwidth users
            cursor.insertText("[+] Top 5 Bandwidth-Consuming Devices:\n\n")

            for device in top_devices:
                color = QColor(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                fmt = QTextCharFormat()
                fmt.setForeground(color)
                cursor.setCharFormat(fmt)
                cursor.insertText(f"Device: {device.get('hostname', 'Unknown')}\n")
                cursor.insertText(f"  MAC Address: {device['mac']}\n")
                cursor.insertText(f"  IP Address: {device.get('ip', 'N/A')}\n")
                cursor.insertText(f"  SSID: {device.get('essid', 'Wired')}\n")
                cursor.insertText(f"  Connection Type: {'Wireless' if 'essid' in device else 'Wired'}\n")
                cursor.insertText(f"  Data Downloaded: {device.get('rx_bytes', 0) / 1e6:.2f} MB\n")
                cursor.insertText(f"  Data Uploaded: {device.get('tx_bytes', 0) / 1e6:.2f} MB\n")
                cursor.insertText("=" * 40 + "\n")
        else:
            self.device_output.setText("Failed to retrieve network data.")
            self.footer_label.setText("❌ Device fetch failed. Check login or network.")


    # 🛠️ Add the clear_output method to clear the device output


    def clear_output(self):
        """Animate clearing the output screen with a loading effect and update footer."""
        self.footer_label.setText("🟡 Clearing output...")
        self.device_output.setText("🟡 Clearing...")  # Initial text
        self.device_output.setStyleSheet("color: yellow;")  # Change text color to yellow

        messages = ["🟡 Clearing...", "🟡 Clearing..", "🟡 Clearing.", "✅ Cleared!"]
        index = 0

        def update_text():
            nonlocal index
            if index < len(messages):
                self.device_output.setText(messages[index])
                index += 1
                QTimer.singleShot(300, update_text)  # Delay each step by 300ms
            else:
                self.device_output.clear()  # Fully clear after animation
                self.device_output.setStyleSheet("color: white;")  # Reset text color
                self.footer_label.setText("✅ Output Cleared. Ready for new data.")  # Update footer

        update_text()  # Start animation




# 🛠️ Add the main block to create the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = UniFiDashboard()
    dashboard.show()
    sys.exit(app.exec())
