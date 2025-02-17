from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget, QComboBox, QLabel, QDialog, 
    QHBoxLayout, QInputDialog, QMessageBox, QFileDialog
)
from PyQt6.QtGui import QFont, QColor, QPalette
import sys
import os
import subprocess
import yaml

class FileEditor(QDialog):
    """A simple pop-up text editor for modifying playbooks and host files."""
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Editing: {os.path.basename(file_path)}")
        self.setGeometry(200, 200, 600, 500)
        self.file_path = file_path

        layout = QVBoxLayout()

        self.text_editor = QTextEdit(self)
        self.text_editor.setFont(QFont("Consolas", 12))
        self.text_editor.setStyleSheet("background-color: #2b2b2b; color: #dddddd;")

        # Load file content
        self.load_file()

        # Save button
        self.save_button = QPushButton("Save Changes", self)
        self.save_button.setFont(QFont("Arial", 12))
        self.save_button.clicked.connect(self.save_file)

        layout.addWidget(self.text_editor)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

    def load_file(self):
        """Loads the file content into the text editor."""
        with open(self.file_path, "r") as file:
            content = file.read()
            self.text_editor.setText(content)

    def save_file(self):
        """Saves the modified content back to the file, validating YAML or INI format if needed."""
        content = self.text_editor.toPlainText()

        # Validate YAML syntax if it's a playbook
        if self.file_path.endswith((".yml", ".yaml")):
            try:
                yaml.safe_load(content)  # Check for syntax errors
            except yaml.YAMLError as e:
                self.text_editor.setText(content + f"\n\nERROR: Invalid YAML syntax!\n{e}")
                return  # Don't save if YAML is invalid

        # Save changes
        with open(self.file_path, "w") as file:
            file.write(content)
        self.accept()  # Close editor on successful save


