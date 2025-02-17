import os
import sys
import json
import subprocess
import socket  

from PyQt6.QtCore import Qt, QStringListModel  
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QTextEdit, 
    QLabel, QInputDialog, QMessageBox, QSpacerItem, QSizePolicy, QCompleter, QLineEdit
)

# Define JSON file path
COMMANDS_FILE = "commands.json"

# Load commands from JSON
def load_json():
    try:
        with open(COMMANDS_FILE, "r", encoding="utf-8") as file:
            return json.load(file).get("commands", [])
    except FileNotFoundError:
        return []

# Class to manage CMD Manager App
class CMDManagerApp(QWidget):
    def __init__(self):
        super().__init__()

        # Set window title and size
        self.setWindowTitle("CommandDock")
        self.setGeometry(200, 200, 600, 500)
        self.current_directory = os.getcwd()

        # Apply dark mode theme
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#1E1E1E"))  # Soft black background
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#DADADA"))  # Light grey text
        palette.setColor(QPalette.ColorRole.Button, QColor("#2E2E2E"))  # Dark grey buttons
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#F0F0F0"))  # Bright button text
        palette.setColor(QPalette.ColorRole.Base, QColor("#292929"))  # Output box background
        palette.setColor(QPalette.ColorRole.Text, QColor("#FFFFFF"))  # Output box text color
        self.setPalette(palette)

        # Set font
        font = QFont("Arial", 12)
        self.setFont(font)

        # Layout
        layout = QVBoxLayout()


        # Header: Welcome with hostname
        hostname = socket.gethostname()
        self.header_label = QLabel(f"Welcome, {hostname}!")
        self.header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center it
        layout.addWidget(self.header_label)

        # Label
        self.label = QLabel("Saved Commands")
        self.label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(self.label)

        # Command List
        self.command_list = QListWidget()
        self.command_list.setFont(QFont("Arial", 12))
        layout.addWidget(self.command_list)

        # Terminal Output Box (With Word Wrapping)
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setFont(QFont("Courier", 12))
        self.output_box.setStyleSheet("background-color: black; color: green;")
        self.output_box.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)  # Enable word wrapping

        # Command Input Box (Now using QLineEdit for better autocompletion)
        self.command_input = QLineEdit()
        self.command_input.setFont(QFont("Courier", 12))
        self.command_input.setStyleSheet("background-color: black; color: white; padding: 5px;")
        self.command_input.setPlaceholderText("Type a command and press Enter...")
        self.command_input.returnPressed.connect(self.process_enter_key)  # Capture Enter key

        # Autocomplete Setup (Moved Before `self.load_commands()`)
        self.completer = QCompleter([], self)  # Start with an empty list
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.command_input.setCompleter(self.completer)  # Attach completer to input

        # Load commands (Must come after `self.completer`)
        self.load_commands()

        # Clear Terminal Button
        self.clear_button = QPushButton("🧹 Clear Terminal")
        self.clear_button.clicked.connect(self.clear_terminal)

        # Interactive Selection Box (For Selectable Items)
        self.selection_box = QListWidget()
        self.selection_box.setFont(QFont("Courier", 12))
        self.selection_box.setStyleSheet("background-color: black; color: cyan;")  # Blue highlight
        self.selection_box.itemActivated.connect(self.select_item)  # Trigger selection when Enter is pressed
        self.selection_box.hide()  # Hide by default

        # Layout Order
        layout.addWidget(self.output_box)  # Terminal output
        layout.addWidget(self.command_input)  # User input box
        layout.addWidget(self.clear_button)  # Clear button
        layout.addWidget(self.selection_box)

        # Buttons
        self.add_button = QPushButton("➕ Add Command")
        self.edit_button = QPushButton("✏️ Edit Command")
        self.delete_button = QPushButton("🗑️ Delete Command")
        self.run_button = QPushButton("▶️ Run Command")

        # Connect buttons to functions
        self.add_button.clicked.connect(self.add_command)
        self.edit_button.clicked.connect(self.edit_command)
        self.delete_button.clicked.connect(self.delete_command)
        self.run_button.clicked.connect(self.run_command)

        # Add buttons to layout
        layout.addWidget(self.run_button)
        layout.addWidget(self.add_button)
        layout.addWidget(self.edit_button)
        layout.addWidget(self.delete_button)

        # Spacer
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Footer: Maintainer info
        self.footer_label = QLabel("Maintained by Sohaib 🛠️💻🚀")
        self.footer_label.setFont(QFont("Arial", 10))  # Slightly smaller font
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center it
        layout.addWidget(self.footer_label)
        self.setLayout(layout)

    # Function to load commands
    def load_commands(self):
        """Load commands into the list widget."""
        self.command_list.clear()
        commands = load_json()
        self.update_autocomplete()  # Update autocomplete when loading commands

        for cmd in commands:
            self.command_list.addItem(f"{cmd['name']} - {cmd['command']}")

    # Function to get system commands
    def get_system_commands(self):
        """Retrieve all available system commands from $PATH."""
        import os 

        system_commands = set()
        for path in os.getenv("PATH", "").split(":"):
            if os.path.isdir(path):
                system_commands.update(os.listdir(path))  # Get executable names
        return sorted(system_commands)


    # Function to update autocomplete
    def update_autocomplete(self):
        """Combine saved commands with system commands for autocomplete."""
        saved_commands = [cmd["command"] for cmd in load_json()]  # Extract saved commands
        system_commands = self.get_system_commands()  # Fetch system-wide commands

        # Merge both command lists
        all_commands = sorted(set(saved_commands + system_commands))  
        self.completer.setModel(QStringListModel(all_commands, self))  


    # Function to add a new command
    def add_command(self):
        """Show dialog to add a new command and save it to JSON."""
        name, ok1 = QInputDialog.getText(self, "Add Command", "Enter command name:")
        if not ok1 or not name.strip():  # If user cancels or enters nothing
            return

        command, ok2 = QInputDialog.getText(self, "Add Command", "Enter actual command:")
        if not ok2 or not command.strip():
            return

        description, ok3 = QInputDialog.getText(self, "Add Command", "Enter command description:")
        if not ok3:
            return

        # Load current data
        data = load_json()
        data.append({"name": name.strip(), "command": command.strip(), "description": description.strip()})

        # Save back to JSON
        with open(COMMANDS_FILE, "w", encoding="utf-8") as file:
            json.dump({"commands": data}, file, indent=4)

        # Refresh UI
        self.load_commands()

        # Show confirmation
        QMessageBox.information(self, "Success", f"Command '{name}' added successfully! 🎉")


    # Function to edit a command
    def edit_command(self):
        """Allow the user to edit an existing command."""
        selected_item = self.command_list.currentRow()
        if selected_item == -1:  # No selection
            QMessageBox.warning(self, "Warning", "Please select a command to edit!")
            return

        # Load current commands
        data = load_json()

        # Get selected command details
        command = data[selected_item]

        # Ask for new values (keep old values if left empty)
        new_name, ok1 = QInputDialog.getText(self, "Edit Command", "Edit name:", text=command["name"])
        if not ok1: return

        new_cmd, ok2 = QInputDialog.getText(self, "Edit Command", "Edit command:", text=command["command"])
        if not ok2: return

        new_desc, ok3 = QInputDialog.getText(self, "Edit Command", "Edit description:", text=command["description"])
        if not ok3: return

        # Update values
        data[selected_item] = {"name": new_name, "command": new_cmd, "description": new_desc}

        # Save back to JSON
        with open(COMMANDS_FILE, "w", encoding="utf-8") as file:
            json.dump({"commands": data}, file, indent=4)

        # Refresh UI
        self.load_commands()

        # Show confirmation
        QMessageBox.information(self, "Success", f"Command '{new_name}' updated successfully! 🎉")

    
    # Function to delete a command
    def delete_command(self):
        """Delete the selected command after confirmation."""
        selected_item = self.command_list.currentRow()
        if selected_item == -1:  # No selection
            QMessageBox.warning(self, "Warning", "Please select a command to delete!")
            return

        # Load current commands
        data = load_json()

        # Get selected command details
        command = data[selected_item]
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete '{command['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirm == QMessageBox.StandardButton.No:
            return

        # Remove selected command
        del data[selected_item]

        # Save back to JSON
        with open(COMMANDS_FILE, "w", encoding="utf-8") as file:
            json.dump({"commands": data}, file, indent=4)

        # Refresh UI
        self.load_commands()

        # Show confirmation
        QMessageBox.information(self, "Success", f"Command '{command['name']}' deleted successfully! 🚮")


    # Function to run the selected command
    def run_command(self, custom_command=None):
        """Run the selected or user-entered command and show live output in the terminal."""
        if custom_command:
            command = custom_command.strip()  # Use typed command
        else:
            selected_item = self.command_list.currentRow()
            if selected_item == -1:
                QMessageBox.warning(self, "Warning", "Please select a command to run or type one below!")
                return
            data = load_json()
            command = data[selected_item]["command"].strip()

        # Handle "cd" commands manually
        if command.startswith("cd "):
            new_dir = command[3:].strip()  # Extract directory name
            if new_dir == "~":
                self.current_directory = os.path.expanduser("~")  # Go home
            elif os.path.isdir(new_dir):
                self.current_directory = os.path.abspath(new_dir)  # Change directory
            else:
                self.output_box.append(f"❌ Directory not found: {new_dir}")
                return
            self.output_box.append(f"📂 Changed directory to: {self.current_directory}")
            return

        try:
            self.output_box.append(f"\n$ {command}")  
            self.output_box.append("-" * 50)

            # Run command in the current working directory
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=self.current_directory)

            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                self.output_box.append(line.strip())  # Append output
                self.output_box.verticalScrollBar().setValue(self.output_box.verticalScrollBar().maximum())  # Auto-scroll

            stderr_output = process.stderr.read()
            if stderr_output:
                self.output_box.append(f"\n❌ Error:\n{stderr_output}")

        except Exception as e:
            self.output_box.append(f"\n❌ Error executing command: {str(e)}")


    # Function to process Enter key
    def process_enter_key(self):
        """Run the command typed by the user."""
        command = self.command_input.text().strip()
        if command:
            self.command_input.clear()
            self.run_command(command)  # Run the command

        else:
            QTextEdit.keyPressEvent(self.command_input, event)  # Allow normal key presses

    def clear_terminal(self):
        """Clear the terminal output."""
        self.output_box.clear()


        
    # Function to select item
    def select_item(self):
        """Handle selection from the interactive list."""
        selected = self.selection_box.currentItem()
        if selected:
            QMessageBox.information(self, "Selected Item", f"You selected: {selected.text()}")
            self.selection_box.hide()
            self.output_box.show()


    # Function to enable Enter selection
    def enable_enter_selection(self):
        """Trigger selection when Enter key is pressed."""
        selected = self.selection_box.currentItem()
        if selected:
            self.select_item()


# Run the app
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CMDManagerApp()
    window.show()
    sys.exit(app.exec())
