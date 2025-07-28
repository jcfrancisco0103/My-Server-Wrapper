#!/usr/bin/env python3
"""
Minecraft Server Wrapper for ARM64 Ubuntu (Termux)
Complete feature parity with Windows version
Optimized for headless operation with web interface
"""

import os
import sys
import json
import time
import threading
import subprocess
import signal
import argparse
from datetime import datetime
import webbrowser
import re
import hashlib
import secrets
import shutil

# Optional GUI imports - will run headless if not available
GUI_AVAILABLE = False
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, filedialog, messagebox
    GUI_AVAILABLE = True
except ImportError:
    print("GUI not available - running in headless mode")

# Web server imports
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from flask_socketio import SocketIO, emit
from werkzeug.serving import make_server
import psutil

class MinecraftServerWrapper:
    def __init__(self, root=None, headless=False, port=5000):
        self.headless = headless or not GUI_AVAILABLE
        self.web_port = port
        
        if not self.headless and GUI_AVAILABLE:
            self.root = root
            self.root.title("Minecraft Server Wrapper - Ubuntu ARM64")
            self.root.geometry("800x600")
            self.root.configure(bg="#2c3e50")
            self.root.resizable(True, True)
            self.root.minsize(700, 500)
            
            # Set default font
            self.default_font = ("Ubuntu", 10)
            self.title_font = ("Ubuntu", 16, "bold")
            self.button_font = ("Ubuntu", 10, "bold")
            self.label_font = ("Ubuntu", 10)
            self.console_font = ("Ubuntu Mono", 10)
        else:
            self.root = None
            
        # Server process
        self.server_process = None
        self.server_running = False
        self.server_start_time = None
        
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
        self.socketio = None
        
        # Configuration
        self.config_file = "server_config.json"
        self.load_config()
        
        # Console history storage
        self.console_history = []
        self.max_console_history = 1000
        self.console_history_file = "console_history.json"
        self.load_console_history()
        
        # GUI variables (only if GUI available)
        if not self.headless and GUI_AVAILABLE:
            self.startup_enabled_var = tk.BooleanVar()
            self.remote_access_enabled = tk.BooleanVar()
            self.startup_enabled_var.set(False)  # Ubuntu doesn't use Windows startup
            self.remote_access_enabled.set(True)
            self.setup_ui()
            # Bind window close event to save configuration
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Start web server automatically
        self.start_web_server()
        
    def signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.on_closing()
        
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
            "remote_access_enabled": True,
            "web_port": self.web_port
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
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Failed to save config: {str(e)}")
            if not self.headless and GUI_AVAILABLE:
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
        
        # Emit to web clients via SocketIO
        if self.socketio:
            self.socketio.emit('console_update', entry)
        
        if len(self.console_history) % 10 == 0:
            self.save_console_history()
    
    def setup_ui(self):
        """Setup the user interface (only if GUI is available)"""
        if self.headless or not GUI_AVAILABLE:
            return
            
        # Main frame
        main_frame = tk.Frame(self.root, bg="#2c3e50")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="Minecraft Server Wrapper - Ubuntu ARM64", 
                              font=self.title_font, fg="#ecf0f1", bg="#2c3e50")
        title_label.pack(pady=(0, 20))
        
        # Web interface info
        web_info = tk.Label(main_frame, text=f"Web Interface: http://localhost:{self.web_port}", 
                           font=self.label_font, fg="#3498db", bg="#2c3e50")
        web_info.pack(pady=(0, 10))
        
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
        
        config_grid = tk.Frame(config_frame, bg="#34495e")
        config_grid.pack(pady=10)
        
        # Server JAR selection
        tk.Label(config_grid, text="Server JAR:", font=self.label_font,
                fg="#ecf0f1", bg="#34495e").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        jar_frame = tk.Frame(config_grid, bg="#34495e")
        jar_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        self.jar_entry = tk.Entry(jar_frame, width=40, font=self.default_font,
                                 bg="#2c3e50", fg="#ecf0f1", insertbackground="#ecf0f1")
        self.jar_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        browse_button = tk.Button(jar_frame, text="Browse", command=self.browse_jar,
                                 bg="#3498db", fg="white", font=self.button_font)
        browse_button.pack(side=tk.LEFT)
        
        # Memory settings
        tk.Label(config_grid, text="Min Memory:", font=self.label_font,
                fg="#ecf0f1", bg="#34495e").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        self.min_memory_entry = tk.Entry(config_grid, width=10, font=self.default_font,
                                        bg="#2c3e50", fg="#ecf0f1", insertbackground="#ecf0f1")
        self.min_memory_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        tk.Label(config_grid, text="Max Memory:", font=self.label_font,
                fg="#ecf0f1", bg="#34495e").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        
        self.max_memory_entry = tk.Entry(config_grid, width=10, font=self.default_font,
                                        bg="#2c3e50", fg="#ecf0f1", insertbackground="#ecf0f1")
        self.max_memory_entry.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        # Console frame
        console_frame = tk.Frame(main_frame, bg="#34495e", relief=tk.GROOVE, bd=2)
        console_frame.pack(fill=tk.BOTH, expand=True)
        
        console_title = tk.Label(console_frame, text="Server Console",
                                font=(self.label_font[0], 12, "bold"), fg="#ecf0f1", bg="#34495e")
        console_title.pack(pady=5)
        
        # Console output
        self.console_output = scrolledtext.ScrolledText(console_frame, height=15, width=80,
                                                       bg="#1a1a1a", fg="#00ff00", font=self.console_font,
                                                       insertbackground="#00ff00", state=tk.DISABLED)
        self.console_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Command input frame
        command_frame = tk.Frame(console_frame, bg="#34495e")
        command_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.command_entry = tk.Entry(command_frame, bg="#2c3e50", fg="#ecf0f1",
                                     font=self.default_font, insertbackground="#ecf0f1")
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.command_entry.bind("<Return>", lambda e: self.send_command())
        
        send_button = tk.Button(command_frame, text="Send", command=self.send_command,
                               bg="#3498db", fg="white", font=self.button_font)
        send_button.pack(side=tk.LEFT)
        
        # Load configuration into UI
        self.load_config_to_ui()
    
    def load_config_to_ui(self):
        """Load configuration values into UI elements"""
        if self.headless or not GUI_AVAILABLE:
            return
            
        self.jar_entry.delete(0, tk.END)
        self.jar_entry.insert(0, self.config.get("server_jar", ""))
        
        self.min_memory_entry.delete(0, tk.END)
        self.min_memory_entry.insert(0, self.config.get("memory_min", "1G"))
        
        self.max_memory_entry.delete(0, tk.END)
        self.max_memory_entry.insert(0, self.config.get("memory_max", "2G"))
    
    def browse_jar(self):
        """Browse for server JAR file"""
        if self.headless or not GUI_AVAILABLE:
            return
            
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
            print("Warning: Server is already running!")
            if not self.headless and GUI_AVAILABLE:
                messagebox.showwarning("Warning", "Server is already running!")
            return
        
        # Get configuration
        server_jar = self.config.get("server_jar", "")
        if not self.headless and GUI_AVAILABLE:
            server_jar = self.jar_entry.get() if self.jar_entry.get() else server_jar
        
        if not server_jar:
            print("Error: Please select a server JAR file!")
            if not self.headless and GUI_AVAILABLE:
                messagebox.showerror("Error", "Please select a server JAR file!")
            return
        
        if not os.path.exists(server_jar):
            print(f"Error: Server JAR file not found: {server_jar}")
            if not self.headless and GUI_AVAILABLE:
                messagebox.showerror("Error", "Server JAR file not found!")
            return
        
        # Get memory settings
        min_memory = self.config.get("memory_min", "1G")
        max_memory = self.config.get("memory_max", "2G")
        
        if not self.headless and GUI_AVAILABLE:
            min_memory = self.min_memory_entry.get() if self.min_memory_entry.get() else min_memory
            max_memory = self.max_memory_entry.get() if self.max_memory_entry.get() else max_memory
        
        # Update config with current values
        self.config["server_jar"] = server_jar
        self.config["memory_min"] = min_memory
        self.config["memory_max"] = max_memory
        self.save_config()
        
        # Build command
        java_path = self.config.get("java_path", "java")
        additional_args = self.config.get("additional_args", "")
        use_aikars_flags = self.config.get("use_aikars_flags", False)
        
        cmd = [java_path]
        
        # Add memory settings
        cmd.extend([f"-Xms{min_memory}", f"-Xmx{max_memory}"])
        
        # Add Aikar's flags if enabled (ARM64 optimized)
        if use_aikars_flags:
            aikars_flags = [
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
            cmd.extend(aikars_flags)
        
        # Add additional arguments
        if additional_args:
            cmd.extend(additional_args.split())
        
        # Add JAR and nogui
        cmd.extend(["-jar", server_jar, "nogui"])
        
        try:
            # Change to server directory
            server_dir = os.path.dirname(os.path.abspath(server_jar))
            
            # Start server process
            self.server_process = subprocess.Popen(
                cmd,
                cwd=server_dir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.server_running = True
            self.server_start_time = time.time()
            
            # Start output monitoring thread
            self.output_thread = threading.Thread(target=self.monitor_server_output, daemon=True)
            self.output_thread.start()
            
            self.log_message("Server starting...")
            print(f"Server started with PID: {self.server_process.pid}")
            
            if not self.headless and GUI_AVAILABLE:
                self.status_label.config(text="Status: Starting...")
            
        except Exception as e:
            error_msg = f"Failed to start server: {str(e)}"
            print(error_msg)
            self.log_message(error_msg)
            if not self.headless and GUI_AVAILABLE:
                messagebox.showerror("Error", error_msg)
    
    def stop_server(self):
        """Stop the Minecraft server with improved shutdown process"""
        if not self.server_running:
            print("Server is not running")
            return
        
        self.log_message("Stopping server...")
        print("Stopping server...")
        
        try:
            if self.server_process and self.server_process.poll() is None:
                # Send stop command first
                self.server_process.stdin.write("stop\n")
                self.server_process.stdin.flush()
                self.log_message("Stop command sent to server")
                
                # Wait for graceful shutdown (reduced timeout for ARM64)
                try:
                    self.server_process.wait(timeout=15)
                    self.log_message("Server stopped gracefully")
                except subprocess.TimeoutExpired:
                    self.log_message("Server did not stop gracefully, attempting force termination...")
                    
                    # First attempt: SIGTERM
                    try:
                        self.server_process.terminate()
                        self.server_process.wait(timeout=5)
                        self.log_message("Server terminated with SIGTERM")
                    except subprocess.TimeoutExpired:
                        # Final attempt: SIGKILL
                        self.log_message("Force killing server process...")
                        self.server_process.kill()
                        self.server_process.wait()
                        self.log_message("Server process killed")
            
            self.server_running = False
            self.server_process = None
            self.server_start_time = None
            self.current_players = 0
            self.player_list.clear()
            
            # Save console history and configuration immediately
            self.save_console_history()
            self.save_config()
            
            if not self.headless and GUI_AVAILABLE:
                self.status_label.config(text="Status: Stopped")
            
            print("Server stopped successfully")
            
        except Exception as e:
            error_msg = f"Error stopping server: {str(e)}"
            print(error_msg)
            self.log_message(error_msg)
    
    def restart_server(self):
        """Restart the Minecraft server"""
        self.log_message("Restarting server...")
        self.stop_server()
        time.sleep(2)  # Brief pause
        self.start_server()
    
    def send_command(self, command=None):
        """Send command to server"""
        if not self.server_running:
            print("Server is not running")
            return
        
        if command is None:
            if self.headless or not GUI_AVAILABLE:
                return
            command = self.command_entry.get().strip()
            self.command_entry.delete(0, tk.END)
        
        if not command:
            return
        
        try:
            self.server_process.stdin.write(command + "\n")
            self.server_process.stdin.flush()
            self.log_message(f"[COMMAND] {command}")
        except Exception as e:
            error_msg = f"Failed to send command: {str(e)}"
            print(error_msg)
            self.log_message(error_msg)
    
    def monitor_server_output(self):
        """Monitor server output in a separate thread"""
        while self.server_running and self.server_process:
            try:
                line = self.server_process.stdout.readline()
                if line:
                    line = line.strip()
                    self.log_message(line)
                    self.parse_server_output(line)
                elif self.server_process.poll() is not None:
                    break
            except Exception as e:
                print(f"Error reading server output: {e}")
                break
        
        # Server process ended
        if self.server_running:
            self.server_running = False
            self.log_message("Server process ended unexpectedly")
            if not self.headless and GUI_AVAILABLE:
                self.status_label.config(text="Status: Stopped (Unexpected)")
    
    def parse_server_output(self, line):
        """Parse server output for player events and status"""
        # Player join detection
        join_patterns = [
            r"(\w+) joined the game",
            r"(\w+)\[.*\] logged in"
        ]
        
        for pattern in join_patterns:
            match = re.search(pattern, line)
            if match:
                player = match.group(1)
                self.player_list.add(player)
                self.current_players = len(self.player_list)
                break
        
        # Player leave detection
        leave_patterns = [
            r"(\w+) left the game",
            r"(\w+) lost connection"
        ]
        
        for pattern in leave_patterns:
            match = re.search(pattern, line)
            if match:
                player = match.group(1)
                self.player_list.discard(player)
                self.current_players = len(self.player_list)
                break
        
        # Server ready detection
        if "Done" in line and "For help, type" in line:
            if not self.headless and GUI_AVAILABLE:
                self.status_label.config(text="Status: Running")
    
    def log_message(self, message):
        """Log message to console"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # Add to console history for web interface
        self.add_to_console_history(message)
        
        # Print to terminal
        print(formatted_message)
        
        # Update GUI console if available
        if not self.headless and GUI_AVAILABLE and hasattr(self, 'console_output'):
            def update_console():
                self.console_output.config(state=tk.NORMAL)
                self.console_output.insert(tk.END, formatted_message + "\n")
                self.console_output.see(tk.END)
                self.console_output.config(state=tk.DISABLED)
            
            if threading.current_thread() == threading.main_thread():
                update_console()
            else:
                self.root.after(0, update_console)
    
    def start_web_server(self):
        """Start the web server"""
        if self.web_server_running:
            return
        
        try:
            self.web_server = Flask(__name__)
            self.web_server.config['SECRET_KEY'] = secrets.token_hex(16)
            
            # Initialize SocketIO
            self.socketio = SocketIO(self.web_server, cors_allowed_origins="*")
            self.setup_socketio_events()
            self.setup_web_routes()
            
            # Start server in a separate thread
            self.web_server_thread = threading.Thread(
                target=lambda: self.socketio.run(
                    self.web_server, 
                    host='0.0.0.0', 
                    port=self.web_port, 
                    debug=False,
                    allow_unsafe_werkzeug=True
                ),
                daemon=True
            )
            self.web_server_thread.start()
            self.web_server_running = True
            
            print(f"Web server started on http://0.0.0.0:{self.web_port}")
            print(f"Access locally: http://localhost:{self.web_port}")
            
        except Exception as e:
            print(f"Failed to start web server: {e}")
    
    def setup_socketio_events(self):
        """Setup SocketIO events for real-time updates"""
        @self.socketio.on('connect')
        def handle_connect():
            print('Client connected to SocketIO')
            # Send recent console history to new client
            recent_logs = self.console_history[-50:] if len(self.console_history) > 50 else self.console_history
            emit('console_history', recent_logs)
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print('Client disconnected from SocketIO')
    
    def setup_web_routes(self):
        """Setup web routes"""
        @self.web_server.route('/')
        def index():
            return self.get_web_interface()
        
        @self.web_server.route('/api/status')
        def api_status():
            """Get server status"""
            uptime = 0
            if self.server_running and self.server_start_time:
                uptime = int(time.time() - self.server_start_time)
            
            return jsonify({
                'running': self.server_running,
                'players': self.current_players,
                'max_players': self.max_players,
                'uptime': uptime,
                'player_list': list(self.player_list)
            })
        
        @self.web_server.route('/api/start', methods=['POST'])
        def api_start():
            if self.server_running:
                return jsonify({'message': 'Server is already running'})
            
            # Start server in main thread if GUI available, otherwise directly
            if not self.headless and GUI_AVAILABLE and self.root:
                self.root.after(0, self.start_server)
            else:
                threading.Thread(target=self.start_server, daemon=True).start()
            
            return jsonify({'message': 'Starting server...'})
        
        @self.web_server.route('/api/stop', methods=['POST'])
        def api_stop():
            if not self.server_running:
                return jsonify({'message': 'Server is not running'})
            
            if not self.headless and GUI_AVAILABLE and self.root:
                self.root.after(0, self.stop_server)
            else:
                threading.Thread(target=self.stop_server, daemon=True).start()
            
            return jsonify({'message': 'Stopping server...'})
        
        @self.web_server.route('/api/restart', methods=['POST'])
        def api_restart():
            if not self.headless and GUI_AVAILABLE and self.root:
                self.root.after(0, self.restart_server)
            else:
                threading.Thread(target=self.restart_server, daemon=True).start()
            
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
                # Ensure the server process is still alive
                if not self.server_process or self.server_process.poll() is not None:
                    return jsonify({'error': 'Server process is not available'})
                
                # Send command to server
                self.server_process.stdin.write(command + "\n")
                self.server_process.stdin.flush()
                
                # Log the command
                self.log_message(f"[WEB] {command}")
                
                return jsonify({'message': 'Command executed'})
            except Exception as e:
                return jsonify({'error': f'Failed to send command: {str(e)}'})
        
        @self.web_server.route('/api/console')
        def api_console():
            """Get recent console output"""
            try:
                # Get the last 100 console entries
                recent_logs = self.console_history[-100:] if len(self.console_history) > 100 else self.console_history
                return jsonify({'logs': recent_logs})
            except Exception as e:
                return jsonify({'error': f'Failed to get console logs: {str(e)}'})
        
        @self.web_server.route('/api/files')
        def api_files():
            path = request.args.get('path', os.getcwd())
            try:
                files = self.get_file_list(path)
                return jsonify({'files': files})
            except Exception as e:
                return jsonify({'error': str(e)})
        
        @self.web_server.route('/api/files/delete', methods=['POST'])
        def api_files_delete():
            data = request.get_json()
            filename = data.get('filename')
            path = data.get('path', os.getcwd())
            
            if not filename:
                return jsonify({'error': 'No filename provided'})
            
            try:
                file_path = os.path.join(path, filename)
                file_path = os.path.normpath(file_path)
                
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    return jsonify({'message': f'File {filename} deleted successfully'})
                elif os.path.isdir(file_path):
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
    
    def get_file_list(self, path=None):
        """Get list of files and directories"""
        try:
            if not path:
                path = os.getcwd()
            
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
    
    def get_web_interface(self):
        """Return the web interface HTML"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Minecraft Server Wrapper - Ubuntu ARM64</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Ubuntu', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
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
            color: white;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .card h2 {
            color: #4a5568;
            margin-bottom: 20px;
            font-size: 1.5em;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 10px;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .status-item {
            text-align: center;
            padding: 15px;
            background: #f7fafc;
            border-radius: 10px;
            border-left: 4px solid #4299e1;
        }
        
        .status-item .label {
            font-size: 0.9em;
            color: #718096;
            margin-bottom: 5px;
        }
        
        .status-item .value {
            font-size: 1.4em;
            font-weight: bold;
            color: #2d3748;
        }
        
        .controls {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .btn {
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        
        .btn-start {
            background: linear-gradient(45deg, #48bb78, #38a169);
            color: white;
        }
        
        .btn-stop {
            background: linear-gradient(45deg, #f56565, #e53e3e);
            color: white;
        }
        
        .btn-restart {
            background: linear-gradient(45deg, #ed8936, #dd6b20);
            color: white;
        }
        
        .btn-kill {
            background: linear-gradient(45deg, #9f7aea, #805ad5);
            color: white;
        }
        
        .console-container {
            grid-column: 1 / -1;
        }
        
        .console {
            background: #1a202c;
            color: #00ff00;
            font-family: 'Ubuntu Mono', 'Courier New', monospace;
            font-size: 14px;
            padding: 20px;
            border-radius: 10px;
            height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            border: 2px solid #2d3748;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .console::-webkit-scrollbar {
            width: 8px;
        }
        
        .console::-webkit-scrollbar-track {
            background: #2d3748;
            border-radius: 4px;
        }
        
        .console::-webkit-scrollbar-thumb {
            background: #4a5568;
            border-radius: 4px;
        }
        
        .console::-webkit-scrollbar-thumb:hover {
            background: #718096;
        }
        
        .command-section {
            margin-top: 20px;
        }
        
        .command-mode-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .mode-button {
            padding: 8px 16px;
            border: 2px solid #4299e1;
            background: transparent;
            color: #4299e1;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: bold;
        }
        
        .mode-button.active {
            background: #4299e1;
            color: white;
        }
        
        .mode-button:hover {
            background: #4299e1;
            color: white;
        }
        
        .command-input-container {
            display: flex;
            gap: 10px;
        }
        
        .command-input {
            flex: 1;
            padding: 12px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 1em;
            background: white;
            transition: border-color 0.3s ease;
        }
        
        .command-input:focus {
            outline: none;
            border-color: #4299e1;
            box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
        }
        
        .btn-send {
            background: linear-gradient(45deg, #4299e1, #3182ce);
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .btn-send:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        
        .footer {
            text-align: center;
            margin-top: 30px;
            color: white;
            opacity: 0.8;
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            
            .controls {
                grid-template-columns: 1fr 1fr;
            }
            
            .status-grid {
                grid-template-columns: 1fr 1fr;
            }
        }
        
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: bold;
            z-index: 1000;
            transform: translateX(400px);
            transition: transform 0.3s ease;
        }
        
        .notification.show {
            transform: translateX(0);
        }
        
        .notification.success {
            background: linear-gradient(45deg, #48bb78, #38a169);
        }
        
        .notification.error {
            background: linear-gradient(45deg, #f56565, #e53e3e);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 Minecraft Server Wrapper</h1>
            <p>🚀 Powered by Flask & SocketIO | 🐧 Running on Ubuntu ARM64</p>
        </div>
        
        <div class="main-content">
            <div class="card">
                <h2>📊 Server Status</h2>
                <div class="status-grid">
                    <div class="status-item">
                        <div class="label">Status</div>
                        <div class="value" id="server-status">Stopped</div>
                    </div>
                    <div class="status-item">
                        <div class="label">Players</div>
                        <div class="value" id="player-count">0/20</div>
                    </div>
                    <div class="status-item">
                        <div class="label">Uptime</div>
                        <div class="value" id="uptime">00:00:00</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>🎛️ Server Controls</h2>
                <div class="controls">
                    <button class="btn btn-start" onclick="startServer()">▶ Start</button>
                    <button class="btn btn-stop" onclick="stopServer()">⏹ Stop</button>
                    <button class="btn btn-restart" onclick="restartServer()">🔄 Restart</button>
                    <button class="btn btn-kill" onclick="killServer()">💀 Kill</button>
                </div>
            </div>
            
            <div class="card console-container">
                <h2>💻 Server Console</h2>
                <div id="console" class="console"></div>
                
                <div class="command-section">
                    <div class="command-mode-buttons">
                        <button class="mode-button active" onclick="setCommandMode(true)">CMD</button>
                        <button class="mode-button" onclick="setCommandMode(false)">Chat</button>
                    </div>
                    <div class="command-input-container">
                        <input type="text" id="command-input" class="command-input" 
                               placeholder="Enter server command..." 
                               onkeypress="handleKeyPress(event)">
                        <button class="btn-send" onclick="sendCommand()">Send</button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>🚀 Powered by Flask & SocketIO | 🐧 Running on Ubuntu ARM64</p>
        </div>
    </div>
    
    <script>
        let commandMode = true;
        let socket = io();
        
        // SocketIO event handlers
        socket.on('connect', function() {
            console.log('Connected to server via SocketIO');
        });
        
        socket.on('console_update', function(data) {
            addConsoleMessage(data.message, data.timestamp);
        });
        
        socket.on('console_history', function(data) {
            const console = document.getElementById('console');
            console.innerHTML = '';
            data.forEach(entry => {
                addConsoleMessage(entry.message, entry.timestamp);
            });
        });
        
        function setCommandMode(isCommand) {
            commandMode = isCommand;
            const buttons = document.querySelectorAll('.mode-button');
            const input = document.getElementById('command-input');
            
            buttons.forEach(btn => btn.classList.remove('active'));
            
            if (isCommand) {
                buttons[0].classList.add('active');
                input.placeholder = 'Enter server command...';
            } else {
                buttons[1].classList.add('active');
                input.placeholder = 'Enter chat message...';
            }
        }
        
        function addConsoleMessage(message, timestamp) {
            const console = document.getElementById('console');
            const line = document.createElement('div');
            line.textContent = `[${timestamp}] ${message}`;
            console.appendChild(line);
            console.scrollTop = console.scrollHeight;
        }
        
        function showNotification(message, type = 'success') {
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            document.body.appendChild(notification);
            
            setTimeout(() => notification.classList.add('show'), 100);
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => document.body.removeChild(notification), 300);
            }, 3000);
        }
        
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('server-status').textContent = data.running ? 'Running' : 'Stopped';
                    document.getElementById('player-count').textContent = `${data.players}/${data.max_players}`;
                    
                    const hours = Math.floor(data.uptime / 3600);
                    const minutes = Math.floor((data.uptime % 3600) / 60);
                    const seconds = data.uptime % 60;
                    const uptime = document.getElementById('uptime');
                    uptime.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                })
                .catch(error => {
                    console.error('Error updating status:', error);
                });
        }
        
        function startServer() {
            fetch('/api/start', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    showNotification(data.message || data.error, data.error ? 'error' : 'success');
                })
                .catch(error => {
                    showNotification('Failed to start server', 'error');
                });
        }
        
        function stopServer() {
            fetch('/api/stop', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    showNotification(data.message || data.error, data.error ? 'error' : 'success');
                })
                .catch(error => {
                    showNotification('Failed to stop server', 'error');
                });
        }
        
        function restartServer() {
            fetch('/api/restart', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    showNotification(data.message || data.error, data.error ? 'error' : 'success');
                })
                .catch(error => {
                    showNotification('Failed to restart server', 'error');
                });
        }
        
        function killServer() {
            if (confirm('Are you sure you want to force kill the server? This may cause data loss.')) {
                fetch('/api/kill', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        showNotification(data.message || data.error, data.error ? 'error' : 'success');
                    })
                    .catch(error => {
                        showNotification('Failed to kill server', 'error');
                    });
            }
        }
        
        function sendCommand() {
            const input = document.getElementById('command-input');
            let command = input.value.trim();
            
            if (!command) return;
            
            // Add "say" prefix for chat mode
            if (!commandMode) {
                command = `say ${command}`;
            }
            
            fetch('/api/command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ command: command })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showNotification(data.error, 'error');
                }
                input.value = '';
            })
            .catch(error => {
                showNotification('Failed to send command', 'error');
            });
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendCommand();
            }
        }
        
        // Update status every 2 seconds
        setInterval(updateStatus, 2000);
        
        // Initial status update
        updateStatus();
    </script>
</body>
</html>
        '''
    
    def on_closing(self):
        """Handle application closing"""
        self.save_config()
        self.save_console_history()
        
        if self.server_running:
            print("Stopping server before exit...")
            self.stop_server()
        
        if not self.headless and GUI_AVAILABLE and self.root:
            self.root.destroy()
        else:
            sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description='Minecraft Server Wrapper for Ubuntu ARM64')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (no GUI)')
    parser.add_argument('--port', type=int, default=5000, help='Web interface port (default: 5000)')
    
    args = parser.parse_args()
    
    if args.headless or not GUI_AVAILABLE:
        print("Starting in headless mode...")
        app = MinecraftServerWrapper(headless=True, port=args.port)
        
        try:
            print(f"Server running. Access web interface at http://localhost:{args.port}")
            print("Press Ctrl+C to stop")
            
            # Keep the main thread alive
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nShutting down...")
            app.on_closing()
    else:
        print("Starting with GUI...")
        root = tk.Tk()
        app = MinecraftServerWrapper(root, headless=False, port=args.port)
        root.mainloop()

if __name__ == "__main__":
    main()