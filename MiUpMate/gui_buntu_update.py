import os
import subprocess
import datetime
import shutil
import psutil
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter import scrolledtext
from threading import Thread, Event
from tqdm import tqdm
import json

# Detect the original user's home directory, even when using sudo
original_user_home = os.path.expanduser("~" + os.getenv("SUDO_USER", os.getenv("USER")))

# Set the central storage directory inside the user's home
storage_dir = os.path.join(original_user_home, "py_sys_logs")
os.makedirs(storage_dir, exist_ok=True)  # Create the directory if it doesn't exist

# Define paths for log and command storage
log_file_path = os.path.join(storage_dir, "update_log.txt")
commands_file = os.path.join(storage_dir, "commands.json")

# Event to allow cancellation of updates
cancel_event = Event()

# Check if script is run as root
if os.geteuid() != 0:
    messagebox.showerror("Permission Denied", "This application must be run as root.\nPlease restart with sudo.")
    exit()

# Load or create commands.json to store custom user commands
if not os.path.exists(commands_file):
    with open(commands_file, "w") as file:
        json.dump({"APT": "sudo apt update && sudo apt upgrade -y"}, file, indent=4)

# Function to load commands from JSON
def load_commands():
    with open(commands_file, "r") as file:
        return json.load(file)

# Function to save commands to JSON
def save_commands(commands):
    with open(commands_file, "w") as file:
        json.dump(commands, file, indent=4)

# Load user-defined commands
commands = load_commands()

# Function to update system info in the GUI
def update_system_info():
    """ Retrieves system information (CPU, RAM, Disk Usage) and updates the GUI labels. """
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent

    root.after(0, cpu_label.config, {"text": f"CPU Usage: {cpu_usage}%"})
    root.after(0, ram_label.config, {"text": f"RAM Usage: {ram_usage}%"})
    root.after(0, disk_label.config, {"text": f"Disk Usage: {disk_usage}%"})

    root.after(5000, update_system_info)

# Function to safely update the progress bar
def update_progress(value):
    """ Updates the progress bar in a thread-safe manner. """
    root.after(0, progress_bar.config, {"value": value})

# Function to update the log display in the GUI (with terminal effect)
def update_gui_log(message):
    """ Displays log messages inside the GUI log window with a terminal-like effect. """
    root.after(0, log_display.insert, tk.END, f"> {message}\n")
    root.after(0, log_display.see, tk.END)

def log_message(message):
    """ Logs a message to console, GUI, and a log file with timestamp. """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {message}"

    print(log_entry.strip())
    update_gui_log(log_entry)

    with open(log_file_path, "a") as log:
        log.write(log_entry + "\n")

# Function to execute a command with progress bar and cancellation support
def run_command(command, description):
    """ Executes a system command, logs progress, updates GUI progress bar, and allows cancellation. """
    if cancel_event.is_set():
        log_message(f"🚫 Cancelled: {description}")
        return

    log_message(f"⚙️ Running command: {description}")

    update_progress(0)

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    with tqdm(total=100, desc=description, bar_format="{l_bar}{bar} {n_fmt}/{total_fmt}") as progress:
        for _ in range(10):
            if cancel_event.is_set():
                process.terminate()
                log_message(f"❌ Update cancelled: {description}")
                return
            progress.update(10)
            process.poll()
            update_progress(_ * 10)

    process.wait()
    update_progress(100)

    if process.returncode == 0:
        log_message(f"✅ Command completed successfully: {description}")
    else:
        log_message(f"❌ Command failed: {description}\nError: {process.stderr.read()}")

# Function to stop all running updates
def cancel_updates():
    """ Cancels ongoing updates. """
    cancel_event.set()
    log_message("🚫 Cancelling updates...")

# Function to add a new command
def add_command():
    """ Allows the user to add a new command. """
    name = simpledialog.askstring("Add Command", "Enter command name:")
    command = simpledialog.askstring("Add Command", "Enter the command:")
    if name and command:
        commands[name] = command
        save_commands(commands)
        refresh_command_list()

# Function to edit a selected command
def edit_command():
    """ Allows the user to edit an existing command. """
    selected_command = command_listbox.get(tk.ACTIVE)
    if selected_command and selected_command in commands:
        new_command = simpledialog.askstring("Edit Command", f"Edit command for {selected_command}:", initialvalue=commands[selected_command])
        if new_command:
            commands[selected_command] = new_command
            save_commands(commands)
            refresh_command_list()

# Function to delete a selected command
def delete_command():
    """ Allows the user to delete a selected command. """
    selected_command = command_listbox.get(tk.ACTIVE)
    if selected_command and selected_command in commands:
        del commands[selected_command]
        save_commands(commands)
        refresh_command_list()

# Function to refresh the command list in the UI
def refresh_command_list():
    """ Refreshes the list of commands in the UI. """
    command_listbox.delete(0, tk.END)
    for cmd in commands.keys():
        command_listbox.insert(tk.END, cmd)

# Function to run a selected command
def run_selected_command():
    """ Runs the selected command from the list. """
    selected_command = command_listbox.get(tk.ACTIVE)
    if selected_command and selected_command in commands:
        run_command(commands[selected_command], f"Running {selected_command}")

# Create the main GUI window
root = tk.Tk()
root.title(" MiUpMate - System Updater")
root.geometry("700x600")
root.resizable(True, True)

# Set a calm, eye-friendly theme
root.configure(bg="#2E2E2E")  # Dark Gray Background

# Greet User with Hostname
hostname = os.uname().nodename
greeting_label = tk.Label(root, text=f"Welcome, {hostname}!", font=("Arial", 14, "bold"), bg="#2E2E2E", fg="#A3BE8C")
greeting_label.pack(pady=5)

# System Info Labels
cpu_label = tk.Label(root, text="CPU Usage: --%", bg="#2E2E2E", fg="#D8DEE9")
cpu_label.pack(pady=5)
ram_label = tk.Label(root, text="RAM Usage: --%", bg="#2E2E2E", fg="#D8DEE9")
ram_label.pack(pady=5)
disk_label = tk.Label(root, text="Disk Usage: --%", bg="#2E2E2E", fg="#D8DEE9")
disk_label.pack(pady=5)

# **Log Display (Fixed `log_display` not being defined)**
log_display = scrolledtext.ScrolledText(root, width=80, height=15, bg="#3B4252", fg="#A3BE8C", font=("Courier", 12))
log_display.pack(pady=10)

# Progress Bar
progress_bar = ttk.Progressbar(root, length=400, mode='determinate')
progress_bar.pack(pady=10)

# Command Management Section
tk.Label(root, text="Available Commands:", bg="#2E2E2E", fg="#D8DEE9").pack()
command_listbox = tk.Listbox(root, height=5, bg="#3B4252", fg="#A3BE8C", font=("Courier", 12))
command_listbox.pack(fill=tk.X, padx=10, pady=5)
refresh_command_list()

# Button Frame
button_frame = tk.Frame(root, bg="#2E2E2E")
button_frame.pack(pady=10)

tk.Button(button_frame, text="Run", command=run_selected_command, bg="#5E81AC", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(button_frame, text="Add", command=add_command, bg="#A3BE8C", fg="black").pack(side=tk.LEFT, padx=5)
tk.Button(button_frame, text="Edit", command=edit_command, bg="#D08770", fg="black").pack(side=tk.LEFT, padx=5)
tk.Button(button_frame, text="Delete", command=delete_command, bg="#BF616A", fg="white").pack(side=tk.LEFT, padx=5)


# Start system info update
update_system_info()

# Start the GUI event loop
root.mainloop()