class AnsibleRemoteController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ansible Remote Controller")
        self.setGeometry(100, 100, 900, 700)

        self.playbook_dir = "playbooks"
        self.hosts_dir = "hosts"

        self.initUI()
        self.load_playbooks()
        self.load_hosts()
        self.apply_dark_theme()


    def initUI(self):
        layout = QVBoxLayout()

        # ✅ Header Section (Hostname & Ansible Status)
        self.header_label = QLabel("")
        self.header_label.setFont(QFont("Arial", 14))
        self.update_header()  # Calls a function to populate this

        # ✅ Enhanced Terminal Output (More Appealing)
        self.output_display = QTextEdit(self)
        self.output_display.setPlaceholderText("Ansible output will appear here...")
        self.output_display.setReadOnly(True)
        self.output_display.setFont(QFont("Consolas", 12))
        self.output_display.setStyleSheet("""
            background-color: #1e1e1e;  /* Dark Gray */
            color: #00ff00;             /* Bright Green Text */
            border: 2px solid #444;     /* Subtle Border */
            padding: 8px;               /* Inner Spacing */
            border-radius: 6px;         /* Rounded Corners */
        """)


        # ✅ Playbook Selection & Actions
        self.playbook_label = QLabel("Select Playbook:")
        self.playbook_combo = QComboBox(self)
        self.playbook_combo.setFont(QFont("Arial", 12))

        self.new_playbook_button = QPushButton("New Playbook", self)
        self.new_playbook_button.setFont(QFont("Arial", 12))
        self.new_playbook_button.setStyleSheet("background-color: #007acc; color: white;")
        self.new_playbook_button.clicked.connect(self.new_playbook)

        self.edit_playbook_button = QPushButton("Edit Playbook", self)
        self.edit_playbook_button.setFont(QFont("Arial", 12))
        self.edit_playbook_button.setStyleSheet("background-color: #ffa500; color: black;")
        self.edit_playbook_button.clicked.connect(self.edit_selected_playbook)

        self.upload_playbook_button = QPushButton("Upload Playbook", self)
        self.upload_playbook_button.setFont(QFont("Arial", 12))
        self.upload_playbook_button.setStyleSheet("background-color: #6a5acd; color: white;")  # Purple button
        self.upload_playbook_button.clicked.connect(self.upload_playbook)

        self.delete_playbook_button = QPushButton("Delete Playbook", self)
        self.delete_playbook_button.setFont(QFont("Arial", 12))
        self.delete_playbook_button.setStyleSheet("background-color: #ff6347; color: white;")  # Red button
        self.delete_playbook_button.clicked.connect(self.delete_selected_playbook)

        # ✅ Host Selection & Actions
        self.host_label = QLabel("Select Host Inventory:")
        self.host_combo = QComboBox(self)
        self.host_combo.setFont(QFont("Arial", 12))

        self.new_host_button = QPushButton("New Host", self)
        self.new_host_button.setFont(QFont("Arial", 12))
        self.new_host_button.setStyleSheet("background-color: #007acc; color: white;")
        self.new_host_button.clicked.connect(self.new_host)

        self.edit_host_button = QPushButton("Edit Host File", self)
        self.edit_host_button.setFont(QFont("Arial", 12))
        self.edit_host_button.setStyleSheet("background-color: #ffa500; color: black;")
        self.edit_host_button.clicked.connect(self.edit_selected_host)

        self.delete_host_button = QPushButton("Delete Host", self)
        self.delete_host_button.setFont(QFont("Arial", 12))
        self.delete_host_button.setStyleSheet("background-color: #ff6347; color: white;")  # Red button
        self.delete_host_button.clicked.connect(self.delete_selected_host)

        # ✅ Run Playbook Button (Always at the Bottom)
        self.run_button = QPushButton("Run Playbook", self)
        self.run_button.setFont(QFont("Arial", 14))
        self.run_button.setStyleSheet("background-color: #32cd32; color: black;")
        self.run_button.clicked.connect(self.run_playbook)

        # ✅ Add widgets to layout (Organized Correctly)
        layout.addWidget(self.header_label)
        layout.addWidget(self.output_display)

        # Playbook Section
        layout.addWidget(self.playbook_label)
        layout.addWidget(self.playbook_combo)
        layout.addWidget(self.new_playbook_button)
        layout.addWidget(self.edit_playbook_button)
        layout.addWidget(self.upload_playbook_button)
        layout.addWidget(self.delete_playbook_button)  # ✅ Delete button is grouped with playbook buttons

        # Host Section
        layout.addWidget(self.host_label)
        layout.addWidget(self.host_combo)
        layout.addWidget(self.new_host_button)
        layout.addWidget(self.edit_host_button)
        layout.addWidget(self.delete_host_button)  # ✅ Delete button is grouped with host buttons

        # Run Button (Always Last)
        layout.addWidget(self.run_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)



    def update_header(self):
        """Enhances the header with concise system and Ansible details."""
        hostname = subprocess.getoutput("hostname")
        os_info = subprocess.getoutput("lsb_release -d | cut -f2")  # Get OS Name
        kernel_version = subprocess.getoutput("uname -r")  # Get Linux Kernel
        ansible_output = subprocess.getoutput("ansible --version | head -n 1").split()

        if len(ansible_output) < 3:
            ansible_version = "N/A"
        else:
            ansible_version = ansible_output[2]  # Get Ansible version safely


        # ✅ Compact Header Format
        header_text = f"<b>Host:</b> {hostname} | <b>OS:</b> {os_info} | <b>Kernel:</b> {kernel_version} | <b>Ansible:</b> {ansible_version}"

        self.header_label.setText(header_text)


    def new_host(self):
        """Prompts user to enter a new host and saves it to hosts.ini"""
        host_name, ok = QInputDialog.getText(self, "New Host", "Enter host name or IP:")
        if not ok or not host_name.strip():
            return

        ansible_user, ok = QInputDialog.getText(self, "Ansible User", "Enter the Ansible user:")
        if not ok or not ansible_user.strip():
            return

        connection_type, ok = QInputDialog.getItem(self, "Connection Type", "Select connection type:",
                                                ["ssh", "local"], 0, False)
        if not ok:
            return

        # Save to hosts.ini
        host_path = os.path.join(self.hosts_dir, "hosts.ini")
        with open(host_path, "a") as f:
            f.write(f"\n[{host_name}]\n{host_name} ansible_user={ansible_user} ansible_connection={connection_type}\n")

        QMessageBox.information(self, "Success", f"Host {host_name} added successfully!")

        # Refresh dropdown
        self.load_hosts()


    def new_playbook(self):
        """Creates a new playbook file and opens it in the editor."""
        playbook_name, ok = QInputDialog.getText(self, "New Playbook", "Enter playbook name (without extension):")
        if not ok or not playbook_name.strip():
            return

        playbook_file = f"{playbook_name}.yml"
        file_path = os.path.join(self.playbook_dir, playbook_file)

        # ✅ Ensure the playbook directory exists
        if not os.path.exists(self.playbook_dir):
            os.makedirs(self.playbook_dir)

        # ✅ Create an empty file if it doesn't exist
        if not os.path.exists(file_path):
            with open(file_path, "w") as file:
                file.write("# New Ansible Playbook\n\n- name: Example Task\n  hosts: all\n  tasks:\n    - debug: msg='Hello, Ansible!'\n")

        # ✅ Open the editor
        editor = FileEditor(file_path, self)
        editor.exec()

        # ✅ Refresh dropdown after saving
        self.load_playbooks()


    def edit_selected_playbook(self):
        """Opens the selected playbook in the built-in editor."""
        selected_playbook = self.playbook_combo.currentText()
        if not selected_playbook:
            QMessageBox.warning(self, "No Playbook Selected", "Please select a playbook to edit.")
            return

        file_path = os.path.join(self.playbook_dir, selected_playbook)
        editor = FileEditor(file_path, self)
        editor.exec()


    def edit_selected_host(self):
        """Opens the selected host file in the built-in editor."""
        selected_host = self.host_combo.currentText()
        if not selected_host:
            QMessageBox.warning(self, "No Host Selected", "Please select a host file to edit.")
            return

        file_path = os.path.join(self.hosts_dir, selected_host)
        editor = FileEditor(file_path, self)
        editor.exec()


    def run_playbook(self):
        """Executes the selected Ansible playbook and displays the output."""
        selected_playbook = self.playbook_combo.currentText()
        selected_host = self.host_combo.currentText()

        if not selected_playbook or not selected_host:
            self.output_display.setText("Please select a playbook and a host inventory file before running.")
            return

        playbook_path = os.path.join(self.playbook_dir, selected_playbook)
        host_path = os.path.join(self.hosts_dir, selected_host)

        command = ["ansible-playbook", "-i", host_path, playbook_path]

        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            
            if stdout:
                self.output_display.setText(stdout)
            if stderr:
                self.output_display.append("\nERRORS:\n" + stderr)

        except Exception as e:
            self.output_display.setText(f"Error running playbook: {str(e)}")
    

    def load_playbooks(self):
        """Loads available playbooks into the dropdown menu."""
        if not os.path.exists(self.playbook_dir):
            os.makedirs(self.playbook_dir)

        playbooks = [f for f in os.listdir(self.playbook_dir) if f.endswith(('.yml', '.yaml'))]
        self.playbook_combo.clear()
        self.playbook_combo.addItems(playbooks)


    def load_hosts(self):
        """Loads available inventory files into the dropdown menu."""
        if not os.path.exists(self.hosts_dir):
            os.makedirs(self.hosts_dir)

        hosts = [f for f in os.listdir(self.hosts_dir) if f.endswith('.ini')]
        self.host_combo.clear()
        self.host_combo.addItems(hosts)


    def apply_dark_theme(self):
        """Applies a dark mode theme to the application."""
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#121212"))  # Dark background
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff"))  # White text
        palette.setColor(QPalette.ColorRole.Base, QColor("#2b2b2b"))  # Text background
        palette.setColor(QPalette.ColorRole.Text, QColor("#ffffff"))  # White text
        palette.setColor(QPalette.ColorRole.Button, QColor("#444444"))  # Dark buttons
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#ffffff"))  # Button text
        self.setPalette(palette)



    def upload_playbook(self):
        """Allows the user to upload an existing playbook."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Playbook", "", "YAML Files (*.yml *.yaml)")

        if not file_path:
            return  # User canceled the file selection

        # Ensure playbooks directory exists
        if not os.path.exists(self.playbook_dir):
            os.makedirs(self.playbook_dir)

        # Get the filename from the full path
        playbook_filename = os.path.basename(file_path)
        destination_path = os.path.join(self.playbook_dir, playbook_filename)

        # Copy the file to the playbooks directory
        with open(file_path, "r") as source, open(destination_path, "w") as dest:
            dest.write(source.read())

        self.output_display.setText(f"Playbook uploaded: {playbook_filename}")

        # Refresh dropdown to show the newly uploaded playbook
        self.load_playbooks()


    def delete_selected_playbook(self):
        """Deletes the selected playbook after confirmation."""
        selected_playbook = self.playbook_combo.currentText()
        if not selected_playbook:
            QMessageBox.warning(self, "No Playbook Selected", "Please select a playbook to delete.")
            return

        playbook_path = os.path.join(self.playbook_dir, selected_playbook)

        if not os.path.exists(playbook_path):  # ✅ Check before deleting
            QMessageBox.warning(self, "File Not Found", "The selected playbook does not exist.")
            return

        confirmation = QMessageBox.question(
            self, "Delete Playbook",
            f"Are you sure you want to delete '{selected_playbook}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirmation == QMessageBox.StandardButton.Yes:
            try:
                os.remove(playbook_path)
                self.output_display.setText(f"Deleted playbook: {selected_playbook}")
                self.load_playbooks()  # Refresh dropdown
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete playbook: {str(e)}")



    def delete_selected_host(self):
        """Deletes the selected host file after confirmation."""
        selected_host = self.host_combo.currentText()
        if not selected_host:
            QMessageBox.warning(self, "No Host Selected", "Please select a host file to delete.")
            return

        host_path = os.path.join(self.hosts_dir, selected_host)

        if not os.path.exists(host_path):  # ✅ Prevent FileNotFoundError
            QMessageBox.warning(self, "File Not Found", "The selected host file does not exist.")
            return

        confirmation = QMessageBox.question(
            self, "Delete Host",
            f"Are you sure you want to delete '{selected_host}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirmation == QMessageBox.StandardButton.Yes:
            try:
                os.remove(host_path)
                self.output_display.setText(f"Deleted host file: {selected_host}")
                self.load_hosts()  # Refresh dropdown
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete host file: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AnsibleRemoteController()
    window.show()
    sys.exit(app.exec())
