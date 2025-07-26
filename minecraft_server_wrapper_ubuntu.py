#!/usr/bin/env python3
"""
Minecraft Server Wrapper for ARM64 Ubuntu (Termux)
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

# Optional GUI imports - will run headless if not available
GUI_AVAILABLE = False
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, filedialog, messagebox
    GUI_AVAILABLE = True
except ImportError:
    print("GUI not available - running in headless mode")
    GUI_AVAILABLE = False

from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from flask_socketio import SocketIO, emit
from werkzeug.serving import make_server

class MinecraftServerWrapper:
    def __init__(self, headless=False):
        self.headless = headless or not GUI_AVAILABLE
        
        if not self.headless and GUI_AVAILABLE:
            self.root = tk.Tk()
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
            print("Running in headless mode - access via web interface")
        
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
        self.web_port = 5000
        
        # Configuration
        self.config_file = "server_config.json"
        self.load_config()
        
        # Console history storage
        self.console_history = []
        self.max_console_history = 1000
        self.console_history_file = "console_history.json"
        self.load_console_history()
        
        # Set remote access settings
        self.web_port = self.config.get("web_port", 5000)
        
        if not self.headless:
            self.setup_ui()
            # Bind window close event to save configuration
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start web server automatically
        self.start_web_server()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
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
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Failed to save config: {str(e)}")
            if not self.headless:
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
        send_button.pack(side=tk.RIGHT)
        
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
    
    def start_server(self):
        """Start the Minecraft server"""
        if self.server_running:
            print("Warning: Server is already running!")
            if not self.headless:
                messagebox.showwarning("Warning", "Server is already running!")
            return
        
        # Get configuration
        server_jar = self.config.get("server_jar", "")
        if not self.headless:
            server_jar = self.jar_entry.get() if self.jar_entry.get() else server_jar
        
        if not server_jar:
            print("Error: Please select a server JAR file!")
            if not self.headless:
                messagebox.showerror("Error", "Please select a server JAR file!")
            return
        
        if not os.path.exists(server_jar):
            print("Error: Server JAR file not found!")
            if not self.headless:
                messagebox.showerror("Error", "Server JAR file not found!")
            return
        
        # Update config with current values
        if not self.headless:
            self.config["server_jar"] = self.jar_entry.get()
            self.config["memory_min"] = self.min_memory_entry.get()
            self.config["memory_max"] = self.max_memory_entry.get()
        
        try:
            # Build Java command
            java_path = self.config.get("java_path", "java")
            memory_min = self.config.get("memory_min", "1G")
            memory_max = self.config.get("memory_max", "2G")
            additional_args = self.config.get("additional_args", "")
            
            # Use Aikar's flags for better performance on ARM64
            if self.config.get("use_aikars_flags", False):
                jvm_args = [
                    f"-Xms{memory_min}",
                    f"-Xmx{memory_max}",
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
                    "-XX:MaxTenuringThreshold=1"
                ]
            else:
                jvm_args = [f"-Xms{memory_min}", f"-Xmx{memory_max}"]
            
            # Add additional arguments
            if additional_args:
                jvm_args.extend(additional_args.split())
            
            # Build command
            cmd = [java_path] + jvm_args + ["-jar", server_jar, "nogui"]
            
            print(f"Starting server with command: {' '.join(cmd)}")
            self.log_message(f"Starting server: {' '.join(cmd)}")
            
            # Start server process
            self.server_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=os.path.dirname(server_jar) if os.path.dirname(server_jar) else "."
            )
            
            self.server_running = True
            self.server_start_time = time.time()
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self.monitor_output, daemon=True)
            self.monitor_thread.start()
            
            self.log_message("Server started successfully!")
            self.update_ui_state()
            
        except Exception as e:
            error_msg = f"Failed to start server: {str(e)}"
            print(f"Error: {error_msg}")
            self.log_message(f"Error: {error_msg}")
            if not self.headless:
                messagebox.showerror("Error", error_msg)
    
    def stop_server(self):
        """Stop the Minecraft server with improved shutdown process"""
        if not self.server_running:
            print("Warning: Server is not running!")
            if not self.headless:
                messagebox.showwarning("Warning", "Server is not running!")
            return
        
        try:
            self.log_message("Stopping server...")
            print("Stopping server...")
            
            # Send stop command to server
            if self.server_process and self.server_process.stdin:
                self.server_process.stdin.write("stop\n")
                self.server_process.stdin.flush()
                self.log_message("Stop command sent to server")
            
            # Wait for graceful shutdown (reduced timeout for ARM64)
            self.log_message("Waiting for graceful shutdown...")
            try:
                self.server_process.wait(timeout=15)
                self.log_message("Server stopped gracefully")
            except subprocess.TimeoutExpired:
                self.log_message("Graceful shutdown timeout, attempting force termination...")
                
                # First attempt: SIGTERM
                self.server_process.terminate()
                try:
                    self.server_process.wait(timeout=5)
                    self.log_message("Server terminated successfully")
                except subprocess.TimeoutExpired:
                    # Final attempt: SIGKILL
                    self.log_message("Force killing server process...")
                    self.server_process.kill()
                    self.server_process.wait()
                    self.log_message("Server process killed")
            
            self.server_running = False
            self.server_process = None
            self.server_start_time = None
            
            # Save console history and configuration immediately
            self.save_console_history()
            self.save_config()
            
            self.log_message("Server stopped successfully!")
            self.update_ui_state()
            
        except Exception as e:
            error_msg = f"Failed to stop server: {str(e)}"
            print(f"Error: {error_msg}")
            self.log_message(f"Error: {error_msg}")
    
    def restart_server(self):
        """Restart the Minecraft server"""
        if self.server_running:
            self.stop_server()
            # Wait a moment for cleanup
            time.sleep(2)
        self.start_server()
    
    def send_command(self, command=None):
        """Send command to the server"""
        if not self.server_running:
            print("Warning: Server is not running!")
            if not self.headless:
                messagebox.showwarning("Warning", "Server is not running!")
            return
        
        try:
            if command is None and not self.headless:
                command = self.command_entry.get()
            
            if command and self.server_process and self.server_process.stdin:
                self.server_process.stdin.write(command + "\n")
                self.server_process.stdin.flush()
                self.log_message(f"Command sent: {command}")
                
                if not self.headless:
                    self.command_entry.delete(0, tk.END)
        except Exception as e:
            error_msg = f"Failed to send command: {str(e)}"
            print(f"Error: {error_msg}")
            self.log_message(f"Error: {error_msg}")
    
    def monitor_output(self):
        """Monitor server output"""
        while self.server_running and self.server_process:
            try:
                line = self.server_process.stdout.readline()
                if line:
                    line = line.strip()
                    self.log_message(line)
                    self.parse_server_output(line)
                elif self.server_process.poll() is not None:
                    # Process has ended
                    break
            except Exception as e:
                print(f"Error monitoring output: {e}")
                break
        
        # Server process ended
        if self.server_running:
            self.server_running = False
            self.log_message("Server process ended unexpectedly")
            self.update_ui_state()
    
    def parse_server_output(self, line):
        """Parse server output for player events and other information"""
        # Player join detection
        if "joined the game" in line:
            # Extract player name (basic parsing)
            parts = line.split()
            for i, part in enumerate(parts):
                if part == "joined":
                    if i > 0:
                        player_name = parts[i-1].split("]")[-1].strip()
                        self.player_list.add(player_name)
                        self.current_players = len(self.player_list)
                        break
        
        # Player leave detection
        elif "left the game" in line:
            # Extract player name (basic parsing)
            parts = line.split()
            for i, part in enumerate(parts):
                if part == "left":
                    if i > 0:
                        player_name = parts[i-1].split("]")[-1].strip()
                        self.player_list.discard(player_name)
                        self.current_players = len(self.player_list)
                        break
    
    def log_message(self, message):
        """Log message to console and history"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # Add to console history
        self.add_to_console_history(message)
        
        # Update GUI console if available
        if not self.headless and hasattr(self, 'console_output'):
            self.console_output.config(state=tk.NORMAL)
            self.console_output.insert(tk.END, formatted_message + "\n")
            self.console_output.see(tk.END)
            self.console_output.config(state=tk.DISABLED)
        
        # Print to stdout for headless mode
        print(formatted_message)
    
    def update_ui_state(self):
        """Update UI button states"""
        if self.headless or not GUI_AVAILABLE:
            return
            
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
    
    # Web server and API methods (same as original but with headless support)
    def start_web_server(self):
        """Start the web server for remote access"""
        if self.web_server_running:
            return
        
        try:
            self.app = Flask(__name__)
            self.app.secret_key = os.urandom(24)
            self.socketio = SocketIO(self.app, cors_allowed_origins="*")
            
            self.setup_routes()
            self.setup_socketio_events()
            
            # Start server in a separate thread
            self.web_server_thread = threading.Thread(
                target=self.run_web_server, 
                daemon=True
            )
            self.web_server_thread.start()
            
            self.web_server_running = True
            print(f"Web server started on http://0.0.0.0:{self.web_port}")
            self.log_message(f"Web server started on port {self.web_port}")
            
        except Exception as e:
            error_msg = f"Failed to start web server: {str(e)}"
            print(f"Error: {error_msg}")
            self.log_message(f"Error: {error_msg}")
    
    def run_web_server(self):
        """Run the web server"""
        try:
            self.socketio.run(
                self.app, 
                host='0.0.0.0', 
                port=self.web_port, 
                debug=False,
                allow_unsafe_werkzeug=True
            )
        except Exception as e:
            print(f"Web server error: {e}")
    
    def setup_routes(self):
        """Setup Flask routes"""
        @self.app.route('/')
        def index():
            return self.render_web_interface()
        
        @self.app.route('/api/status')
        def api_status():
            uptime = int(time.time() - self.server_start_time) if self.server_start_time else 0
            return jsonify({
                'running': self.server_running,
                'players': self.current_players,
                'max_players': self.max_players,
                'uptime': uptime,
                'player_list': list(self.player_list)
            })
        
        @self.app.route('/api/console')
        def api_console():
            return jsonify({
                'history': self.console_history[-100:],  # Last 100 messages
                'total': len(self.console_history)
            })
        
        @self.app.route('/api/command', methods=['POST'])
        def api_command():
            if not self.server_running:
                return jsonify({'success': False, 'message': 'Server is not running'})
            
            data = request.get_json()
            command = data.get('command', '').strip()
            
            if not command:
                return jsonify({'success': False, 'message': 'No command provided'})
            
            try:
                # Check if server process is still alive
                if not self.server_process or self.server_process.poll() is not None:
                    return jsonify({'success': False, 'message': 'Server process is not responding'})
                
                # Send command to server
                self.server_process.stdin.write(command + "\n")
                self.server_process.stdin.flush()
                
                # Log the command execution
                self.log_message(f"Command executed: {command}")
                
                return jsonify({'success': True, 'message': 'Command executed'})
            except Exception as e:
                error_msg = f"Failed to execute command: {str(e)}"
                self.log_message(f"Error: {error_msg}")
                return jsonify({'success': False, 'message': error_msg})
        
        @self.app.route('/api/start', methods=['POST'])
        def api_start():
            self.start_server()
            return jsonify({'success': True, 'message': 'Server start initiated'})
        
        @self.app.route('/api/stop', methods=['POST'])
        def api_stop():
            self.stop_server()
            return jsonify({'success': True, 'message': 'Server stop initiated'})
        
        @self.app.route('/api/restart', methods=['POST'])
        def api_restart():
            self.restart_server()
            return jsonify({'success': True, 'message': 'Server restart initiated'})
    
    def setup_socketio_events(self):
        """Setup SocketIO events for real-time updates"""
        @self.socketio.on('connect')
        def handle_connect():
            print('Client connected to SocketIO')
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print('Client disconnected from SocketIO')
    
    def render_web_interface(self):
        """Render the web interface HTML"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Minecraft Server Wrapper - Ubuntu ARM64</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Ubuntu', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #2c3e50, #34495e);
            color: #ecf0f1;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(52, 73, 94, 0.9);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #3498db, #2ecc71);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header .subtitle {
            font-size: 1.1em;
            color: #bdc3c7;
            margin-bottom: 20px;
        }
        
        .status-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(44, 62, 80, 0.8);
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #e74c3c;
            animation: pulse 2s infinite;
        }
        
        .status-indicator.running {
            background: #27ae60;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            flex-wrap: wrap;
            justify-content: center;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
            min-width: 120px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
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
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .console-section {
            margin-bottom: 30px;
        }
        
        .section-title {
            font-size: 1.5em;
            margin-bottom: 15px;
            color: #3498db;
            border-bottom: 2px solid #3498db;
            padding-bottom: 5px;
        }
        
        .console {
            background: #1a1a1a;
            border: 2px solid #34495e;
            border-radius: 8px;
            padding: 15px;
            height: 400px;
            overflow-y: auto;
            font-family: 'Ubuntu Mono', 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.4;
            color: #00ff00;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .console::-webkit-scrollbar {
            width: 8px;
        }
        
        .console::-webkit-scrollbar-track {
            background: #2c3e50;
            border-radius: 4px;
        }
        
        .console::-webkit-scrollbar-thumb {
            background: #3498db;
            border-radius: 4px;
        }
        
        .command-input-section {
            margin-top: 20px;
        }
        
        .command-mode-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            justify-content: center;
        }
        
        .mode-button {
            padding: 8px 16px;
            border: 2px solid #3498db;
            background: transparent;
            color: #3498db;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
        }
        
        .mode-button.active {
            background: #3498db;
            color: white;
        }
        
        .mode-button:hover {
            background: #3498db;
            color: white;
        }
        
        .command-input-container {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .command-input {
            flex: 1;
            padding: 12px 15px;
            border: 2px solid #34495e;
            border-radius: 8px;
            background: #2c3e50;
            color: #ecf0f1;
            font-size: 16px;
            font-family: 'Ubuntu Mono', monospace;
        }
        
        .command-input:focus {
            outline: none;
            border-color: #3498db;
            box-shadow: 0 0 10px rgba(52, 152, 219, 0.3);
        }
        
        .send-btn {
            padding: 12px 20px;
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .send-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
        }
        
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            z-index: 1000;
            transform: translateX(400px);
            transition: transform 0.3s ease;
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
        
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #34495e;
            color: #7f8c8d;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .status-bar {
                flex-direction: column;
                text-align: center;
            }
            
            .controls {
                flex-direction: column;
                align-items: center;
            }
            
            .btn {
                width: 100%;
                max-width: 200px;
            }
            
            .command-input-container {
                flex-direction: column;
            }
            
            .command-input {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 Minecraft Server Wrapper</h1>
            <div class="subtitle">Ubuntu ARM64 Edition - Optimized for Termux</div>
        </div>
        
        <div class="status-bar">
            <div class="status-item">
                <div class="status-indicator" id="serverStatus"></div>
                <span id="statusText">Stopped</span>
            </div>
            <div class="status-item">
                <span>👥 Players: <span id="playerCount">0</span>/<span id="maxPlayers">20</span></span>
            </div>
            <div class="status-item">
                <span>⏱️ Uptime: <span id="uptime">00:00:00</span></span>
            </div>
        </div>
        
        <div class="controls">
            <button class="btn btn-start" id="startBtn" onclick="startServer()">▶️ Start</button>
            <button class="btn btn-stop" id="stopBtn" onclick="stopServer()" disabled>⏹️ Stop</button>
            <button class="btn btn-restart" id="restartBtn" onclick="restartServer()" disabled>🔄 Restart</button>
        </div>
        
        <div class="console-section">
            <h2 class="section-title">📋 Server Console</h2>
            <div class="console" id="console"></div>
            
            <div class="command-input-section">
                <div class="command-mode-buttons">
                    <button class="mode-button active" id="cmdModeBtn" onclick="setCommandMode(true)">CMD</button>
                    <button class="mode-button" id="chatModeBtn" onclick="setCommandMode(false)">Chat</button>
                </div>
                
                <div class="command-input-container">
                    <input type="text" class="command-input" id="commandInput" 
                           placeholder="Enter server command..." 
                           onkeypress="handleKeyPress(event)">
                    <button class="send-btn" onclick="sendCommand()">Send</button>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>🚀 Powered by Flask & SocketIO | 🐧 Running on Ubuntu ARM64</p>
        </div>
    </div>
    
    <script>
        let commandMode = true;
        let lastConsoleLength = 0;
        
        function setCommandMode(isCommand) {
            commandMode = isCommand;
            const cmdBtn = document.getElementById('cmdModeBtn');
            const chatBtn = document.getElementById('chatModeBtn');
            const input = document.getElementById('commandInput');
            
            if (isCommand) {
                cmdBtn.classList.add('active');
                chatBtn.classList.remove('active');
                input.placeholder = 'Enter server command...';
            } else {
                cmdBtn.classList.remove('active');
                chatBtn.classList.add('active');
                input.placeholder = 'Enter chat message...';
            }
        }
        
        function startServer() {
            fetch('/api/start', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showNotification('Server start initiated', 'success');
                    } else {
                        showNotification(data.message || 'Failed to start server', 'error');
                    }
                })
                .catch(error => {
                    showNotification('Error starting server', 'error');
                });
        }
        
        function stopServer() {
            fetch('/api/stop', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showNotification('Server stop initiated', 'success');
                    } else {
                        showNotification(data.message || 'Failed to stop server', 'error');
                    }
                })
                .catch(error => {
                    showNotification('Error stopping server', 'error');
                });
        }
        
        function restartServer() {
            fetch('/api/restart', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showNotification('Server restart initiated', 'success');
                    } else {
                        showNotification(data.message || 'Failed to restart server', 'error');
                    }
                })
                .catch(error => {
                    showNotification('Error restarting server', 'error');
                });
        }
        
        function sendCommand() {
            const input = document.getElementById('commandInput');
            const command = input.value.trim();
            
            if (!command) return;
            
            // Prepare the final command based on mode
            let finalCommand = command;
            if (!commandMode) {
                finalCommand = 'say ' + command;
            }
            
            fetch('/api/command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ command: finalCommand })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    input.value = '';
                } else {
                    showNotification(data.message || 'Failed to send command', 'error');
                }
            })
            .catch(error => {
                showNotification('Error sending command', 'error');
            });
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendCommand();
            }
        }
        
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    const statusIndicator = document.getElementById('serverStatus');
                    const statusText = document.getElementById('statusText');
                    const playerCount = document.getElementById('playerCount');
                    const maxPlayers = document.getElementById('maxPlayers');
                    const uptime = document.getElementById('uptime');
                    const startBtn = document.getElementById('startBtn');
                    const stopBtn = document.getElementById('stopBtn');
                    const restartBtn = document.getElementById('restartBtn');
                    
                    if (data.running) {
                        statusIndicator.classList.add('running');
                        statusText.textContent = 'Running';
                        startBtn.disabled = true;
                        stopBtn.disabled = false;
                        restartBtn.disabled = false;
                    } else {
                        statusIndicator.classList.remove('running');
                        statusText.textContent = 'Stopped';
                        startBtn.disabled = false;
                        stopBtn.disabled = true;
                        restartBtn.disabled = true;
                    }
                    
                    playerCount.textContent = data.players;
                    maxPlayers.textContent = data.max_players;
                    
                    // Format uptime
                    const hours = Math.floor(data.uptime / 3600);
                    const minutes = Math.floor((data.uptime % 3600) / 60);
                    const seconds = data.uptime % 60;
                    uptime.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                })
                .catch(error => {
                    console.error('Error updating status:', error);
                });
        }
        
        function updateConsole() {
            fetch('/api/console')
                .then(response => response.json())
                .then(data => {
                    const console = document.getElementById('console');
                    
                    // Only update if there are new messages
                    if (data.history.length > lastConsoleLength) {
                        // Get new messages
                        const newMessages = data.history.slice(lastConsoleLength);
                        
                        // Add new messages to console
                        newMessages.forEach(entry => {
                            const line = `[${entry.timestamp}] ${entry.message}\n`;
                            console.textContent += line;
                        });
                        
                        // Auto-scroll to bottom
                        console.scrollTop = console.scrollHeight;
                        
                        // Update last length
                        lastConsoleLength = data.history.length;
                    }
                })
                .catch(error => {
                    console.error('Error updating console:', error);
                });
        }
        
        function showNotification(message, type) {
            // Remove existing notifications
            const existing = document.querySelector('.notification');
            if (existing) {
                existing.remove();
            }
            
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            document.body.appendChild(notification);
            
            // Show notification
            setTimeout(() => {
                notification.classList.add('show');
            }, 100);
            
            // Hide notification after 3 seconds
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => {
                    notification.remove();
                }, 300);
            }, 3000);
        }
        
        // Initialize
        updateStatus();
        updateConsole();
        
        // Update every 2 seconds
        setInterval(updateStatus, 2000);
        setInterval(updateConsole, 1000);
    </script>
</body>
</html>
        '''
    
    # User management methods (simplified for headless operation)
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
        """Handle application closing"""
        print("Shutting down...")
        
        # Stop server if running
        if self.server_running:
            self.stop_server()
        
        # Save configuration and console history
        self.save_config()
        self.save_console_history()
        
        # Stop web server
        if self.web_server_running:
            print("Stopping web server...")
        
        if not self.headless and self.root:
            self.root.destroy()
        
        print("Shutdown complete")
        sys.exit(0)
    
    def run(self):
        """Run the application"""
        if self.headless:
            print(f"Minecraft Server Wrapper running in headless mode")
            print(f"Web interface available at: http://localhost:{self.web_port}")
            print("Press Ctrl+C to stop")
            
            try:
                # Keep the main thread alive
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.on_closing()
        else:
            # Run GUI
            self.root.mainloop()

def main():
    """Main function with command line argument support"""
    parser = argparse.ArgumentParser(description='Minecraft Server Wrapper for Ubuntu ARM64')
    parser.add_argument('--headless', action='store_true', 
                       help='Run in headless mode (web interface only)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Web interface port (default: 5000)')
    
    args = parser.parse_args()
    
    # Create and run the wrapper
    wrapper = MinecraftServerWrapper(headless=args.headless)
    
    # Set custom port if specified
    if args.port != 5000:
        wrapper.web_port = args.port
        wrapper.config["web_port"] = args.port
        wrapper.save_config()
    
    wrapper.run()

if __name__ == "__main__":
    main()