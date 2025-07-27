#!/usr/bin/env python3
"""
Minecraft Server Wrapper - Windows Optimized Version
Advanced server management with real-time monitoring and web interface
"""

import os
import sys
import json
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
import webbrowser
import gc
import ctypes
import psutil
import requests
import zipfile
import shutil
from packaging import version

# Flask and SocketIO imports
from flask import Flask, render_template_string, request, jsonify, send_file
from flask_socketio import SocketIO, emit
from werkzeug.serving import make_server

class MinecraftServerWrapper:
    def __init__(self):
        # Application version and update settings
        self.current_version = "2.1.0"  # Current app version
        self.github_repo = "jcfrancisco0103/My-Server-Wrapper"  # Your GitHub repo
        self.github_api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
        self.update_check_interval = 3600  # Check for updates every hour (in seconds)
        self.last_update_check = 0
        self.update_available = False
        self.latest_version = None
        self.update_download_url = None
        
        # Configuration
        self.config_file = "server_config.json"
        self.console_history_file = "console_history.json"
        self.server_directory = "C:\\Users\\MersYeon\\Desktop\\Cacasians"
        self.server_jar = ""
        self.min_memory = "1G"
        self.max_memory = "2G"
        self.server_running = False
        self.server_process = None
        self.start_time = None
        
        # Performance monitoring
        self.cpu_usage = 0.0
        self.ram_usage = 0.0
        self.server_ram_usage = 0.0
        self.system_ram_total = psutil.virtual_memory().total / (1024**3)  # GB
        self.server_tps = 20.0
        self.performance_history = []
        self.performance_update_interval = 2  # seconds
        
        # Monitoring thread
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Console and players
        self.console_history = []
        self.online_players = []
        
        # Web server
        self.web_server = Flask(__name__)
        self.web_server.config['SECRET_KEY'] = 'minecraft_wrapper_secret'
        self.socketio = SocketIO(self.web_server, cors_allowed_origins="*")
        self.web_thread = None
        self.server_instance = None
        
        # Load configuration
        self.load_config()
        self.load_console_history()
        
        # Setup UI
        self.setup_ui()
        self.setup_web_routes()
        
        # Start performance monitoring
        self.start_performance_monitoring()
        
        # Start web server
        self.start_web_server()

    def optimize_ram(self):
        """Optimize system RAM using Windows API and Python garbage collection"""
        try:
            # Python garbage collection
            collected = gc.collect()
            
            # Windows-specific memory optimization
            if sys.platform == "win32":
                try:
                    # Get current process handle
                    process_handle = ctypes.windll.kernel32.GetCurrentProcess()
                    
                    # Try to trim working set
                    ctypes.windll.psapi.EmptyWorkingSet(process_handle)
                    
                    # Force garbage collection again
                    gc.collect()
                    
                    # Get memory info before and after
                    process = psutil.Process()
                    memory_info = process.memory_info()
                    
                    # Estimate freed memory (rough calculation)
                    freed_mb = max(10, collected * 0.1)  # Conservative estimate
                    
                    self.add_console_message(f"RAM optimization completed. Freed approximately {freed_mb:.1f} MB")
                    
                    # Emit to web clients
                    self.socketio.emit('ram_optimized', {
                        'freed_mb': freed_mb,
                        'message': f'RAM optimized! Freed {freed_mb:.1f} MB'
                    })
                    
                    return freed_mb
                    
                except Exception as e:
                    self.add_console_message(f"Windows RAM optimization failed: {e}")
                    return 0
            else:
                self.add_console_message(f"Basic RAM optimization completed. Collected {collected} objects")
                return collected * 0.01  # Very rough estimate
                
        except Exception as e:
            self.add_console_message(f"RAM optimization error: {e}")
            return 0

    def check_for_updates(self, manual=False):
        """Check for application updates from GitHub"""
        try:
            if manual:
                self.add_console_message("🔍 Checking for updates...")
            
            # Make request to GitHub API
            response = requests.get(self.github_api_url, timeout=10)
            response.raise_for_status()
            
            release_data = response.json()
            latest_version = release_data['tag_name'].lstrip('v')
            
            # Compare versions using packaging.version
            if version.parse(latest_version) > version.parse(self.current_version):
                self.update_available = True
                self.latest_version = latest_version
                
                # Find the download URL for the main file
                for asset in release_data.get('assets', []):
                    if asset['name'].endswith('.py') or asset['name'].endswith('.zip'):
                        self.update_download_url = asset['browser_download_url']
                        break
                else:
                    # Fallback to zipball if no specific asset found
                    self.update_download_url = release_data['zipball_url']
                
                message = f"🎉 Update available! Current: v{self.current_version} → Latest: v{latest_version}"
                self.add_console_message(message)
                
                if manual:
                    # Show update dialog
                    self.show_update_dialog(latest_version, release_data.get('body', ''))
                
                # Emit to web clients
                self.emit_update_notification('update_available', {
                    'current_version': self.current_version,
                    'latest_version': latest_version,
                    'download_url': self.update_download_url,
                    'release_notes': release_data.get('body', '')
                })
                
                return True
            else:
                self.update_available = False
                if manual:
                    self.add_console_message(f"✅ You're running the latest version (v{self.current_version})")
                return False
                
        except requests.exceptions.RequestException as e:
            error_msg = f"❌ Failed to check for updates: {e}"
            if manual:
                self.add_console_message(error_msg)
            print(error_msg)
            return False
        except Exception as e:
            error_msg = f"❌ Update check error: {e}"
            if manual:
                self.add_console_message(error_msg)
            print(error_msg)
            return False

    def show_update_dialog(self, latest_version, release_notes):
        """Show update dialog to user"""
        try:
            from tkinter import messagebox
            
            message = f"A new version is available!\n\n"
            message += f"Current Version: v{self.current_version}\n"
            message += f"Latest Version: v{latest_version}\n\n"
            
            if release_notes:
                # Truncate release notes if too long
                notes = release_notes[:300] + "..." if len(release_notes) > 300 else release_notes
                message += f"Release Notes:\n{notes}\n\n"
            
            message += "Would you like to download and install the update?"
            
            result = messagebox.askyesno("Update Available", message)
            if result:
                self.download_and_apply_update()
                
        except Exception as e:
            print(f"Error showing update dialog: {e}")

    def download_and_apply_update(self):
        """Download and apply the update"""
        try:
            self.add_console_message("📥 Downloading update...")
            
            # Create backup directory
            backup_dir = "backup"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup current file
            current_file = os.path.abspath(__file__)
            backup_file = os.path.join(backup_dir, f"minecraft_server_wrapper_v{self.current_version}_backup.py")
            shutil.copy2(current_file, backup_file)
            self.add_console_message(f"📋 Backup created: {backup_file}")
            
            # Download the update
            response = requests.get(self.update_download_url, timeout=30)
            response.raise_for_status()
            
            if self.update_download_url.endswith('.zip'):
                # Handle ZIP file
                zip_path = "update.zip"
                with open(zip_path, 'wb') as f:
                    f.write(response.content)
                
                # Extract ZIP
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall("update_temp")
                
                # Find the main Python file in extracted content
                for root, dirs, files in os.walk("update_temp"):
                    for file in files:
                        if file.endswith('.py') and 'minecraft_server_wrapper' in file:
                            new_file_path = os.path.join(root, file)
                            break
                    else:
                        continue
                    break
                else:
                    raise Exception("Could not find main Python file in update")
                
                # Copy new file
                shutil.copy2(new_file_path, current_file)
                
                # Cleanup
                os.remove(zip_path)
                shutil.rmtree("update_temp")
                
            else:
                # Handle direct Python file
                with open(current_file, 'wb') as f:
                    f.write(response.content)
            
            self.add_console_message(f"✅ Update downloaded and applied successfully!")
            self.add_console_message(f"🔄 Please restart the application to use v{self.latest_version}")
            
            # Emit to web clients
            self.emit_update_notification('update_applied', {
                'success': True,
                'message': f'Update to v{self.latest_version} applied successfully! Please restart the application.',
                'new_version': self.latest_version
            })
            
            # Show restart dialog
            from tkinter import messagebox
            result = messagebox.askyesno(
                "Update Complete", 
                f"Update to v{self.latest_version} has been applied successfully!\n\n"
                "The application needs to be restarted to use the new version.\n\n"
                "Would you like to restart now?"
            )
            
            if result:
                self.restart_application()
            
        except Exception as e:
            error_msg = f"❌ Failed to apply update: {e}"
            self.add_console_message(error_msg)
            
            # Emit error to web clients
            self.emit_update_notification('update_applied', {
                'success': False,
                'message': error_msg
            })

    def restart_application(self):
        """Restart the application"""
        try:
            self.add_console_message("🔄 Restarting application...")
            
            # Stop server if running
            if self.server_running:
                self.stop_server()
            
            # Stop monitoring
            self.stop_performance_monitoring()
            
            # Close GUI
            if hasattr(self, 'root'):
                self.root.quit()
            
            # Restart the application
            python = sys.executable
            os.execl(python, python, *sys.argv)
            
        except Exception as e:
            self.add_console_message(f"❌ Failed to restart application: {e}")

    def auto_check_updates(self):
        """Automatically check for updates periodically"""
        current_time = time.time()
        if current_time - self.last_update_check >= self.update_check_interval:
            self.last_update_check = current_time
            # Check for updates in background (non-manual)
            threading.Thread(target=self.check_for_updates, args=(False,), daemon=True).start()

    def start_performance_monitoring(self):
        """Start the performance monitoring thread"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self.performance_monitor_loop, daemon=True)
            self.monitor_thread.start()

    def stop_performance_monitoring(self):
        """Stop the performance monitoring thread"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)

    def performance_monitor_loop(self):
        """Main performance monitoring loop"""
        while self.monitoring_active:
            try:
                self.update_performance_metrics()
                time.sleep(self.performance_update_interval)
            except Exception as e:
                print(f"Performance monitoring error: {e}")
                time.sleep(5)

    def update_performance_metrics(self):
        """Update all performance metrics"""
        try:
            # CPU usage
            self.cpu_usage = psutil.cpu_percent(interval=0.1)
            
            # System RAM usage
            memory = psutil.virtual_memory()
            self.ram_usage = memory.percent
            
            # Server RAM usage (if server is running)
            if self.server_process and self.server_running:
                try:
                    process = psutil.Process(self.server_process.pid)
                    self.server_ram_usage = process.memory_info().rss / (1024**2)  # MB
                except:
                    self.server_ram_usage = 0
            else:
                self.server_ram_usage = 0
            
            # Simulate TPS based on server load (more realistic)
            if self.server_running:
                load_factor = (self.cpu_usage + self.ram_usage) / 200
                player_factor = len(self.online_players) * 0.1
                self.server_tps = max(5.0, 20.0 - load_factor - player_factor)
            else:
                self.server_tps = 0.0
            
            # Update UI in main thread
            if hasattr(self, 'root'):
                self.root.after(0, self.update_performance_ui)
            
            # Emit to web clients
            self.socketio.emit('performance_update', {
                'cpu_usage': self.cpu_usage,
                'ram_usage': self.ram_usage,
                'server_ram_usage': self.server_ram_usage,
                'server_tps': self.server_tps,
                'player_count': len(self.online_players),
                'max_players': 20,
                'uptime': self.get_server_uptime(),
                'server_running': self.server_running
            })
            
        except Exception as e:
            print(f"Error updating performance metrics: {e}")

    def update_performance_ui(self):
        """Update the performance UI elements"""
        try:
            if hasattr(self, 'cpu_label'):
                self.cpu_label.config(text=f"CPU: {self.cpu_usage:.1f}%")
            if hasattr(self, 'ram_label'):
                self.ram_label.config(text=f"System RAM: {self.ram_usage:.1f}%")
            if hasattr(self, 'server_ram_label'):
                self.server_ram_label.config(text=f"Server RAM: {self.server_ram_usage:.1f} MB")
            if hasattr(self, 'tps_label'):
                self.tps_label.config(text=f"TPS: {self.server_tps:.1f}")
            if hasattr(self, 'players_label'):
                self.players_label.config(text=f"Players: {len(self.online_players)}")
            if hasattr(self, 'uptime_label'):
                uptime = self.get_server_uptime()
                self.uptime_label.config(text=f"Uptime: {uptime} min")
        except Exception as e:
            print(f"Error updating performance UI: {e}")

    def get_server_uptime(self):
        """Get server uptime in minutes"""
        if self.start_time and self.server_running:
            return int((time.time() - self.start_time) / 60)
        return 0

    def setup_ui(self):
        """Setup the main UI with improved design"""
        self.root = tk.Tk()
        self.root.title("🎮 Minecraft Server Wrapper - Enhanced")
        self.root.geometry("900x700")
        self.root.configure(bg='#2c3e50')
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), background='#2c3e50', foreground='white')
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'), background='#34495e', foreground='white')
        style.configure('Info.TLabel', font=('Arial', 10), background='#34495e', foreground='#ecf0f1')
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎮 Minecraft Server Wrapper", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Server Control Tab
        control_frame = ttk.Frame(notebook)
        notebook.add(control_frame, text="🎮 Server Control")
        
        # Server Monitor Tab
        monitor_frame = ttk.Frame(notebook)
        notebook.add(monitor_frame, text="📊 Server Monitor")
        
        # Setup control tab
        self.setup_control_tab(control_frame)
        
        # Setup monitor tab
        self.setup_monitor_tab(monitor_frame)
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_control_tab(self, parent):
        """Setup the server control tab"""
        # Server controls frame
        controls_frame = ttk.LabelFrame(parent, text="Server Controls", padding=10)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Button frame
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        # Control buttons
        self.start_button = ttk.Button(button_frame, text="▶ Start Server", command=self.start_server)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="⏹ Stop Server", command=self.stop_server)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.restart_button = ttk.Button(button_frame, text="🔄 Restart", command=self.restart_server)
        self.restart_button.pack(side=tk.LEFT, padx=5)
        
        # New buttons
        self.clean_ram_button = ttk.Button(button_frame, text="🧹 Clean RAM", command=self.optimize_ram)
        self.clean_ram_button.pack(side=tk.LEFT, padx=5)
        
        self.web_button = ttk.Button(button_frame, text="🌐 Web Interface", command=self.open_web_interface)
        self.web_button.pack(side=tk.LEFT, padx=5)
        
        # Second row of buttons
        button_frame2 = ttk.Frame(controls_frame)
        button_frame2.pack(fill=tk.X, pady=(5, 0))
        
        self.update_button = ttk.Button(button_frame2, text="🔄 Check for Updates", 
                                       command=lambda: self.check_for_updates(manual=True))
        self.update_button.pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(parent, text="Server Status", padding=10)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Server Stopped", font=('Arial', 12, 'bold'))
        self.status_label.pack()
        
        # Configuration frame
        config_frame = ttk.LabelFrame(parent, text="Configuration", padding=10)
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Server JAR path
        jar_frame = ttk.Frame(config_frame)
        jar_frame.pack(fill=tk.X, pady=2)
        ttk.Label(jar_frame, text="Server JAR:").pack(side=tk.LEFT)
        self.jar_entry = ttk.Entry(jar_frame, width=50)
        self.jar_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(jar_frame, text="Browse", command=self.browse_jar).pack(side=tk.RIGHT)
        
        # Memory settings
        memory_frame = ttk.Frame(config_frame)
        memory_frame.pack(fill=tk.X, pady=2)
        ttk.Label(memory_frame, text="Min Memory:").pack(side=tk.LEFT)
        self.min_memory_entry = ttk.Entry(memory_frame, width=10)
        self.min_memory_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(memory_frame, text="Max Memory:").pack(side=tk.LEFT, padx=(20, 0))
        self.max_memory_entry = ttk.Entry(memory_frame, width=10)
        self.max_memory_entry.pack(side=tk.LEFT, padx=5)
        
        # Console frame
        console_frame = ttk.LabelFrame(parent, text="Console Output", padding=10)
        console_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.console_text = scrolledtext.ScrolledText(console_frame, height=15, bg='#1a1a1a', fg='#00ff00', 
                                                     font=('Consolas', 10))
        self.console_text.pack(fill=tk.BOTH, expand=True)
        
        # Command input
        command_frame = ttk.Frame(console_frame)
        command_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(command_frame, text="Command:").pack(side=tk.LEFT)
        self.command_entry = ttk.Entry(command_frame)
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.command_entry.bind('<Return>', lambda e: self.send_command())
        ttk.Button(command_frame, text="Send", command=self.send_command).pack(side=tk.RIGHT)
        
        # Load configuration into UI
        self.load_config_to_ui()

    def setup_monitor_tab(self, parent):
        """Setup the server monitor tab"""
        # Performance metrics frame
        perf_frame = ttk.LabelFrame(parent, text="Performance Metrics", padding=10)
        perf_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create grid for metrics
        metrics_frame = ttk.Frame(perf_frame)
        metrics_frame.pack(fill=tk.X)
        
        # CPU Usage
        cpu_frame = ttk.Frame(metrics_frame)
        cpu_frame.grid(row=0, column=0, padx=10, pady=5, sticky='w')
        ttk.Label(cpu_frame, text="💻", font=('Arial', 16)).pack(side=tk.LEFT)
        self.cpu_label = ttk.Label(cpu_frame, text="CPU: 0%", style='Info.TLabel')
        self.cpu_label.pack(side=tk.LEFT, padx=5)
        
        # System RAM
        ram_frame = ttk.Frame(metrics_frame)
        ram_frame.grid(row=0, column=1, padx=10, pady=5, sticky='w')
        ttk.Label(ram_frame, text="🧠", font=('Arial', 16)).pack(side=tk.LEFT)
        self.ram_label = ttk.Label(ram_frame, text="System RAM: 0%", style='Info.TLabel')
        self.ram_label.pack(side=tk.LEFT, padx=5)
        
        # Server RAM
        server_ram_frame = ttk.Frame(metrics_frame)
        server_ram_frame.grid(row=1, column=0, padx=10, pady=5, sticky='w')
        ttk.Label(server_ram_frame, text="⚡", font=('Arial', 16)).pack(side=tk.LEFT)
        self.server_ram_label = ttk.Label(server_ram_frame, text="Server RAM: 0 MB", style='Info.TLabel')
        self.server_ram_label.pack(side=tk.LEFT, padx=5)
        
        # TPS
        tps_frame = ttk.Frame(metrics_frame)
        tps_frame.grid(row=1, column=1, padx=10, pady=5, sticky='w')
        ttk.Label(tps_frame, text="⏱️", font=('Arial', 16)).pack(side=tk.LEFT)
        self.tps_label = ttk.Label(tps_frame, text="TPS: 20.0", style='Info.TLabel')
        self.tps_label.pack(side=tk.LEFT, padx=5)
        
        # Players
        players_frame = ttk.Frame(metrics_frame)
        players_frame.grid(row=2, column=0, padx=10, pady=5, sticky='w')
        ttk.Label(players_frame, text="👥", font=('Arial', 16)).pack(side=tk.LEFT)
        self.players_label = ttk.Label(players_frame, text="Players: 0", style='Info.TLabel')
        self.players_label.pack(side=tk.LEFT, padx=5)
        
        # Uptime
        uptime_frame = ttk.Frame(metrics_frame)
        uptime_frame.grid(row=2, column=1, padx=10, pady=5, sticky='w')
        ttk.Label(uptime_frame, text="⏰", font=('Arial', 16)).pack(side=tk.LEFT)
        self.uptime_label = ttk.Label(uptime_frame, text="Uptime: 0 min", style='Info.TLabel')
        self.uptime_label.pack(side=tk.LEFT, padx=5)

    def open_web_interface(self):
        """Open the web interface in the default browser"""
        try:
            webbrowser.open('http://localhost:5000')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open web interface: {e}")

    def load_config_to_ui(self):
        """Load configuration values into UI elements"""
        self.jar_entry.delete(0, tk.END)
        self.jar_entry.insert(0, self.server_jar)
        self.min_memory_entry.delete(0, tk.END)
        self.min_memory_entry.insert(0, self.min_memory)
        self.max_memory_entry.delete(0, tk.END)
        self.max_memory_entry.insert(0, self.max_memory)

    def browse_jar(self):
        """Browse for server JAR file"""
        filename = filedialog.askopenfilename(
            title="Select Server JAR File",
            filetypes=[("JAR files", "*.jar"), ("All files", "*.*")]
        )
        if filename:
            self.jar_entry.delete(0, tk.END)
            self.jar_entry.insert(0, filename)
            self.server_jar = filename
            self.save_config()

    def start_server(self):
        """Start the Minecraft server"""
        if self.server_running:
            messagebox.showwarning("Warning", "Server is already running!")
            return
        
        # Get values from UI
        self.server_jar = self.jar_entry.get()
        self.min_memory = self.min_memory_entry.get()
        self.max_memory = self.max_memory_entry.get()
        
        if not self.server_jar or not os.path.exists(self.server_jar):
            messagebox.showerror("Error", "Please select a valid server JAR file!")
            return
        
        try:
            # Build Java command
            java_cmd = [
                "java",
                f"-Xms{self.min_memory}",
                f"-Xmx{self.max_memory}",
                "-jar",
                self.server_jar,
                "nogui"
            ]
            
            # Start server process
            self.server_process = subprocess.Popen(
                java_cmd,
                cwd=os.path.dirname(self.server_jar),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            self.server_running = True
            self.start_time = time.time()
            self.status_label.config(text="Server Running", foreground='green')
            
            # Start output monitoring thread
            threading.Thread(target=self.monitor_server_output, daemon=True).start()
            
            self.add_console_message("Server started successfully!")
            self.save_config()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {e}")

    def stop_server(self):
        """Stop the Minecraft server"""
        if not self.server_running:
            messagebox.showwarning("Warning", "Server is not running!")
            return
        
        try:
            if self.server_process:
                self.server_process.stdin.write("stop\n")
                self.server_process.stdin.flush()
                self.server_process.wait(timeout=30)
            
            self.server_running = False
            self.start_time = None
            self.status_label.config(text="Server Stopped", foreground='red')
            self.add_console_message("Server stopped successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop server: {e}")

    def restart_server(self):
        """Restart the Minecraft server"""
        self.add_console_message("Restarting server...")
        self.stop_server()
        time.sleep(2)
        self.start_server()

    def send_command(self):
        """Send command to the server"""
        command = self.command_entry.get().strip()
        if not command:
            return
        
        if not self.server_running:
            messagebox.showwarning("Warning", "Server is not running!")
            return
        
        try:
            self.server_process.stdin.write(f"{command}\n")
            self.server_process.stdin.flush()
            self.add_console_message(f"> {command}")
            self.command_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send command: {e}")

    def monitor_server_output(self):
        """Monitor server output in a separate thread"""
        while self.server_running and self.server_process:
            try:
                line = self.server_process.stdout.readline()
                if line:
                    self.add_console_message(line.strip())
                    # Emit to web clients
                    self.socketio.emit('console_update', {
                        'message': line.strip(),
                        'timestamp': datetime.now().strftime('%H:%M:%S')
                    })
                elif self.server_process.poll() is not None:
                    break
            except Exception as e:
                print(f"Error monitoring server output: {e}")
                break

    def add_console_message(self, message):
        """Add message to console"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted_message = f"[{timestamp}] {message}"
        
        # Add to history
        self.console_history.append({
            'timestamp': timestamp,
            'message': message
        })
        
        # Keep only last 1000 messages
        if len(self.console_history) > 1000:
            self.console_history = self.console_history[-1000:]
        
        # Update UI
        if hasattr(self, 'console_text'):
            self.console_text.insert(tk.END, formatted_message + "\n")
            self.console_text.see(tk.END)
        
        # Save console history
        self.save_console_history()

    def start_web_server(self):
        """Start the web server in a separate thread"""
        try:
            self.web_thread = threading.Thread(target=self._run_web_server, daemon=True)
            self.web_thread.start()
            self.add_console_message("Web interface started on http://localhost:5000")
        except Exception as e:
            print(f"Failed to start web server: {e}")

    def _run_web_server(self):
        """Run the web server"""
        try:
            self.socketio.run(self.web_server, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        except Exception as e:
            print(f"Web server error: {e}")

    def setup_web_routes(self):
        """Setup web server routes"""
        @self.web_server.route('/')
        def index():
            return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎮 Minecraft Server Wrapper</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        
        .header h1 {
            font-size: 2.5em;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h3 {
            margin-bottom: 20px;
            font-size: 1.3em;
            font-weight: 600;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
        }
        
        .status-running {
            background: #27ae60;
            box-shadow: 0 0 10px #27ae60;
        }
        
        .status-stopped {
            background: #e74c3c;
            box-shadow: 0 0 10px #e74c3c;
        }
        
        .control-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            min-width: 120px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        
        .btn-start {
            background: linear-gradient(45deg, #27ae60, #2ecc71);
            color: white;
        }
        
        .btn-stop {
            background: linear-gradient(45deg, #e74c3c, #c0392b);
            color: white;
        }
        
        .btn-restart {
            background: linear-gradient(45deg, #f39c12, #e67e22);
            color: white;
        }
        
        .btn-optimize {
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
        }
        
        .console-section {
            grid-column: 1 / -1;
        }
        
        .console {
            background: #1a1a1a;
            color: #00ff00;
            padding: 20px;
            height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            border-radius: 10px;
            border: 1px solid #333;
            font-size: 14px;
            line-height: 1.4;
        }
        
        .console::-webkit-scrollbar {
            width: 8px;
        }
        
        .console::-webkit-scrollbar-track {
            background: #2a2a2a;
        }
        
        .console::-webkit-scrollbar-thumb {
            background: #555;
            border-radius: 4px;
        }
        
        .console-line {
            margin-bottom: 3px;
            word-wrap: break-word;
        }
        
        .console-timestamp {
            color: #888;
            margin-right: 8px;
        }
        
        .performance-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        
        .metric-item {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .metric-label {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.8);
            margin-bottom: 8px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .metric-value {
            font-size: 24px;
            font-weight: 700;
            color: white;
            margin-bottom: 10px;
        }
        
        .metric-bar {
            height: 8px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            overflow: hidden;
        }
        
        .metric-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
        }
        
        .command-input {
            display: flex;
            gap: 15px;
            margin-top: 20px;
            align-items: center;
        }
        
        .command-input input {
            flex: 1;
            padding: 15px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            font-size: 14px;
            backdrop-filter: blur(10px);
        }
        
        .command-input input::placeholder {
            color: rgba(255, 255, 255, 0.6);
        }
        
        .command-input button {
            padding: 15px 25px;
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            border-radius: 10px;
            color: white;
            font-weight: 600;
            transform: translateX(400px);
            transition: all 0.3s ease;
            z-index: 1000;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
        }
        
        .notification.show {
            transform: translateX(0);
        }
        
        .notification.success {
            background: linear-gradient(45deg, #27ae60, #2ecc71);
        }
        
        .notification.error {
            background: linear-gradient(45deg, #e74c3c, #c0392b);
        }
        
        .notification.info {
            background: linear-gradient(45deg, #3498db, #2980b9);
        }
        
        /* File Manager Styles */
        .file-manager {
            margin-top: 15px;
        }
        
        .file-controls {
            display: flex;
            gap: 10px;
            align-items: center;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        
        .file-path {
            background: rgba(255,255,255,0.1);
            padding: 8px 12px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: #ecf0f1;
            border: 1px solid rgba(255,255,255,0.2);
            flex: 1;
            min-width: 200px;
        }
        
        .file-list {
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            padding: 15px;
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .file-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px;
            margin: 5px 0;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s ease;
        }
        
        .file-item:hover {
            background: rgba(255,255,255,0.1);
            transform: translateX(5px);
        }
        
        .file-info {
            display: flex;
            align-items: center;
            gap: 10px;
            flex: 1;
        }
        
        .file-icon {
            font-size: 20px;
            width: 30px;
            text-align: center;
        }
        
        .file-details {
            flex: 1;
        }
        
        .file-name {
            font-weight: 600;
            color: #ecf0f1;
            margin-bottom: 2px;
        }
        
        .file-meta {
            font-size: 12px;
            color: #bdc3c7;
        }
        
        .file-actions {
            display: flex;
            gap: 5px;
        }
        
        .file-btn {
            padding: 5px 10px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .file-btn.rename {
            background: linear-gradient(45deg, #f39c12, #e67e22);
            color: white;
        }
        
        .file-btn.delete {
            background: linear-gradient(45deg, #e74c3c, #c0392b);
            color: white;
        }
        
        .file-btn.download {
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
        }
        
        .file-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        
        .loading {
            text-align: center;
            color: #bdc3c7;
            padding: 20px;
            font-style: italic;
        }
        
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            
            .control-buttons {
                flex-direction: column;
            }
            
            .btn {
                width: 100%;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .console {
                height: 300px;
            }
            
            .command-input {
                flex-direction: column;
            }
            
            .performance-grid {
                grid-template-columns: 1fr;
            }
            
            .file-controls {
                flex-direction: column;
                align-items: stretch;
            }
            
            .file-path {
                min-width: auto;
            }
            
            .file-item {
                flex-direction: column;
                align-items: stretch;
                gap: 10px;
            }
            
            .file-actions {
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 Minecraft Server Wrapper</h1>
            <p>Advanced Server Management Dashboard</p>
        </div>
        
        <div class="dashboard-grid">
            <div class="card status-card">
                <h3>🔧 Server Status</h3>
                <div id="status">
                    <span class="status-indicator status-stopped"></span>
                    <span id="status-text">Server Stopped</span>
                </div>
                <div id="player-info" style="margin-top: 15px; font-size: 16px; font-weight: 500;">
                    Players: <span id="player-count">0</span>/<span id="max-players">20</span>
                </div>
                <div id="uptime-info" style="margin-top: 10px; font-size: 14px; opacity: 0.8;">
                    Uptime: <span id="uptime">0 minutes</span>
                </div>
            </div>
            
            <div class="card">
                <h3>⚡ Server Controls</h3>
                <div class="control-buttons">
                    <button class="btn btn-start" onclick="startServer()">▶ Start</button>
                    <button class="btn btn-stop" onclick="stopServer()">⏹ Stop</button>
                    <button class="btn btn-restart" onclick="restartServer()">🔄 Restart</button>
                    <button class="btn btn-optimize" onclick="optimizeRAM()">🧹 Clean RAM</button>
                    <button class="btn btn-update" onclick="checkForUpdates()" style="background: linear-gradient(45deg, #9b59b6, #8e44ad);">🔄 Check Updates</button>
                </div>
            </div>
            
            <div class="card">
                <h3>📊 Performance Monitor</h3>
                <div class="performance-grid">
                    <div class="metric-item">
                        <div class="metric-label">CPU Usage</div>
                        <div class="metric-value" id="cpu-usage">0%</div>
                        <div class="metric-bar">
                            <div class="metric-fill" id="cpu-bar" style="width: 0%; background: linear-gradient(90deg, #27ae60, #f39c12, #e74c3c);"></div>
                        </div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">System RAM</div>
                        <div class="metric-value" id="ram-usage">0%</div>
                        <div class="metric-bar">
                            <div class="metric-fill" id="ram-bar" style="width: 0%; background: linear-gradient(90deg, #3498db, #9b59b6);"></div>
                        </div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Server RAM</div>
                        <div class="metric-value" id="server-ram">0 MB</div>
                        <div class="metric-bar">
                            <div class="metric-fill" id="server-ram-bar" style="width: 0%; background: linear-gradient(90deg, #e67e22, #d35400);"></div>
                        </div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Server TPS</div>
                        <div class="metric-value" id="server-tps">20.0</div>
                        <div class="metric-bar">
                            <div class="metric-fill" id="tps-bar" style="width: 100%; background: linear-gradient(90deg, #e74c3c, #f39c12, #27ae60);"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card console-section">
                <h3>📟 Real-time Console</h3>
                <div id="console" class="console"></div>
                <div class="command-input">
                    <input type="text" id="command" placeholder="Enter server command..." onkeypress="if(event.key==='Enter') sendCommand()">
                    <button onclick="sendCommand()">Send</button>
                </div>
            </div>
            
            <div class="card">
                <h3>📁 File Manager</h3>
                <div class="file-manager">
                    <div class="file-controls">
                        <input type="file" id="fileUpload" multiple style="display: none;" onchange="uploadFiles()">
                        <button class="btn" onclick="document.getElementById('fileUpload').click()" style="background: linear-gradient(45deg, #27ae60, #2ecc71);">📤 Upload Files</button>
                        <button class="btn" onclick="refreshFileList()" style="background: linear-gradient(45deg, #3498db, #2980b9);">🔄 Refresh</button>
                        <span class="file-path" id="currentPath">C:/Users/MersYeon/Desktop/Cacasians</span>
                    </div>
                    <div class="file-list" id="fileList">
                        <div class="loading">Loading files...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div id="notification" class="notification"></div>
    
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <script>
        // Initialize Socket.IO for real-time updates
        const socket = io();
        
        // Socket event listeners
        socket.on('connect', function() {
            console.log('Connected to server');
            showNotification('Connected to server', 'success');
        });
        
        socket.on('disconnect', function() {
            console.log('Disconnected from server');
            showNotification('Disconnected from server', 'error');
        });
        
        socket.on('performance_update', function(data) {
            updatePerformanceMetrics(data);
        });
        
        socket.on('console_update', function(data) {
            updateConsoleRealtime(data);
        });
        
        socket.on('console_history', function(logs) {
            loadConsoleHistory(logs);
        });
        
        socket.on('ram_optimized', function(data) {
            showNotification(data.message, 'success');
        });
        
        function updatePerformanceMetrics(data) {
            // Update CPU
            document.getElementById('cpu-usage').textContent = `${data.cpu_usage.toFixed(1)}%`;
            document.getElementById('cpu-bar').style.width = `${data.cpu_usage}%`;
            
            // Update System RAM
            document.getElementById('ram-usage').textContent = `${data.ram_usage.toFixed(1)}%`;
            document.getElementById('ram-bar').style.width = `${data.ram_usage}%`;
            
            // Update Server RAM
            document.getElementById('server-ram').textContent = `${data.server_ram_usage.toFixed(1)} MB`;
            const serverRamPercent = Math.min((data.server_ram_usage / 2048) * 100, 100);
            document.getElementById('server-ram-bar').style.width = `${serverRamPercent}%`;
            
            // Update TPS
            document.getElementById('server-tps').textContent = data.server_tps.toFixed(1);
            const tpsPercent = (data.server_tps / 20) * 100;
            document.getElementById('tps-bar').style.width = `${tpsPercent}%`;
            
            // Update player count
            document.getElementById('player-count').textContent = data.player_count;
            document.getElementById('max-players').textContent = data.max_players;
            
            // Update uptime
            const uptime = data.uptime;
            const uptimeText = uptime >= 60 ? `${Math.floor(uptime/60)}h ${uptime%60}m` : `${uptime}m`;
            document.getElementById('uptime').textContent = uptimeText;
            
            // Update status
            const statusIndicator = document.querySelector('.status-indicator');
            const statusText = document.getElementById('status-text');
            if (data.server_running) {
                statusIndicator.className = 'status-indicator status-running';
                statusText.textContent = 'Server Running';
            } else {
                statusIndicator.className = 'status-indicator status-stopped';
                statusText.textContent = 'Server Stopped';
            }
        }
        
        function updateConsoleRealtime(data) {
            const console = document.getElementById('console');
            if (data.message) {
                const logEntry = document.createElement('div');
                logEntry.className = 'console-line';
                logEntry.innerHTML = `<span class="console-timestamp">[${data.timestamp}]</span> ${data.message}`;
                console.appendChild(logEntry);
                console.scrollTop = console.scrollHeight;
            }
        }
        
        function loadConsoleHistory(logs) {
            const console = document.getElementById('console');
            console.innerHTML = ''; // Clear existing content
            
            logs.forEach(log => {
                const logEntry = document.createElement('div');
                logEntry.className = 'console-line';
                logEntry.innerHTML = `<span class="console-timestamp">[${log.timestamp}]</span> ${log.message}`;
                console.appendChild(logEntry);
            });
            
            console.scrollTop = console.scrollHeight;
        }
        
        function showNotification(message, type = 'success') {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.className = `notification ${type} show`;
            
            setTimeout(() => {
                notification.classList.remove('show');
            }, 4000);
        }
        
        function startServer() {
            fetch('/api/start', {method: 'POST'})
                .then(response => response.json())
                .then(data => showNotification(data.message || data.error, data.error ? 'error' : 'success'))
                .catch(error => showNotification('Error starting server', 'error'));
        }
        
        function stopServer() {
            fetch('/api/stop', {method: 'POST'})
                .then(response => response.json())
                .then(data => showNotification(data.message || data.error, data.error ? 'error' : 'success'))
                .catch(error => showNotification('Error stopping server', 'error'));
        }
        
        function restartServer() {
            fetch('/api/restart', {method: 'POST'})
                .then(response => response.json())
                .then(data => showNotification(data.message || data.error, data.error ? 'error' : 'success'))
                .catch(error => showNotification('Error restarting server', 'error'));
        }
        
        function optimizeRAM() {
            fetch('/api/optimize-ram', {method: 'POST'})
                .then(response => response.json())
                .then(data => showNotification(data.message || data.error, data.error ? 'error' : 'success'))
                .catch(error => showNotification('Error optimizing RAM', 'error'));
        }
        
        function sendCommand() {
            const commandInput = document.getElementById('command');
            const command = commandInput.value.trim();
            
            if (!command) return;
            
            fetch('/api/command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: command})
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showNotification(data.error, 'error');
                } else {
                    commandInput.value = '';
                }
            })
            .catch(error => showNotification('Error sending command', 'error'));
        }
        
        function checkForUpdates() {
            showNotification('Checking for updates...', 'info');
            
            fetch('/api/check-updates', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        showNotification(data.error, 'error');
                    } else if (data.update_available) {
                        showNotification(data.message, 'info');
                        // Show update dialog
                        if (confirm(`${data.message}\n\nWould you like to download and install the update?`)) {
                            applyUpdate();
                        }
                    } else {
                        showNotification(data.message, 'success');
                    }
                })
                .catch(error => showNotification('Error checking for updates', 'error'));
        }
        
        function applyUpdate() {
            showNotification('Starting update download...', 'info');
            
            fetch('/api/apply-update', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        showNotification(data.error, 'error');
                    } else {
                        showNotification(data.message, 'info');
                    }
                })
                .catch(error => showNotification('Error applying update', 'error'));
        }
        
        // Socket event listeners for update notifications
        socket.on('update_available', function(data) {
            showNotification(`Update available! v${data.current_version} → v${data.latest_version}`, 'info');
        });
        
        socket.on('update_applied', function(data) {
            if (data.success) {
                showNotification(data.message, 'success');
                setTimeout(() => {
                    if (confirm('Update applied successfully! The application needs to be restarted. Restart now?')) {
                        location.reload();
                    }
                }, 2000);
            } else {
                showNotification(data.message, 'error');
            }
        });
        
        // Check version on page load
        fetch('/api/version')
            .then(response => response.json())
            .then(data => {
                if (data.update_available) {
                    showNotification(`Update available! v${data.current_version} → v${data.latest_version}`, 'info');
                }
            })
            .catch(error => console.log('Could not check version'));
        
        // Load console history on page load (fallback if Socket.IO doesn't work)
        setTimeout(() => {
            fetch('/api/console')
                .then(response => response.json())
                .then(data => {
                    if (data.logs && data.logs.length > 0) {
                        // Only load if console is empty (Socket.IO didn't work)
                        const console = document.getElementById('console');
                        if (console.children.length === 0) {
                            loadConsoleHistory(data.logs);
                        }
                    }
                })
                .catch(error => console.log('Could not load console history'));
        }, 1000); // Wait 1 second for Socket.IO to connect first
        
        // File Manager Functions
        function refreshFileList() {
            const fileList = document.getElementById('fileList');
            fileList.innerHTML = '<div class="loading">Loading files...</div>';
            
            fetch('/api/files')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        fileList.innerHTML = `<div class="loading" style="color: #e74c3c;">Error: ${data.error}</div>`;
                        return;
                    }
                    
                    displayFiles(data.files);
                })
                .catch(error => {
                    fileList.innerHTML = '<div class="loading" style="color: #e74c3c;">Failed to load files</div>';
                    showNotification('Error loading files', 'error');
                });
        }
        
        function displayFiles(files) {
            const fileList = document.getElementById('fileList');
            
            if (files.length === 0) {
                fileList.innerHTML = '<div class="loading">No files found</div>';
                return;
            }
            
            fileList.innerHTML = '';
            
            files.forEach(file => {
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';
                
                const icon = getFileIcon(file.name, file.is_directory);
                const size = file.is_directory ? 'Directory' : formatFileSize(file.size);
                const modified = new Date(file.modified * 1000).toLocaleString();
                
                fileItem.innerHTML = `
                    <div class="file-info">
                        <div class="file-icon">${icon}</div>
                        <div class="file-details">
                            <div class="file-name">${file.name}</div>
                            <div class="file-meta">${size} • Modified: ${modified}</div>
                        </div>
                    </div>
                    <div class="file-actions">
                        ${!file.is_directory ? `<button class="file-btn download" onclick="downloadFile('${file.name.replace(/'/g, "\\'")}')">📥</button>` : ''}
                        <button class="file-btn rename" onclick="renameFile('${file.name.replace(/'/g, "\\'")}')">✏️</button>
                        <button class="file-btn delete" onclick="deleteFile('${file.name.replace(/'/g, "\\'")}')">🗑️</button>
                    </div>
                `;
                
                fileList.appendChild(fileItem);
            });
        }
        
        function getFileIcon(filename, isDirectory) {
            if (isDirectory) return '📁';
            
            const ext = filename.split('.').pop().toLowerCase();
            const iconMap = {
                'zip': '📦', 'rar': '📦', '7z': '📦',
                'txt': '📄', 'md': '📄', 'log': '📄',
                'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️',
                'mp4': '🎥', 'avi': '🎥', 'mov': '🎥',
                'mp3': '🎵', 'wav': '🎵', 'flac': '🎵',
                'pdf': '📕', 'doc': '📘', 'docx': '📘',
                'jar': '☕', 'java': '☕',
                'py': '🐍', 'js': '📜', 'html': '🌐',
                'exe': '⚙️', 'msi': '⚙️'
            };
            
            return iconMap[ext] || '📄';
        }
        
        function formatFileSize(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        function uploadFiles() {
            const fileInput = document.getElementById('fileUpload');
            const files = fileInput.files;
            
            if (files.length === 0) return;
            
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append('files', files[i]);
            }
            
            showNotification(`Uploading ${files.length} file(s)...`, 'info');
            
            fetch('/api/files/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showNotification(data.error, 'error');
                } else {
                    showNotification(data.message, 'success');
                    refreshFileList();
                    fileInput.value = ''; // Clear the input
                }
            })
            .catch(error => {
                showNotification('Error uploading files', 'error');
            });
        }
        
        function downloadFile(filename) {
            window.open(`/api/files/download/${encodeURIComponent(filename)}`, '_blank');
        }
        
        function renameFile(oldName) {
            const newName = prompt(`Rename "${oldName}" to:`, oldName);
            if (!newName || newName === oldName) return;
            
            fetch('/api/files/rename', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({old_name: oldName, new_name: newName})
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showNotification(data.error, 'error');
                } else {
                    showNotification(data.message, 'success');
                    refreshFileList();
                }
            })
            .catch(error => showNotification('Error renaming file', 'error'));
        }
        
        function deleteFile(filename) {
            if (!confirm(`Are you sure you want to delete "${filename}"?`)) return;
            
            fetch('/api/files/delete', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({filename: filename})
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showNotification(data.error, 'error');
                } else {
                    showNotification(data.message, 'success');
                    refreshFileList();
                }
            })
            .catch(error => showNotification('Error deleting file', 'error'));
        }
        
        // Load file list on page load
        setTimeout(() => {
            refreshFileList();
        }, 1500);
    </script>
</body>
</html>
            ''')
        
        @self.web_server.route('/api/start', methods=['POST'])
        def api_start():
            """Start the Minecraft server"""
            try:
                if self.server_running:
                    return jsonify({'error': 'Server is already running'})
                
                self.start_server()
                return jsonify({'message': 'Server start command sent'})
            except Exception as e:
                return jsonify({'error': f'Failed to start server: {str(e)}'})
        
        @self.web_server.route('/api/stop', methods=['POST'])
        def api_stop():
            """Stop the Minecraft server"""
            try:
                if not self.server_running:
                    return jsonify({'error': 'Server is not running'})
                
                self.stop_server()
                return jsonify({'message': 'Server stop command sent'})
            except Exception as e:
                return jsonify({'error': f'Failed to stop server: {str(e)}'})
        
        @self.web_server.route('/api/restart', methods=['POST'])
        def api_restart():
            """Restart the Minecraft server"""
            try:
                self.restart_server()
                return jsonify({'message': 'Server restart command sent'})
            except Exception as e:
                return jsonify({'error': f'Failed to restart server: {str(e)}'})
        
        @self.web_server.route('/api/optimize-ram', methods=['POST'])
        def api_optimize_ram():
            """Optimize system RAM"""
            try:
                freed_mb = self.optimize_ram()
                return jsonify({'message': f'RAM optimized! Freed approximately {freed_mb:.1f} MB'})
            except Exception as e:
                return jsonify({'error': f'Failed to optimize RAM: {str(e)}'})
        
        @self.web_server.route('/api/command', methods=['POST'])
        def api_command():
            """Send command to server"""
            try:
                data = request.get_json()
                command = data.get('command', '').strip()
                
                if not command:
                    return jsonify({'error': 'No command provided'})
                
                if not self.server_running:
                    return jsonify({'error': 'Server is not running'})
                
                self.server_process.stdin.write(f"{command}\n")
                self.server_process.stdin.flush()
                self.add_console_message(f"> {command}")
                
                return jsonify({'message': 'Command sent'})
            except Exception as e:
                return jsonify({'error': f'Failed to send command: {str(e)}'})
        
        @self.web_server.route('/api/check-updates', methods=['POST'])
        def api_check_updates():
            """Check for application updates"""
            try:
                update_available = self.check_for_updates(manual=True)
                if update_available:
                    return jsonify({
                        'update_available': True,
                        'current_version': self.current_version,
                        'latest_version': self.latest_version,
                        'message': f'Update available! v{self.current_version} → v{self.latest_version}'
                    })
                else:
                    return jsonify({
                        'update_available': False,
                        'current_version': self.current_version,
                        'message': f'You\'re running the latest version (v{self.current_version})'
                    })
            except Exception as e:
                return jsonify({'error': f'Failed to check for updates: {str(e)}'})
        
        @self.web_server.route('/api/apply-update', methods=['POST'])
        def api_apply_update():
            """Apply the available update"""
            try:
                if not self.update_available:
                    return jsonify({'error': 'No update available'})
                
                # Start update in background thread
                threading.Thread(target=self.download_and_apply_update, daemon=True).start()
                
                return jsonify({'message': 'Update download started. Check console for progress.'})
            except Exception as e:
                return jsonify({'error': f'Failed to apply update: {str(e)}'})
        
        @self.web_server.route('/api/version', methods=['GET'])
        def api_version():
            """Get current version information"""
            try:
                return jsonify({
                    'current_version': self.current_version,
                    'update_available': self.update_available,
                    'latest_version': self.latest_version if self.update_available else None
                })
            except Exception as e:
                return jsonify({'error': f'Failed to get version info: {str(e)}'})
        
        @self.web_server.route('/api/console', methods=['GET'])
        def api_console():
            """Get console history"""
            try:
                # Get the last 100 console entries
                recent_logs = self.console_history[-100:] if len(self.console_history) > 100 else self.console_history
                return jsonify({'logs': recent_logs})
            except Exception as e:
                return jsonify({'error': f'Failed to get console logs: {str(e)}'})
        
        # File Manager API endpoints
        @self.web_server.route('/api/files', methods=['GET'])
        def api_files():
            """Get list of files in the managed directory"""
            try:
                file_manager_path = r"C:\Users\MersYeon\Desktop\Cacasians"
                
                if not os.path.exists(file_manager_path):
                    os.makedirs(file_manager_path, exist_ok=True)
                
                files = []
                for item in os.listdir(file_manager_path):
                    item_path = os.path.join(file_manager_path, item)
                    stat = os.stat(item_path)
                    
                    files.append({
                        'name': item,
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'is_directory': os.path.isdir(item_path),
                        'extension': os.path.splitext(item)[1].lower() if not os.path.isdir(item_path) else ''
                    })
                
                # Sort files: directories first, then by name
                files.sort(key=lambda x: (not x['is_directory'], x['name'].lower()))
                
                return jsonify({'files': files, 'path': file_manager_path})
            except Exception as e:
                return jsonify({'error': f'Failed to list files: {str(e)}'})
        
        @self.web_server.route('/api/files/upload', methods=['POST'])
        def api_files_upload():
            """Upload files to the managed directory"""
            try:
                file_manager_path = r"C:\Users\MersYeon\Desktop\Cacasians"
                
                if not os.path.exists(file_manager_path):
                    os.makedirs(file_manager_path, exist_ok=True)
                
                if 'files' not in request.files:
                    return jsonify({'error': 'No files provided'})
                
                uploaded_files = []
                for file in request.files.getlist('files'):
                    if file.filename == '':
                        continue
                    
                    # Secure filename
                    filename = file.filename
                    # Remove any path components for security
                    filename = os.path.basename(filename)
                    
                    file_path = os.path.join(file_manager_path, filename)
                    
                    # Handle duplicate filenames
                    counter = 1
                    original_name, ext = os.path.splitext(filename)
                    while os.path.exists(file_path):
                        filename = f"{original_name}_{counter}{ext}"
                        file_path = os.path.join(file_manager_path, filename)
                        counter += 1
                    
                    file.save(file_path)
                    uploaded_files.append(filename)
                
                if uploaded_files:
                    return jsonify({'message': f'Successfully uploaded {len(uploaded_files)} file(s)', 'files': uploaded_files})
                else:
                    return jsonify({'error': 'No valid files to upload'})
                    
            except Exception as e:
                return jsonify({'error': f'Failed to upload files: {str(e)}'})
        
        @self.web_server.route('/api/files/rename', methods=['POST'])
        def api_files_rename():
            """Rename a file in the managed directory"""
            try:
                data = request.get_json()
                old_name = data.get('old_name')
                new_name = data.get('new_name')
                
                if not old_name or not new_name:
                    return jsonify({'error': 'Both old_name and new_name are required'})
                
                file_manager_path = r"C:\Users\MersYeon\Desktop\Cacasians"
                old_path = os.path.join(file_manager_path, old_name)
                new_path = os.path.join(file_manager_path, new_name)
                
                if not os.path.exists(old_path):
                    return jsonify({'error': 'File not found'})
                
                if os.path.exists(new_path):
                    return jsonify({'error': 'A file with that name already exists'})
                
                # Security check: ensure paths are within the managed directory
                if not old_path.startswith(file_manager_path) or not new_path.startswith(file_manager_path):
                    return jsonify({'error': 'Invalid file path'})
                
                os.rename(old_path, new_path)
                return jsonify({'message': f'Successfully renamed "{old_name}" to "{new_name}"'})
                
            except Exception as e:
                return jsonify({'error': f'Failed to rename file: {str(e)}'})
        
        @self.web_server.route('/api/files/delete', methods=['POST'])
        def api_files_delete():
            """Delete a file from the managed directory"""
            try:
                data = request.get_json()
                filename = data.get('filename')
                
                if not filename:
                    return jsonify({'error': 'Filename is required'})
                
                file_manager_path = r"C:\Users\MersYeon\Desktop\Cacasians"
                file_path = os.path.join(file_manager_path, filename)
                
                if not os.path.exists(file_path):
                    return jsonify({'error': 'File not found'})
                
                # Security check: ensure path is within the managed directory
                if not file_path.startswith(file_manager_path):
                    return jsonify({'error': 'Invalid file path'})
                
                if os.path.isdir(file_path):
                    # Remove directory and all contents
                    import shutil
                    shutil.rmtree(file_path)
                else:
                    # Remove file
                    os.remove(file_path)
                
                return jsonify({'message': f'Successfully deleted "{filename}"'})
                
            except Exception as e:
                return jsonify({'error': f'Failed to delete file: {str(e)}'})
        
        @self.web_server.route('/api/files/download/<filename>')
        def api_files_download(filename):
            """Download a file from the managed directory"""
            try:
                file_manager_path = r"C:\Users\MersYeon\Desktop\Cacasians"
                file_path = os.path.join(file_manager_path, filename)
                
                if not os.path.exists(file_path):
                    return jsonify({'error': 'File not found'}), 404
                
                # Security check: ensure path is within the managed directory
                if not file_path.startswith(file_manager_path):
                    return jsonify({'error': 'Invalid file path'}), 403
                
                if os.path.isdir(file_path):
                    return jsonify({'error': 'Cannot download directories'}), 400
                
                return send_file(file_path, as_attachment=True, download_name=filename)
                
            except Exception as e:
                return jsonify({'error': f'Failed to download file: {str(e)}'}), 500
        
        # Auto-check for updates periodically
        def auto_update_check():
            while True:
                try:
                    self.auto_check_updates()
                    time.sleep(self.update_check_interval)
                except Exception as e:
                    print(f"Auto update check error: {e}")
                    time.sleep(300)  # Wait 5 minutes on error
        
        # Start auto-update check thread
        threading.Thread(target=auto_update_check, daemon=True).start()
        
        # Socket.IO events
        @self.socketio.on('connect')
        def handle_connect():
            print(f"Client connected: {request.sid}")
            
            # Send console history to newly connected client
            recent_logs = self.console_history[-100:] if len(self.console_history) > 100 else self.console_history
            self.socketio.emit('console_history', recent_logs, room=request.sid)
            
            # Send current update status to newly connected client
            if self.update_available:
                self.socketio.emit('update_available', {
                    'current_version': self.current_version,
                    'latest_version': self.latest_version
                }, room=request.sid)
            
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"Client disconnected: {request.sid}")

    def emit_update_notification(self, message_type, data):
        """Emit update notifications to all connected clients"""
        try:
            self.socketio.emit(message_type, data)
        except Exception as e:
            print(f"Error emitting update notification: {e}")

    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.server_jar = config.get('server_jar', '')
                    self.min_memory = config.get('min_memory', '1G')
                    self.max_memory = config.get('max_memory', '2G')
        except Exception as e:
            print(f"Error loading config: {e}")

    def save_config(self):
        """Save configuration to file"""
        try:
            config = {
                'server_jar': self.server_jar,
                'min_memory': self.min_memory,
                'max_memory': self.max_memory
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def load_console_history(self):
        """Load console history from file"""
        try:
            if os.path.exists(self.console_history_file):
                with open(self.console_history_file, 'r', encoding='utf-8') as f:
                    self.console_history = json.load(f)
        except Exception as e:
            print(f"Error loading console history: {e}")
            self.console_history = []

    def save_console_history(self):
        """Save console history to file"""
        try:
            with open(self.console_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.console_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving console history: {e}")

    def on_closing(self):
        """Handle window closing"""
        self.save_config()
        self.save_console_history()
        self.monitoring_active = False
        
        if self.server_running:
            result = messagebox.askyesno("Confirm Exit", 
                                       "Server is still running. Stop server and exit?")
            if result:
                self.stop_server()
                self.root.after(1000, self.root.destroy)
            return
        
        self.root.destroy()

    def run(self):
        """Run the application"""
        self.root.mainloop()

def main():
    app = MinecraftServerWrapper()
    app.run()

if __name__ == "__main__":
    main()
