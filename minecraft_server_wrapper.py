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
# Windows-specific imports (conditional)
try:
    import winreg
    WINDOWS_PLATFORM = True
except ImportError:
    WINDOWS_PLATFORM = False
    winreg = None
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from flask_socketio import SocketIO, emit
from werkzeug.serving import make_server

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
        
        # Server process
        self.server_process = None
        self.server_running = False
        self.server_start_time = None
        self.startup_enabled_var = tk.BooleanVar()
        
        # Player tracking
        self.current_players = 0
        self.max_players = 20
        self.player_list = set()
        
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
        self.web_port = 5000
        
        # Configuration
        self.config_file = "server_config.json"
        self.load_config()
        
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
        self.web_port = self.config.get("web_port", 5000)
        
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
            "use_aikars_flags": False,
            "auto_start_server": False,
            "startup_enabled": False,
            "remote_access_enabled": True,
            "web_port": 5000
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
        command = [
            java_path,
            f"-Xms{min_memory}",
            f"-Xmx{max_memory}",
            "-jar",
            jar_file,
            "nogui"
        ]
        
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
            
            # Update UI
            self.update_button_states()
            self.log_message("Server starting...")
            
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
    
    def log_message(self, message):
        """Log message to console"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
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
                <title>Minecraft Server Wrapper</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    * {
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }
                    
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        min-height: 100vh;
                    }
                    
                    .container {
                        max-width: 1200px;
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
                        margin-bottom: 10px;
                        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                    }
                    
                    .nav-tabs {
                        display: flex;
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 10px;
                        padding: 5px;
                        margin-bottom: 20px;
                        backdrop-filter: blur(10px);
                    }
                    
                    .nav-tab {
                        flex: 1;
                        padding: 12px 20px;
                        background: transparent;
                        border: none;
                        color: white;
                        cursor: pointer;
                        border-radius: 8px;
                        transition: all 0.3s ease;
                        font-size: 16px;
                        font-weight: 500;
                    }
                    
                    .nav-tab:hover {
                        background: rgba(255, 255, 255, 0.2);
                    }
                    
                    .nav-tab.active {
                        background: rgba(255, 255, 255, 0.3);
                        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                    }
                    
                    .tab-content {
                        display: none;
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 15px;
                        padding: 25px;
                        backdrop-filter: blur(10px);
                        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                    }
                    
                    .tab-content.active {
                        display: block;
                    }
                    
                    .dashboard-grid {
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 20px;
                        margin-bottom: 20px;
                    }
                    
                    .card {
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 12px;
                        padding: 20px;
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                    }
                    
                    .card h3 {
                        margin-bottom: 15px;
                        color: #fff;
                        font-size: 1.3em;
                    }
                    
                    .status-card {
                        text-align: center;
                    }
                    
                    .status-indicator {
                        display: inline-block;
                        width: 20px;
                        height: 20px;
                        border-radius: 50%;
                        margin-right: 10px;
                        animation: pulse 2s infinite;
                    }
                    
                    .status-running {
                        background: #27ae60;
                    }
                    
                    .status-stopped {
                        background: #e74c3c;
                    }
                    
                    @keyframes pulse {
                        0% { opacity: 1; }
                        50% { opacity: 0.5; }
                        100% { opacity: 1; }
                    }
                    
                    .control-buttons {
                        display: flex;
                        gap: 10px;
                        flex-wrap: wrap;
                        justify-content: center;
                        margin-top: 15px;
                    }
                    
                    .btn {
                        padding: 12px 24px;
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
                    
                    .btn-kill {
                        background: linear-gradient(45deg, #8e44ad, #9b59b6);
                        color: white;
                    }
                    
                    .console-section {
                        grid-column: 1 / -1;
                    }
                    
                    .console {
                        background: #1a1a1a;
                        color: #00ff00;
                        padding: 15px;
                        height: 300px;
                        overflow-y: auto;
                        font-family: 'Courier New', monospace;
                        border-radius: 8px;
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
                    
                    .command-input {
                        display: flex;
                        gap: 10px;
                        margin-top: 15px;
                    }
                    
                    .command-input input {
                        flex: 1;
                        padding: 12px;
                        border: 1px solid rgba(255, 255, 255, 0.3);
                        border-radius: 8px;
                        background: rgba(255, 255, 255, 0.1);
                        color: white;
                        font-size: 14px;
                    }
                    
                    .command-input input::placeholder {
                        color: rgba(255, 255, 255, 0.6);
                    }
                    
                    .command-input button {
                        padding: 12px 20px;
                        background: linear-gradient(45deg, #3498db, #2980b9);
                        color: white;
                        border: none;
                        border-radius: 8px;
                        cursor: pointer;
                        font-weight: 600;
                        transition: all 0.3s ease;
                    }
                    
                    .file-manager {
                        max-height: 500px;
                        overflow-y: auto;
                    }
                    
                    .file-path {
                        background: rgba(255, 255, 255, 0.1);
                        padding: 10px;
                        border-radius: 8px;
                        margin-bottom: 15px;
                        font-family: monospace;
                        word-break: break-all;
                    }
                    
                    .file-list {
                        list-style: none;
                    }
                    
                    .file-item {
                        display: flex;
                        align-items: center;
                        padding: 10px;
                        border-radius: 8px;
                        margin-bottom: 5px;
                        background: rgba(255, 255, 255, 0.05);
                        transition: all 0.3s ease;
                        cursor: pointer;
                    }
                    
                    .file-item:hover {
                        background: rgba(255, 255, 255, 0.1);
                        transform: translateX(5px);
                    }
                    
                    .file-icon {
                        margin-right: 10px;
                        font-size: 18px;
                    }
                    
                    .file-info {
                        flex: 1;
                    }
                    
                    .file-name {
                        font-weight: 500;
                        margin-bottom: 2px;
                    }
                    
                    .file-details {
                        font-size: 12px;
                        color: rgba(255, 255, 255, 0.7);
                    }
                    
                    .file-actions {
                        display: flex;
                        gap: 5px;
                    }
                    
                    .file-action {
                        padding: 5px 10px;
                        background: rgba(255, 255, 255, 0.2);
                        border: none;
                        border-radius: 4px;
                        color: white;
                        cursor: pointer;
                        font-size: 12px;
                        transition: all 0.3s ease;
                    }
                    
                    .file-action:hover {
                        background: rgba(255, 255, 255, 0.3);
                    }
                    
                    .notification {
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        padding: 15px 20px;
                        background: rgba(0, 0, 0, 0.9);
                        color: white;
                        border-radius: 8px;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                        z-index: 1000;
                        transform: translateX(400px);
                        transition: transform 0.3s ease;
                    }
                    
                    .notification.show {
                        transform: translateX(0);
                    }
                    
                    .notification.success {
                        border-left: 4px solid #27ae60;
                    }
                    
                    .notification.error {
                        border-left: 4px solid #e74c3c;
                    }
                    
                    @media (max-width: 768px) {
                        .dashboard-grid {
                            grid-template-columns: 1fr;
                        }
                        
                        .nav-tabs {
                            flex-direction: column;
                        }
                        
                        .control-buttons {
                            flex-direction: column;
                        }
                        
                        .btn {
                            width: 100%;
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
                    
                    <div class="nav-tabs">
                        <button class="nav-tab active" onclick="switchTab('dashboard')">Dashboard & Console</button>
                        <button class="nav-tab" onclick="switchTab('monitor')">Server Monitor</button>
                        <button class="nav-tab" onclick="switchTab('plugins')">Plugins</button>
                        <button class="nav-tab" onclick="switchTab('files')">File Manager</button>
                    </div>
                    
                    <div id="dashboard" class="tab-content active">
                        <div class="dashboard-grid">
                            <div class="card status-card">
                                <h3>🔧 Server Status</h3>
                                <div id="status">
                                    <span class="status-indicator status-stopped"></span>
                                    <span id="status-text">Server Stopped</span>
                                </div>
                                <div id="player-info" style="margin-top: 10px; font-size: 14px;">
                                    Players: <span id="player-count">0</span>/<span id="max-players">20</span>
                                </div>
                            </div>
                            
                            <div class="card">
                                <h3>⚡ Server Controls</h3>
                                <div class="control-buttons">
                                    <button class="btn btn-start" onclick="startServer()">Start</button>
                                    <button class="btn btn-stop" onclick="stopServer()">Stop</button>
                                    <button class="btn btn-restart" onclick="restartServer()">Restart</button>
                                    <button class="btn btn-kill" onclick="killServer()">Kill Server</button>
                                </div>
                            </div>
                            
                            <div class="card console-section">
                                <h3>📟 Console Output</h3>
                                <div id="console" class="console"></div>
                                <div class="command-input">
                                    <input type="text" id="command" placeholder="Enter server command..." onkeypress="if(event.key==='Enter') sendCommand()">
                                    <button onclick="sendCommand()">Send</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div id="monitor" class="tab-content">
                        <div class="card">
                            <h3>📊 Server Monitoring</h3>
                            <p>Real-time server performance metrics will be displayed here.</p>
                            <div id="server-stats" style="margin-top: 20px;">
                                <div>CPU Usage: <span id="cpu-usage">0%</span></div>
                                <div>Memory Usage: <span id="memory-usage">0 MB</span></div>
                                <div>Uptime: <span id="uptime">0 minutes</span></div>
                            </div>
                        </div>
                    </div>
                    
                    <div id="plugins" class="tab-content">
                        <div class="card">
                            <h3>🔌 Plugin Management</h3>
                            <p>Manage your server plugins here.</p>
                            <div id="plugin-list" style="margin-top: 20px;">
                                <p>No plugins loaded.</p>
                            </div>
                        </div>
                    </div>
                    
                    <div id="files" class="tab-content">
                        <div class="card">
                            <h3>📁 File Manager</h3>
                            <div class="file-path" id="current-path">C:\\</div>
                            <div class="file-manager">
                                <ul id="file-list" class="file-list">
                                    <li>Loading files...</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div id="notification" class="notification"></div>
                
                <script>
                    let currentPath = 'C:\\\\';
                    
                    function switchTab(tabName) {
                        // Hide all tab contents
                        document.querySelectorAll('.tab-content').forEach(tab => {
                            tab.classList.remove('active');
                        });
                        
                        // Remove active class from all nav tabs
                        document.querySelectorAll('.nav-tab').forEach(tab => {
                            tab.classList.remove('active');
                        });
                        
                        // Show selected tab content
                        document.getElementById(tabName).classList.add('active');
                        
                        // Add active class to clicked nav tab
                        event.target.classList.add('active');
                        
                        // Load content based on tab
                        if (tabName === 'files') {
                            loadFiles(currentPath);
                        }
                    }
                    
                    function showNotification(message, type = 'success') {
                        const notification = document.getElementById('notification');
                        notification.textContent = message;
                        notification.className = `notification ${type} show`;
                        
                        setTimeout(() => {
                            notification.classList.remove('show');
                        }, 3000);
                    }
                    
                    function startServer() {
                        fetch('/api/start', {method: 'POST'})
                            .then(response => response.json())
                            .then(data => showNotification(data.message))
                            .catch(error => showNotification('Error starting server', 'error'));
                    }
                    
                    function stopServer() {
                        fetch('/api/stop', {method: 'POST'})
                            .then(response => response.json())
                            .then(data => showNotification(data.message))
                            .catch(error => showNotification('Error stopping server', 'error'));
                    }
                    
                    function restartServer() {
                        fetch('/api/restart', {method: 'POST'})
                            .then(response => response.json())
                            .then(data => showNotification(data.message))
                            .catch(error => showNotification('Error restarting server', 'error'));
                    }
                    
                    function killServer() {
                        if (confirm('Are you sure you want to force kill the server? This may cause data loss.')) {
                            fetch('/api/kill', {method: 'POST'})
                                .then(response => response.json())
                                .then(data => showNotification(data.message))
                                .catch(error => showNotification('Error killing server', 'error'));
                        }
                    }
                    
                    function sendCommand() {
                        const command = document.getElementById('command').value;
                        if (!command) return;
                        
                        fetch('/api/command', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({command: command})
                        })
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('command').value = '';
                            if (data.error) {
                                showNotification(data.error, 'error');
                            } else {
                                showNotification('Command sent successfully');
                            }
                        })
                        .catch(error => showNotification('Error sending command', 'error'));
                    }
                    
                    function updateStatus() {
                        fetch('/api/status')
                            .then(response => response.json())
                            .then(data => {
                                const statusIndicator = document.querySelector('.status-indicator');
                                const statusText = document.getElementById('status-text');
                                const playerCount = document.getElementById('player-count');
                                const maxPlayers = document.getElementById('max-players');
                                
                                if (data.running) {
                                    statusIndicator.className = 'status-indicator status-running';
                                    statusText.textContent = 'Server Running';
                                } else {
                                    statusIndicator.className = 'status-indicator status-stopped';
                                    statusText.textContent = 'Server Stopped';
                                }
                                
                                playerCount.textContent = data.players || 0;
                                maxPlayers.textContent = data.max_players || 20;
                            })
                            .catch(error => console.error('Error updating status:', error));
                    }
                    
                    function loadFiles(path = 'C:\\\\') {
                        fetch(`/api/files?path=${encodeURIComponent(path)}`)
                            .then(response => response.json())
                            .then(data => {
                                const fileList = document.getElementById('file-list');
                                const currentPathDiv = document.getElementById('current-path');
                                
                                currentPath = path;
                                currentPathDiv.textContent = path;
                                
                                if (data.error) {
                                    fileList.innerHTML = `<li class="file-item"><span class="file-name">Error: ${data.error}</span></li>`;
                                    return;
                                }
                                
                                fileList.innerHTML = '';
                                
                                // Add parent directory link if not at root
                                if (path !== 'C:\\\\' && path !== 'C:') {
                                    const parentPath = path.split('\\\\').slice(0, -1).join('\\\\') || 'C:\\\\';
                                    const parentItem = document.createElement('li');
                                    parentItem.className = 'file-item';
                                    parentItem.innerHTML = `
                                        <span class="file-icon">📁</span>
                                        <div class="file-info">
                                            <div class="file-name">..</div>
                                            <div class="file-details">Parent Directory</div>
                                        </div>
                                    `;
                                    parentItem.onclick = () => loadFiles(parentPath);
                                    fileList.appendChild(parentItem);
                                }
                                
                                data.files.forEach(file => {
                                    const item = document.createElement('li');
                                    item.className = 'file-item';
                                    
                                    const icon = file.type === 'directory' ? '📁' : '📄';
                                    const size = file.type === 'directory' ? '' : ` - ${file.size}`;
                                    
                                    item.innerHTML = `
                                        <span class="file-icon">${icon}</span>
                                        <div class="file-info">
                                            <div class="file-name">${file.name}</div>
                                            <div class="file-details">${file.modified}${size}</div>
                                        </div>
                                        <div class="file-actions">
                                            ${file.type === 'file' ? '<button class="file-action" onclick="downloadFile(\\''+file.name+'\\')">Download</button>' : ''}
                                            <button class="file-action" onclick="deleteFile(\\''+file.name+'\\')">Delete</button>
                                        </div>
                                    `;
                                    
                                    if (file.type === 'directory') {
                                        item.onclick = (e) => {
                                            if (!e.target.classList.contains('file-action')) {
                                                const newPath = path.endsWith('\\\\') ? path + file.name : path + '\\\\' + file.name;
                                                loadFiles(newPath);
                                            }
                                        };
                                    }
                                    
                                    fileList.appendChild(item);
                                });
                            })
                            .catch(error => {
                                console.error('Error loading files:', error);
                                showNotification('Error loading files', 'error');
                            });
                    }
                    
                    function downloadFile(filename) {
                        const url = `/api/files/download/${encodeURIComponent(currentPath)}/${encodeURIComponent(filename)}`;
                        window.open(url, '_blank');
                    }
                    
                    function deleteFile(filename) {
                        if (confirm(`Are you sure you want to delete "${filename}"?`)) {
                            fetch('/api/files/delete', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({filename: filename, path: currentPath})
                            })
                            .then(response => response.json())
                            .then(data => {
                                if (data.error) {
                                    showNotification(data.error, 'error');
                                } else {
                                    showNotification(data.message);
                                    loadFiles(currentPath);
                                }
                            })
                            .catch(error => showNotification('Error deleting file', 'error'));
                        }
                    }
                    
                    // Update status every 5 seconds
                    setInterval(updateStatus, 5000);
                    updateStatus();
                    
                    // Load initial files
                    loadFiles();
                </script>
            </body>
            </html>
            '''
        
        @self.web_server.route('/api/status')
        def api_status():
            return jsonify({
                'running': self.server_running,
                'players': self.current_players,
                'max_players': self.max_players
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
        
        @self.web_server.route('/api/kill', methods=['POST'])
        def api_kill():
            try:
                if self.server_process and self.server_process.poll() is None:
                    self.server_process.kill()
                    self.server_running = False
                    self.log_message("Server process forcefully terminated")
                    return jsonify({'message': 'Server killed successfully'})
                else:
                    return jsonify({'message': 'No server process to kill'})
            except Exception as e:
                return jsonify({'error': f'Failed to kill server: {str(e)}'})
        
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
        
        @self.web_server.route('/api/files')
        def api_files():
            path = request.args.get('path', 'C:\\\\')
            try:
                files = self.get_file_list(path)
                return jsonify({'files': files})
            except Exception as e:
                return jsonify({'error': str(e)})
        
        @self.web_server.route('/api/files/delete', methods=['POST'])
        def api_files_delete():
            data = request.get_json()
            filename = data.get('filename')
            path = data.get('path', 'C:\\\\')
            
            if not filename:
                return jsonify({'error': 'No filename provided'})
            
            try:
                file_path = os.path.join(path, filename)
                file_path = os.path.normpath(file_path)
                
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    return jsonify({'message': f'File {filename} deleted successfully'})
                elif os.path.isdir(file_path):
                    import shutil
                    shutil.rmtree(file_path)
                    return jsonify({'message': f'Directory {filename} deleted successfully'})
                else:
                    return jsonify({'error': 'File or directory not found'})
            except Exception as e:
                return jsonify({'error': f'Failed to delete: {str(e)}'})
        
        @self.web_server.route('/api/files/download/<path:filename>')
        def api_files_download(filename):
            try:
                # Decode the path
                file_path = os.path.normpath(filename)
                
                if os.path.isfile(file_path):
                    return send_file(file_path, as_attachment=True)
                else:
                    return jsonify({'error': 'File not found'}), 404
            except Exception as e:
                return jsonify({'error': f'Failed to download file: {str(e)}'}), 500
    
    def get_file_list(self, path='C:\\\\'):
        """Get list of files and directories"""
        try:
            # Normalize the path
            if not path or path == '':
                path = 'C:\\\\'
            
            path = os.path.normpath(path)
            
            if not os.path.exists(path):
                raise Exception(f"Path does not exist: {path}")
            
            if not os.path.isdir(path):
                raise Exception(f"Path is not a directory: {path}")
            
            files = []
            try:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    try:
                        stat = os.stat(item_path)
                        is_dir = os.path.isdir(item_path)
                        
                        file_info = {
                            'name': item,
                            'type': 'directory' if is_dir else 'file',
                            'size': self.format_file_size(stat.st_size) if not is_dir else '',
                            'modified': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
                        }
                        files.append(file_info)
                    except (OSError, PermissionError):
                        # Skip files we can't access
                        continue
                        
            except PermissionError:
                raise Exception(f"Permission denied accessing: {path}")
            
            # Sort directories first, then files
            files.sort(key=lambda x: (x['type'] == 'file', x['name'].lower()))
            return files
            
        except Exception as e:
            raise Exception(f"Error listing files: {str(e)}")
    
    def format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
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
