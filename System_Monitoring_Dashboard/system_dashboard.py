import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import datetime
import psutil
import platform
import os
import subprocess
import socket
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import shutil
from pathlib import Path
import re

class SystemDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("System Monitoring Dashboard")
        self.geometry("1200x800")
        self.configure(bg="#2E2E2E")
        
        # Data storage
        self.cpu_history = [0] * 60
        self.memory_history = [0] * 60
        self.net_sent_history = [0] * 60
        self.net_recv_history = [0] * 60
        self.disk_read_history = [0] * 60
        self.disk_write_history = [0] * 60
        
        # Network info for tracking
        self.last_net_io = psutil.net_io_counters()
        self.last_disk_io = psutil.disk_io_counters(perdisk=False)
        self.last_update_time = time.time()
        
        # Setup UI
        self.setup_ui()
        
        # Start monitoring threads
        self.start_monitors()
    
    def setup_ui(self):
        # Set the style
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use the 'clam' theme as base
        self.style.configure("TFrame", background="#2E2E2E")
        self.style.configure("TLabel", background="#2E2E2E", foreground="#FFFFFF")
        self.style.configure("TButton", background="#4A4A4A", foreground="#FFFFFF")
        self.style.map("TButton", background=[("active", "#3E8ADE")])
        
        # Configure progress bar styles
        self.style.configure("green.Horizontal.TProgressbar", 
                             background="#28A745", troughcolor="#2E2E2E")
        self.style.configure("blue.Horizontal.TProgressbar", 
                             background="#3E8ADE", troughcolor="#2E2E2E")
        self.style.configure("red.Horizontal.TProgressbar", 
                             background="#DC3545", troughcolor="#2E2E2E")
        self.style.configure("yellow.Horizontal.TProgressbar", 
                             background="#FFC107", troughcolor="#2E2E2E")
        self.style.configure("purple.Horizontal.TProgressbar", 
                             background="#6A0DAD", troughcolor="#2E2E2E")
        
        # Create main container with tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.overview_tab = ttk.Frame(self.notebook)
        self.processes_tab = ttk.Frame(self.notebook)
        self.network_tab = ttk.Frame(self.notebook)
        self.disk_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.overview_tab, text="Overview")
        self.notebook.add(self.processes_tab, text="Processes")
        self.notebook.add(self.network_tab, text="Network")
        self.notebook.add(self.disk_tab, text="Disk")
        
        # Set up each tab
        self.setup_overview_tab()
        self.setup_processes_tab()
        self.setup_network_tab()
        self.setup_disk_tab()
        
        # Setup console output at the bottom
        self.setup_console()
    
    def setup_overview_tab(self):
        # System info at top
        info_frame = ttk.LabelFrame(self.overview_tab, text="System Information")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.system_info = ttk.Label(info_frame, text="Loading system information...")
        self.system_info.pack(anchor=tk.W, padx=5, pady=5)
        
        # Split into two columns
        metrics_frame = ttk.Frame(self.overview_tab)
        metrics_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        left_frame = ttk.Frame(metrics_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        right_frame = ttk.Frame(metrics_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # CPU Usage graph
        cpu_frame = ttk.LabelFrame(left_frame, text="CPU Usage")
        cpu_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.cpu_figure = Figure(figsize=(5, 3), dpi=100, facecolor="#2E2E2E")
        self.cpu_plot = self.cpu_figure.add_subplot(111)
        self.cpu_plot.set_facecolor("#2E2E2E")
        self.cpu_plot.tick_params(colors="#FFFFFF")
        self.cpu_plot.set_xlim(0, 60)
        self.cpu_plot.set_ylim(0, 100)
        self.cpu_plot.set_xlabel("Time (s)", color="#FFFFFF")
        self.cpu_plot.set_ylabel("CPU %", color="#FFFFFF")
        
        self.cpu_canvas = FigureCanvasTkAgg(self.cpu_figure, cpu_frame)
        self.cpu_canvas.draw()
        self.cpu_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.cpu_info_frame = ttk.Frame(cpu_frame)
        self.cpu_info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.cpu_percentage = ttk.Label(self.cpu_info_frame, text="Current: 0%")
        self.cpu_percentage.pack(side=tk.LEFT, padx=5)
        
        self.cpu_cores = ttk.Label(self.cpu_info_frame, text="Cores: 0")
        self.cpu_cores.pack(side=tk.RIGHT, padx=5)
        
        # Memory Usage graph
        memory_frame = ttk.LabelFrame(right_frame, text="Memory Usage")
        memory_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.memory_figure = Figure(figsize=(5, 3), dpi=100, facecolor="#2E2E2E")
        self.memory_plot = self.memory_figure.add_subplot(111)
        self.memory_plot.set_facecolor("#2E2E2E")
        self.memory_plot.tick_params(colors="#FFFFFF")
        self.memory_plot.set_xlim(0, 60)
        self.memory_plot.set_ylim(0, 100)
        self.memory_plot.set_xlabel("Time (s)", color="#FFFFFF")
        self.memory_plot.set_ylabel("Memory %", color="#FFFFFF")
        
        self.memory_canvas = FigureCanvasTkAgg(self.memory_figure, memory_frame)
        self.memory_canvas.draw()
        self.memory_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.memory_info_frame = ttk.Frame(memory_frame)
        self.memory_info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.memory_percentage = ttk.Label(self.memory_info_frame, text="Current: 0%")
        self.memory_percentage.pack(side=tk.LEFT, padx=5)
        
        self.memory_usage = ttk.Label(self.memory_info_frame, text="0 MB / 0 MB")
        self.memory_usage.pack(side=tk.RIGHT, padx=5)
        
        # Temperature and battery info (bottom row)
        status_frame = ttk.Frame(self.overview_tab)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # CPU Temperature (if available)
        self.temp_frame = ttk.LabelFrame(status_frame, text="CPU Temperature")
        self.temp_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.temp_label = ttk.Label(self.temp_frame, text="Checking...")
        self.temp_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.temp_progress = ttk.Progressbar(self.temp_frame, style="red.Horizontal.TProgressbar", 
                                           orient=tk.HORIZONTAL, length=100, mode="determinate")
        self.temp_progress.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5, pady=5)
        
        # Battery info (if available)
        self.battery_frame = ttk.LabelFrame(status_frame, text="Battery Status")
        self.battery_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
        self.battery_label = ttk.Label(self.battery_frame, text="Checking...")
        self.battery_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.battery_progress = ttk.Progressbar(self.battery_frame, style="green.Horizontal.TProgressbar", 
                                              orient=tk.HORIZONTAL, length=100, mode="determinate")
        self.battery_progress.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5, pady=5)
    
    def setup_processes_tab(self):
        # Top processes frame
        control_frame = ttk.Frame(self.processes_tab)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        refresh_btn = ttk.Button(control_frame, text="Refresh", command=self.refresh_processes)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        self.sort_var = tk.StringVar(value="CPU")
        sort_options = ttk.Combobox(control_frame, textvariable=self.sort_var, 
                                   values=["CPU", "Memory", "Name", "PID"])
        sort_options.pack(side=tk.LEFT, padx=5)
        sort_options.bind("<<ComboboxSelected>>", lambda e: self.refresh_processes())
        
        kill_btn = ttk.Button(control_frame, text="End Process", command=self.kill_selected_process)
        kill_btn.pack(side=tk.RIGHT, padx=5)
        
        # Process list with scrollbar
        list_frame = ttk.Frame(self.processes_tab)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("pid", "name", "cpu", "memory", "status", "threads", "created")
        self.process_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # Define column headings
        self.process_tree.heading("pid", text="PID")
        self.process_tree.heading("name", text="Name")
        self.process_tree.heading("cpu", text="CPU %")
        self.process_tree.heading("memory", text="Memory")
        self.process_tree.heading("status", text="Status")
        self.process_tree.heading("threads", text="Threads")
        self.process_tree.heading("created", text="Created")
        
        # Set column widths
        self.process_tree.column("pid", width=70)
        self.process_tree.column("name", width=200)
        self.process_tree.column("cpu", width=70)
        self.process_tree.column("memory", width=100)
        self.process_tree.column("status", width=100)
        self.process_tree.column("threads", width=70)
        self.process_tree.column("created", width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.process_tree.yview)
        self.process_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.process_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Process details frame
        details_frame = ttk.LabelFrame(self.processes_tab, text="Process Details")
        details_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.process_details = ttk.Label(details_frame, text="Select a process to view details")
        self.process_details.pack(anchor=tk.W, padx=5, pady=5)
        
        # Bind selection event
        self.process_tree.bind("<<TreeviewSelect>>", self.show_process_details)
    
    def setup_network_tab(self):
        # Network info at top
        info_frame = ttk.LabelFrame(self.network_tab, text="Network Information")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.network_info = ttk.Label(info_frame, text="Loading network information...")
        self.network_info.pack(anchor=tk.W, padx=5, pady=5)
        
        # Network usage graphs
        graphs_frame = ttk.Frame(self.network_tab)
        graphs_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Network speed
        speed_frame = ttk.LabelFrame(graphs_frame, text="Network Speed")
        speed_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.network_figure = Figure(figsize=(5, 3), dpi=100, facecolor="#2E2E2E")
        self.network_plot = self.network_figure.add_subplot(111)
        self.network_plot.set_facecolor("#2E2E2E")
        self.network_plot.tick_params(colors="#FFFFFF")
        self.network_plot.set_xlim(0, 60)
        self.network_plot.set_ylim(0, 100)  # Will be auto-adjusted
        self.network_plot.set_xlabel("Time (s)", color="#FFFFFF")
        self.network_plot.set_ylabel("KB/s", color="#FFFFFF")
        
        self.network_canvas = FigureCanvasTkAgg(self.network_figure, speed_frame)
        self.network_canvas.draw()
        self.network_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Network labels
        self.network_labels_frame = ttk.Frame(speed_frame)
        self.network_labels_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.sent_label = ttk.Label(self.network_labels_frame, text="Sent: 0 KB/s", foreground="#3E8ADE")
        self.sent_label.pack(side=tk.LEFT, padx=5)
        
        self.recv_label = ttk.Label(self.network_labels_frame, text="Received: 0 KB/s", foreground="#28A745")
        self.recv_label.pack(side=tk.RIGHT, padx=5)
        
        # Network connections
        connections_frame = ttk.LabelFrame(self.network_tab, text="Active Connections")
        connections_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Connections treeview
        columns = ("proto", "local_addr", "remote_addr", "status", "pid", "program")
        self.connections_tree = ttk.Treeview(connections_frame, columns=columns, show="headings")
        
        # Define column headings
        self.connections_tree.heading("proto", text="Protocol")
        self.connections_tree.heading("local_addr", text="Local Address")
        self.connections_tree.heading("remote_addr", text="Remote Address")
        self.connections_tree.heading("status", text="Status")
        self.connections_tree.heading("pid", text="PID")
        self.connections_tree.heading("program", text="Program")
        
        # Set column widths
        self.connections_tree.column("proto", width=70)
        self.connections_tree.column("local_addr", width=150)
        self.connections_tree.column("remote_addr", width=150)
        self.connections_tree.column("status", width=100)
        self.connections_tree.column("pid", width=70)
        self.connections_tree.column("program", width=150)
        
        # Add scrollbar
        conn_scrollbar = ttk.Scrollbar(connections_frame, orient=tk.VERTICAL, command=self.connections_tree.yview)
        self.connections_tree.configure(yscrollcommand=conn_scrollbar.set)
        
        # Pack widgets
        self.connections_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        conn_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_disk_tab(self):
        # Disk usage overview
        usage_frame = ttk.LabelFrame(self.disk_tab, text="Disk Usage")
        usage_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.disks_frame = ttk.Frame(usage_frame)
        self.disks_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # IO activity
        io_frame = ttk.LabelFrame(self.disk_tab, text="Disk I/O Activity")
        io_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.disk_figure = Figure(figsize=(5, 3), dpi=100, facecolor="#2E2E2E")
        self.disk_plot = self.disk_figure.add_subplot(111)
        self.disk_plot.set_facecolor("#2E2E2E")
        self.disk_plot.tick_params(colors="#FFFFFF")
        self.disk_plot.set_xlim(0, 60)
        self.disk_plot.set_ylim(0, 100)  # Will be auto-adjusted
        self.disk_plot.set_xlabel("Time (s)", color="#FFFFFF")
        self.disk_plot.set_ylabel("KB/s", color="#FFFFFF")
        
        self.disk_canvas = FigureCanvasTkAgg(self.disk_figure, io_frame)
        self.disk_canvas.draw()
        self.disk_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Disk IO labels
        self.disk_labels_frame = ttk.Frame(io_frame)
        self.disk_labels_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.read_label = ttk.Label(self.disk_labels_frame, text="Read: 0 KB/s", foreground="#3E8ADE")
        self.read_label.pack(side=tk.LEFT, padx=5)
        
        self.write_label = ttk.Label(self.disk_labels_frame, text="Write: 0 KB/s", foreground="#28A745")
        self.write_label.pack(side=tk.RIGHT, padx=5)
        
        # Directory size analyzer
        analyzer_frame = ttk.LabelFrame(self.disk_tab, text="Directory Size Analyzer")
        analyzer_frame.pack(fill=tk.X, padx=5, pady=5)
        
        input_frame = ttk.Frame(analyzer_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Path:").pack(side=tk.LEFT, padx=5)
        
        self.dir_path = tk.StringVar(value=str(Path.home()))
        dir_entry = ttk.Entry(input_frame, textvariable=self.dir_path, width=50)
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        analyze_btn = ttk.Button(input_frame, text="Analyze", command=self.analyze_directory)
        analyze_btn.pack(side=tk.RIGHT, padx=5)
        
        # Results frame for directory analysis
        self.dir_results_frame = ttk.Frame(analyzer_frame)
        self.dir_results_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.dir_results = ttk.Label(self.dir_results_frame, text="Enter a path and click Analyze")
        self.dir_results.pack(anchor=tk.W)
    
    def setup_console(self):
        console_frame = ttk.LabelFrame(self, text="System Log")
        console_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.console = scrolledtext.ScrolledText(console_frame, height=6, bg="#1E1E1E", fg="#FFFFFF")
        self.console.pack(fill=tk.X, padx=5, pady=5)
        self.console.config(state=tk.DISABLED)
    
    def log_to_console(self, message):
        self.console.config(state=tk.NORMAL)
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.console.insert(tk.END, f"[{timestamp}] {message}\n")
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)
    
    def start_monitors(self):
        # Start monitoring threads
        self.start_thread(self.update_system_info)
        self.start_thread(self.update_cpu_memory)
        self.start_thread(self.update_network)
        self.start_thread(self.update_disk)
        self.start_thread(self.update_status)
        
        # Initial updates
        self.refresh_processes()
        self.update_disk_usage()
        self.update_network_connections()
        
        # Log startup
        self.log_to_console("System monitoring started")
    
    def start_thread(self, target):
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
    
    def update_system_info(self):
        """Update system information once every 30 seconds"""
        while True:
            uname = platform.uname()
            boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.datetime.now() - boot_time
            
            # Format uptime
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
            
            # Get IP address
            hostname = socket.gethostname()
            try:
                ip_address = socket.gethostbyname(hostname)
            except:
                ip_address = "Unknown"
            
            info_text = (
                f"System: {uname.system} {uname.release} ({platform.architecture()[0]})\n"
                f"Host: {uname.node} | CPU: {uname.machine} {uname.processor}\n"
                f"Boot Time: {boot_time.strftime('%Y-%m-%d %H:%M:%S')} | Uptime: {uptime_str}\n"
                f"Hostname: {hostname} | IP: {ip_address}"
            )
            
            self.system_info.config(text=info_text)
            
            # Update network info
            net_if_addrs = psutil.net_if_addrs()
            net_info = "Network Interfaces:\n"
            
            for interface, addrs in net_if_addrs.items():
                net_info += f"{interface}:\n"
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        net_info += f"  IPv4: {addr.address} | Netmask: {addr.netmask}\n"
                    elif addr.family == socket.AF_INET6:
                        net_info += f"  IPv6: {addr.address}\n"
                    elif addr.family == psutil.AF_LINK:
                        net_info += f"  MAC: {addr.address}\n"
            
            self.network_info.config(text=net_info)
            
            time.sleep(30)
    
    def update_cpu_memory(self):
        """Update CPU and memory usage every second"""
        while True:
            # CPU usage
            cpu_percent = psutil.cpu_percent()
            self.cpu_history.pop(0)
            self.cpu_history.append(cpu_percent)
            
            # Update CPU plot
            self.cpu_plot.clear()
            self.cpu_plot.set_facecolor("#2E2E2E")
            self.cpu_plot.tick_params(colors="#FFFFFF")
            self.cpu_plot.set_xlim(0, 60)
            self.cpu_plot.set_ylim(0, 100)
            self.cpu_plot.set_xlabel("Time (s)", color="#FFFFFF")
            self.cpu_plot.set_ylabel("CPU %", color="#FFFFFF")
            self.cpu_plot.plot(range(60), self.cpu_history, color="#3E8ADE", linewidth=2)
            self.cpu_plot.fill_between(range(60), self.cpu_history, color="#3E8ADE", alpha=0.2)
            self.cpu_canvas.draw()
            
            # Update CPU info
            self.cpu_percentage.config(text=f"Current: {cpu_percent:.1f}%")
            self.cpu_cores.config(text=f"Cores: {psutil.cpu_count(logical=True)}")
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used / (1024 * 1024 * 1024)  # Convert to GB
            memory_total = memory.total / (1024 * 1024 * 1024)  # Convert to GB
            
            self.memory_history.pop(0)
            self.memory_history.append(memory_percent)
            
            # Update memory plot
            self.memory_plot.clear()
            self.memory_plot.set_facecolor("#2E2E2E")
            self.memory_plot.tick_params(colors="#FFFFFF")
            self.memory_plot.set_xlim(0, 60)
            self.memory_plot.set_ylim(0, 100)
            self.memory_plot.set_xlabel("Time (s)", color="#FFFFFF")
            self.memory_plot.set_ylabel("Memory %", color="#FFFFFF")
            self.memory_plot.plot(range(60), self.memory_history, color="#28A745", linewidth=2)
            self.memory_plot.fill_between(range(60), self.memory_history, color="#28A745", alpha=0.2)
            self.memory_canvas.draw()
            
            # Update memory info
            self.memory_percentage.config(text=f"Current: {memory_percent:.1f}%")
            self.memory_usage.config(text=f"{memory_used:.2f} GB / {memory_total:.2f} GB")
            
            # Log high resource usage
            if cpu_percent > 90:
                self.log_to_console(f"High CPU usage: {cpu_percent:.1f}%")
            if memory_percent > 90:
                self.log_to_console(f"High memory usage: {memory_percent:.1f}%")
            
            time.sleep(1)
    
    def update_network(self):
        """Update network statistics every second"""
        while True:
            current_time = time.time()
            time_delta = current_time - self.last_update_time
            
            # Get current network IO
            net_io = psutil.net_io_counters()
            
            # Calculate speed
            sent_bytes = net_io.bytes_sent - self.last_net_io.bytes_sent
            recv_bytes = net_io.bytes_recv - self.last_net_io.bytes_recv
            
            sent_kb_s = sent_bytes / time_delta / 1024
            recv_kb_s = recv_bytes / time_delta / 1024
            
            # Update history
            self.net_sent_history.pop(0)
            self.net_sent_history.append(sent_kb_s)
            
            self.net_recv_history.pop(0)
            self.net_recv_history.append(recv_kb_s)
            
            # Calculate max for y-axis
            max_value = max(max(self.net_sent_history), max(self.net_recv_history), 100)
            
            # Update network plot
            self.network_plot.clear()
            self.network_plot.set_facecolor("#2E2E2E")
            self.network_plot.tick_params(colors="#FFFFFF")
            self.network_plot.set_xlim(0, 60)
            self.network_plot.set_ylim(0, max_value * 1.1)  # Add 10% margin
            self.network_plot.set_xlabel("Time (s)", color="#FFFFFF")
            self.network_plot.set_ylabel("KB/s", color="#FFFFFF")
            
            # Plot sent
            self.network_plot.plot(range(60), self.net_sent_history, color="#3E8ADE", linewidth=2, label="Sent")
            self.network_plot.fill_between(range(60), self.net_sent_history, color="#3E8ADE", alpha=0.2)
            
            # Plot received
            self.network_plot.plot(range(60), self.net_recv_history, color="#28A745", linewidth=2, label="Received")
            self.network_plot.fill_between(range(60), self.net_recv_history, color="#28A745", alpha=0.2)
            
            self.network_plot.legend(loc="upper right", facecolor="#2E2E2E", labelcolor="#FFFFFF")
            self.network_canvas.draw()
            
            # Update network labels
            self.sent_label.config(text=f"Sent: {sent_kb_s:.2f} KB/s")
            self.recv_label.config(text=f"Received: {recv_kb_s:.2f} KB/s")
            
            # Log high network activity
            if sent_kb_s > 1000 or recv_kb_s > 1000:
                self.log_to_console(f"High network activity: {sent_kb_s:.2f} KB/s sent, {recv_kb_s:.2f} KB/s received")
            
            # Store current values for next iteration
            self.last_net_io = net_io
            self.last_update_time = current_time
            
            time.sleep(1)
    
    def update_disk(self):
        """Update disk I/O statistics every second"""
        while True:
            current_time = time.time()
            time_delta = current_time - self.last_update_time
            
            # Get current disk IO
            disk_io = psutil.disk_io_counters(perdisk=False)
            
            # Calculate speed
            read_bytes = disk_io.read_bytes - self.last_disk_io.read_bytes
            write_bytes = disk_io.write_bytes - self.last_disk_io.write_bytes
            
            read_kb_s = read_bytes / time_delta / 1024
            write_kb_s = write_bytes / time_delta / 1024
            
            # Update history
            self.disk_read_history.pop(0)
            self.disk_read_history.append(read_kb_s)
            
            self.disk_write_history.pop(0)
            self.disk_write_history.append(write_kb_s)
            
            # Calculate max for y-axis
            max_value = max(max(self.disk_read_history), max(self.disk_write_history), 100)
            
            # Update disk plot
            self.disk_plot.clear()
            self.disk_plot.set_facecolor("#2E2E2E")
            self.disk_plot.tick_params(colors="#FFFFFF")
            self.disk_plot.set_xlim(0, 60)
            self.disk_plot.set_ylim(0, max_value * 1.1)  # Add 10% margin
            self.disk_plot.set_xlabel("Time (s)", color="#FFFFFF")
            self.disk_plot.set_ylabel("KB/s", color="#FFFFFF")
            
            # Plot read
            self.disk_plot.plot(range(60), self.disk_read_history, color="#3E8ADE", linewidth=2, label="Read")
            self.disk_plot.fill_between(range(60), self.disk_read_history, color="#3E8ADE", alpha=0.2)
            
            # Plot write
            self.disk_plot.plot(range(60), self.disk_write_history, color="#28A745", linewidth=2, label="Write")
            self.disk_plot.fill_between(range(60), self.disk_write_history, color="#28A745", alpha=0.2)
            
            self.disk_plot.legend(loc="upper right", facecolor="#2E2E2E", labelcolor="#FFFFFF")
            self.disk_canvas.draw()
            
            # Update disk labels
            self.read_label.config(text=f"Read: {read_kb_s:.2f} KB/s")
            self.write_label.config(text=f"Write: {write_kb_s:.2f} KB/s")
            
            # Log high disk activity
            if read_kb_s > 5000 or write_kb_s > 5000:
                self.log_to_console(f"High disk activity: {read_kb_s:.2f} KB/s read, {write_kb_s:.2f} KB/s write")
            
            # Store current values for next iteration
            self.last_disk_io = disk_io
            
            time.sleep(1)
    
    def update_status(self):
        """Update temperature and battery status every 5 seconds"""
        while True:
            # Update CPU temperature if available
            try:
                # Try different methods to get temperature
                temperature = None
                
                # Try psutil (works on some systems)
                if hasattr(psutil, "sensors_temperatures"):
                    temps = psutil.sensors_temperatures()
                    if temps:
                        for name, entries in temps.items():
                            for entry in entries:
                                if entry.current > 0:
                                    temperature = entry.current
                                    break
                            if temperature:
                                break
                
                # If not found and on Linux, try reading from thermal_zone
                if not temperature and os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
                    with open("/sys/class/thermal/thermal_zone0/temp") as f:
                        temperature = int(f.read().strip()) / 1000.0
                
                if temperature:
                    self.temp_label.config(text=f"{temperature:.1f}°C")
                    self.temp_progress["value"] = min(100, temperature)
                    
                    # Change color based on temperature
                    temp_style = "green.Horizontal.TProgressbar"
                    if temperature > 70:
                        temp_style = "red.Horizontal.TProgressbar"
                    elif temperature > 60:
                        temp_style = "yellow.Horizontal.TProgressbar"
                    self.temp_progress["style"] = temp_style
                    
                    # Log high temperature
                    if temperature > 80:
                        self.log_to_console(f"Warning: High CPU temperature: {temperature:.1f}°C")
                else:
                    self.temp_label.config(text="Not available")
                    self.temp_progress["value"] = 0
            except Exception as e:
                self.temp_label.config(text="Not available")
                self.temp_progress["value"] = 0
            
            # Update battery status if available
            try:
                battery = psutil.sensors_battery()
                if battery:
                    percent = battery.percent
                    power_plugged = battery.power_plugged
                    
                    status = "Charging" if power_plugged else "Discharging"
                    self.battery_label.config(text=f"{percent:.1f}% ({status})")
                    self.battery_progress["value"] = percent
                    
                    # Change color based on battery level and status
                    batt_style = "green.Horizontal.TProgressbar"
                    if not power_plugged and percent < 20:
                        batt_style = "red.Horizontal.TProgressbar"
                    elif not power_plugged and percent < 50:
                        batt_style = "yellow.Horizontal.TProgressbar"
                    self.battery_progress["style"] = batt_style
                    
                    # Log low battery
                    if not power_plugged and percent < 15:
                        self.log_to_console(f"Warning: Low battery: {percent:.1f}%")
                else:
                    self.battery_label.config(text="Not available")
                    self.battery_progress["value"] = 0
            except Exception as e:
                self.battery_label.config(text="Not available")
                self.battery_progress["value"] = 0
            
            time.sleep(5)
    
    def refresh_processes(self):
        """Refresh the process list"""
        # Clear the list
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)
        
        # Get all processes
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status', 'num_threads', 'create_time']):
            try:
                pinfo = proc.info
                # Get memory in MB
                memory_mb = pinfo['memory_percent'] * psutil.virtual_memory().total / (1024 * 1024 * 100)
                create_time = datetime.datetime.fromtimestamp(pinfo['create_time']).strftime('%Y-%m-%d %H:%M:%S')
                processes.append({
                    'pid': pinfo['pid'],
                    'name': pinfo['name'],
                    'cpu': pinfo['cpu_percent'],
                    'memory': f"{memory_mb:.2f} MB",
                    'memory_value': memory_mb,
                    'status': pinfo['status'],
                    'threads': pinfo['num_threads'],
                    'created': create_time
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Sort processes
        sort_by = self.sort_var.get()
        if sort_by == "CPU":
            processes.sort(key=lambda x: x['cpu'], reverse=True)
        elif sort_by == "Memory":
            processes.sort(key=lambda x: x['memory_value'], reverse=True)
        elif sort_by == "Name":
            processes.sort(key=lambda x: x['name'].lower())
        elif sort_by == "PID":
            processes.sort(key=lambda x: x['pid'])
        
        # Add processes to treeview
        for proc in processes[:100]:  # Show top 100 processes
            self.process_tree.insert('', 'end', values=(
                proc['pid'],
                proc['name'],
                f"{proc['cpu']:.1f}",
                proc['memory'],
                proc['status'],
                proc['threads'],
                proc['created']
            ))
        
        self.log_to_console(f"Process list refreshed - {len(processes)} processes found")
    
    def show_process_details(self, event):
        """Show details of the selected process"""
        selected_items = self.process_tree.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        pid = int(self.process_tree.item(item, 'values')[0])
        
        try:
            proc = psutil.Process(pid)
            
            # Get process details
            details = []
            details.append(f"PID: {pid}")
            details.append(f"Name: {proc.name()}")
            details.append(f"Executable: {proc.exe()}")
            details.append(f"Command Line: {' '.join(proc.cmdline())}")
            details.append(f"Working Directory: {proc.cwd()}")
            details.append(f"Status: {proc.status()}")
            details.append(f"User: {proc.username()}")
            details.append(f"CPU Usage: {proc.cpu_percent(interval=0.1):.1f}%")
            details.append(f"Memory Usage: {proc.memory_info().rss / (1024 * 1024):.2f} MB")
            details.append(f"Open Files: {len(proc.open_files())}")
            details.append(f"Threads: {proc.num_threads()}")
            
            self.process_details.config(text='\n'.join(details))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            self.process_details.config(text=f"Error getting process details: {e}")
    
    def kill_selected_process(self):
        """Kill the selected process"""
        selected_items = self.process_tree.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        pid = int(self.process_tree.item(item, 'values')[0])
        name = self.process_tree.item(item, 'values')[1]
        
        if not tk.messagebox.askyesno("Confirm", f"Are you sure you want to terminate process {name} (PID: {pid})?"):
            return
        
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            self.log_to_console(f"Process {name} (PID: {pid}) terminated")
            
            # Refresh process list after a short delay
            self.after(1000, self.refresh_processes)
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.log_to_console(f"Error terminating process: {e}")
            tk.messagebox.showerror("Error", f"Could not terminate process: {e}")
    
    def update_disk_usage(self):
        """Update disk usage information"""
        # Clear existing disk frames
        for widget in self.disks_frame.winfo_children():
            widget.destroy()
        
        # Get disk partitions
        partitions = psutil.disk_partitions()
        
        # Create a frame for each partition
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                
                # Create a frame for this partition
                partition_frame = ttk.Frame(self.disks_frame)
                partition_frame.pack(fill=tk.X, pady=5)
                
                # Disk info
                info_text = f"{partition.mountpoint} ({partition.device})"
                if partition.fstype:
                    info_text += f" - {partition.fstype}"
                
                label = ttk.Label(partition_frame, text=info_text)
                label.pack(side=tk.LEFT, padx=5)
                
                # Usage text
                used_gb = usage.used / (1024**3)
                total_gb = usage.total / (1024**3)
                percent = usage.percent
                
                usage_label = ttk.Label(partition_frame, text=f"{used_gb:.2f} GB / {total_gb:.2f} GB ({percent}%)")
                usage_label.pack(side=tk.RIGHT, padx=5)
                
                # Progress bar
                style = "green.Horizontal.TProgressbar"
                if percent > 90:
                    style = "red.Horizontal.TProgressbar"
                elif percent > 70:
                    style = "yellow.Horizontal.TProgressbar"
                
                progress = ttk.Progressbar(partition_frame, style=style, 
                                          orient=tk.HORIZONTAL, length=100, mode="determinate")
                progress["value"] = percent
                progress.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
                
                # Log critical disk space
                if percent > 95:
                    self.log_to_console(f"Critical: Disk {partition.mountpoint} is almost full ({percent}%)")
            except (PermissionError, FileNotFoundError):
                # Skip partitions we can't access
                continue
        
        # Schedule next update
        self.after(30000, self.update_disk_usage)  # Update every 30 seconds
    
    def update_network_connections(self):
        """Update list of network connections"""
        # Clear existing items
        for item in self.connections_tree.get_children():
            self.connections_tree.delete(item)
        
        # Get network connections
        connections = psutil.net_connections(kind='inet')
        
        # Process and add connections to the tree
        for conn in connections:
            try:
                # Format addresses
                laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "-"
                raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "-"
                
                # Get process name
                proc_name = "-"
                if conn.pid:
                    try:
                        proc_name = psutil.Process(conn.pid).name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Add to tree
                self.connections_tree.insert('', 'end', values=(
                    conn.type,
                    laddr,
                    raddr,
                    conn.status,
                    conn.pid or "-",
                    proc_name
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Schedule next update
        self.after(10000, self.update_network_connections)  # Update every 10 seconds
    
    def analyze_directory(self):
        """Analyze the size of a directory"""
        path = self.dir_path.get()
        
        if not os.path.exists(path):
            tk.messagebox.showerror("Error", "The specified path does not exist")
            return
        
        if not os.path.isdir(path):
            tk.messagebox.showerror("Error", "The specified path is not a directory")
            return
        
        # Clear existing results
        for widget in self.dir_results_frame.winfo_children():
            widget.destroy()
        
        # Show analyzing message
        analyzing_label = ttk.Label(self.dir_results_frame, text="Analyzing directory... This may take a while.")
        analyzing_label.pack(anchor=tk.W)
        self.update_idletasks()
        
        # Start analysis in a separate thread
        self.start_thread(lambda: self._analyze_directory_thread(path))
    
    def _analyze_directory_thread(self, path):
        """Thread function for directory analysis"""
        try:
            # Get total size
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    try:
                        total_size += os.path.getsize(fp)
                    except (PermissionError, FileNotFoundError):
                        pass
            
            # Get subdirectories and their sizes
            subdirs = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    try:
                        dir_size = sum(os.path.getsize(os.path.join(dirpath, f))
                                      for dirpath, dirnames, filenames in os.walk(item_path)
                                      for f in filenames if os.path.exists(os.path.join(dirpath, f)))
                        subdirs.append((item, dir_size))
                    except (PermissionError, FileNotFoundError):
                        subdirs.append((item, 0))  # Can't access
            
            # Sort subdirectories by size
            subdirs.sort(key=lambda x: x[1], reverse=True)
            
            # Update UI
            self.after(0, lambda: self._update_dir_analysis_ui(path, total_size, subdirs))
        except Exception as e:
            self.after(0, lambda: self._show_dir_analysis_error(str(e)))
    
    def _update_dir_analysis_ui(self, path, total_size, subdirs):
        """Update UI with directory analysis results"""
        # Clear existing results
        for widget in self.dir_results_frame.winfo_children():
            widget.destroy()
        
        # Format total size
        if total_size > 1024**3:
            size_str = f"{total_size / 1024**3:.2f} GB"
        elif total_size > 1024**2:
            size_str = f"{total_size / 1024**2:.2f} MB"
        else:
            size_str = f"{total_size / 1024:.2f} KB"
        
        # Show total size
        ttk.Label(self.dir_results_frame, 
                 text=f"Total size of {path}: {size_str}").pack(anchor=tk.W, pady=(0, 10))
        
        # Show subdirectories
        ttk.Label(self.dir_results_frame, 
                 text="Subdirectories by size:").pack(anchor=tk.W)
        
        # Create a frame for the subdirectories list
        subdir_frame = ttk.Frame(self.dir_results_frame)
        subdir_frame.pack(fill=tk.X, pady=5)
        
        # Create a canvas with scrollbar for the subdirectories
        canvas = tk.Canvas(subdir_frame, bg="#2E2E2E", highlightthickness=0)
        scrollbar = ttk.Scrollbar(subdir_frame, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create a frame inside the canvas
        inner_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner_frame, anchor=tk.NW)
        
        # Add subdirectories to the frame
        for i, (subdir, size) in enumerate(subdirs[:20]):  # Show top 20
            if size > 1024**3:
                size_str = f"{size / 1024**3:.2f} GB"
            elif size > 1024**2:
                size_str = f"{size / 1024**2:.2f} MB"
            else:
                size_str = f"{size / 1024:.2f} KB"
            
            item_frame = ttk.Frame(inner_frame)
            item_frame.pack(fill=tk.X, pady=2)
            
            # Calculate percentage
            if total_size > 0:
                percent = size / total_size * 100
            else:
                percent = 0
            
            ttk.Label(item_frame, text=f"{subdir}").pack(side=tk.LEFT, padx=5)
            ttk.Label(item_frame, text=f"{size_str} ({percent:.1f}%)").pack(side=tk.RIGHT, padx=5)
            
            # Add progress bar
            style = "blue.Horizontal.TProgressbar"
            if percent > 50:
                style = "red.Horizontal.TProgressbar"
            elif percent > 25:
                style = "yellow.Horizontal.TProgressbar"
            
            progress = ttk.Progressbar(item_frame, style=style, 
                                      orient=tk.HORIZONTAL, length=100, mode="determinate")
            progress["value"] = percent
            progress.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
        
        # Configure the canvas to adjust to the inner frame size
        inner_frame.update_idletasks()
        canvas.config(width=500, height=min(300, inner_frame.winfo_height()))
        canvas.config(scrollregion=canvas.bbox(tk.ALL))
        
        # Log completion
        self.log_to_console(f"Directory analysis completed for {path}")
    
    def _show_dir_analysis_error(self, error_message):
        """Show error message for directory analysis"""
        # Clear existing results
        for widget in self.dir_results_frame.winfo_children():
            widget.destroy()
        
        # Show error message
        ttk.Label(self.dir_results_frame, 
                 text=f"Error analyzing directory: {error_message}").pack(anchor=tk.W)
        
        self.log_to_console(f"Error in directory analysis: {error_message}")

if __name__ == "__main__":
    app = SystemDashboard()
    app.mainloop()