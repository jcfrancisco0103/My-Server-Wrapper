import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import subprocess
import threading
import os
import json
import time
from datetime import datetime
import webbrowser
import sys
import psutil
import re
import hashlib
import secrets
import zipfile
import shutil
from pathlib import Path
import requests
# Windows-specific imports (conditional)
try:
    import winreg
    WINDOWS_PLATFORM = True
except ImportError:
    WINDOWS_PLATFORM = False
    winreg = None
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, send_file
from flask_socketio import SocketIO, emit
from werkzeug.serving import make_server
from werkzeug.utils import secure_filename

class MinecraftServerWrapper:
    def __init__(self, root):
        self.root = root
        self.root.title("Cacasians Minecraft Server Wrapper")
        self.root.geometry("800x600")
        self.root.configure(bg="#2c3e50")
        self.root.resizable(True, True)
        self.root.minsize(700, 500)
        
        # Set default font
        self.default_font = ("Segoe UI", 10)
        self.title_font = ("Segoe UI", 16, "bold")
        self.button_font = ("Segoe UI", 10, "bold")
        self.label_font = ("Segoe UI", 10)
        self.console_font = ("Consolas", 10)
        
        # Configuration - Load first
        self.config_file = "server_config.json"
        self.load_config()
        
        # Server process
        self.server_process = None
        self.server_running = False
        self.server_start_time = None
        self.startup_enabled_var = tk.BooleanVar()
        
        # Player tracking
        self.current_players = 0
        self.max_players = 20
        self.player_list = set()
        
        # Server monitoring variables
        self.cpu_usage = 0
        self.memory_usage = 0
        self.tps = 20.0
        self.monitoring_enabled = True
        self.performance_thread = None
        
        # Plugins management
        self.plugins_dir = os.path.join(os.path.dirname(self.config.get("server_jar", "")), "plugins")
        self.installed_plugins = []
        
        # File management
        self.file_manager_root = self.config.get("file_manager_root", r"C:\Users\MersYeon\Desktop\Cacasians")
        self.allowed_extensions = {'.txt', '.yml', '.yaml', '.json', '.properties', '.jar', '.zip'}
        
        # Performance optimization
        self.use_aikars_flags = tk.BooleanVar()
        self.optimization_enabled = tk.BooleanVar()
        
        # User authentication system
        self.users_file = "users.json"
        self.sessions_file = "sessions.json"
        self.users = self.load_users()
        self.active_sessions = {}
        self.pending_registrations = self.load_pending_registrations()
        
        # Initialize command/chat mode (True = Command mode, False = Chat mode)
        self.command_mode = True
        
        # Web server for remote access
        self.web_server = None
        self.web_server_thread = None
        self.web_server_running = False
        self.remote_access_enabled = tk.BooleanVar()
        self.web_port = self.config.get("web_port", 5000)
        
        # Console history storage
        self.console_history = []
        self.max_console_history = 1000
        self.console_history_file = "console_history.json"
        self.load_console_history()
        
        # Check actual startup status and sync with config
        actual_startup_status = self.check_startup_status()
        if actual_startup_status != self.config.get("startup_enabled", False):
            self.config["startup_enabled"] = actual_startup_status
            self.save_config()
        
        # Set startup_enabled_var from config
        self.startup_enabled_var.set(self.config.get("startup_enabled", False))
        
        # Set remote access settings
        self.remote_access_enabled.set(True)
        
        self.setup_ui()
        
        # Bind window close event to save configuration
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start web server automatically
        self.start_web_server()
        
    def load_config(self):
        """Load server configuration from file"""
        default_config = {
            "server_jar": "",
            "java_path": "java",
            "memory_min": "1G",
            "memory_max": "2G",
            "server_port": "25565",
            "additional_args": "",
            "use_aikars_flags": True,
            "optimization_enabled": True,
            "auto_start_server": False,
            "startup_enabled": False,
            "remote_access_enabled": True,
            "web_port": 5000,
            "file_manager_root": r"C:\Users\MersYeon\Desktop\Cacasians"
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = default_config
        except:
            self.config = default_config
    
    def save_config(self):
        """Save server configuration to file"""
        self.config["startup_enabled"] = self.startup_enabled_var.get()
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {str(e)}")
    
    def load_console_history(self):
        """Load console history from file"""
        try:
            if os.path.exists(self.console_history_file):
                with open(self.console_history_file, 'r', encoding='utf-8') as f:
                    self.console_history = json.load(f)
                    if len(self.console_history) > self.max_console_history:
                        self.console_history = self.console_history[-self.max_console_history:]
        except Exception as e:
            self.console_history = []
            print(f"Could not load console history: {e}")
    
    def save_console_history(self):
        """Save console history to file"""
        try:
            if len(self.console_history) > self.max_console_history:
                self.console_history = self.console_history[-self.max_console_history:]
            
            with open(self.console_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.console_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Could not save console history: {e}")
    
    def add_to_console_history(self, message):
        """Add message to console history"""
        timestamp = time.strftime("%H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "message": message,
            "time": time.time()
        }
        self.console_history.append(entry)
        
        if len(self.console_history) > self.max_console_history:
            self.console_history = self.console_history[-self.max_console_history:]
        
        if len(self.console_history) % 10 == 0:
            self.save_console_history()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = tk.Frame(self.root, bg="#2c3e50")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="Cacasians Minecraft Server Wrapper", 
                              font=self.title_font, fg="#ecf0f1", bg="#2c3e50")
        title_label.pack(pady=(0, 20))
        
        # Server controls frame
        controls_frame = tk.Frame(main_frame, bg="#34495e", relief=tk.GROOVE, bd=2)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        controls_title = tk.Label(controls_frame, text="Server Controls", 
                                 font=(self.label_font[0], 12, "bold"), fg="#ecf0f1", bg="#34495e")
        controls_title.pack(pady=5)
        
        # Buttons frame
        buttons_frame = tk.Frame(controls_frame, bg="#34495e")
        buttons_frame.pack(pady=10)
        
        # Server control buttons
        self.start_button = tk.Button(buttons_frame, text="▶ Start Server",
                                     command=self.start_server, bg="#27ae60", fg="white",
                                     font=self.button_font, width=12)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(buttons_frame, text="⏹ Stop Server",
                                    command=self.stop_server, bg="#e74c3c", fg="white",
                                    font=self.button_font, width=12)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.restart_button = tk.Button(buttons_frame, text="🔄 Restart Server",
                                       command=self.restart_server, bg="#f39c12", fg="white",
                                       font=self.button_font, width=12)
        self.restart_button.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = tk.Label(controls_frame, text="Status: Stopped",
                                    font=self.label_font, fg="#ecf0f1", bg="#34495e")
        self.status_label.pack(pady=5)
        
        # Configuration frame
        config_frame = tk.Frame(main_frame, bg="#34495e", relief=tk.GROOVE, bd=2)
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        config_title = tk.Label(config_frame, text="Server Configuration",
                               font=(self.label_font[0], 12, "bold"), fg="#ecf0f1", bg="#34495e")
        config_title.pack(pady=5)
        
        # Configuration grid
        config_grid = tk.Frame(config_frame, bg="#34495e")
        config_grid.pack(pady=10)
        
        # Server JAR file
        tk.Label(config_grid, text="Server JAR:", font=self.label_font,
                fg="#ecf0f1", bg="#34495e").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        jar_frame = tk.Frame(config_grid, bg="#34495e")
        jar_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        self.jar_entry = tk.Entry(jar_frame, width=40, font=self.default_font,
                                 bg="#2c3e50", fg="#ecf0f1", insertbackground="#ecf0f1")
        self.jar_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        browse_button = tk.Button(jar_frame, text="Browse", command=self.browse_jar,
                                 bg="#3498db", fg="white", font=self.default_font)
        browse_button.pack(side=tk.LEFT)
        
        # Memory settings
        tk.Label(config_grid, text="Min Memory:", font=self.label_font,
                fg="#ecf0f1", bg="#34495e").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        self.min_memory_entry = tk.Entry(config_grid, width=10, font=self.default_font,
                                        bg="#2c3e50", fg="#ecf0f1", insertbackground="#ecf0f1")
        self.min_memory_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        tk.Label(config_grid, text="Max Memory:", font=self.label_font,
                fg="#ecf0f1", bg="#34495e").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        
        self.max_memory_entry = tk.Entry(config_grid, width=10, font=self.default_font,
                                        bg="#2c3e50", fg="#ecf0f1", insertbackground="#ecf0f1")
        self.max_memory_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        # Console frame
        console_frame = tk.Frame(main_frame, bg="#34495e", relief=tk.GROOVE, bd=2)
        console_frame.pack(fill=tk.BOTH, expand=True)
        
        console_title = tk.Label(console_frame, text="Server Console",
                                font=(self.label_font[0], 12, "bold"), fg="#ecf0f1", bg="#34495e")
        console_title.pack(pady=5)
        
        self.console_output = scrolledtext.ScrolledText(console_frame, height=15,
                                                       bg="#1a1a1a", fg="#00ff00",
                                                       font=self.console_font,
                                                       insertbackground="#00ff00")
        self.console_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Command input frame
        command_frame = tk.Frame(console_frame, bg="#34495e")
        command_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.command_entry = tk.Entry(command_frame, bg="#2c3e50", fg="#ecf0f1",
                                     font=self.default_font, insertbackground="#ecf0f1")
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.command_entry.bind("<Return>", lambda e: self.send_command())
        
        send_button = tk.Button(command_frame, text="Send", command=self.send_command,
                               bg="#3498db", fg="white", font=self.default_font)
        send_button.pack(side=tk.RIGHT)
        
        # Load configuration into UI
        self.load_config_to_ui()
        
    def load_config_to_ui(self):
        """Load configuration values into UI elements"""
        self.jar_entry.delete(0, tk.END)
        self.jar_entry.insert(0, self.config.get("server_jar", ""))
        
        self.min_memory_entry.delete(0, tk.END)
        self.min_memory_entry.insert(0, self.config.get("memory_min", "1G"))
        
        self.max_memory_entry.delete(0, tk.END)
        self.max_memory_entry.insert(0, self.config.get("memory_max", "2G"))
        
    def browse_jar(self):
        """Browse for server JAR file"""
        filename = filedialog.askopenfilename(
            title="Select Minecraft Server JAR",
            filetypes=[("JAR files", "*.jar"), ("All files", "*.*")]
        )
        if filename:
            self.jar_entry.delete(0, tk.END)
            self.jar_entry.insert(0, filename)
            self.config["server_jar"] = filename
            self.save_config()
    
    def start_server(self):
        """Start the Minecraft server"""
        if self.server_running:
            messagebox.showwarning("Warning", "Server is already running!")
            return
        
        # Get configuration from UI
        jar_file = self.jar_entry.get().strip()
        min_memory = self.min_memory_entry.get().strip()
        max_memory = self.max_memory_entry.get().strip()
        
        if not jar_file:
            messagebox.showerror("Error", "Please select a server JAR file!")
            return
        
        if not os.path.exists(jar_file):
            messagebox.showerror("Error", "Server JAR file not found!")
            return
        
        # Save current configuration
        self.config["server_jar"] = jar_file
        self.config["memory_min"] = min_memory
        self.config["memory_max"] = max_memory
        self.save_config()
        
        # Build command
        java_path = self.config.get("java_path", "java")
        command = [java_path]
        
        # Add Aikar's flags if enabled
        if self.config.get("use_aikars_flags", True):
            # Aikar's flags for better garbage collection
            aikars_flags = [
                f"-Xms{min_memory}",
                f"-Xmx{max_memory}",
                "-XX:+UseG1GC",
                "-XX:+ParallelRefProcEnabled",
                "-XX:MaxGCPauseMillis=200",
                "-XX:+UnlockExperimentalVMOptions",
                "-XX:+DisableExplicitGC",
                "-XX:+AlwaysPreTouch",
                "-XX:G1NewSizePercent=30",
                "-XX:G1MaxNewSizePercent=40",
                "-XX:G1HeapRegionSize=8M",
                "-XX:G1ReservePercent=20",
                "-XX:G1HeapWastePercent=5",
                "-XX:G1MixedGCCountTarget=4",
                "-XX:InitiatingHeapOccupancyPercent=15",
                "-XX:G1MixedGCLiveThresholdPercent=90",
                "-XX:G1RSetUpdatingPauseTimePercent=5",
                "-XX:SurvivorRatio=32",
                "-XX:+PerfDisableSharedMem",
                "-XX:MaxTenuringThreshold=1",
                "-Dusing.aikars.flags=https://mcflags.emc.gs",
                "-Daikars.new.flags=true"
            ]
            command.extend(aikars_flags)
        else:
            # Standard memory flags
            command.extend([f"-Xms{min_memory}", f"-Xmx{max_memory}"])
        
        # Add optimization flags if enabled
        if self.config.get("optimization_enabled", True):
            optimization_flags = [
                "-XX:+UseStringDeduplication",
                "-XX:+UseCompressedOops",
                "-XX:+OptimizeStringConcat"
            ]
            command.extend(optimization_flags)
        
        # Add JAR and nogui
        command.extend(["-jar", jar_file, "nogui"])
        
        # Add additional arguments if any
        additional_args = self.config.get("additional_args", "").strip()
        if additional_args:
            command.extend(additional_args.split())
        
        try:
            # Change to server directory
            server_dir = os.path.dirname(jar_file)
            if server_dir:
                os.chdir(server_dir)
            
            # Start server process
            self.server_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.server_running = True
            self.server_start_time = time.time()
            
            # Start output monitoring thread
            self.output_thread = threading.Thread(target=self.monitor_output, daemon=True)
            self.output_thread.start()
            
            # Start performance monitoring thread
            self.performance_thread = threading.Thread(target=self.monitor_server_performance, daemon=True)
            self.performance_thread.start()
            
            # Update UI
            self.update_button_states()
            self.log_message("Server starting...")
            self.log_message(f"Using command: {' '.join(command)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {str(e)}")
    
    def stop_server(self):
        """Stop the Minecraft server"""
        if not self.server_running:
            messagebox.showwarning("Warning", "Server is not running!")
            return
        
        try:
            if self.server_process:
                # Send stop command
                self.server_process.stdin.write("stop\\n")
                self.server_process.stdin.flush()
                
                # Wait for graceful shutdown
                try:
                    self.server_process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    # Force kill if not stopped gracefully
                    self.server_process.kill()
                    self.log_message("Server force killed after timeout")
                
                self.server_process = None
            
            self.server_running = False
            self.update_button_states()
            self.log_message("Server stopped")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop server: {str(e)}")
    
    def restart_server(self):
        """Restart the Minecraft server"""
        if self.server_running:
            self.stop_server()
            # Wait a moment for cleanup
            self.root.after(2000, self.start_server)
        else:
            self.start_server()
    
    def send_command(self):
        """Send command to server"""
        command = self.command_entry.get().strip()
        if not command:
            return
        
        if not self.server_running:
            messagebox.showwarning("Warning", "Server is not running!")
            return
        
        try:
            self.server_process.stdin.write(command + "\\n")
            self.server_process.stdin.flush()
            self.log_message(f"[COMMAND] {command}")
            self.command_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send command: {str(e)}")
    
    def monitor_output(self):
        """Monitor server output"""
        while self.server_running and self.server_process:
            try:
                line = self.server_process.stdout.readline()
                if line:
                    line = line.strip()
                    self.log_message(line)
                    self.add_to_console_history(line)
                    
                    # Check for player join/leave
                    self.parse_player_activity(line)
                    
                elif self.server_process.poll() is not None:
                    # Process has ended
                    break
                    
            except Exception as e:
                self.log_message(f"Error reading output: {str(e)}")
                break
        
        # Server has stopped
        self.server_running = False
        self.root.after(0, self.update_button_states)
        self.root.after(0, lambda: self.log_message("Server process ended"))
    
    def parse_player_activity(self, line):
        """Parse player join/leave messages"""
        # Player joined
        join_match = re.search(r"(\\w+) joined the game", line)
        if join_match:
            player = join_match.group(1)
            self.player_list.add(player)
            self.current_players = len(self.player_list)
            return
        
        # Player left
        leave_match = re.search(r"(\\w+) left the game", line)
        if leave_match:
            player = leave_match.group(1)
            self.player_list.discard(player)
            self.current_players = len(self.player_list)
            return
        
        # Parse TPS from server output
        tps_match = re.search(r"TPS from last 1m, 5m, 15m: ([\d.]+)", line)
        if tps_match:
            self.server_tps = float(tps_match.group(1))
            return
    
    def monitor_server_performance(self):
        """Monitor server performance metrics"""
        while self.server_running and self.monitoring_enabled:
            try:
                if self.server_process:
                    # Get process info
                    process = psutil.Process(self.server_process.pid)
                    
                    # CPU usage
                    self.server_cpu_usage = process.cpu_percent()
                    
                    # Memory usage in MB
                    memory_info = process.memory_info()
                    self.server_memory_usage = memory_info.rss / 1024 / 1024
                    
                time.sleep(5)  # Update every 5 seconds
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
            except Exception as e:
                print(f"Error monitoring performance: {e}")
                break
    
    def get_plugins_list(self):
        """Get list of installed plugins"""
        plugins = []
        if os.path.exists(self.plugins_dir):
            for file in os.listdir(self.plugins_dir):
                if file.endswith('.jar'):
                    plugin_path = os.path.join(self.plugins_dir, file)
                    plugin_info = {
                        'name': file[:-4],  # Remove .jar extension
                        'filename': file,
                        'size': os.path.getsize(plugin_path),
                        'modified': os.path.getmtime(plugin_path)
                    }
                    plugins.append(plugin_info)
        return plugins
    
    def get_file_list(self, path=""):
        """Get file list for file manager"""
        try:
            full_path = os.path.join(self.file_manager_root, path) if path else self.file_manager_root
            full_path = os.path.normpath(full_path)
            
            # Security check - ensure path is within allowed directory
            if not full_path.startswith(self.file_manager_root):
                return []
            
            if not os.path.exists(full_path):
                return []
            
            files = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                relative_path = os.path.relpath(item_path, self.file_manager_root)
                
                file_info = {
                    'name': item,
                    'path': relative_path.replace('\\', '/'),
                    'is_directory': os.path.isdir(item_path),
                    'size': os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
                    'modified': os.path.getmtime(item_path)
                }
                files.append(file_info)
            
            return sorted(files, key=lambda x: (not x['is_directory'], x['name'].lower()))
        except Exception as e:
            print(f"Error getting file list: {e}")
            return []
    
    def log_message(self, message):
        """Log message to console"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # Add to console history for web interface
        self.console_history.append({
            'timestamp': timestamp,
            'message': message
        })
        
        # Keep only last 1000 messages
        if len(self.console_history) > 1000:
            self.console_history = self.console_history[-1000:]
        
        def update_console():
            self.console_output.insert(tk.END, formatted_message + "\\n")
            self.console_output.see(tk.END)
        
        if threading.current_thread() == threading.main_thread():
            update_console()
        else:
            self.root.after(0, update_console)
    
    def update_button_states(self):
        """Update button states based on server status"""
        if self.server_running:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.restart_button.config(state=tk.NORMAL)
            self.status_label.config(text="Status: Running", fg="#27ae60")
        else:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.restart_button.config(state=tk.DISABLED)
            self.status_label.config(text="Status: Stopped", fg="#e74c3c")
    
    def check_startup_status(self):
        """Check if the wrapper is set to start with Windows"""
        if not WINDOWS_PLATFORM:
            return False
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Run")
            try:
                winreg.QueryValueEx(key, "MinecraftServerWrapper")
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except:
            return False
    
    def start_web_server(self):
        """Start the web server for remote access"""
        if self.web_server_running:
            return
        
        try:
            self.web_server = Flask(__name__)
            self.setup_web_routes()
            
            # Start server in a separate thread
            self.web_server_thread = threading.Thread(
                target=lambda: self.web_server.run(
                    host='0.0.0.0',
                    port=self.web_port,
                    debug=False,
                    use_reloader=False
                ),
                daemon=True
            )
            self.web_server_thread.start()
            self.web_server_running = True
            
            self.log_message(f"Web interface started on port {self.web_port}")
            
        except Exception as e:
            self.log_message(f"Failed to start web server: {str(e)}")
    
    def setup_web_routes(self):
        """Setup web server routes"""
        @self.web_server.route('/')
        def index():
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Cacasians Minecraft Server Wrapper</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body { 
                        font-family: 'Segoe UI', Arial, sans-serif; 
                        background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460); 
                        color: white; 
                        min-height: 100vh;
                        overflow-x: hidden;
                    }
                    .navbar {
                        background: rgba(0,0,0,0.3);
                        padding: 1rem 2rem;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        backdrop-filter: blur(10px);
                        border-bottom: 1px solid rgba(255,255,255,0.1);
                    }
                    .navbar h1 {
                        font-size: 1.8rem;
                        background: linear-gradient(45deg, #00d4ff, #ff6b6b);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        background-clip: text;
                    }
                    .nav-tabs {
                        display: flex;
                        gap: 1rem;
                    }
                    .nav-tab {
                        padding: 0.5rem 1rem;
                        background: rgba(255,255,255,0.1);
                        border: none;
                        border-radius: 8px;
                        color: white;
                        cursor: pointer;
                        transition: all 0.3s ease;
                    }
                    .nav-tab:hover, .nav-tab.active {
                        background: rgba(0,212,255,0.3);
                        transform: translateY(-2px);
                    }
                    .container {
                        max-width: 1400px;
                        margin: 0 auto;
                        padding: 2rem;
                    }
                    .tab-content {
                        display: none;
                        animation: fadeIn 0.3s ease;
                    }
                    .tab-content.active {
                        display: block;
                    }
                    @keyframes fadeIn {
                        from { opacity: 0; transform: translateY(20px); }
                        to { opacity: 1; transform: translateY(0); }
                    }
                    .grid {
                        display: grid;
                        gap: 2rem;
                        margin-bottom: 2rem;
                    }
                    .grid-2 { grid-template-columns: 1fr 1fr; }
                    .grid-3 { grid-template-columns: 1fr 1fr 1fr; }
                    .card {
                        background: rgba(255,255,255,0.1);
                        border-radius: 15px;
                        padding: 1.5rem;
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255,255,255,0.1);
                        transition: transform 0.3s ease;
                    }
                    .card:hover {
                        transform: translateY(-5px);
                    }
                    .card h3 {
                        margin-bottom: 1rem;
                        color: #00d4ff;
                        font-size: 1.2rem;
                    }
                    .status-card {
                        text-align: center;
                        padding: 2rem;
                    }
                    .status-indicator {
                        width: 20px;
                        height: 20px;
                        border-radius: 50%;
                        display: inline-block;
                        margin-right: 10px;
                    }
                    .status-running { background: #27ae60; }
                    .status-stopped { background: #e74c3c; }
                    .controls {
                        display: flex;
                        gap: 1rem;
                        justify-content: center;
                        margin-top: 1rem;
                    }
                    button {
                        padding: 0.8rem 1.5rem;
                        border: none;
                        border-radius: 8px;
                        cursor: pointer;
                        font-weight: bold;
                        transition: all 0.3s ease;
                        font-size: 0.9rem;
                    }
                    button:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
                    }
                    .btn-start { background: linear-gradient(45deg, #27ae60, #2ecc71); color: white; }
                    .btn-stop { background: linear-gradient(45deg, #e74c3c, #c0392b); color: white; }
                    .btn-restart { background: linear-gradient(45deg, #f39c12, #e67e22); color: white; }
                    .btn-primary { background: linear-gradient(45deg, #3498db, #2980b9); color: white; }
                    .btn-danger { background: linear-gradient(45deg, #e74c3c, #c0392b); color: white; }
                    .btn-success { background: linear-gradient(45deg, #27ae60, #2ecc71); color: white; }
                    #console {
                        background: #000;
                        color: #00ff00;
                        padding: 1rem;
                        height: 400px;
                        overflow-y: auto;
                        font-family: 'Consolas', monospace;
                        border-radius: 8px;
                        border: 1px solid rgba(255,255,255,0.2);
                        font-size: 0.9rem;
                        line-height: 1.4;
                    }
                    .command-section {
                        display: flex;
                        gap: 0.5rem;
                        margin-top: 1rem;
                    }
                    input[type="text"], input[type="file"] {
                        flex: 1;
                        padding: 0.8rem;
                        border: 1px solid rgba(255,255,255,0.3);
                        border-radius: 8px;
                        background: rgba(255,255,255,0.1);
                        color: white;
                        font-size: 0.9rem;
                    }
                    input[type="text"]:focus, input[type="file"]:focus {
                        outline: none;
                        border-color: #00d4ff;
                        box-shadow: 0 0 10px rgba(0,212,255,0.3);
                    }
                    .metric {
                        text-align: center;
                        padding: 1rem;
                    }
                    .metric-value {
                        font-size: 2rem;
                        font-weight: bold;
                        color: #00d4ff;
                        display: block;
                    }
                    .metric-label {
                        font-size: 0.9rem;
                        opacity: 0.8;
                        margin-top: 0.5rem;
                    }
                    .file-list {
                        max-height: 500px;
                        overflow-y: auto;
                        border: 1px solid rgba(255,255,255,0.2);
                        border-radius: 8px;
                    }
                    .file-item {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        padding: 0.8rem;
                        border-bottom: 1px solid rgba(255,255,255,0.1);
                        transition: background 0.2s ease;
                    }
                    .file-item:hover {
                        background: rgba(255,255,255,0.1);
                    }
                    .file-info {
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                    }
                    .file-icon {
                        width: 20px;
                        height: 20px;
                        display: inline-block;
                    }
                    .file-actions {
                        display: flex;
                        gap: 0.5rem;
                    }
                    .file-actions button {
                        padding: 0.3rem 0.6rem;
                        font-size: 0.8rem;
                    }
                    .plugin-item {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        padding: 1rem;
                        background: rgba(255,255,255,0.05);
                        border-radius: 8px;
                        margin-bottom: 0.5rem;
                    }
                    .plugin-info h4 {
                        color: #00d4ff;
                        margin-bottom: 0.3rem;
                    }
                    .plugin-info small {
                        opacity: 0.7;
                    }
                    .notification {
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        padding: 1rem 1.5rem;
                        border-radius: 8px;
                        color: white;
                        font-weight: bold;
                        z-index: 1000;
                        animation: slideIn 0.3s ease;
                        max-width: 300px;
                    }
                    .notification.success { background: #27ae60; }
                    .notification.error { background: #e74c3c; }
                    .notification.info { background: #3498db; }
                    @keyframes slideIn {
                        from { transform: translateX(100%); opacity: 0; }
                        to { transform: translateX(0); opacity: 1; }
                    }
                    @media (max-width: 768px) {
                        .grid-2, .grid-3 { grid-template-columns: 1fr; }
                        .navbar { flex-direction: column; gap: 1rem; }
                        .controls { flex-direction: column; }
                        .container { padding: 1rem; }
                    }
                </style>
            </head>
            <body>
                <nav class="navbar">
                    <h1>🎮 Cacasians Minecraft Server</h1>
                    <div class="nav-tabs">
                        <button class="nav-tab active" onclick="showTab('dashboard')">Dashboard</button>
                        <button class="nav-tab" onclick="showTab('monitor')">Server Monitor</button>
                        <button class="nav-tab" onclick="showTab('plugins')">Plugins</button>
                        <button class="nav-tab" onclick="showTab('files')">File Manager</button>
                        <button class="nav-tab" onclick="showTab('console')">Console</button>
                    </div>
                </nav>

                <div class="container">
                    <!-- Dashboard Tab -->
                    <div id="dashboard" class="tab-content active">
                        <div class="grid grid-2">
                            <div class="card status-card">
                                <h3>Server Status</h3>
                                <div id="status">
                                    <span class="status-indicator status-stopped"></span>
                                    <span id="status-text">Stopped</span>
                                </div>
                                <div class="controls">
                                    <button class="btn-start" onclick="startServer()">▶ Start</button>
                                    <button class="btn-stop" onclick="stopServer()">⏹ Stop</button>
                                    <button class="btn-restart" onclick="restartServer()">🔄 Restart</button>
                                </div>
                            </div>
                            <div class="card">
                                <h3>Quick Stats</h3>
                                <div class="grid grid-3">
                                    <div class="metric">
                                        <span class="metric-value" id="player-count">0</span>
                                        <div class="metric-label">Players Online</div>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-value" id="tps-value">20.0</span>
                                        <div class="metric-label">TPS</div>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-value" id="uptime">0m</span>
                                        <div class="metric-label">Uptime</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Server Monitor Tab -->
                    <div id="monitor" class="tab-content">
                        <div class="grid grid-2">
                            <div class="card">
                                <h3>📊 Performance Metrics</h3>
                                <div class="grid grid-2">
                                    <div class="metric">
                                        <span class="metric-value" id="cpu-usage">0%</span>
                                        <div class="metric-label">CPU Usage</div>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-value" id="memory-usage">0 MB</span>
                                        <div class="metric-label">Memory Usage</div>
                                    </div>
                                </div>
                            </div>
                            <div class="card">
                                <h3>🎯 Server Performance</h3>
                                <div class="grid grid-2">
                                    <div class="metric">
                                        <span class="metric-value" id="monitor-tps">20.0</span>
                                        <div class="metric-label">Current TPS</div>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-value" id="monitor-players">0</span>
                                        <div class="metric-label">Active Players</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="card">
                            <h3>⚙️ Optimization Settings</h3>
                            <p>✅ Aikar's Flags: Enabled</p>
                            <p>✅ Performance Optimization: Enabled</p>
                            <p>✅ G1 Garbage Collector: Active</p>
                            <p>✅ String Deduplication: Enabled</p>
                        </div>
                    </div>

                    <!-- Plugins Tab -->
                    <div id="plugins" class="tab-content">
                        <div class="card">
                            <h3>🔌 Installed Plugins</h3>
                            <div id="plugins-list">
                                <p>Loading plugins...</p>
                            </div>
                            <div style="margin-top: 1rem;">
                                <input type="file" id="plugin-upload" accept=".jar" style="display: none;">
                                <button class="btn-primary" onclick="document.getElementById('plugin-upload').click()">📁 Upload Plugin</button>
                                <button class="btn-success" onclick="refreshPlugins()">🔄 Refresh</button>
                            </div>
                        </div>
                    </div>

                    <!-- File Manager Tab -->
                    <div id="files" class="tab-content">
                        <div class="card">
                            <h3>📁 File Manager - C:\\Users\\MersYeon\\Desktop\\Cacasians</h3>
                            <div style="margin-bottom: 1rem;">
                                <input type="file" id="file-upload" multiple style="display: none;">
                                <button class="btn-primary" onclick="document.getElementById('file-upload').click()">📁 Upload Files</button>
                                <button class="btn-primary" onclick="createNewFile()">📄 New File</button>
                                <button class="btn-success" onclick="refreshFiles()">🔄 Refresh</button>
                            </div>
                            <div class="file-list" id="file-list">
                                <p>Loading files...</p>
                            </div>
                        </div>
                    </div>

                    <!-- Console Tab -->
                    <div id="console" class="tab-content">
                        <div class="card">
                            <h3>💻 Server Console</h3>
                            <div id="console-output"></div>
                            <div class="command-section">
                                <input type="text" id="command-input" placeholder="Enter server command..." onkeypress="if(event.key==='Enter') sendCommand()">
                                <button class="btn-primary" onclick="sendCommand()">📤 Send</button>
                            </div>
                        </div>
                    </div>
                </div>

                <script>
                    let currentTab = 'dashboard';
                    let updateInterval;

                    function showTab(tabName) {
                        // Hide all tabs
                        document.querySelectorAll('.tab-content').forEach(tab => {
                            tab.classList.remove('active');
                        });
                        document.querySelectorAll('.nav-tab').forEach(tab => {
                            tab.classList.remove('active');
                        });

                        // Show selected tab
                        document.getElementById(tabName).classList.add('active');
                        event.target.classList.add('active');
                        currentTab = tabName;

                        // Load tab-specific data
                        if (tabName === 'plugins') refreshPlugins();
                        if (tabName === 'files') refreshFiles();
                        if (tabName === 'console') loadConsole();
                    }

                    function startServer() {
                        fetch('/api/start', {method: 'POST'})
                            .then(response => response.json())
                            .then(data => {
                                showNotification(data.message, 'success');
                                updateStatus();
                            });
                    }

                    function stopServer() {
                        fetch('/api/stop', {method: 'POST'})
                            .then(response => response.json())
                            .then(data => {
                                showNotification(data.message, 'info');
                                updateStatus();
                            });
                    }

                    function restartServer() {
                        fetch('/api/restart', {method: 'POST'})
                            .then(response => response.json())
                            .then(data => {
                                showNotification(data.message, 'info');
                                updateStatus();
                            });
                    }

                    function sendCommand() {
                        const command = document.getElementById('command-input').value;
                        if (!command) return;

                        fetch('/api/command', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({command: command})
                        })
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('command-input').value = '';
                            if (data.error) {
                                showNotification(data.error, 'error');
                            } else {
                                showNotification('Command sent successfully', 'success');
                            }
                        });
                    }

                    function updateStatus() {
                        fetch('/api/status')
                            .then(response => response.json())
                            .then(data => {
                                const statusIndicator = document.querySelector('.status-indicator');
                                const statusText = document.getElementById('status-text');
                                const playerCount = document.getElementById('player-count');
                                const tpsValue = document.getElementById('tps-value');
                                const cpuUsage = document.getElementById('cpu-usage');
                                const memoryUsage = document.getElementById('memory-usage');
                                const monitorTps = document.getElementById('monitor-tps');
                                const monitorPlayers = document.getElementById('monitor-players');

                                if (data.running) {
                                    statusIndicator.className = 'status-indicator status-running';
                                    statusText.textContent = 'Running';
                                } else {
                                    statusIndicator.className = 'status-indicator status-stopped';
                                    statusText.textContent = 'Stopped';
                                }

                                playerCount.textContent = data.players || 0;
                                tpsValue.textContent = (data.tps || 20.0).toFixed(1);
                                cpuUsage.textContent = (data.cpu || 0).toFixed(1) + '%';
                                memoryUsage.textContent = Math.round(data.memory || 0) + ' MB';
                                monitorTps.textContent = (data.tps || 20.0).toFixed(1);
                                monitorPlayers.textContent = data.players || 0;
                            });
                    }

                    function refreshPlugins() {
                        fetch('/api/plugins')
                            .then(response => response.json())
                            .then(data => {
                                const pluginsList = document.getElementById('plugins-list');
                                if (data.plugins && data.plugins.length > 0) {
                                    pluginsList.innerHTML = data.plugins.map(plugin => `
                                        <div class="plugin-item">
                                            <div class="plugin-info">
                                                <h4>${plugin.name}</h4>
                                                <small>Size: ${(plugin.size / 1024).toFixed(1)} KB</small>
                                            </div>
                                            <div class="file-actions">
                                                <button class="btn-danger" onclick="deletePlugin('${plugin.filename}')">🗑️ Delete</button>
                                            </div>
                                        </div>
                                    `).join('');
                                } else {
                                    pluginsList.innerHTML = '<p>No plugins installed</p>';
                                }
                            });
                    }

                    function refreshFiles() {
                        fetch('/api/files')
                            .then(response => response.json())
                            .then(data => {
                                const fileList = document.getElementById('file-list');
                                if (data.files && data.files.length > 0) {
                                    fileList.innerHTML = data.files.map(file => `
                                        <div class="file-item">
                                            <div class="file-info">
                                                <span class="file-icon">${file.is_directory ? '📁' : '📄'}</span>
                                                <span>${file.name}</span>
                                                ${!file.is_directory ? `<small>(${(file.size / 1024).toFixed(1)} KB)</small>` : ''}
                                            </div>
                                            <div class="file-actions">
                                                ${!file.is_directory ? `<button class="btn-primary" onclick="downloadFile('${file.path}')">⬇️ Download</button>` : ''}
                                                <button class="btn-primary" onclick="renameFile('${file.path}', '${file.name}')">✏️ Rename</button>
                                                <button class="btn-danger" onclick="deleteFile('${file.path}')">🗑️ Delete</button>
                                            </div>
                                        </div>
                                    `).join('');
                                } else {
                                    fileList.innerHTML = '<p>No files found</p>';
                                }
                            });
                    }

                    function loadConsole() {
                        fetch('/api/console')
                            .then(response => response.json())
                            .then(data => {
                                const consoleOutput = document.getElementById('console-output');
                                consoleOutput.innerHTML = data.history.map(entry => 
                                    `<div>[${entry.timestamp}] ${entry.message}</div>`
                                ).join('');
                                consoleOutput.scrollTop = consoleOutput.scrollHeight;
                            });
                    }

                    function deletePlugin(filename) {
                        if (confirm(`Delete plugin ${filename}?`)) {
                            fetch('/api/plugins/delete', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({filename: filename})
                            })
                            .then(response => response.json())
                            .then(data => {
                                showNotification(data.message, data.success ? 'success' : 'error');
                                if (data.success) refreshPlugins();
                            });
                        }
                    }

                    function deleteFile(path) {
                        if (confirm(`Delete ${path}?`)) {
                            fetch('/api/files/delete', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({path: path})
                            })
                            .then(response => response.json())
                            .then(data => {
                                showNotification(data.message, data.success ? 'success' : 'error');
                                if (data.success) refreshFiles();
                            });
                        }
                    }

                    function renameFile(path, currentName) {
                        const newName = prompt(`Rename ${currentName} to:`, currentName);
                        if (newName && newName !== currentName) {
                            fetch('/api/files/rename', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({path: path, newName: newName})
                            })
                            .then(response => response.json())
                            .then(data => {
                                showNotification(data.message, data.success ? 'success' : 'error');
                                if (data.success) refreshFiles();
                            });
                        }
                    }

                    function downloadFile(path) {
                        window.open(`/api/files/download/${encodeURIComponent(path)}`, '_blank');
                    }

                    function createNewFile() {
                        const fileName = prompt('Enter file name:');
                        if (fileName) {
                            fetch('/api/files/create', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({name: fileName, content: ''})
                            })
                            .then(response => response.json())
                            .then(data => {
                                showNotification(data.message, data.success ? 'success' : 'error');
                                if (data.success) refreshFiles();
                            });
                        }
                    }

                    function showNotification(message, type) {
                        const notification = document.createElement('div');
                        notification.className = `notification ${type}`;
                        notification.textContent = message;
                        document.body.appendChild(notification);
                        setTimeout(() => notification.remove(), 4000);
                    }

                    // File upload handlers
                    document.getElementById('plugin-upload').addEventListener('change', function(e) {
                        const file = e.target.files[0];
                        if (file) {
                            const formData = new FormData();
                            formData.append('plugin', file);
                            fetch('/api/plugins/upload', {
                                method: 'POST',
                                body: formData
                            })
                            .then(response => response.json())
                            .then(data => {
                                showNotification(data.message, data.success ? 'success' : 'error');
                                if (data.success) refreshPlugins();
                            });
                        }
                    });

                    document.getElementById('file-upload').addEventListener('change', function(e) {
                        const files = e.target.files;
                        if (files.length > 0) {
                            const formData = new FormData();
                            for (let file of files) {
                                formData.append('files', file);
                            }
                            fetch('/api/files/upload', {
                                method: 'POST',
                                body: formData
                            })
                            .then(response => response.json())
                            .then(data => {
                                showNotification(data.message, data.success ? 'success' : 'error');
                                if (data.success) refreshFiles();
                            });
                        }
                    });

                    // Auto-update every 5 seconds
                    updateInterval = setInterval(updateStatus, 5000);
                    updateStatus();
                </script>
            </body>
            </html>
            '''
        
        @self.web_server.route('/api/status')
        def api_status():
            return jsonify({
                'running': self.server_running,
                'players': self.current_players,
                'max_players': self.max_players,
                'cpu': self.cpu_usage,
                'memory': self.memory_usage,
                'tps': self.tps
            })
        
        @self.web_server.route('/api/start', methods=['POST'])
        def api_start():
            if self.server_running:
                return jsonify({'message': 'Server is already running'})
            
            self.root.after(0, self.start_server)
            return jsonify({'message': 'Starting server...'})
        
        @self.web_server.route('/api/stop', methods=['POST'])
        def api_stop():
            if not self.server_running:
                return jsonify({'message': 'Server is not running'})
            
            self.root.after(0, self.stop_server)
            return jsonify({'message': 'Stopping server...'})
        
        @self.web_server.route('/api/restart', methods=['POST'])
        def api_restart():
            self.root.after(0, self.restart_server)
            return jsonify({'message': 'Restarting server...'})
        
        @self.web_server.route('/api/command', methods=['POST'])
        def api_command():
            data = request.get_json()
            command = data.get('command', '').strip()
            
            if not command:
                return jsonify({'error': 'No command provided'})
            
            if not self.server_running:
                return jsonify({'error': 'Server is not running'})
            
            try:
                self.server_process.stdin.write(command + "\\n")
                self.server_process.stdin.flush()
                self.root.after(0, lambda: self.log_message(f"[WEB] {command}"))
                return jsonify({'message': 'Command sent'})
            except Exception as e:
                return jsonify({'error': f'Failed to send command: {str(e)}'})

        @self.web_server.route('/api/plugins')
        def api_plugins():
            """Get plugins list"""
            try:
                plugins = self.get_plugins_list()
                return jsonify({'plugins': plugins})
            except Exception as e:
                return jsonify({'error': str(e), 'plugins': []})

        @self.web_server.route('/api/plugins/upload', methods=['POST'])
        def api_plugins_upload():
            """Upload plugin"""
            try:
                if 'plugin' not in request.files:
                    return jsonify({'success': False, 'message': 'No plugin file provided'})
                
                file = request.files['plugin']
                if file.filename == '':
                    return jsonify({'success': False, 'message': 'No file selected'})
                
                if not file.filename.endswith('.jar'):
                    return jsonify({'success': False, 'message': 'Only .jar files are allowed'})
                
                filename = secure_filename(file.filename)
                filepath = os.path.join(self.plugins_dir, filename)
                file.save(filepath)
                
                return jsonify({'success': True, 'message': f'Plugin {filename} uploaded successfully'})
            except Exception as e:
                return jsonify({'success': False, 'message': f'Upload failed: {str(e)}'})

        @self.web_server.route('/api/plugins/delete', methods=['POST'])
        def api_plugins_delete():
            """Delete plugin"""
            try:
                data = request.get_json()
                filename = data.get('filename', '')
                
                if not filename:
                    return jsonify({'success': False, 'message': 'No filename provided'})
                
                filepath = os.path.join(self.plugins_dir, filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
                    return jsonify({'success': True, 'message': f'Plugin {filename} deleted successfully'})
                else:
                    return jsonify({'success': False, 'message': 'Plugin not found'})
            except Exception as e:
                return jsonify({'success': False, 'message': f'Delete failed: {str(e)}'})

        @self.web_server.route('/api/files')
        def api_files():
            """Get files list"""
            try:
                files = self.get_file_list()
                return jsonify({'files': files})
            except Exception as e:
                return jsonify({'error': str(e), 'files': []})

        @self.web_server.route('/api/files/upload', methods=['POST'])
        def api_files_upload():
            """Upload files"""
            try:
                if 'files' not in request.files:
                    return jsonify({'success': False, 'message': 'No files provided'})
                
                files = request.files.getlist('files')
                uploaded_count = 0
                
                for file in files:
                    if file.filename != '':
                        filename = secure_filename(file.filename)
                        filepath = os.path.join(self.file_manager_root, filename)
                        file.save(filepath)
                        uploaded_count += 1
                
                return jsonify({'success': True, 'message': f'{uploaded_count} file(s) uploaded successfully'})
            except Exception as e:
                return jsonify({'success': False, 'message': f'Upload failed: {str(e)}'})

        @self.web_server.route('/api/files/delete', methods=['POST'])
        def api_files_delete():
            """Delete file"""
            try:
                data = request.get_json()
                path = data.get('path', '')
                
                if not path:
                    return jsonify({'success': False, 'message': 'No path provided'})
                
                # Security check - ensure path is within allowed directory
                full_path = os.path.abspath(path)
                allowed_path = os.path.abspath(self.file_manager_root)
                
                if not full_path.startswith(allowed_path):
                    return jsonify({'success': False, 'message': 'Access denied'})
                
                if os.path.exists(full_path):
                    if os.path.isdir(full_path):
                        shutil.rmtree(full_path)
                    else:
                        os.remove(full_path)
                    return jsonify({'success': True, 'message': f'Deleted successfully'})
                else:
                    return jsonify({'success': False, 'message': 'File not found'})
            except Exception as e:
                return jsonify({'success': False, 'message': f'Delete failed: {str(e)}'})

        @self.web_server.route('/api/files/rename', methods=['POST'])
        def api_files_rename():
            """Rename file"""
            try:
                data = request.get_json()
                path = data.get('path', '')
                new_name = data.get('newName', '')
                
                if not path or not new_name:
                    return jsonify({'success': False, 'message': 'Path and new name required'})
                
                # Security check
                full_path = os.path.abspath(path)
                allowed_path = os.path.abspath(self.file_manager_root)
                
                if not full_path.startswith(allowed_path):
                    return jsonify({'success': False, 'message': 'Access denied'})
                
                if os.path.exists(full_path):
                    new_path = os.path.join(os.path.dirname(full_path), secure_filename(new_name))
                    os.rename(full_path, new_path)
                    return jsonify({'success': True, 'message': f'Renamed successfully'})
                else:
                    return jsonify({'success': False, 'message': 'File not found'})
            except Exception as e:
                return jsonify({'success': False, 'message': f'Rename failed: {str(e)}'})

        @self.web_server.route('/api/files/create', methods=['POST'])
        def api_files_create():
            """Create new file"""
            try:
                data = request.get_json()
                name = data.get('name', '')
                content = data.get('content', '')
                
                if not name:
                    return jsonify({'success': False, 'message': 'Filename required'})
                
                filename = secure_filename(name)
                filepath = os.path.join(self.file_manager_root, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                return jsonify({'success': True, 'message': f'File {filename} created successfully'})
            except Exception as e:
                return jsonify({'success': False, 'message': f'Create failed: {str(e)}'})

        @self.web_server.route('/api/files/download/<path:filename>')
        def api_files_download(filename):
            """Download file"""
            try:
                filepath = os.path.join(self.file_manager_root, filename)
                
                # Security check
                full_path = os.path.abspath(filepath)
                allowed_path = os.path.abspath(self.file_manager_root)
                
                if not full_path.startswith(allowed_path):
                    return jsonify({'error': 'Access denied'}), 403
                
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    return send_file(full_path, as_attachment=True)
                else:
                    return jsonify({'error': 'File not found'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.web_server.route('/api/console')
        def api_console():
            """Get console history"""
            try:
                # Return recent console messages
                history = []
                for message in self.console_history[-100:]:  # Last 100 messages
                    history.append({
                        'timestamp': message.get('timestamp', ''),
                        'message': message.get('message', '')
                    })
                return jsonify({'history': history})
            except Exception as e:
                return jsonify({'error': str(e), 'history': []})
    
    def load_users(self):
        """Load users from file"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def load_pending_registrations(self):
        """Load pending registrations"""
        return {}
    
    def on_closing(self):
        """Handle window closing"""
        self.save_config()
        self.save_console_history()
        
        if self.server_running:
            result = messagebox.askyesno("Confirm Exit", 
                                       "Server is still running. Stop server and exit?")
            if result:
                self.stop_server()
                self.root.after(1000, self.root.destroy)
            return
        
        self.root.destroy()

def main():
    root = tk.Tk()
    app = MinecraftServerWrapper(root)
    root.mainloop()

if __name__ == "__main__":
    main()
