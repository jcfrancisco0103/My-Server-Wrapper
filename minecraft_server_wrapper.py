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
# Windows-specific imports (conditional)
try:
    import winreg
    WINDOWS_PLATFORM = True
except ImportError:
    WINDOWS_PLATFORM = False
    winreg = None
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from werkzeug.serving import make_server

class MinecraftServerWrapper:
    def __init__(self, root):
        self.root = root
        self.root.title("Cacasians Minecraft Server Wrapper")
        self.root.geometry("900x700")
        self.root.configure(bg="#1e3c72")  # Gradient-like background color
        self.root.resizable(True, True)
        self.root.minsize(800, 600)
        

        
        # Set default font to Segoe UI (matching web interface)
        self.default_font = ("Segoe UI", 10)
        self.title_font = ("Segoe UI", 18, "bold")
        self.button_font = ("Segoe UI", 10, "bold")
        self.label_font = ("Segoe UI", 10)
        self.console_font = ("Consolas", 10)
        
        # Server process
        self.server_process = None
        self.server_running = False
        self.server_start_time = None
        self.startup_enabled_var = tk.BooleanVar()
        
        # Performance monitoring
        self.tps_values = []
        self.cpu_values = []
        self.ram_values = []
        self.monitoring_active = False
        
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
        
        # Set remote access settings from config
        self.remote_access_enabled.set(self.config.get("remote_access_enabled", False))
        self.web_port = self.config.get("web_port", 5000)
        
        self.setup_ui()
        
        # Bind window close event to save configuration
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
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
            "remote_access_enabled": False,
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
                    # Limit history size
                    if len(self.console_history) > self.max_console_history:
                        self.console_history = self.console_history[-self.max_console_history:]
        except Exception as e:
            self.console_history = []
            print(f"Could not load console history: {e}")
    
    def save_console_history(self):
        """Save console history to file"""
        try:
            # Limit history size before saving
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
        
        # Limit history size
        if len(self.console_history) > self.max_console_history:
            self.console_history = self.console_history[-self.max_console_history:]
        
        # Save periodically (every 10 messages)
        if len(self.console_history) % 10 == 0:
            self.save_console_history()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame with gradient-like background
        main_frame = tk.Frame(self.root, bg="#1e3c72")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Title with improved styling
        title_label = tk.Label(main_frame, text="Cacasians Minecraft Server Wrapper", 
                              font=self.title_font, fg="#ecf0f1", bg="#1e3c72")
        title_label.pack(pady=(0, 25))
        
        # Server controls frame with modern styling
        controls_frame = tk.Frame(main_frame, bg="#34495e", relief=tk.GROOVE, bd=3)
        controls_frame.pack(fill=tk.X, pady=(0, 15))
        
        controls_title = tk.Label(controls_frame, text="Server Controls", 
                                 font=(self.label_font[0], 14, "bold"), fg="#ecf0f1", bg="#34495e")
        controls_title.pack(pady=8)
        
        # Buttons frame
        buttons_frame = tk.Frame(controls_frame, bg="#34495e")
        buttons_frame.pack(pady=15)
        
        # Modern styled buttons with better spacing
        self.start_button = tk.Button(buttons_frame, text="▶ Start Server", 
                                     command=self.start_server, bg="#27ae60", fg="white",
                                     font=self.button_font, width=14, height=2,
                                     relief=tk.FLAT, bd=0, cursor="hand2")
        self.start_button.pack(side=tk.LEFT, padx=8)
        
        self.stop_button = tk.Button(buttons_frame, text="⏹ Stop Server", 
                                    command=self.stop_server, bg="#e74c3c", fg="white",
                                    font=self.button_font, width=14, height=2, state=tk.DISABLED,
                                    relief=tk.FLAT, bd=0, cursor="hand2")
        self.stop_button.pack(side=tk.LEFT, padx=8)
        
        self.restart_button = tk.Button(buttons_frame, text="🔄 Restart Server", 
                                       command=self.restart_server, bg="#f39c12", fg="white",
                                       font=self.button_font, width=14, height=2, state=tk.DISABLED,
                                       relief=tk.FLAT, bd=0, cursor="hand2")
        self.restart_button.pack(side=tk.LEFT, padx=8)
        
        self.kill_button = tk.Button(buttons_frame, text="💀 Kill Server", 
                                    command=self.kill_server, bg="#8e44ad", fg="white",
                                    font=self.button_font, width=14, height=2, state=tk.DISABLED,
                                    relief=tk.FLAT, bd=0, cursor="hand2")
        self.kill_button.pack(side=tk.LEFT, padx=8)
        
        # Status with better styling
        self.status_label = tk.Label(controls_frame, text="Status: Stopped", 
                                    fg="#e74c3c", bg="#34495e", font=(self.button_font[0], 11, "bold"))
        self.status_label.pack(pady=8)
        
        # Configuration frame with modern styling
        config_frame = tk.Frame(main_frame, bg="#34495e", relief=tk.GROOVE, bd=3)
        config_frame.pack(fill=tk.X, pady=(0, 15))
        
        config_title = tk.Label(config_frame, text="Server Configuration", 
                               font=(self.label_font[0], 14, "bold"), fg="#ecf0f1", bg="#34495e")
        config_title.pack(pady=8)
        
        # Config grid with better spacing
        config_grid = tk.Frame(config_frame, bg="#34495e")
        config_grid.pack(padx=15, pady=15)
        
        # Server JAR with modern styling
        tk.Label(config_grid, text="Server JAR:", fg="#ecf0f1", bg="#34495e", font=self.label_font).grid(row=0, column=0, sticky="w", padx=8, pady=5)
        jar_frame = tk.Frame(config_grid, bg="#34495e")
        jar_frame.grid(row=0, column=1, sticky="ew", padx=8, pady=5)
        
        self.jar_entry = tk.Entry(jar_frame, width=45, font=self.default_font, 
                                 bg="#2c3e50", fg="#ecf0f1", insertbackground="#ecf0f1",
                                 relief=tk.FLAT, bd=5)
        self.jar_entry.pack(side=tk.LEFT, padx=(0, 8))
        self.jar_entry.insert(0, self.config.get("server_jar", ""))
        self.jar_entry.bind('<FocusOut>', self.auto_save_config)
        self.jar_entry.bind('<KeyRelease>', self.schedule_auto_save)
        
        browse_button = tk.Button(jar_frame, text="📁 Browse", command=self.browse_jar, 
                                 bg="#3498db", fg="white", font=self.default_font,
                                 relief=tk.FLAT, bd=0, cursor="hand2")
        browse_button.pack(side=tk.LEFT)
        
        # Memory settings with modern styling
        tk.Label(config_grid, text="Min Memory:", fg="#ecf0f1", bg="#34495e", font=self.label_font).grid(row=1, column=0, sticky="w", padx=8, pady=5)
        self.min_memory_entry = tk.Entry(config_grid, width=12, font=self.default_font,
                                        bg="#2c3e50", fg="#ecf0f1", insertbackground="#ecf0f1",
                                        relief=tk.FLAT, bd=5)
        self.min_memory_entry.grid(row=1, column=1, sticky="w", padx=8, pady=5)
        self.min_memory_entry.insert(0, self.config.get("memory_min", "1G"))
        self.min_memory_entry.bind('<FocusOut>', self.auto_save_config)
        self.min_memory_entry.bind('<KeyRelease>', self.schedule_auto_save)
        
        tk.Label(config_grid, text="Max Memory:", fg="#ecf0f1", bg="#34495e", font=self.label_font).grid(row=2, column=0, sticky="w", padx=8, pady=5)
        self.max_memory_entry = tk.Entry(config_grid, width=12, font=self.default_font,
                                        bg="#2c3e50", fg="#ecf0f1", insertbackground="#ecf0f1",
                                        relief=tk.FLAT, bd=5)
        self.max_memory_entry.grid(row=2, column=1, sticky="w", padx=8, pady=5)
        self.max_memory_entry.insert(0, self.config.get("memory_max", "2G"))
        self.max_memory_entry.bind('<FocusOut>', self.auto_save_config)
        self.max_memory_entry.bind('<KeyRelease>', self.schedule_auto_save)
        
        # Port with modern styling
        tk.Label(config_grid, text="Server Port:", fg="#ecf0f1", bg="#34495e", font=self.label_font).grid(row=3, column=0, sticky="w", padx=8, pady=5)
        self.port_entry = tk.Entry(config_grid, width=12, font=self.default_font,
                                  bg="#2c3e50", fg="#ecf0f1", insertbackground="#ecf0f1",
                                  relief=tk.FLAT, bd=5)
        self.port_entry.grid(row=3, column=1, sticky="w", padx=8, pady=5)
        self.port_entry.insert(0, self.config.get("server_port", "25565"))
        self.port_entry.bind('<FocusOut>', self.auto_save_config)
        self.port_entry.bind('<KeyRelease>', self.schedule_auto_save)
        
        # Aikar's Flags with modern styling
        self.aikars_flags_var = tk.BooleanVar()
        self.aikars_flags_var.set(self.config.get("use_aikars_flags", False))
        self.aikars_flags_var.trace('w', self.auto_save_config_trace)
        aikars_checkbox = tk.Checkbutton(config_grid, text="Use Aikar's Flags (Optimized JVM)", 
                                        variable=self.aikars_flags_var, fg="#ecf0f1", bg="#34495e",
                                        selectcolor="#2c3e50", activebackground="#34495e",
                                        activeforeground="#ecf0f1", font=self.label_font)
        aikars_checkbox.grid(row=4, column=0, columnspan=2, sticky="w", padx=8, pady=8)
        
        # Info button for Aikar's Flags with modern styling
        info_button = tk.Button(config_grid, text="ℹ️ Info", command=self.show_aikars_info,
                               bg="#3498db", fg="white", font=(self.default_font[0], 9), width=8,
                               relief=tk.FLAT, bd=0, cursor="hand2")
        info_button.grid(row=4, column=1, sticky="e", padx=8, pady=8)
        
        # Auto-start server with modern styling
        self.auto_start_var = tk.BooleanVar()
        self.auto_start_var.set(self.config.get("auto_start_server", False))
        self.auto_start_var.trace('w', self.auto_save_config_trace)
        auto_start_checkbox = tk.Checkbutton(config_grid, text="Auto-start server when app opens", 
                                           variable=self.auto_start_var, fg="#ecf0f1", bg="#34495e",
                                           selectcolor="#2c3e50", activebackground="#34495e",
                                           activeforeground="#ecf0f1", font=self.label_font)
        auto_start_checkbox.grid(row=5, column=0, columnspan=2, sticky="w", padx=8, pady=8)
        
        # Windows startup checkbox with modern styling
        startup_checkbox = tk.Checkbutton(config_grid, text="Start with Windows (Run at startup)", 
                                        variable=self.startup_enabled_var, fg="#ecf0f1", bg="#34495e",
                                        selectcolor="#2c3e50", activebackground="#34495e",
                                        activeforeground="#ecf0f1", font=self.label_font,
                                        command=self.toggle_windows_startup)
        startup_checkbox.grid(row=6, column=0, columnspan=2, sticky="w", padx=8, pady=8)
        
        # Remote access checkbox with modern styling
        remote_access_checkbox = tk.Checkbutton(config_grid, text="Enable Remote Access (Web Interface)", 
                                               variable=self.remote_access_enabled, fg="#ecf0f1", bg="#34495e",
                                               selectcolor="#2c3e50", activebackground="#34495e",
                                               activeforeground="#ecf0f1", font=self.label_font,
                                               command=self.toggle_remote_access)
        remote_access_checkbox.grid(row=7, column=0, columnspan=2, sticky="w", padx=8, pady=8)
        
        # Web port configuration with modern styling
        tk.Label(config_grid, text="Web Port:", fg="#ecf0f1", bg="#34495e", font=self.label_font).grid(row=8, column=0, sticky="w", padx=8, pady=8)
        self.web_port_entry = tk.Entry(config_grid, bg="#2c3e50", fg="#ecf0f1", font=self.default_font, width=12,
                                      insertbackground="#ecf0f1", relief=tk.FLAT, bd=5)
        self.web_port_entry.insert(0, str(self.config.get("web_port", 5000)))
        self.web_port_entry.grid(row=8, column=1, sticky="w", padx=8, pady=8)
        
        # Save config button with modern styling
        save_config_button = tk.Button(config_grid, text="💾 Save Config", command=self.save_config_ui,
                                      bg="#9b59b6", fg="white", font=self.button_font,
                                      relief=tk.FLAT, bd=0, cursor="hand2", height=2)
        save_config_button.grid(row=9, column=0, columnspan=2, pady=15)
        
        # Server properties management with modern styling
        properties_frame = tk.Frame(config_frame, bg="#34495e")
        properties_frame.pack(pady=15)
        
        properties_label = tk.Label(properties_frame, text="Server Properties Management:", 
                                   fg="#ecf0f1", bg="#34495e", font=(self.label_font[0], 11, "bold"))
        properties_label.pack(pady=(0, 8))
        
        properties_buttons_frame = tk.Frame(properties_frame, bg="#34495e")
        properties_buttons_frame.pack()
        
        self.open_properties_button = tk.Button(properties_buttons_frame, text="📄 Open server.properties", 
                                               command=self.open_server_properties, bg="#e67e22", fg="white",
                                               font=self.default_font, width=20,
                                               relief=tk.FLAT, bd=0, cursor="hand2")
        self.open_properties_button.pack(side=tk.LEFT, padx=8)
        
        self.edit_properties_button = tk.Button(properties_buttons_frame, text="✏️ Edit in Wrapper", 
                                               command=self.edit_server_properties, bg="#16a085", fg="white",
                                               font=self.default_font, width=17,
                                               relief=tk.FLAT, bd=0, cursor="hand2")
        self.edit_properties_button.pack(side=tk.LEFT, padx=8)
        
        self.reload_properties_button = tk.Button(properties_buttons_frame, text="🔄 Reload Properties", 
                                                 command=self.reload_server_properties, bg="#8e44ad", fg="white",
                                                 font=self.default_font, width=17,
                                                 relief=tk.FLAT, bd=0, cursor="hand2")
        self.reload_properties_button.pack(side=tk.LEFT, padx=8)
        
        # Console frame with modern styling
        console_frame = tk.Frame(main_frame, bg="#34495e", relief=tk.GROOVE, bd=2)
        console_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        console_title = tk.Label(console_frame, text="🖥️ Server Console", 
                                font=(self.title_font[0], 12, "bold"), fg="#ecf0f1", bg="#34495e")
        console_title.pack(pady=10)
        
        # Console output with modern styling
        self.console_output = scrolledtext.ScrolledText(console_frame, height=15, 
                                                       bg="#1e1e1e", fg="#00ff00", 
                                                       font=("Consolas", 10),
                                                       state=tk.DISABLED, wrap=tk.WORD,
                                                       relief=tk.FLAT, bd=5,
                                                       insertbackground="#00ff00")
        self.console_output.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        # Command input frame with modern styling
        command_frame = tk.Frame(console_frame, bg="#34495e")
        command_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Mode toggle button with modern styling
        self.mode_button = tk.Button(command_frame, text="CMD", command=self.toggle_input_mode,
                                    bg="#3498db", fg="white", font=self.button_font, width=6,
                                    relief=tk.FLAT, bd=0, cursor="hand2")
        self.mode_button.pack(side=tk.LEFT, padx=(0, 8))
        
        # Command input label with modern styling
        self.command_label = tk.Label(command_frame, text="Command:", 
                                     font=self.label_font, fg="#ecf0f1", bg="#34495e")
        self.command_label.pack(side=tk.LEFT, padx=(0, 8))
        
        # Command input field with modern styling
        self.command_entry = tk.Entry(command_frame, bg="#2c3e50", fg="#ecf0f1", 
                                     font=("Consolas", 10), insertbackground="#ecf0f1",
                                     state=tk.NORMAL, relief=tk.FLAT, bd=5)
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.command_entry.bind("<Return>", self.send_command)
        self.command_entry.bind("<Button-1>", self.focus_command_entry)
        self.command_entry.focus_set()
        
        # Send button with modern styling
        send_button = tk.Button(command_frame, text="📤 Send", command=self.send_command,
                               bg="#27ae60", fg="white", font=self.button_font,
                               relief=tk.FLAT, bd=0, cursor="hand2")
        send_button.pack(side=tk.RIGHT)
        
        # Performance monitoring frame
        self.setup_performance_monitor(main_frame)
        
        # Initial console message
        self.log_message("Cacasians initialized. Configure your server and click 'Start Server'.")
        
        # Check for auto-start after UI is fully loaded
        self.root.after(1000, self.check_auto_start)
        
        # Start performance monitoring
        self.start_performance_monitoring()
    
    def browse_jar(self):
        """Browse for server JAR file"""
        filename = filedialog.askopenfilename(
            title="Select Minecraft Server JAR",
            filetypes=[("JAR files", "*.jar"), ("All files", "*.*")]
        )
        if filename:
            self.jar_entry.delete(0, tk.END)
            self.jar_entry.insert(0, filename)
            # Auto-save when JAR is selected
            self.auto_save_config()
    
    def save_config_ui(self):
        """Save configuration from UI"""
        self.config["server_jar"] = self.jar_entry.get()
        self.config["memory_min"] = self.min_memory_entry.get()
        self.config["memory_max"] = self.max_memory_entry.get()
        self.config["server_port"] = self.port_entry.get()
        self.config["use_aikars_flags"] = self.aikars_flags_var.get()
        self.config["auto_start_server"] = self.auto_start_var.get()
        self.config["startup_enabled"] = self.startup_enabled_var.get()
        self.config["remote_access_enabled"] = self.remote_access_enabled.get()
        self.config["web_port"] = int(self.web_port_entry.get())
        
        self.save_config()
        self.log_message("Configuration saved successfully!")
    
    def log_message(self, message):
        """Add message to console with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # Add to console history
        self.add_to_console_history(message)
        
        # Enable text widget temporarily to insert text
        self.console_output.config(state=tk.NORMAL)
        self.console_output.insert(tk.END, formatted_message)
        self.console_output.see(tk.END)
        # Disable text widget to make it read-only
        self.console_output.config(state=tk.DISABLED)
        
        # Broadcast to web clients
        self.broadcast_console_output(formatted_message.strip())
    
    def start_server(self):
        """Start the Minecraft server"""
        if self.server_running:
            return
        
        jar_path = self.jar_entry.get().strip()
        if not jar_path or not os.path.exists(jar_path):
            messagebox.showerror("Error", "Please select a valid server JAR file!")
            return
        
        try:
            # Build command
            java_path = self.config.get("java_path", "java")
            min_mem = self.min_memory_entry.get()
            max_mem = self.max_memory_entry.get()
            use_aikars = self.config.get("use_aikars_flags", False)
            
            command = [java_path]
            
            # Add Aikar's Flags if enabled
            if use_aikars:
                aikars_flags = self.get_aikars_flags(min_mem, max_mem)
                command.extend(aikars_flags)
                self.log_message("Using Aikar's Flags for optimized performance")
            else:
                command.extend([f"-Xms{min_mem}", f"-Xmx{max_mem}"])
            
            # Add JAR and nogui
            command.extend(["-jar", jar_path, "nogui"])
            
            # Change to server directory
            server_dir = os.path.dirname(jar_path)
            if server_dir:
                os.chdir(server_dir)
            
            self.log_message(f"Starting server with command: {' '.join(command)}")
            
            # Start server process
            self.server_process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.server_running = True
            self.server_start_time = time.time()  # Track server start time
            self.update_ui_state()
            
            # Start output reader thread
            threading.Thread(target=self.read_server_output, daemon=True).start()
            
            # Enable performance monitoring
            self.monitoring_active = True
            
            self.log_message("Server started successfully!")
            
        except Exception as e:
            self.log_message(f"Failed to start server: {str(e)}")
            messagebox.showerror("Error", f"Failed to start server: {str(e)}")
    
    def stop_server(self):
        """Stop the Minecraft server"""
        if not self.server_running or not self.server_process:
            return
        
        try:
            # Send stop command
            self.server_process.stdin.write("stop\n")
            self.server_process.stdin.flush()
            
            # Wait for process to end
            self.server_process.wait(timeout=30)
            
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't stop gracefully
            self.server_process.kill()
            self.log_message("Server was forcefully terminated.")
        except Exception as e:
            self.log_message(f"Error stopping server: {str(e)}")
        
        self.server_running = False
        self.server_process = None
        self.server_start_time = None  # Reset start time
        self.monitoring_active = False
        self.update_ui_state()
        self.log_message("Server stopped.")
    
    def restart_server(self):
        """Restart the Minecraft server"""
        self.log_message("Restarting server...")
        self.stop_server()
        time.sleep(2)  # Wait a moment
        self.start_server()
    
    def kill_server(self):
        """Forcefully kill the Minecraft server process"""
        if not self.server_running or not self.server_process:
            self.log_message("No server process to kill.")
            return
        
        try:
            # Force kill the process
            self.server_process.kill()
            self.log_message("Server process forcefully terminated.")
            
            # Wait for process to end
            self.server_process.wait(timeout=5)
            
        except subprocess.TimeoutExpired:
            self.log_message("Server process killed but cleanup timed out.")
        except Exception as e:
            self.log_message(f"Error killing server: {str(e)}")
        
        self.server_running = False
        self.server_process = None
        self.server_start_time = None
        self.monitoring_active = False
        self.update_ui_state()
        self.log_message("Server killed successfully.")
    
    def send_command(self, event=None):
        """Send command to server or as chat message based on current mode"""
        command = self.command_entry.get().strip()
        if not command:
            return
            
        if not self.server_running or not self.server_process:
            self.log_message("Server is not running. Cannot send command.")
            return
            
        try:
            if self.command_mode:
                # Command mode - send directly to server
                self.log_message(f"[ADMIN COMMAND] {command}")
                self.server_process.stdin.write(f"{command}\n")
            else:
                # Chat mode - use 'say' command to broadcast
                self.log_message(f"[ADMIN CHAT] {command}")
                self.server_process.stdin.write(f"say [ADMIN] {command}\n")
                
            self.server_process.stdin.flush()
            self.command_entry.delete(0, tk.END)
            
        except Exception as e:
            self.log_message(f"Error sending command: {str(e)}")
    
    def send_command_from_entry(self, event=None):
        """Wrapper method for send_command to handle both button click and Enter key"""
        self.send_command(event)
    
    def focus_command_entry(self, event=None):
        """Ensure command entry has focus when clicked"""
        self.command_entry.focus_set()
        return "break"  # Prevent default behavior
    
    def toggle_input_mode(self):
        """Toggle between Command mode and Chat mode"""
        self.command_mode = not self.command_mode
        
        if self.command_mode:
            # Command mode
            self.mode_button.config(text="CMD", bg="#3498db")
            self.command_label.config(text="Command:")
            self.log_message("Switched to Command mode. Commands will be sent directly to server.")
        else:
            # Chat mode
            self.mode_button.config(text="CHAT", bg="#e67e22")
            self.command_label.config(text="Chat:")
            self.log_message("Switched to Chat mode. Messages will be broadcast as admin chat.")
        
        # Refocus the entry field
        self.command_entry.focus_set()
    
    def read_server_output(self):
        """Read server output in a separate thread"""
        try:
            while self.server_running and self.server_process:
                line = self.server_process.stdout.readline()
                if line:
                    # Parse TPS if monitoring is active
                    if self.monitoring_active:
                        self.parse_tps_from_output(line)
                    
                    # Schedule UI update in main thread
                    self.root.after(0, lambda: self.log_message(f"[SERVER] {line.strip()}"))
                elif self.server_process.poll() is not None:
                    break
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"Error reading server output: {str(e)}"))
        
        # Server process ended
        self.server_running = False
        self.server_process = None
        self.server_start_time = None  # Reset start time
        self.monitoring_active = False
        self.root.after(0, self.update_ui_state)
        self.root.after(0, lambda: self.log_message("Server process ended."))
    
    def update_ui_state(self):
        """Update UI based on server state"""
        if self.server_running:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.restart_button.config(state=tk.NORMAL)
            self.kill_button.config(state=tk.NORMAL)
            self.status_label.config(text="Status: Running", fg="#27ae60")
        else:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.restart_button.config(state=tk.DISABLED)
            self.kill_button.config(state=tk.DISABLED)
            self.status_label.config(text="Status: Stopped", fg="#e74c3c")
        
        # Emit status update to web clients
        if hasattr(self, 'socketio') and self.web_server_running:
            try:
                self.socketio.emit('status_update', {
                    'running': self.server_running,
                    'uptime': self.get_uptime() if self.server_running else 0
                })
            except:
                pass  # Silently handle errors
    
    def get_uptime(self):
        """Get server uptime in seconds"""
        if self.server_running and self.server_start_time:
            return int(time.time() - self.server_start_time)
        return 0
    
    def get_server_directory(self):
        """Get the directory where the server JAR is located"""
        jar_path = self.jar_entry.get().strip()
        if jar_path and os.path.exists(jar_path):
            return os.path.dirname(jar_path)
        return None
    
    def get_properties_path(self):
        """Get the path to server.properties file"""
        server_dir = self.get_server_directory()
        if server_dir:
            return os.path.join(server_dir, "server.properties")
        return None
    
    def open_server_properties(self):
        """Open server.properties file with default system editor"""
        properties_path = self.get_properties_path()
        
        if not properties_path:
            messagebox.showerror("Error", "Please select a server JAR file first!")
            return
        
        if not os.path.exists(properties_path):
            # Create a default server.properties file
            self.create_default_properties(properties_path)
        
        try:
            # Open with default system application
            if os.name == 'nt':  # Windows
                os.startfile(properties_path)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', properties_path])
            
            self.log_message(f"Opened server.properties in default editor: {properties_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open server.properties: {str(e)}")
            self.log_message(f"Failed to open server.properties: {str(e)}")
    
    def create_default_properties(self, properties_path):
        """Create a default server.properties file"""
        default_properties = """#Minecraft server properties
#Generated by Minecraft Server Wrapper
server-name=Minecraft Server
server-port=25565
gamemode=survival
difficulty=easy
allow-flight=false
allow-nether=true
allow-cheats=false
announce-player-achievements=true
enable-command-block=false
force-gamemode=false
generate-structures=true
hardcore=false
level-name=world
level-seed=
level-type=default
max-build-height=256
max-players=20
max-world-size=29999984
motd=A Minecraft Server
online-mode=true
op-permission-level=4
player-idle-timeout=0
pvp=true
snooper-enabled=true
spawn-animals=true
spawn-monsters=true
spawn-npcs=true
spawn-protection=16
view-distance=10
white-list=false
"""
        try:
            with open(properties_path, 'w') as f:
                f.write(default_properties)
            self.log_message("Created default server.properties file")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create server.properties: {str(e)}")
    
    def edit_server_properties(self):
        """Open server.properties editor window within the wrapper"""
        properties_path = self.get_properties_path()
        
        if not properties_path:
            messagebox.showerror("Error", "Please select a server JAR file first!")
            return
        
        if not os.path.exists(properties_path):
            self.create_default_properties(properties_path)
        
        # Create properties editor window
        self.properties_window = tk.Toplevel(self.root)
        self.properties_window.title("Server Properties Editor")
        self.properties_window.geometry("600x500")
        self.properties_window.configure(bg="#2c3e50")
        
        # Title
        title_label = tk.Label(self.properties_window, text="Server Properties Editor", 
                              font=("Arial", 14, "bold"), fg="#ecf0f1", bg="#2c3e50")
        title_label.pack(pady=10)
        
        # Text editor
        text_frame = tk.Frame(self.properties_window, bg="#2c3e50")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.properties_text = scrolledtext.ScrolledText(text_frame, height=20, 
                                                        bg="#1e1e1e", fg="#ecf0f1", 
                                                        font=("Consolas", 10))
        self.properties_text.pack(fill=tk.BOTH, expand=True)
        
        # Load current properties
        try:
            with open(properties_path, 'r') as f:
                content = f.read()
            self.properties_text.insert(tk.END, content)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load server.properties: {str(e)}")
            return
        
        # Buttons
        button_frame = tk.Frame(self.properties_window, bg="#2c3e50")
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        save_button = tk.Button(button_frame, text="Save Changes", 
                               command=lambda: self.save_properties(properties_path),
                               bg="#27ae60", fg="white", font=("Arial", 10, "bold"))
        save_button.pack(side=tk.LEFT, padx=5)
        
        cancel_button = tk.Button(button_frame, text="Cancel", 
                                 command=self.properties_window.destroy,
                                 bg="#e74c3c", fg="white", font=("Arial", 10, "bold"))
        cancel_button.pack(side=tk.LEFT, padx=5)
        
        reload_button = tk.Button(button_frame, text="Reload from File", 
                                 command=lambda: self.reload_properties_editor(properties_path),
                                 bg="#3498db", fg="white", font=("Arial", 10, "bold"))
        reload_button.pack(side=tk.RIGHT, padx=5)
    
    def save_properties(self, properties_path):
        """Save the edited properties to file"""
        try:
            content = self.properties_text.get(1.0, tk.END)
            with open(properties_path, 'w') as f:
                f.write(content)
            
            self.log_message("Server properties saved successfully!")
            messagebox.showinfo("Success", "Server properties saved successfully!")
            
            # Ask if user wants to reload server properties
            if self.server_running:
                if messagebox.askyesno("Reload Properties", 
                                     "Server is running. Do you want to reload properties?\n"
                                     "(This will send 'reload' command to the server)"):
                    self.send_server_command("reload")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save server.properties: {str(e)}")
            self.log_message(f"Failed to save server.properties: {str(e)}")
    
    def reload_properties_editor(self, properties_path):
        """Reload properties from file into the editor"""
        try:
            with open(properties_path, 'r') as f:
                content = f.read()
            
            self.properties_text.delete(1.0, tk.END)
            self.properties_text.insert(tk.END, content)
            self.log_message("Properties reloaded from file")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reload properties: {str(e)}")
    
    def reload_server_properties(self):
        """Send reload command to running server"""
        if not self.server_running:
            messagebox.showwarning("Warning", "Server is not running!")
            return
        
        self.send_server_command("reload")
        self.log_message("Sent reload command to server")
    
    def send_server_command(self, command):
        """Send a command to the server (helper method)"""
        if not self.server_running or not self.server_process:
            return False
        
        try:
            self.server_process.stdin.write(f"{command}\n")
            self.server_process.stdin.flush()
            return True
        except Exception as e:
            self.log_message(f"Failed to send command '{command}': {str(e)}")
            return False
    
    def get_aikars_flags(self, min_mem, max_mem):
        """Get Aikar's optimized JVM flags"""
        # Aikar's flags for optimal Minecraft server performance
        # These flags are designed to reduce lag and improve garbage collection
        flags = [
            f"-Xms{min_mem}",
            f"-Xmx{max_mem}",
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
        return flags
    
    def show_aikars_info(self):
        """Show information about Aikar's Flags"""
        info_text = """Aikar's Flags - Optimized JVM Arguments

What are Aikar's Flags?
Aikar's Flags are a set of carefully tuned JVM (Java Virtual Machine) arguments 
designed specifically for Minecraft servers to improve performance and reduce lag.

Benefits:
• Reduced garbage collection pauses
• Better memory management
• Improved server tick performance
• Reduced lag spikes
• Optimized for Minecraft's memory usage patterns

These flags use the G1 garbage collector with optimized settings that work well 
for most Minecraft servers, especially those with 2GB+ of RAM.

Recommended for:
• Servers with 2GB or more RAM
• Servers experiencing lag or memory issues
• Production servers with multiple players

Note: These flags are most effective with Java 8+ and work best with 
adequate RAM allocation (2GB minimum recommended).

Source: https://mcflags.emc.gs
Created by: Aikar (Empire Minecraft)"""
        
        # Create info window
        info_window = tk.Toplevel(self.root)
        info_window.title("Aikar's Flags Information")
        info_window.geometry("500x400")
        info_window.configure(bg="#2c3e50")
        
        # Title
        title_label = tk.Label(info_window, text="Aikar's Flags Information", 
                              font=("Arial", 14, "bold"), fg="#ecf0f1", bg="#2c3e50")
        title_label.pack(pady=10)
        
        # Text area
        text_frame = tk.Frame(info_window, bg="#2c3e50")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        info_text_widget = scrolledtext.ScrolledText(text_frame, height=20, 
                                                    bg="#1e1e1e", fg="#ecf0f1", 
                                                    font=("Arial", 10), wrap=tk.WORD)
        info_text_widget.pack(fill=tk.BOTH, expand=True)
        info_text_widget.insert(tk.END, info_text)
        info_text_widget.config(state=tk.DISABLED)  # Make read-only
        
        # Close button
        close_button = tk.Button(info_window, text="Close", 
                                command=info_window.destroy,
                                bg="#e74c3c", fg="white", font=("Arial", 10, "bold"))
        close_button.pack(pady=10)
    
    def auto_save_config(self, event=None):
        """Automatically save configuration when values change"""
        try:
            self.config["server_jar"] = self.jar_entry.get()
            self.config["memory_min"] = self.min_memory_entry.get()
            self.config["memory_max"] = self.max_memory_entry.get()
            self.config["server_port"] = self.port_entry.get()
            self.config["use_aikars_flags"] = self.aikars_flags_var.get()
            self.config["auto_start_server"] = self.auto_start_var.get()
            self.config["startup_enabled"] = self.startup_enabled_var.get()
            
            self.save_config()
        except Exception as e:
            # Silently handle errors to avoid disrupting user experience
            pass
    
    def auto_save_config_trace(self, *args):
        """Auto-save config when traced variables change (for checkboxes)"""
        self.auto_save_config()
    
    def schedule_auto_save(self, event=None):
        """Schedule auto-save after a short delay to avoid saving on every keystroke"""
        # Cancel previous scheduled save
        if hasattr(self, '_auto_save_job'):
            self.root.after_cancel(self._auto_save_job)
        
        # Schedule new save after 1 second of inactivity
        self._auto_save_job = self.root.after(1000, self.auto_save_config)
    
    def on_closing(self):
        """Handle application closing"""
        # Save configuration before closing
        self.auto_save_config()
        
        if self.server_running:
            if messagebox.askokcancel("Quit", "Server is running. Stop server and quit?"):
                self.stop_server()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def check_auto_start(self):
        """Check if auto-start is enabled and start server if configured"""
        if self.config.get("auto_start_server", False):
            jar_path = self.jar_entry.get().strip()
            if jar_path and os.path.exists(jar_path):
                self.log_message("Auto-start enabled - Starting server automatically...")
                self.start_server()
            else:
                self.log_message("Auto-start enabled but no valid server JAR configured. Please select a server JAR file.")
                messagebox.showwarning("Auto-start Warning", 
                                     "Auto-start is enabled but no valid server JAR is configured.\n"
                                     "Please select a server JAR file to enable auto-start functionality.")
    
    def setup_performance_monitor(self, parent):
        """Setup the performance monitoring UI with modern styling"""
        # Performance monitoring frame with modern styling
        perf_frame = tk.Frame(parent, bg="#34495e", relief=tk.GROOVE, bd=2)
        perf_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        perf_title = tk.Label(perf_frame, text="📊 Performance Monitor", 
                             font=(self.title_font[0], 12, "bold"), fg="#ecf0f1", bg="#34495e")
        perf_title.pack(pady=10)
        
        # Performance metrics frame with modern styling
        metrics_frame = tk.Frame(perf_frame, bg="#34495e")
        metrics_frame.pack(padx=15, pady=15)
        
        # TPS (Ticks Per Second) with modern styling
        tps_frame = tk.Frame(metrics_frame, bg="#2c3e50", relief=tk.FLAT, bd=5)
        tps_frame.pack(side=tk.LEFT, padx=8, pady=8, fill=tk.BOTH, expand=True)
        
        tk.Label(tps_frame, text="TPS", font=self.label_font, 
                fg="#ecf0f1", bg="#2c3e50").pack(pady=5)
        self.tps_label = tk.Label(tps_frame, text="--", font=(self.default_font[0], 16, "bold"), 
                                 fg="#27ae60", bg="#2c3e50")
        self.tps_label.pack(pady=5)
        tk.Label(tps_frame, text="(Target: 20)", font=(self.default_font[0], 8), 
                fg="#bdc3c7", bg="#2c3e50").pack(pady=(0, 5))
        
        # CPU Usage with modern styling
        cpu_frame = tk.Frame(metrics_frame, bg="#2c3e50", relief=tk.FLAT, bd=5)
        cpu_frame.pack(side=tk.LEFT, padx=8, pady=8, fill=tk.BOTH, expand=True)
        
        tk.Label(cpu_frame, text="CPU", font=self.label_font, 
                fg="#ecf0f1", bg="#2c3e50").pack(pady=5)
        self.cpu_label = tk.Label(cpu_frame, text="--", font=(self.default_font[0], 16, "bold"), 
                                 fg="#3498db", bg="#2c3e50")
        self.cpu_label.pack(pady=5)
        tk.Label(cpu_frame, text="(Server Process)", font=(self.default_font[0], 8), 
                fg="#bdc3c7", bg="#2c3e50").pack(pady=(0, 5))
        
        # RAM Usage with modern styling
        ram_frame = tk.Frame(metrics_frame, bg="#2c3e50", relief=tk.FLAT, bd=5)
        ram_frame.pack(side=tk.LEFT, padx=8, pady=8, fill=tk.BOTH, expand=True)
        
        tk.Label(ram_frame, text="RAM", font=self.label_font, 
                fg="#ecf0f1", bg="#2c3e50").pack(pady=5)
        self.ram_label = tk.Label(ram_frame, text="--", font=(self.default_font[0], 16, "bold"), 
                                 fg="#e67e22", bg="#2c3e50")
        self.ram_label.pack(pady=5)
        tk.Label(ram_frame, text="(Server Process)", font=(self.default_font[0], 8), 
                fg="#bdc3c7", bg="#2c3e50").pack(pady=(0, 5))
        
        # System RAM with modern styling
        sys_ram_frame = tk.Frame(metrics_frame, bg="#2c3e50", relief=tk.FLAT, bd=5)
        sys_ram_frame.pack(side=tk.LEFT, padx=8, pady=8, fill=tk.BOTH, expand=True)
        
        tk.Label(sys_ram_frame, text="System RAM", font=self.label_font, 
                fg="#ecf0f1", bg="#2c3e50").pack(pady=5)
        self.sys_ram_label = tk.Label(sys_ram_frame, text="--", font=(self.default_font[0], 16, "bold"), 
                                     fg="#9b59b6", bg="#2c3e50")
        self.sys_ram_label.pack(pady=5)
        tk.Label(sys_ram_frame, text="(Total Usage)", font=(self.default_font[0], 8), 
                fg="#bdc3c7", bg="#2c3e50").pack(pady=(0, 5))
    
    def start_performance_monitoring(self):
        """Start the performance monitoring loop"""
        self.update_performance_metrics()
    
    def update_performance_metrics(self):
        """Update performance metrics display"""
        try:
            # Update TPS from server output
            self.update_tps_display()
            
            # Update CPU and RAM if server is running
            if self.server_running and self.server_process:
                self.update_cpu_ram_metrics()
            else:
                self.cpu_label.config(text="--")
                self.ram_label.config(text="--")
            
            # Update system RAM
            self.update_system_ram()
            
        except Exception as e:
            # Silently handle errors to avoid disrupting the UI
            pass
        
        # Schedule next update
        self.root.after(2000, self.update_performance_metrics)  # Update every 2 seconds
    
    def update_tps_display(self):
        """Update TPS display based on recent values"""
        if self.tps_values:
            # Get average of recent TPS values
            recent_tps = self.tps_values[-5:]  # Last 5 values
            avg_tps = sum(recent_tps) / len(recent_tps)
            
            # Color code based on TPS
            if avg_tps >= 19.5:
                color = "#27ae60"  # Green
            elif avg_tps >= 18:
                color = "#f39c12"  # Orange
            else:
                color = "#e74c3c"  # Red
            
            self.tps_label.config(text=f"{avg_tps:.1f}", fg=color)
        else:
            if self.server_running:
                self.tps_label.config(text="Calculating...", fg="#bdc3c7")
            else:
                self.tps_label.config(text="--", fg="#bdc3c7")
    
    def update_cpu_ram_metrics(self):
        """Update CPU and RAM metrics for the server process"""
        try:
            if self.server_process and self.server_process.poll() is None:
                # Get process info
                process = psutil.Process(self.server_process.pid)
                
                # CPU usage (percentage)
                cpu_percent = process.cpu_percent()
                
                # RAM usage (in MB)
                memory_info = process.memory_info()
                ram_mb = memory_info.rss / 1024 / 1024
                
                # Update displays
                self.cpu_label.config(text=f"{cpu_percent:.1f}%")
                
                if ram_mb >= 1024:
                    self.ram_label.config(text=f"{ram_mb/1024:.1f}GB")
                else:
                    self.ram_label.config(text=f"{ram_mb:.0f}MB")
                
                # Store values for history
                self.cpu_values.append(cpu_percent)
                self.ram_values.append(ram_mb)
                
                # Keep only recent values (last 30 readings)
                if len(self.cpu_values) > 30:
                    self.cpu_values.pop(0)
                if len(self.ram_values) > 30:
                    self.ram_values.pop(0)
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
            self.cpu_label.config(text="--")
            self.ram_label.config(text="--")
    
    def update_system_ram(self):
        """Update system RAM usage"""
        try:
            # Get system memory info
            memory = psutil.virtual_memory()
            used_gb = memory.used / 1024 / 1024 / 1024
            total_gb = memory.total / 1024 / 1024 / 1024
            percent = memory.percent
            
            # Color code based on usage
            if percent < 70:
                color = "#27ae60"  # Green
            elif percent < 85:
                color = "#f39c12"  # Orange
            else:
                color = "#e74c3c"  # Red
            
            self.sys_ram_label.config(text=f"{used_gb:.1f}GB\n({percent:.0f}%)", fg=color)
            
        except Exception:
            self.sys_ram_label.config(text="--")
    
    def parse_tps_from_output(self, line):
        """Parse TPS information from server output"""
        # Look for TPS in server output (common patterns)
        tps_patterns = [
            r"TPS from last 1m, 5m, 15m: ([0-9.]+)",  # Paper/Spigot
            r"Current TPS = ([0-9.]+)",  # Some plugins
            r"TPS: ([0-9.]+)",  # Generic TPS
            r"\*\s*([0-9.]+)\s*TPS",  # Some TPS plugins
        ]
        
        for pattern in tps_patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    tps = float(match.group(1))
                    if 0 <= tps <= 20:  # Valid TPS range
                        self.tps_values.append(tps)
                        # Keep only recent values
                        if len(self.tps_values) > 20:
                            self.tps_values.pop(0)
                        return tps
                except ValueError:
                    pass
        return None
    
    def toggle_windows_startup(self):
        """Toggle Windows startup registry entry"""
        if not WINDOWS_PLATFORM:
            self.log_message("Windows startup feature is only available on Windows systems.")
            self.startup_enabled_var.set(False)
            return
            
        try:
            if self.startup_enabled_var.get():
                self.add_to_startup()
                self.log_message("Added to Windows startup successfully!")
            else:
                self.remove_from_startup()
                self.log_message("Removed from Windows startup successfully!")
            
            # Auto-save the configuration
            self.auto_save_config()
            
        except Exception as e:
            self.log_message(f"Error managing Windows startup: {str(e)}")
            # Revert the checkbox state on error
            self.startup_enabled_var.set(not self.startup_enabled_var.get())
    
    def add_to_startup(self):
        """Add application to Windows startup"""
        if not WINDOWS_PLATFORM:
            raise Exception("Windows startup feature is only available on Windows systems.")
            
        try:
            # Get the path to the current script
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                app_path = sys.executable
            else:
                # Running as Python script
                app_path = f'python "{os.path.abspath(__file__)}"'
            
            # Open the registry key for startup programs
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                r"Software\Microsoft\Windows\CurrentVersion\Run", 
                                0, winreg.KEY_SET_VALUE)
            
            # Set the registry value
            winreg.SetValueEx(key, "MinecraftServerWrapper", 0, winreg.REG_SZ, app_path)
            winreg.CloseKey(key)
            
        except Exception as e:
            raise Exception(f"Failed to add to startup: {str(e)}")
    
    def remove_from_startup(self):
        """Remove application from Windows startup"""
        if not WINDOWS_PLATFORM:
            raise Exception("Windows startup feature is only available on Windows systems.")
            
        try:
            # Open the registry key for startup programs
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                r"Software\Microsoft\Windows\CurrentVersion\Run", 
                                0, winreg.KEY_SET_VALUE)
            
            # Delete the registry value
            try:
                winreg.DeleteValue(key, "MinecraftServerWrapper")
            except FileNotFoundError:
                # Value doesn't exist, which is fine
                pass
            
            winreg.CloseKey(key)
            
        except Exception as e:
            raise Exception(f"Failed to remove from startup: {str(e)}")
    
    def check_startup_status(self):
        """Check if application is currently in Windows startup"""
        if not WINDOWS_PLATFORM:
            return False
            
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                r"Software\Microsoft\Windows\CurrentVersion\Run", 
                                0, winreg.KEY_READ)
            
            try:
                value, _ = winreg.QueryValueEx(key, "MinecraftServerWrapper")
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
                
        except Exception:
            return False
    
    def toggle_remote_access(self):
        """Toggle remote access web server"""
        try:
            if self.remote_access_enabled.get():
                self.start_web_server()
                self.log_message("Remote access enabled! Web interface starting...")
            else:
                self.stop_web_server()
                self.log_message("Remote access disabled. Web interface stopped.")
            
            # Auto-save the configuration
            self.auto_save_config()
            
        except Exception as e:
            self.log_message(f"Error managing remote access: {str(e)}")
            # Revert the checkbox state on error
            self.remote_access_enabled.set(not self.remote_access_enabled.get())
    
    def start_web_server(self):
        """Start the Flask web server for remote access"""
        if self.web_server_running:
            return
        
        try:
            from flask import Flask, render_template_string, request, jsonify
            from flask_socketio import SocketIO, emit
            
            # Create Flask app
            self.web_server = Flask(__name__)
            self.web_server.config['SECRET_KEY'] = 'minecraft_server_wrapper_secret'
            self.socketio = SocketIO(self.web_server, cors_allowed_origins="*")
            
            # Get port from config
            port = int(self.web_port_entry.get())
            
            # HTML template for the web interface
            html_template = '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Cacasians - Remote Server Control</title>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
                <style>
                    * {
                        box-sizing: border-box;
                        margin: 0;
                        padding: 0;
                    }
                    
                    body { 
                        font-family: 'Segoe UI', 'Microsoft Sans Serif', Arial, sans-serif; 
                        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                        color: #ecf0f1; 
                        margin: 0; 
                        padding: 20px;
                        min-height: 100vh;
                        animation: fadeIn 0.8s ease-out;
                    }
                    
                    @keyframes fadeIn {
                        from { opacity: 0; transform: translateY(20px); }
                        to { opacity: 1; transform: translateY(0); }
                    }
                    
                    @keyframes slideIn {
                        from { transform: translateX(-20px); opacity: 0; }
                        to { transform: translateX(0); opacity: 1; }
                    }
                    
                    @keyframes pulse {
                        0% { transform: scale(1); }
                        50% { transform: scale(1.05); }
                        100% { transform: scale(1); }
                    }
                    
                    @keyframes glow {
                        0% { box-shadow: 0 0 5px rgba(52, 152, 219, 0.5); }
                        50% { box-shadow: 0 0 20px rgba(52, 152, 219, 0.8); }
                        100% { box-shadow: 0 0 5px rgba(52, 152, 219, 0.5); }
                    }
                    
                    .container { 
                        max-width: 1400px; 
                        margin: 0 auto; 
                        animation: slideIn 0.6s ease-out;
                    }
                    
                    .header { 
                        text-align: center; 
                        margin-bottom: 30px; 
                        background: rgba(255, 255, 255, 0.1);
                        backdrop-filter: blur(10px);
                        border-radius: 15px;
                        padding: 20px;
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        transition: all 0.3s ease;
                    }
                    
                    .header:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                    }
                    
                    .header h1 {
                        font-size: 2.5em;
                        margin-bottom: 15px;
                        background: linear-gradient(45deg, #3498db, #e74c3c);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        background-clip: text;
                        animation: pulse 2s infinite;
                    }
                    
                    .nav { 
                        display: flex; 
                        gap: 15px; 
                        margin-bottom: 20px; 
                        justify-content: center; 
                    }
                    
                    .nav-btn { 
                        padding: 12px 25px; 
                        background: rgba(52, 73, 94, 0.8);
                        color: #ecf0f1; 
                        text-decoration: none; 
                        border-radius: 25px; 
                        font-family: 'Segoe UI', Arial, sans-serif;
                        transition: all 0.3s ease;
                        border: 2px solid transparent;
                        position: relative;
                        overflow: hidden;
                    }
                    
                    .nav-btn::before {
                        content: '';
                        position: absolute;
                        top: 0;
                        left: -100%;
                        width: 100%;
                        height: 100%;
                        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
                        transition: left 0.5s;
                    }
                    
                    .nav-btn:hover::before {
                        left: 100%;
                    }
                    
                    .nav-btn:hover {
                        transform: translateY(-3px);
                        box-shadow: 0 8px 25px rgba(52, 152, 219, 0.4);
                        border-color: #3498db;
                    }
                    
                    .nav-btn.active { 
                        background: linear-gradient(45deg, #3498db, #2980b9);
                        animation: glow 2s infinite;
                    }
                    
                    .console { 
                        background: rgba(30, 30, 30, 0.95);
                        color: #00ff00; 
                        padding: 20px; 
                        height: 400px; 
                        overflow-y: scroll; 
                        font-family: 'Consolas', 'Courier New', monospace; 
                        font-size: 14px;
                        line-height: 1.4;
                        border: 2px solid rgba(52, 73, 94, 0.5);
                        border-radius: 15px;
                        backdrop-filter: blur(10px);
                        transition: all 0.3s ease;
                        box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.5);
                        white-space: pre-wrap;
                        word-wrap: break-word;
                    }
                    
                    .console:hover {
                        border-color: #3498db;
                        box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.5), 0 0 20px rgba(52, 152, 219, 0.3);
                    }
                    
                    .input-section { 
                        margin-top: 20px; 
                        display: flex; 
                        gap: 15px;
                        animation: slideIn 0.8s ease-out;
                    }
                    
                    .mode-btn { 
                        padding: 12px 25px; 
                        background: linear-gradient(45deg, #3498db, #2980b9);
                        color: white; 
                        border: none; 
                        cursor: pointer; 
                        font-family: 'Segoe UI', Arial, sans-serif;
                        border-radius: 25px;
                        transition: all 0.3s ease;
                        font-weight: bold;
                        position: relative;
                        overflow: hidden;
                    }
                    
                    .mode-btn:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 8px 25px rgba(52, 152, 219, 0.4);
                    }
                    
                    .mode-btn.chat { 
                        background: linear-gradient(45deg, #e67e22, #d35400);
                    }
                    
                    .mode-btn.chat:hover {
                        box-shadow: 0 8px 25px rgba(230, 126, 34, 0.4);
                    }
                    
                    input[type="text"] { 
                        flex: 1; 
                        padding: 12px 20px; 
                        background: rgba(52, 73, 94, 0.8);
                        color: #ecf0f1; 
                        border: 2px solid transparent;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        border-radius: 25px;
                        transition: all 0.3s ease;
                        backdrop-filter: blur(10px);
                    }
                    
                    input[type="text"]:focus {
                        outline: none;
                        border-color: #3498db;
                        box-shadow: 0 0 20px rgba(52, 152, 219, 0.3);
                        transform: scale(1.02);
                    }
                    
                    .send-btn { 
                        padding: 12px 25px; 
                        background: linear-gradient(45deg, #27ae60, #229954);
                        color: white; 
                        border: none; 
                        cursor: pointer; 
                        font-family: 'Segoe UI', Arial, sans-serif;
                        border-radius: 25px;
                        transition: all 0.3s ease;
                        font-weight: bold;
                    }
                    
                    .send-btn:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 8px 25px rgba(39, 174, 96, 0.4);
                    }
                    
                    .controls { 
                        display: flex; 
                        gap: 15px; 
                        margin-bottom: 20px;
                        justify-content: center;
                        animation: slideIn 0.6s ease-out;
                    }
                    
                    .control-btn { 
                        padding: 12px 25px; 
                        background: linear-gradient(45deg, #9b59b6, #8e44ad);
                        color: white; 
                        border: none; 
                        cursor: pointer; 
                        font-family: 'Segoe UI', Arial, sans-serif;
                        border-radius: 25px;
                        transition: all 0.3s ease;
                        font-weight: bold;
                        position: relative;
                        overflow: hidden;
                    }
                    
                    .control-btn:hover {
                        transform: translateY(-3px);
                        box-shadow: 0 10px 30px rgba(155, 89, 182, 0.4);
                    }
                    
                    .control-btn:active {
                        transform: translateY(-1px);
                        animation: pulse 0.3s ease;
                    }
                    
                    .status { 
                        padding: 15px 25px; 
                        background: rgba(52, 73, 94, 0.8);
                        margin-bottom: 20px; 
                        border-radius: 15px;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        transition: all 0.3s ease;
                    }
                    
                    .status:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
                    }
                    
                    /* Server Monitor Styles */
                    .monitor-dashboard {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                        gap: 20px;
                        margin: 25px 0;
                        padding: 25px;
                        background: rgba(255, 255, 255, 0.05);
                        border-radius: 20px;
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        backdrop-filter: blur(15px);
                        animation: slideIn 0.8s ease-out;
                    }
                    
                    .monitor-card {
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 15px;
                        padding: 20px;
                        text-align: center;
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        transition: all 0.4s ease;
                        position: relative;
                        overflow: hidden;
                        backdrop-filter: blur(10px);
                    }
                    
                    .monitor-card::before {
                        content: '';
                        position: absolute;
                        top: 0;
                        left: -100%;
                        width: 100%;
                        height: 100%;
                        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
                        transition: left 0.6s;
                    }
                    
                    .monitor-card:hover::before {
                        left: 100%;
                    }
                    
                    .monitor-card:hover {
                        transform: translateY(-8px) scale(1.02);
                        border-color: #3498db;
                        box-shadow: 0 15px 40px rgba(52, 152, 219, 0.3);
                    }
                    
                    .monitor-title {
                        color: #bdc3c7;
                        font-size: 13px;
                        margin-bottom: 12px;
                        text-transform: uppercase;
                        font-weight: 600;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        letter-spacing: 1px;
                    }
                    
                    .monitor-value {
                        color: #ecf0f1;
                        font-size: 28px;
                        font-weight: bold;
                        margin-bottom: 8px;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        transition: all 0.3s ease;
                    }
                    
                    .monitor-unit {
                        color: #95a5a6;
                        font-size: 12px;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        font-weight: 500;
                    }
                    
                    .monitor-status-online {
                        color: #27ae60;
                        text-shadow: 0 0 10px rgba(39, 174, 96, 0.5);
                    }
                    
                    .monitor-status-offline {
                        color: #e74c3c;
                        text-shadow: 0 0 10px rgba(231, 76, 60, 0.5);
                    }
                    
                    .monitor-header {
                        grid-column: 1 / -1;
                        text-align: center;
                        margin-bottom: 15px;
                        color: #ecf0f1;
                        font-size: 22px;
                        font-weight: bold;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        background: linear-gradient(45deg, #3498db, #e74c3c);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        background-clip: text;
                    }
                    
                    /* Scrollbar Styling */
                    ::-webkit-scrollbar {
                        width: 8px;
                    }
                    
                    ::-webkit-scrollbar-track {
                        background: rgba(52, 73, 94, 0.3);
                        border-radius: 10px;
                    }
                    
                    ::-webkit-scrollbar-thumb {
                        background: linear-gradient(45deg, #3498db, #2980b9);
                        border-radius: 10px;
                    }
                    
                    ::-webkit-scrollbar-thumb:hover {
                        background: linear-gradient(45deg, #2980b9, #3498db);
                    }
                    
                    /* Loading Animation */
                    .loading {
                        animation: pulse 1.5s infinite;
                    }
                    
                    /* Responsive Design */
                    @media (max-width: 768px) {
                        .container {
                            padding: 10px;
                        }
                        
                        .header h1 {
                            font-size: 2em;
                        }
                        
                        .nav {
                            flex-direction: column;
                            align-items: center;
                        }
                        
                        .controls {
                            flex-direction: column;
                            align-items: center;
                        }
                        
                        .input-section {
                            flex-direction: column;
                        }
                        
                        .monitor-dashboard {
                            grid-template-columns: 1fr;
                        }
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎮 Cacasians - Remote Server Control</h1>
                        <div class="nav">
                            <a href="/" class="nav-btn active">Console</a>
                            <a href="/files" class="nav-btn">File Manager</a>
                        </div>
                        <div class="status">
                            <strong>Server Status:</strong> <span id="server-status">Checking...</span> |
                            <strong>Players Online:</strong> <span id="players-online">--</span>
                        </div>
                    </div>
                    
                    <div class="controls">
                        <button class="control-btn" id="start-btn" onclick="startServer()">🚀 Start Server</button>
                        <button class="control-btn" id="stop-btn" onclick="stopServer()">🛑 Stop Server</button>
                        <button class="control-btn" id="restart-btn" onclick="restartServer()">🔄 Restart Server</button>
                        <button class="control-btn" id="kill-btn" onclick="killServer()" style="background: linear-gradient(45deg, #8e44ad, #9b59b6);">💀 Kill Server</button>
                    </div>
                    
                    <!-- Server Monitor Dashboard -->
                    <div class="monitor-dashboard">
                        <div class="monitor-header">📊 Server Monitor Dashboard</div>
                        <div class="monitor-card">
                            <div class="monitor-title">Server Status</div>
                            <div class="monitor-value" id="monitor-status">Offline</div>
                            <div class="monitor-unit">Status</div>
                        </div>
                        <div class="monitor-card">
                            <div class="monitor-title">Players Online</div>
                            <div class="monitor-value" id="monitor-players">0</div>
                            <div class="monitor-unit">Players</div>
                        </div>
                        <div class="monitor-card">
                            <div class="monitor-title">CPU Usage</div>
                            <div class="monitor-value" id="monitor-cpu">0</div>
                            <div class="monitor-unit">%</div>
                        </div>
                        <div class="monitor-card">
                            <div class="monitor-title">Memory Usage</div>
                            <div class="monitor-value" id="monitor-memory">0</div>
                            <div class="monitor-unit">MB</div>
                        </div>
                        <div class="monitor-card">
                            <div class="monitor-title">Uptime</div>
                            <div class="monitor-value" id="monitor-uptime">00:00:00</div>
                            <div class="monitor-unit">H:M:S</div>
                        </div>
                        <div class="monitor-card">
                            <div class="monitor-title">TPS</div>
                            <div class="monitor-value" id="monitor-tps">20.0</div>
                            <div class="monitor-unit">Ticks/Sec</div>
                        </div>
                    </div>
                    
                    <div class="console" id="console"></div>
                    
                    <div class="input-section">
                        <button class="mode-btn" id="mode-btn" onclick="toggleMode()">CMD</button>
                        <input type="text" id="command-input" placeholder="Enter command..." onkeypress="handleKeyPress(event)">
                        <button class="send-btn" onclick="sendCommand()">📤 Send</button>
                        <button class="control-btn" onclick="clearConsole()" style="background: linear-gradient(45deg, #e74c3c, #c0392b); margin-left: 10px;">🗑️ Clear</button>
                    </div>
                </div>
                
                <script>
                    const socket = io();
                    let commandMode = true;
                    
                    // Console persistence
                    const CONSOLE_STORAGE_KEY = 'minecraft_console_history';
                    const MAX_CONSOLE_LINES = 1000; // Maximum lines to store
                    
                    // Load console history on page load
                    function loadConsoleHistory() {
                        // First, try to load from backend API
                        fetch('/api/console/history')
                            .then(response => response.json())
                            .then(data => {
                                if (data.success && data.history) {
                                    const consoleElement = document.getElementById('console');
                                    consoleElement.innerHTML = ''; // Clear existing content
                                    
                                    // Load backend history
                                    data.history.forEach(entry => {
                                        const timestamp = new Date(entry.timestamp).toLocaleTimeString();
                                        const formattedMessage = `<span style="color: #888;">[${timestamp}]</span> <span style="color: #00ff00;">${entry.message}</span>`;
                                        consoleElement.innerHTML += formattedMessage + '<br>';
                                    });
                                    
                                    consoleElement.scrollTop = consoleElement.scrollHeight;
                                }
                            })
                            .catch(error => {
                                console.log('Could not load backend console history:', error);
                                // Fallback to localStorage
                                try {
                                    const savedConsole = localStorage.getItem(CONSOLE_STORAGE_KEY);
                                    if (savedConsole) {
                                        const consoleElement = document.getElementById('console');
                                        consoleElement.innerHTML = savedConsole;
                                        consoleElement.scrollTop = consoleElement.scrollHeight;
                                    }
                                } catch (e) {
                                    console.log('Could not load localStorage console history:', e);
                                }
                            });
                    }
                    
                    // Save console history to localStorage
                    function saveConsoleHistory() {
                        try {
                            const consoleElement = document.getElementById('console');
                            let content = consoleElement.innerHTML;
                            
                            // Limit the number of lines stored
                            const lines = content.split('<br>');
                            if (lines.length > MAX_CONSOLE_LINES) {
                                content = lines.slice(-MAX_CONSOLE_LINES).join('<br>');
                                consoleElement.innerHTML = content;
                            }
                            
                            localStorage.setItem(CONSOLE_STORAGE_KEY, content);
                        } catch (e) {
                            console.log('Could not save console history:', e);
                        }
                    }
                    
                    // Add message to console with timestamp
                    function addConsoleMessage(message, type = 'normal') {
                        const consoleElement = document.getElementById('console');
                        const timestamp = new Date().toLocaleTimeString();
                        
                        let colorClass = '';
                        switch (type) {
                            case 'error':
                                colorClass = 'style="color: #ff6b6b;"';
                                break;
                            case 'warning':
                                colorClass = 'style="color: #ffa500;"';
                                break;
                            case 'info':
                                colorClass = 'style="color: #74b9ff;"';
                                break;
                            case 'success':
                                colorClass = 'style="color: #00d2d3;"';
                                break;
                            default:
                                colorClass = 'style="color: #00ff00;"';
                        }
                        
                        const formattedMessage = `<span style="color: #888;">[${timestamp}]</span> <span ${colorClass}>${message}</span>`;
                        consoleElement.innerHTML += formattedMessage + '<br>';
                        consoleElement.scrollTop = consoleElement.scrollHeight;
                        
                        // Save to localStorage
                        saveConsoleHistory();
                    }
                    
                    // Clear console function
                    function clearConsole() {
                        const consoleElement = document.getElementById('console');
                        consoleElement.innerHTML = '';
                        localStorage.removeItem(CONSOLE_STORAGE_KEY);
                        addConsoleMessage('Console cleared', 'info');
                    }
                    
                    socket.on('console_output', function(data) {
                        // Determine message type based on content
                        let messageType = 'normal';
                        const message = data.message.toLowerCase();
                        
                        if (message.includes('error') || message.includes('exception') || message.includes('failed')) {
                            messageType = 'error';
                        } else if (message.includes('warn')) {
                            messageType = 'warning';
                        } else if (message.includes('info') || message.includes('starting') || message.includes('loading')) {
                            messageType = 'info';
                        } else if (message.includes('done') || message.includes('complete') || message.includes('success')) {
                            messageType = 'success';
                        }
                        
                        addConsoleMessage(data.message, messageType);
                    });
                    
                    socket.on('status_update', function(data) {
                        // Update button states when server status changes
                        updateButtonStates(data.running);
                    });
                    
                    // Load console history when page loads
                    document.addEventListener('DOMContentLoaded', function() {
                        loadConsoleHistory();
                        addConsoleMessage('Console loaded - history preserved', 'info');
                    });
                    
                    socket.on('server_status', function(data) {
                        document.getElementById('server-status').textContent = data.running ? 'Running' : 'Stopped';
                        document.getElementById('players-online').textContent = data.players || '--';
                        
                        // Update button states based on server status
                        updateButtonStates(data.running);
                        
                        // Update monitor dashboard
                        updateMonitorDashboard(data);
                    });
                    
                    // Monitor dashboard update function with animations
                    function updateMonitorDashboard(data) {
                        const statusElement = document.getElementById('monitor-status');
                        const playersElement = document.getElementById('monitor-players');
                        const cpuElement = document.getElementById('monitor-cpu');
                        const memoryElement = document.getElementById('monitor-memory');
                        const uptimeElement = document.getElementById('monitor-uptime');
                        const tpsElement = document.getElementById('monitor-tps');
                        
                        // Add loading animation before update
                        [statusElement, playersElement, cpuElement, memoryElement, uptimeElement, tpsElement].forEach(el => {
                            el.classList.add('loading');
                            setTimeout(() => el.classList.remove('loading'), 300);
                        });
                        
                        // Update server status with color coding
                        setTimeout(() => {
                            if (data.running) {
                                statusElement.textContent = 'Online';
                                statusElement.className = 'monitor-value monitor-status-online';
                            } else {
                                statusElement.textContent = 'Offline';
                                statusElement.className = 'monitor-value monitor-status-offline';
                            }
                            
                            // Update players with animation
                            const currentPlayers = data.current_players || data.players || '0';
                            const maxPlayers = data.max_players || '20';
                            playersElement.textContent = `${currentPlayers}/${maxPlayers}`;
                            
                            // Update system metrics with real data or simulation
                            if (data.running) {
                                cpuElement.textContent = (data.cpu_usage || Math.random() * 30 + 10).toFixed(1);
                                memoryElement.textContent = (data.memory_usage || Math.random() * 500 + 200).toFixed(0);
                                tpsElement.textContent = (data.tps || Math.random() * 2 + 19).toFixed(1);
                                
                                // Update uptime
                                const uptime = data.uptime || 0;
                                const hours = Math.floor(uptime / 3600);
                                const minutes = Math.floor((uptime % 3600) / 60);
                                const seconds = uptime % 60;
                                uptimeElement.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                            } else {
                                cpuElement.textContent = '0';
                                memoryElement.textContent = '0';
                                tpsElement.textContent = '0.0';
                                uptimeElement.textContent = '00:00:00';
                            }
                        }, 150);
                    }
                    
                    // Auto-refresh monitor data every 5 seconds
                    setInterval(function() {
                        socket.emit('request_status');
                    }, 5000);
                    
                    function toggleMode() {
                        commandMode = !commandMode;
                        const btn = document.getElementById('mode-btn');
                        const input = document.getElementById('command-input');
                        
                        btn.style.transform = 'scale(0.95)';
                        setTimeout(() => btn.style.transform = 'scale(1)', 150);
                        
                        if (commandMode) {
                            btn.textContent = 'CMD';
                            btn.className = 'mode-btn';
                            input.placeholder = 'Enter command...';
                        } else {
                            btn.textContent = 'CHAT';
                            btn.className = 'mode-btn chat';
                            input.placeholder = 'Enter chat message...';
                        }
                    }
                    
                    function sendCommand() {
                        const input = document.getElementById('command-input');
                        const command = input.value.trim();
                        if (command) {
                            // Add send animation
                            const sendBtn = document.querySelector('.send-btn');
                            sendBtn.style.transform = 'scale(0.95)';
                            setTimeout(() => sendBtn.style.transform = 'scale(1)', 150);
                            
                            socket.emit('send_command', {command: command, mode: commandMode ? 'command' : 'chat'});
                            input.value = '';
                        }
                    }
                    
                    function handleKeyPress(event) {
                        if (event.key === 'Enter') {
                            sendCommand();
                        }
                    }
                    
                    function startServer() {
                        socket.emit('server_control', {action: 'start'});
                        animateButton(event.target);
                    }
                    
                    function stopServer() {
                        socket.emit('server_control', {action: 'stop'});
                        animateButton(event.target);
                    }
                    
                    function restartServer() {
                        socket.emit('server_control', {action: 'restart'});
                        animateButton(event.target);
                    }
                    
                    function killServer() {
                        if (confirm('Are you sure you want to forcefully kill the server? This may cause data loss.')) {
                            socket.emit('server_control', {action: 'kill'});
                            animateButton(event.target);
                        }
                    }
                    
                    function updateButtonStates(serverRunning) {
                        const startBtn = document.getElementById('start-btn');
                        const stopBtn = document.getElementById('stop-btn');
                        const restartBtn = document.getElementById('restart-btn');
                        const killBtn = document.getElementById('kill-btn');
                        
                        if (serverRunning) {
                            startBtn.disabled = true;
                            startBtn.style.opacity = '0.5';
                            startBtn.style.cursor = 'not-allowed';
                            
                            stopBtn.disabled = false;
                            stopBtn.style.opacity = '1';
                            stopBtn.style.cursor = 'pointer';
                            
                            restartBtn.disabled = false;
                            restartBtn.style.opacity = '1';
                            restartBtn.style.cursor = 'pointer';
                            
                            killBtn.disabled = false;
                            killBtn.style.opacity = '1';
                            killBtn.style.cursor = 'pointer';
                        } else {
                            startBtn.disabled = false;
                            startBtn.style.opacity = '1';
                            startBtn.style.cursor = 'pointer';
                            
                            stopBtn.disabled = true;
                            stopBtn.style.opacity = '0.5';
                            stopBtn.style.cursor = 'not-allowed';
                            
                            restartBtn.disabled = true;
                            restartBtn.style.opacity = '0.5';
                            restartBtn.style.cursor = 'not-allowed';
                            
                            killBtn.disabled = true;
                            killBtn.style.opacity = '0.5';
                            killBtn.style.cursor = 'not-allowed';
                        }
                    }
                    
                    function animateButton(button) {
                        button.style.transform = 'scale(0.95)';
                        setTimeout(() => button.style.transform = 'scale(1)', 150);
                    }
                    
                    // Request initial status
                    socket.emit('request_status');
                    
                    // Add smooth scroll behavior
                    document.documentElement.style.scrollBehavior = 'smooth';
                </script>
            </body>
            </html>
            '''
            
            # File manager template
            file_manager_template = '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Cacasians - File Manager</title>
                <style>
                    * {
                        box-sizing: border-box;
                        margin: 0;
                        padding: 0;
                    }
                    
                    body { 
                        font-family: 'Segoe UI', 'Microsoft Sans Serif', Arial, sans-serif; 
                        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                        color: #ecf0f1; 
                        margin: 0; 
                        padding: 20px;
                        min-height: 100vh;
                        animation: fadeIn 0.8s ease-out;
                    }
                    
                    @keyframes fadeIn {
                        from { opacity: 0; transform: translateY(20px); }
                        to { opacity: 1; transform: translateY(0); }
                    }
                    
                    @keyframes slideIn {
                        from { transform: translateX(-20px); opacity: 0; }
                        to { transform: translateX(0); opacity: 1; }
                    }
                    
                    @keyframes pulse {
                        0% { transform: scale(1); }
                        50% { transform: scale(1.05); }
                        100% { transform: scale(1); }
                    }
                    
                    @keyframes glow {
                        0% { box-shadow: 0 0 5px rgba(52, 152, 219, 0.5); }
                        50% { box-shadow: 0 0 20px rgba(52, 152, 219, 0.8); }
                        100% { box-shadow: 0 0 5px rgba(52, 152, 219, 0.5); }
                    }
                    
                    .container { 
                        max-width: 1400px; 
                        margin: 0 auto; 
                        animation: slideIn 0.6s ease-out;
                    }
                    
                    .header { 
                        text-align: center; 
                        margin-bottom: 30px; 
                        background: rgba(255, 255, 255, 0.1);
                        backdrop-filter: blur(10px);
                        border-radius: 15px;
                        padding: 20px;
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        transition: all 0.3s ease;
                    }
                    
                    .header:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                    }
                    
                    .header h1 {
                        font-size: 2.5em;
                        margin-bottom: 15px;
                        background: linear-gradient(45deg, #3498db, #e74c3c);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        background-clip: text;
                        animation: pulse 2s infinite;
                    }
                    
                    .nav { 
                        display: flex; 
                        gap: 15px; 
                        margin-bottom: 20px; 
                        justify-content: center; 
                    }
                    
                    .nav-btn { 
                        padding: 12px 25px; 
                        background: rgba(52, 73, 94, 0.8);
                        color: #ecf0f1; 
                        text-decoration: none; 
                        border-radius: 25px; 
                        font-family: 'Segoe UI', Arial, sans-serif;
                        transition: all 0.3s ease;
                        border: 2px solid transparent;
                        position: relative;
                        overflow: hidden;
                    }
                    
                    .nav-btn::before {
                        content: '';
                        position: absolute;
                        top: 0;
                        left: -100%;
                        width: 100%;
                        height: 100%;
                        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
                        transition: left 0.5s;
                    }
                    
                    .nav-btn:hover::before {
                        left: 100%;
                    }
                    
                    .nav-btn:hover {
                        transform: translateY(-3px);
                        box-shadow: 0 8px 25px rgba(52, 152, 219, 0.4);
                        border-color: #3498db;
                    }
                    
                    .nav-btn.active { 
                        background: linear-gradient(45deg, #3498db, #2980b9);
                        animation: glow 2s infinite;
                    }
                    
                    .file-browser { 
                        display: flex; 
                        gap: 20px; 
                        height: 600px; 
                        animation: slideIn 0.8s ease-out;
                    }
                    
                    .file-list { 
                        flex: 1; 
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 15px; 
                        overflow: hidden;
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        transition: all 0.3s ease;
                    }
                    
                    .file-list:hover {
                        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                    }
                    
                    .file-editor { 
                        flex: 1; 
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 15px; 
                        overflow: hidden; 
                        display: none;
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        transition: all 0.3s ease;
                    }
                    
                    .file-editor:hover {
                        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                    }
                    
                    .file-list-header { 
                        background: rgba(44, 62, 80, 0.8);
                        padding: 20px; 
                        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                        font-family: 'Segoe UI', Arial, sans-serif;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }
                    
                    .file-actions {
                        display: flex;
                        align-items: center;
                        gap: 15px;
                    }
                    
                    /* Checkbox Styles */
                    .checkbox-container {
                        display: flex;
                        align-items: center;
                        cursor: pointer;
                        font-size: 14px;
                        color: #ecf0f1;
                        user-select: none;
                    }
                    
                    .checkbox-container input[type="checkbox"] {
                        display: none;
                    }
                    
                    .checkmark {
                        width: 18px;
                        height: 18px;
                        background: rgba(52, 73, 94, 0.8);
                        border: 2px solid rgba(255, 255, 255, 0.3);
                        border-radius: 4px;
                        margin-right: 8px;
                        position: relative;
                        transition: all 0.3s ease;
                    }
                    
                    .checkbox-container input[type="checkbox"]:checked + .checkmark {
                        background: linear-gradient(45deg, #3498db, #2980b9);
                        border-color: #3498db;
                    }
                    
                    .checkbox-container input[type="checkbox"]:checked + .checkmark::after {
                        content: '✓';
                        position: absolute;
                        top: -2px;
                        left: 2px;
                        color: white;
                        font-size: 14px;
                        font-weight: bold;
                    }
                    
                    .file-checkbox {
                        margin-right: 10px;
                    }
                    
                    /* Button Variants */
                    .btn.delete {
                        background: linear-gradient(45deg, #e74c3c, #c0392b);
                    }
                    
                    .btn.delete:hover {
                        box-shadow: 0 8px 25px rgba(231, 76, 60, 0.4);
                    }
                    
                    .btn.rename {
                        background: linear-gradient(45deg, #f39c12, #e67e22);
                    }
                    
                    .btn.rename:hover {
                        box-shadow: 0 8px 25px rgba(243, 156, 18, 0.4);
                    }
                    
                    .btn:disabled {
                        background: rgba(127, 140, 141, 0.5);
                        cursor: not-allowed;
                        transform: none;
                        box-shadow: none;
                    }
                    
                    .btn:disabled:hover {
                        transform: none;
                        box-shadow: none;
                    }
                    
                    .breadcrumb { 
                        background: rgba(44, 62, 80, 0.6);
                        padding: 15px 20px; 
                        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                        font-size: 14px; 
                        font-family: 'Segoe UI', Arial, sans-serif;
                        backdrop-filter: blur(5px);
                    }
                    
                    .file-items { 
                        height: calc(100% - 120px); 
                        overflow-y: auto; 
                    }
                    
                    .file-item { 
                        padding: 15px 20px; 
                        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                        cursor: pointer; 
                        display: flex; 
                        align-items: center; 
                        font-family: 'Segoe UI', Arial, sans-serif;
                        transition: all 0.3s ease;
                        position: relative;
                        overflow: hidden;
                    }
                    
                    .file-item::before {
                        content: '';
                        position: absolute;
                        top: 0;
                        left: -100%;
                        width: 100%;
                        height: 100%;
                        background: linear-gradient(90deg, transparent, rgba(52, 152, 219, 0.1), transparent);
                        transition: left 0.5s;
                    }
                    
                    .file-item:hover::before {
                        left: 100%;
                    }
                    
                    .file-item:hover { 
                        background: rgba(52, 152, 219, 0.2);
                        transform: translateX(5px);
                        border-left: 3px solid #3498db;
                    }
                    
                    .file-icon { 
                        margin-right: 15px; 
                        width: 20px; 
                        font-size: 18px;
                    }
                    
                    .file-info { 
                        flex: 1; 
                        font-weight: 500;
                    }
                    
                    .file-size { 
                        font-size: 12px; 
                        color: #bdc3c7; 
                        margin-left: auto; 
                        background: rgba(52, 73, 94, 0.6);
                        padding: 4px 8px;
                        border-radius: 10px;
                    }
                    
                    .editor-header { 
                        background: rgba(44, 62, 80, 0.8);
                        padding: 20px; 
                        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                        display: flex; 
                        justify-content: space-between; 
                        align-items: center; 
                        font-family: 'Segoe UI', Arial, sans-serif;
                    }
                    
                    .editor-content { 
                        height: calc(100% - 80px); 
                    }
                    
                    .editor-textarea { 
                        width: 100%; 
                        height: 100%; 
                        background: rgba(30, 30, 30, 0.95);
                        color: #ecf0f1; 
                        border: none; 
                        padding: 20px; 
                        font-family: 'Consolas', 'Microsoft Sans Serif', monospace; 
                        resize: none;
                        font-size: 14px;
                        line-height: 1.5;
                    }
                    
                    .editor-textarea:focus {
                        outline: none;
                        box-shadow: inset 0 0 20px rgba(52, 152, 219, 0.2);
                    }
                    
                    .btn { 
                        padding: 10px 20px; 
                        background: linear-gradient(45deg, #3498db, #2980b9);
                        color: white; 
                        border: none; 
                        cursor: pointer; 
                        border-radius: 25px; 
                        margin-left: 10px; 
                        font-family: 'Segoe UI', Arial, sans-serif;
                        transition: all 0.3s ease;
                        font-weight: 500;
                        position: relative;
                        overflow: hidden;
                    }
                    
                    .btn:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 8px 25px rgba(52, 152, 219, 0.4);
                    }
                    
                    .btn:active {
                        transform: translateY(0);
                        animation: pulse 0.3s ease;
                    }
                    
                    /* File Upload Styles */
                    .upload-area {
                        border: 2px dashed rgba(255, 255, 255, 0.3);
                        border-radius: 15px;
                        padding: 30px;
                        margin: 25px 0;
                        text-align: center;
                        background: rgba(255, 255, 255, 0.05);
                        transition: all 0.4s ease;
                        cursor: pointer;
                        backdrop-filter: blur(10px);
                        position: relative;
                        overflow: hidden;
                    }
                    
                    .upload-area::before {
                        content: '';
                        position: absolute;
                        top: 0;
                        left: -100%;
                        width: 100%;
                        height: 100%;
                        background: linear-gradient(90deg, transparent, rgba(52, 152, 219, 0.1), transparent);
                        transition: left 0.6s;
                    }
                    
                    .upload-area:hover::before {
                        left: 100%;
                    }
                    
                    .upload-area.dragover {
                        border-color: #3498db;
                        background: rgba(52, 152, 219, 0.1);
                        transform: scale(1.02);
                        box-shadow: 0 10px 30px rgba(52, 152, 219, 0.3);
                    }
                    
                    .upload-area:hover {
                        border-color: rgba(255, 255, 255, 0.5);
                        background: rgba(255, 255, 255, 0.08);
                        transform: translateY(-2px);
                        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                    }
                    
                    .upload-text {
                        color: #ecf0f1;
                        font-size: 18px;
                        margin: 10px 0;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        font-weight: 500;
                    }
                    
                    .upload-input {
                        display: none;
                    }
                    
                    .upload-progress {
                        width: 100%;
                        height: 25px;
                        background: rgba(52, 73, 94, 0.6);
                        border-radius: 15px;
                        margin: 15px 0;
                        overflow: hidden;
                        display: none;
                        box-shadow: inset 0 2px 5px rgba(0, 0, 0, 0.3);
                    }
                    
                    .upload-progress-bar {
                        height: 100%;
                        background: linear-gradient(90deg, #3498db, #2ecc71);
                        width: 0%;
                        transition: width 0.3s ease;
                        border-radius: 15px;
                        box-shadow: 0 2px 10px rgba(52, 152, 219, 0.4);
                    }
                    
                    /* Server Monitor Styles */
                    .monitor-dashboard {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                        gap: 20px;
                        margin: 25px 0;
                        padding: 25px;
                        background: rgba(255, 255, 255, 0.05);
                        border-radius: 20px;
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        backdrop-filter: blur(15px);
                        animation: slideIn 0.8s ease-out;
                    }
                    
                    .monitor-card {
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 15px;
                        padding: 25px;
                        text-align: center;
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        transition: all 0.4s ease;
                        position: relative;
                        overflow: hidden;
                        backdrop-filter: blur(10px);
                    }
                    
                    .monitor-card::before {
                        content: '';
                        position: absolute;
                        top: 0;
                        left: -100%;
                        width: 100%;
                        height: 100%;
                        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
                        transition: left 0.6s;
                    }
                    
                    .monitor-card:hover::before {
                        left: 100%;
                    }
                    
                    .monitor-card:hover {
                        transform: translateY(-8px) scale(1.02);
                        border-color: #3498db;
                        box-shadow: 0 15px 40px rgba(52, 152, 219, 0.3);
                    }
                    
                    .monitor-title {
                        color: #bdc3c7;
                        font-size: 14px;
                        margin-bottom: 15px;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        font-weight: 600;
                    }
                    
                    .monitor-value {
                        color: #ecf0f1;
                        font-size: 28px;
                        font-weight: bold;
                        margin-bottom: 15px;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        transition: all 0.3s ease;
                    }
                    
                    .monitor-bar {
                        width: 100%;
                        height: 12px;
                        background: rgba(52, 73, 94, 0.6);
                        border-radius: 8px;
                        overflow: hidden;
                        margin-bottom: 10px;
                        box-shadow: inset 0 2px 5px rgba(0, 0, 0, 0.3);
                    }
                    
                    .monitor-bar-fill {
                        height: 100%;
                        border-radius: 8px;
                        transition: width 0.8s ease;
                        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
                    }
                    
                    .monitor-bar-fill.cpu { 
                        background: linear-gradient(90deg, #3498db, #e74c3c);
                        box-shadow: 0 2px 10px rgba(52, 152, 219, 0.4);
                    }
                    
                    .monitor-bar-fill.ram { 
                        background: linear-gradient(90deg, #2ecc71, #f39c12);
                        box-shadow: 0 2px 10px rgba(46, 204, 113, 0.4);
                    }
                    
                    .monitor-bar-fill.storage { 
                        background: linear-gradient(90deg, #9b59b6, #e67e22);
                        box-shadow: 0 2px 10px rgba(155, 89, 182, 0.4);
                    }
                    
                    .monitor-bar-fill.tps { 
                        background: linear-gradient(90deg, #1abc9c, #f1c40f);
                        box-shadow: 0 2px 10px rgba(26, 188, 156, 0.4);
                    }
                    
                    .monitor-status {
                        color: #bdc3c7;
                        font-size: 13px;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        font-weight: 500;
                    }
                    
                    .btn.save { 
                        background: linear-gradient(45deg, #27ae60, #229954);
                    }
                    
                    .btn.save:hover {
                        box-shadow: 0 8px 25px rgba(39, 174, 96, 0.4);
                    }
                    
                    .btn.close { 
                        background: linear-gradient(45deg, #e74c3c, #c0392b);
                    }
                    
                    .btn.close:hover {
                        box-shadow: 0 8px 25px rgba(231, 76, 60, 0.4);
                    }
                    
                    .btn.download { 
                        background: linear-gradient(45deg, #f39c12, #e67e22);
                    }
                    
                    .btn.download:hover {
                        box-shadow: 0 8px 25px rgba(243, 156, 18, 0.4);
                    }
                    
                    .btn.new { 
                        background: linear-gradient(45deg, #9b59b6, #8e44ad);
                    }
                    
                    .btn.new:hover {
                        box-shadow: 0 8px 25px rgba(155, 89, 182, 0.4);
                    }
                    
                    .modal { 
                        display: none; 
                        position: fixed; 
                        z-index: 1000; 
                        left: 0; 
                        top: 0; 
                        width: 100%; 
                        height: 100%; 
                        background-color: rgba(0,0,0,0.7);
                        backdrop-filter: blur(5px);
                        animation: fadeIn 0.3s ease;
                    }
                    
                    .modal-content { 
                        background: rgba(52, 73, 94, 0.95);
                        margin: 15% auto; 
                        padding: 30px; 
                        border-radius: 15px; 
                        width: 450px; 
                        font-family: 'Segoe UI', Arial, sans-serif;
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
                        animation: slideIn 0.4s ease;
                    }
                    
                    .modal-header { 
                        display: flex; 
                        justify-content: space-between; 
                        align-items: center; 
                        margin-bottom: 25px; 
                        font-family: 'Segoe UI', Arial, sans-serif;
                    }
                    
                    .modal-close { 
                        background: linear-gradient(45deg, #e74c3c, #c0392b);
                        color: white; 
                        border: none; 
                        padding: 8px 15px; 
                        cursor: pointer; 
                        border-radius: 20px; 
                        font-family: 'Segoe UI', Arial, sans-serif;
                        transition: all 0.3s ease;
                    }
                    
                    .modal-close:hover {
                        transform: scale(1.1);
                        box-shadow: 0 5px 15px rgba(231, 76, 60, 0.4);
                    }
                    
                    .form-group { 
                        margin-bottom: 20px; 
                    }
                    
                    .form-group label { 
                        display: block; 
                        margin-bottom: 8px; 
                        font-family: 'Segoe UI', Arial, sans-serif;
                        font-weight: 500;
                        color: #ecf0f1;
                    }
                    
                    .form-group input { 
                        width: 100%; 
                        padding: 12px 15px; 
                        background: rgba(44, 62, 80, 0.8);
                        color: #ecf0f1; 
                        border: 2px solid transparent;
                        border-radius: 25px; 
                        font-family: 'Segoe UI', Arial, sans-serif;
                        transition: all 0.3s ease;
                        backdrop-filter: blur(5px);
                    }
                    
                    .form-group input:focus {
                        outline: none;
                        border-color: #3498db;
                        box-shadow: 0 0 20px rgba(52, 152, 219, 0.3);
                        transform: scale(1.02);
                    }
                    
                    /* Scrollbar Styling */
                    ::-webkit-scrollbar {
                        width: 8px;
                    }
                    
                    ::-webkit-scrollbar-track {
                        background: rgba(52, 73, 94, 0.3);
                        border-radius: 10px;
                    }
                    
                    ::-webkit-scrollbar-thumb {
                        background: linear-gradient(45deg, #3498db, #2980b9);
                        border-radius: 10px;
                    }
                    
                    ::-webkit-scrollbar-thumb:hover {
                        background: linear-gradient(45deg, #2980b9, #3498db);
                    }
                    
                    /* Loading Animation */
                    .loading {
                        animation: pulse 1.5s infinite;
                    }
                    
                    /* Responsive Design */
                    @media (max-width: 768px) {
                        .container {
                            padding: 10px;
                        }
                        
                        .header h1 {
                            font-size: 2em;
                        }
                        
                        .nav {
                            flex-direction: column;
                            align-items: center;
                        }
                        
                        .file-browser {
                            flex-direction: column;
                            height: auto;
                        }
                        
                        .file-list, .file-editor {
                            height: 400px;
                        }
                        
                        .monitor-dashboard {
                            grid-template-columns: 1fr;
                        }
                        
                        .modal-content {
                            width: 90%;
                            margin: 10% auto;
                        }
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📁 Cacasians - File Manager</h1>
                        <div class="nav">
                            <a href="/" class="nav-btn">Console</a>
                            <a href="/files" class="nav-btn active">File Manager</a>
                        </div>
                    </div>
                    
                    <!-- Server Monitor Dashboard -->
                    <div class="monitor-dashboard" id="monitor-dashboard">
                        <div class="monitor-card">
                            <div class="monitor-title">🖥️ CPU Usage</div>
                            <div class="monitor-value" id="cpu-value">0%</div>
                            <div class="monitor-bar">
                                <div class="monitor-bar-fill cpu" id="cpu-bar" style="width: 0%"></div>
                            </div>
                            <div class="monitor-status" id="cpu-status">Monitoring...</div>
                        </div>
                        <div class="monitor-card">
                            <div class="monitor-title">🧠 RAM Usage</div>
                            <div class="monitor-value" id="ram-value">0%</div>
                            <div class="monitor-bar">
                                <div class="monitor-bar-fill ram" id="ram-bar" style="width: 0%"></div>
                            </div>
                            <div class="monitor-status" id="ram-status">Monitoring...</div>
                        </div>
                        <div class="monitor-card">
                            <div class="monitor-title">💾 Storage</div>
                            <div class="monitor-value" id="storage-value">0%</div>
                            <div class="monitor-bar">
                                <div class="monitor-bar-fill storage" id="storage-bar" style="width: 0%"></div>
                            </div>
                            <div class="monitor-status" id="storage-status">Monitoring...</div>
                        </div>
                        <div class="monitor-card">
                            <div class="monitor-title">⚡ Server TPS</div>
                            <div class="monitor-value" id="tps-value">20.0</div>
                            <div class="monitor-bar">
                                <div class="monitor-bar-fill tps" id="tps-bar" style="width: 100%"></div>
                            </div>
                            <div class="monitor-status" id="tps-status">Optimal</div>
                        </div>
                    </div>
                    
                    <!-- File Upload Area -->
                    <div class="upload-area" id="upload-area" onclick="document.getElementById('file-input').click()">
                        <div class="upload-text">
                            📁 Drag & Drop files here or click to browse
                        </div>
                        <div class="upload-text" style="font-size: 14px; color: #bdc3c7;">
                            Supports all file types
                        </div>
                        <input type="file" id="file-input" class="upload-input" multiple>
                        <div class="upload-progress" id="upload-progress">
                            <div class="upload-progress-bar" id="upload-progress-bar"></div>
                        </div>
                    </div>
                    
                    <div class="file-browser">
                        <div class="file-list" id="file-list">
                             <div class="file-list-header">
                                 <h3>📂 Server Files</h3>
                                 <div class="file-actions">
                                     <label class="checkbox-container">
                                         <input type="checkbox" id="select-all" onchange="toggleSelectAll()">
                                         <span class="checkmark"></span>
                                         Select All
                                     </label>
                                     <button class="btn new" onclick="showNewFileModal()">📄 New File</button>
                                     <button class="btn delete" id="delete-btn" onclick="deleteSelected()" disabled>🗑️ Delete</button>
                                     <button class="btn rename" id="rename-btn" onclick="renameSelected()" disabled>✏️ Rename</button>
                                 </div>
                             </div>
                            <div class="breadcrumb" id="breadcrumb">Loading...</div>
                            <div class="file-items" id="file-items">
                                Loading files...
                            </div>
                        </div>
                        
                        <div class="file-editor" id="file-editor">
                            <div class="editor-header">
                                <span id="editor-filename">No file selected</span>
                                <div>
                                    <button class="btn save" onclick="saveFile()">💾 Save</button>
                                    <button class="btn download" onclick="downloadFile()">⬇️ Download</button>
                                    <button class="btn close" onclick="closeEditor()">✖️ Close</button>
                                </div>
                            </div>
                            <div class="editor-content">
                                <textarea id="editor-textarea" class="editor-textarea" placeholder="Select a file to edit..."></textarea>
                            </div>
                     </div>
                     
                     <!-- New File Modal -->
                     <div id="newFileModal" class="modal">
                         <div class="modal-content">
                             <div class="modal-header">
                                 <h3>📄 Create New File</h3>
                                 <button class="modal-close" onclick="hideNewFileModal()">✖️</button>
                             </div>
                             <div class="form-group">
                                 <label for="newFileName">File Name:</label>
                                 <input type="text" id="newFileName" placeholder="example.txt" onkeypress="handleNewFileKeyPress(event)">
                             </div>
                             <div style="text-align: right;">
                                 <button class="btn" onclick="hideNewFileModal()">Cancel</button>
                                 <button class="btn save" onclick="createNewFile()">Create File</button>
                             </div>
                         </div>
                     </div>
                 </div>
                </div>
                
                <script>
                    let currentPath = '.';
                    let currentFile = null;
                    
                    function loadFiles(path = '.') {
                        currentPath = path;
                        fetch(`/api/files?path=${encodeURIComponent(path)}`)
                            .then(response => response.json())
                            .then(data => {
                                if (data.error) {
                                    alert('Error: ' + data.error);
                                    return;
                                }
                                
                                // Update breadcrumb
                                document.getElementById('breadcrumb').textContent = 'Path: ' + (data.current_path === '.' ? 'Root' : data.current_path);
                                
                                // Update file list
                                const fileItems = document.getElementById('file-items');
                                fileItems.innerHTML = '';
                                
                                // Add parent directory link if not in root
                                if (data.current_path !== '.') {
                                    const parentItem = document.createElement('div');
                                    parentItem.className = 'file-item';
                                    parentItem.innerHTML = '<span class="file-icon">📁</span><span class="file-info">.. (Parent Directory)</span>';
                                    parentItem.onclick = () => {
                                        const parentPath = data.current_path.split('/').slice(0, -1).join('/') || '.';
                                        loadFiles(parentPath);
                                    };
                                    fileItems.appendChild(parentItem);
                                }
                                
                                // Sort items: folders first, then files
                                const sortedItems = data.items.sort((a, b) => {
                                    // Folders first
                                    if (a.is_directory && !b.is_directory) return -1;
                                    if (!a.is_directory && b.is_directory) return 1;
                                    // Then alphabetically within each group
                                    return a.name.toLowerCase().localeCompare(b.name.toLowerCase());
                                });
                                
                                // Add files and directories
                                sortedItems.forEach(item => {
                                    const fileItem = document.createElement('div');
                                    fileItem.className = 'file-item';
                                    fileItem.dataset.path = item.path;
                                    fileItem.dataset.name = item.name;
                                    fileItem.dataset.isDirectory = item.is_directory;
                                    
                                    const icon = item.is_directory ? '📁' : '📄';
                                    const size = item.is_directory ? '' : formatFileSize(item.size);
                                    
                                    fileItem.innerHTML = `
                                        <label class="checkbox-container file-checkbox" onclick="event.stopPropagation()">
                                            <input type="checkbox" class="file-select" onchange="updateActionButtons()">
                                            <span class="checkmark"></span>
                                        </label>
                                        <span class="file-icon">${icon}</span>
                                        <span class="file-info">${item.name}</span>
                                        <span class="file-size">${size}</span>
                                    `;
                                    
                                    fileItem.onclick = (e) => {
                                        // Don't trigger if clicking on checkbox
                                        if (e.target.closest('.file-checkbox')) return;
                                        
                                        if (item.is_directory) {
                                            loadFiles(item.path);
                                        } else {
                                            openFile(item.path, item.name);
                                        }
                                    };
                                    
                                    fileItems.appendChild(fileItem);
                                });
                            })
                            .catch(error => {
                                console.error('Error loading files:', error);
                                alert('Error loading files: ' + error.message);
                            });
                    }
                    
                    function openFile(filepath, filename) {
                        currentFile = filepath;
                        document.getElementById('editor-filename').textContent = filename;
                        
                        fetch(`/api/file/${encodeURIComponent(filepath)}`)
                            .then(response => response.json())
                            .then(data => {
                                if (data.error) {
                                    alert('Error: ' + data.error);
                                    return;
                                }
                                
                                if (data.is_text) {
                                    document.getElementById('editor-textarea').value = data.content;
                                    document.getElementById('file-editor').style.display = 'block';
                                } else {
                                    alert('This is a binary file and cannot be edited in the web interface. You can download it instead.');
                                }
                            })
                            .catch(error => {
                                console.error('Error loading file:', error);
                                alert('Error loading file: ' + error.message);
                            });
                    }
                    
                    function saveFile() {
                        if (!currentFile) {
                            alert('No file is currently open');
                            return;
                        }
                        
                        const content = document.getElementById('editor-textarea').value;
                        
                        fetch(`/api/file/${encodeURIComponent(currentFile)}`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ content: content })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.error) {
                                alert('Error saving file: ' + data.error);
                            } else {
                                alert('File saved successfully!');
                            }
                        })
                        .catch(error => {
                            console.error('Error saving file:', error);
                            alert('Error saving file: ' + error.message);
                        });
                    }
                    
                    function downloadFile() {
                        if (!currentFile) {
                            alert('No file is currently open');
                            return;
                        }
                        
                        window.open(`/download/${encodeURIComponent(currentFile)}`, '_blank');
                    }
                    
                    function closeEditor() {
                        document.getElementById('file-editor').style.display = 'none';
                        currentFile = null;
                        document.getElementById('editor-filename').textContent = 'No file selected';
                        document.getElementById('editor-textarea').value = '';
                    }
                    
                    function formatFileSize(bytes) {
                         if (bytes === 0) return '0 B';
                         const k = 1024;
                         const sizes = ['B', 'KB', 'MB', 'GB'];
                         const i = Math.floor(Math.log(bytes) / Math.log(k));
                         return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
                     }
                     
                     function showNewFileModal() {
                         document.getElementById('newFileModal').style.display = 'block';
                         document.getElementById('newFileName').focus();
                     }
                     
                     function hideNewFileModal() {
                         document.getElementById('newFileModal').style.display = 'none';
                         document.getElementById('newFileName').value = '';
                     }
                     
                     function handleNewFileKeyPress(event) {
                         if (event.key === 'Enter') {
                             createNewFile();
                         }
                     }
                     
                     function createNewFile() {
                         const fileName = document.getElementById('newFileName').value.trim();
                         if (!fileName) {
                             alert('Please enter a file name');
                             return;
                         }
                         
                         // Construct the full path
                         const fullPath = currentPath === '.' ? fileName : currentPath + '/' + fileName;
                         
                         // Create empty file
                         fetch(`/api/file/${encodeURIComponent(fullPath)}`, {
                             method: 'POST',
                             headers: {
                                 'Content-Type': 'application/json',
                             },
                             body: JSON.stringify({ content: '' })
                         })
                         .then(response => response.json())
                         .then(data => {
                             if (data.error) {
                                 alert('Error creating file: ' + data.error);
                             } else {
                                 alert('File created successfully!');
                                 hideNewFileModal();
                                 loadFiles(currentPath); // Refresh file list
                                 // Automatically open the new file for editing
                                 setTimeout(() => openFile(fullPath, fileName), 500);
                             }
                         })
                         .catch(error => {
                             console.error('Error creating file:', error);
                             alert('Error creating file: ' + error.message);
                         });
                     }
                     
                     // Close modal when clicking outside of it
                     window.onclick = function(event) {
                         const modal = document.getElementById('newFileModal');
                         if (event.target === modal) {
                             hideNewFileModal();
                         }
                     }
                     
                     // Load files on page load
                     loadFiles();
                     
                     // File Upload Functionality
                     const uploadArea = document.getElementById('upload-area');
                     const fileInput = document.getElementById('file-input');
                     const uploadProgress = document.getElementById('upload-progress');
                     const uploadProgressBar = document.getElementById('upload-progress-bar');
                     
                     // Drag and drop events
                     uploadArea.addEventListener('dragover', (e) => {
                         e.preventDefault();
                         uploadArea.classList.add('dragover');
                     });
                     
                     uploadArea.addEventListener('dragleave', (e) => {
                         e.preventDefault();
                         uploadArea.classList.remove('dragover');
                     });
                     
                     uploadArea.addEventListener('drop', (e) => {
                         e.preventDefault();
                         uploadArea.classList.remove('dragover');
                         const files = e.dataTransfer.files;
                         uploadFiles(files);
                     });
                     
                     // File input change event
                     fileInput.addEventListener('change', (e) => {
                         uploadFiles(e.target.files);
                     });
                     
                     function uploadFiles(files) {
                         if (files.length === 0) return;
                         
                         uploadProgress.style.display = 'block';
                         uploadProgressBar.style.width = '0%';
                         
                         const formData = new FormData();
                         for (let file of files) {
                             formData.append('files', file);
                         }
                         formData.append('path', currentPath);
                         
                         const xhr = new XMLHttpRequest();
                         
                         xhr.upload.addEventListener('progress', (e) => {
                             if (e.lengthComputable) {
                                 const percentComplete = (e.loaded / e.total) * 100;
                                 uploadProgressBar.style.width = percentComplete + '%';
                             }
                         });
                         
                         xhr.addEventListener('load', () => {
                             uploadProgress.style.display = 'none';
                             if (xhr.status === 200) {
                                 const response = JSON.parse(xhr.responseText);
                                 if (response.error) {
                                     alert('Upload error: ' + response.error);
                                 } else {
                                     alert(`Successfully uploaded ${response.uploaded} file(s)!`);
                                     loadFiles(currentPath); // Refresh file list
                                 }
                             } else {
                                 alert('Upload failed: ' + xhr.statusText);
                             }
                             fileInput.value = ''; // Reset file input
                         });
                         
                         xhr.addEventListener('error', () => {
                             uploadProgress.style.display = 'none';
                             alert('Upload failed: Network error');
                             fileInput.value = '';
                         });
                         
                         xhr.open('POST', '/api/upload');
                         xhr.send(formData);
                     }
                     
                     // Server Monitoring
                     function updateServerMonitor() {
                         fetch('/api/monitor')
                             .then(response => response.json())
                             .then(data => {
                                 // Update CPU
                                 document.getElementById('cpu-value').textContent = data.cpu.toFixed(1) + '%';
                                 document.getElementById('cpu-bar').style.width = data.cpu + '%';
                                 document.getElementById('cpu-status').textContent = data.cpu > 80 ? 'High' : data.cpu > 50 ? 'Medium' : 'Low';
                                 
                                 // Update RAM
                                 document.getElementById('ram-value').textContent = data.ram.toFixed(1) + '%';
                                 document.getElementById('ram-bar').style.width = data.ram + '%';
                                 document.getElementById('ram-status').textContent = `${data.ram_used}GB / ${data.ram_total}GB`;
                                 
                                 // Update Storage
                                 document.getElementById('storage-value').textContent = data.storage.toFixed(1) + '%';
                                 document.getElementById('storage-bar').style.width = data.storage + '%';
                                 document.getElementById('storage-status').textContent = `${data.storage_used}GB / ${data.storage_total}GB`;
                                 
                                 // Update TPS
                                 document.getElementById('tps-value').textContent = data.tps.toFixed(1);
                                 const tpsPercent = (data.tps / 20) * 100;
                                 document.getElementById('tps-bar').style.width = Math.min(tpsPercent, 100) + '%';
                                 document.getElementById('tps-status').textContent = data.tps >= 19 ? 'Optimal' : data.tps >= 15 ? 'Good' : data.tps >= 10 ? 'Poor' : 'Critical';
                             })
                             .catch(error => {
                                 console.error('Error fetching monitor data:', error);
                             });
                     }
                     
                     // Update monitor every 2 seconds
                     setInterval(updateServerMonitor, 2000);
                     updateServerMonitor(); // Initial update
                     
                     // File Selection and Operations
                     function toggleSelectAll() {
                         const selectAllCheckbox = document.getElementById('select-all');
                         const fileCheckboxes = document.querySelectorAll('.file-select');
                         
                         fileCheckboxes.forEach(checkbox => {
                             checkbox.checked = selectAllCheckbox.checked;
                         });
                         
                         updateActionButtons();
                     }
                     
                     function updateActionButtons() {
                         const selectedFiles = getSelectedFiles();
                         const deleteBtn = document.getElementById('delete-btn');
                         const renameBtn = document.getElementById('rename-btn');
                         
                         deleteBtn.disabled = selectedFiles.length === 0;
                         renameBtn.disabled = selectedFiles.length !== 1; // Only allow rename for single file
                         
                         // Update select all checkbox state
                         const selectAllCheckbox = document.getElementById('select-all');
                         const fileCheckboxes = document.querySelectorAll('.file-select');
                         const checkedCount = document.querySelectorAll('.file-select:checked').length;
                         
                         if (checkedCount === 0) {
                             selectAllCheckbox.indeterminate = false;
                             selectAllCheckbox.checked = false;
                         } else if (checkedCount === fileCheckboxes.length) {
                             selectAllCheckbox.indeterminate = false;
                             selectAllCheckbox.checked = true;
                         } else {
                             selectAllCheckbox.indeterminate = true;
                         }
                     }
                     
                     function getSelectedFiles() {
                         const selectedFiles = [];
                         const checkedBoxes = document.querySelectorAll('.file-select:checked');
                         
                         checkedBoxes.forEach(checkbox => {
                             const fileItem = checkbox.closest('.file-item');
                             selectedFiles.push({
                                 path: fileItem.dataset.path,
                                 name: fileItem.dataset.name,
                                 isDirectory: fileItem.dataset.isDirectory === 'true'
                             });
                         });
                         
                         return selectedFiles;
                     }
                     
                     function deleteSelected() {
                         const selectedFiles = getSelectedFiles();
                         if (selectedFiles.length === 0) return;
                         
                         const fileNames = selectedFiles.map(f => f.name).join(', ');
                         const confirmMessage = `Are you sure you want to delete ${selectedFiles.length} item(s)?\n\n${fileNames}`;
                         
                         if (!confirm(confirmMessage)) return;
                         
                         // Delete files one by one
                         let deletedCount = 0;
                         let errors = [];
                         
                         selectedFiles.forEach((file, index) => {
                             fetch(`/api/file/${encodeURIComponent(file.path)}`, {
                                 method: 'DELETE'
                             })
                             .then(response => response.json())
                             .then(data => {
                                 if (data.error) {
                                     errors.push(`${file.name}: ${data.error}`);
                                 } else {
                                     deletedCount++;
                                 }
                                 
                                 // Check if this is the last file
                                 if (index === selectedFiles.length - 1) {
                                     if (errors.length > 0) {
                                         alert(`Deleted ${deletedCount} file(s). Errors:\n${errors.join('\n')}`);
                                     } else {
                                         alert(`Successfully deleted ${deletedCount} file(s)!`);
                                     }
                                     loadFiles(currentPath); // Refresh file list
                                 }
                             })
                             .catch(error => {
                                 errors.push(`${file.name}: ${error.message}`);
                                 if (index === selectedFiles.length - 1) {
                                     alert(`Deleted ${deletedCount} file(s). Errors:\n${errors.join('\n')}`);
                                     loadFiles(currentPath);
                                 }
                             });
                         });
                     }
                     
                     function renameSelected() {
                         const selectedFiles = getSelectedFiles();
                         if (selectedFiles.length !== 1) return;
                         
                         const file = selectedFiles[0];
                         const newName = prompt(`Rename "${file.name}" to:`, file.name);
                         
                         if (!newName || newName === file.name) return;
                         
                         // Construct new path
                         const pathParts = file.path.split('/');
                         pathParts[pathParts.length - 1] = newName;
                         const newPath = pathParts.join('/');
                         
                         fetch(`/api/file/${encodeURIComponent(file.path)}/rename`, {
                             method: 'POST',
                             headers: {
                                 'Content-Type': 'application/json',
                             },
                             body: JSON.stringify({ new_name: newName, new_path: newPath })
                         })
                         .then(response => response.json())
                         .then(data => {
                             if (data.error) {
                                 alert('Error renaming file: ' + data.error);
                             } else {
                                 alert('File renamed successfully!');
                                 loadFiles(currentPath); // Refresh file list
                             }
                         })
                         .catch(error => {
                             console.error('Error renaming file:', error);
                             alert('Error renaming file: ' + error.message);
                         });
                     }
                </script>
            </body>
            </html>
            '''
            
            @self.web_server.route('/')
            def index():
                return html_template
            
            @self.web_server.route('/files')
            def file_manager():
                return file_manager_template
            
            @self.web_server.route('/api/files')
            def list_files():
                path = request.args.get('path', '.')
                try:
                    # Set the server directory as the base path
                    server_base_dir = os.path.abspath('C:/Users/MersYeon/Desktop/Cacasians/')
                    
                    # Handle relative paths from the server directory
                    if path == '.':
                        abs_path = server_base_dir
                    else:
                        abs_path = os.path.abspath(os.path.join(server_base_dir, path))
                    
                    # Security: Only allow access to server directory and subdirectories
                    if not abs_path.startswith(server_base_dir):
                        return jsonify({'error': 'Access denied'}), 403
                    
                    items = []
                    if os.path.exists(abs_path) and os.path.isdir(abs_path):
                        for item in sorted(os.listdir(abs_path)):
                            item_path = os.path.join(abs_path, item)
                            rel_path = os.path.relpath(item_path, server_base_dir)
                            is_dir = os.path.isdir(item_path)
                            size = 0 if is_dir else os.path.getsize(item_path)
                            modified = os.path.getmtime(item_path)
                            
                            items.append({
                                'name': item,
                                'path': rel_path.replace('\\', '/'),
                                'is_directory': is_dir,
                                'size': size,
                                'modified': modified
                            })
                    
                    return jsonify({
                        'current_path': os.path.relpath(abs_path, server_base_dir).replace('\\', '/') if abs_path != server_base_dir else '.',
                        'items': items
                    })
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            @self.web_server.route('/api/file/<path:filepath>')
            def get_file(filepath):
                try:
                    # Set the server directory as the base path
                    server_base_dir = os.path.abspath('C:/Users/MersYeon/Desktop/Cacasians/')
                    abs_path = os.path.abspath(os.path.join(server_base_dir, filepath))
                    
                    # Security check
                    if not abs_path.startswith(server_base_dir):
                        return jsonify({'error': 'Access denied'}), 403
                    
                    if not os.path.exists(abs_path) or os.path.isdir(abs_path):
                        return jsonify({'error': 'File not found'}), 404
                    
                    # Check if file is text-based
                    try:
                        with open(abs_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        return jsonify({
                            'content': content,
                            'is_text': True,
                            'size': len(content)
                        })
                    except UnicodeDecodeError:
                        return jsonify({
                            'error': 'Binary file - cannot display',
                            'is_text': False,
                            'size': os.path.getsize(abs_path)
                        })
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            @self.web_server.route('/api/file/<path:filepath>', methods=['POST'])
            def save_file(filepath):
                try:
                    # Set the server directory as the base path
                    server_base_dir = os.path.abspath('C:/Users/MersYeon/Desktop/Cacasians/')
                    abs_path = os.path.abspath(os.path.join(server_base_dir, filepath))
                    
                    # Security check
                    if not abs_path.startswith(server_base_dir):
                        return jsonify({'error': 'Access denied'}), 403
                    
                    data = request.get_json()
                    content = data.get('content', '')
                    
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                    
                    with open(abs_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    self.log_message(f"[WEB] File saved: {filepath}")
                    return jsonify({'success': True})
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            @self.web_server.route('/download/<path:filepath>')
            def download_file(filepath):
                try:
                    # Set the server directory as the base path
                    server_base_dir = os.path.abspath('C:/Users/MersYeon/Desktop/Cacasians/')
                    abs_path = os.path.abspath(os.path.join(server_base_dir, filepath))
                    
                    # Security check
                    if not abs_path.startswith(server_base_dir):
                        return "Access denied", 403
                    
                    if not os.path.exists(abs_path) or os.path.isdir(abs_path):
                        return "File not found", 404
                    
                    return send_from_directory(
                        os.path.dirname(abs_path),
                        os.path.basename(abs_path),
                        as_attachment=True
                    )
                except Exception as e:
                    return str(e), 500
            
            @self.web_server.route('/api/file/<path:filepath>', methods=['DELETE'])
            def delete_file(filepath):
                try:
                    # Set the server directory as the base path
                    server_base_dir = os.path.abspath('C:\Users\MersYeon\Desktop\Cacasians')
                    abs_path = os.path.abspath(os.path.join(server_base_dir, filepath))
                    
                    # Security check
                    if not abs_path.startswith(server_base_dir):
                        return jsonify({'error': 'Access denied'}), 403
                    
                    if not os.path.exists(abs_path):
                        return jsonify({'error': 'File not found'}), 404
                    
                    # Delete file or directory
                    if os.path.isdir(abs_path):
                        import shutil
                        shutil.rmtree(abs_path)
                        self.log_message(f"[WEB] Directory deleted: {filepath}")
                    else:
                        os.remove(abs_path)
                        self.log_message(f"[WEB] File deleted: {filepath}")
                    
                    return jsonify({'success': True})
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            @self.web_server.route('/api/file/<path:filepath>/rename', methods=['POST'])
            def rename_file(filepath):
                try:
                    # Set the server directory as the base path
                    server_base_dir = os.path.abspath('C:\Users\MersYeon\Desktop\Cacasians')
                    abs_path = os.path.abspath(os.path.join(server_base_dir, filepath))
                    
                    # Security check
                    if not abs_path.startswith(server_base_dir):
                        return jsonify({'error': 'Access denied'}), 403
                    
                    if not os.path.exists(abs_path):
                        return jsonify({'error': 'File not found'}), 404
                    
                    data = request.get_json()
                    new_name = data.get('new_name', '')
                    
                    if not new_name:
                        return jsonify({'error': 'New name is required'}), 400
                    
                    # Construct new path
                    parent_dir = os.path.dirname(abs_path)
                    new_abs_path = os.path.join(parent_dir, new_name)
                    
                    # Security check for new path
                    if not new_abs_path.startswith(server_base_dir):
                        return jsonify({'error': 'Access denied'}), 403
                    
                    # Check if new name already exists
                    if os.path.exists(new_abs_path):
                        return jsonify({'error': 'A file with that name already exists'}), 400
                    
                    # Rename the file/directory
                    os.rename(abs_path, new_abs_path)
                    
                    new_rel_path = os.path.relpath(new_abs_path, server_base_dir).replace('\\', '/')
                    self.log_message(f"[WEB] Renamed: {filepath} -> {new_rel_path}")
                    
                    return jsonify({
                        'success': True,
                        'new_path': new_rel_path
                    })
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            @self.web_server.route('/api/upload', methods=['POST'])
            def upload_files():
                try:
                    # Set the server directory as the base path
                    server_base_dir = os.path.abspath('C:/Users/MersYeon/Desktop/Cacasians/')
                    upload_path = request.form.get('path', '.')
                    
                    # Handle relative paths from the server directory
                    if upload_path == '.':
                        abs_upload_path = server_base_dir
                    else:
                        abs_upload_path = os.path.abspath(os.path.join(server_base_dir, upload_path))
                    
                    # Security check
                    if not abs_upload_path.startswith(server_base_dir):
                        return jsonify({'error': 'Access denied'}), 403
                    
                    # Create directory if it doesn't exist
                    os.makedirs(abs_upload_path, exist_ok=True)
                    
                    uploaded_files = request.files.getlist('files')
                    uploaded_count = 0
                    
                    for file in uploaded_files:
                        if file.filename:
                            # Secure filename
                            filename = file.filename.replace('..', '').replace('/', '').replace('\\', '')
                            if filename:
                                file_path = os.path.join(abs_upload_path, filename)
                                file.save(file_path)
                                uploaded_count += 1
                                self.log_message(f"[WEB] File uploaded: {filename}")
                    
                    return jsonify({
                        'success': True,
                        'uploaded': uploaded_count,
                        'message': f'Successfully uploaded {uploaded_count} file(s)'
                    })
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            @self.web_server.route('/api/console/history')
            def get_console_history():
                """Get console history for web interface"""
                try:
                    return jsonify({
                        'history': self.console_history,
                        'success': True
                    })
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            @self.web_server.route('/api/monitor')
            def get_monitor_data():
                try:
                    import psutil
                    import shutil
                    
                    # Get CPU usage
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    
                    # Get RAM usage
                    memory = psutil.virtual_memory()
                    ram_percent = memory.percent
                    ram_used = round(memory.used / (1024**3), 1)  # GB
                    ram_total = round(memory.total / (1024**3), 1)  # GB
                    
                    # Get storage usage for server directory
                    server_dir = 'C:/Users/MersYeon/Desktop/Cacasians/'
                    if os.path.exists(server_dir):
                        total, used, free = shutil.disk_usage(server_dir)
                        storage_percent = (used / total) * 100
                        storage_used = round(used / (1024**3), 1)  # GB
                        storage_total = round(total / (1024**3), 1)  # GB
                    else:
                        storage_percent = 0
                        storage_used = 0
                        storage_total = 0
                    
                    # Get TPS (placeholder - would need to parse from server output)
                    # For now, simulate TPS based on CPU usage
                    if cpu_percent < 30:
                        tps = 20.0
                    elif cpu_percent < 60:
                        tps = 19.5 - (cpu_percent - 30) * 0.5 / 30
                    elif cpu_percent < 80:
                        tps = 19.0 - (cpu_percent - 60) * 4 / 20
                    else:
                        tps = max(15.0 - (cpu_percent - 80) * 10 / 20, 5.0)
                    
                    return jsonify({
                        'cpu': cpu_percent,
                        'ram': ram_percent,
                        'ram_used': ram_used,
                        'ram_total': ram_total,
                        'storage': storage_percent,
                        'storage_used': storage_used,
                        'storage_total': storage_total,
                        'tps': tps
                    })
                except Exception as e:
                    return jsonify({
                        'cpu': 0,
                        'ram': 0,
                        'ram_used': 0,
                        'ram_total': 0,
                        'storage': 0,
                        'storage_used': 0,
                        'storage_total': 0,
                        'tps': 20.0,
                        'error': str(e)
                    })
            
            @self.socketio.on('send_command')
            def handle_command(data):
                command = data.get('command', '').strip()
                mode = data.get('mode', 'command')
                
                if command:
                    if mode == 'command':
                        self.send_server_command(command)
                    else:  # chat mode
                        self.send_server_command(f"say [ADMIN] {command}")
            
            @self.socketio.on('server_control')
            def handle_server_control(data):
                action = data.get('action')
                if action == 'start':
                    self.start_server()
                elif action == 'stop':
                    self.stop_server()
                elif action == 'restart':
                    self.restart_server()
                elif action == 'kill':
                    self.kill_server()
            
            @self.socketio.on('request_status')
            def handle_status_request():
                # Calculate uptime
                uptime = 0
                if self.server_running and self.server_start_time:
                    uptime = int(time.time() - self.server_start_time)
                
                # Get current monitoring data
                cpu_usage = getattr(self, 'cpu_usage', 0)
                memory_usage = getattr(self, 'memory_usage', 0)
                tps = getattr(self, 'current_tps', 20.0)
                
                # Get player count
                current_players = self.get_player_count()
                max_players = 20  # Default, could be read from server.properties
                
                emit('server_status', {
                    'running': self.server_running,
                    'uptime': uptime,
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage,
                    'tps': tps,
                    'current_players': current_players,
                    'max_players': max_players,
                    'players': current_players  # Keep for backward compatibility
                })
            
            # Start server in a separate thread
            def run_server():
                try:
                    self.socketio.run(self.web_server, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
                except Exception as e:
                    self.log_message(f"Web server error: {str(e)}")
                    self.web_server_running = False
            
            self.web_server_thread = threading.Thread(target=run_server, daemon=True)
            self.web_server_thread.start()
            self.web_server_running = True
            
            self.log_message(f"Web interface started on http://0.0.0.0:{port}")
            self.log_message("Remote users can now access the server control panel!")
            
        except ImportError:
            self.log_message("Error: Flask and Flask-SocketIO are required for remote access.")
            self.log_message("Please install them with: pip install flask flask-socketio")
            self.remote_access_enabled.set(False)
        except Exception as e:
            self.log_message(f"Failed to start web server: {str(e)}")
            self.remote_access_enabled.set(False)
    
    def stop_web_server(self):
        """Stop the Flask web server"""
        if not self.web_server_running:
            return
        
        try:
            self.web_server_running = False
            # Note: Flask-SocketIO doesn't have a clean shutdown method
            # The server will stop when the main application exits
            self.log_message("Web server stopped.")
        except Exception as e:
            self.log_message(f"Error stopping web server: {str(e)}")
    
    def send_server_command(self, command):
        """Send command to server (used by web interface)"""
        if self.server_running and self.server_process:
            try:
                self.server_process.stdin.write(command + "\n")
                self.server_process.stdin.flush()
                self.log_message(f"[WEB] Command sent: {command}")
            except Exception as e:
                self.log_message(f"Error sending command: {str(e)}")
    
    def get_player_count(self):
        """Get current player count (placeholder - would need to parse from server output)"""
        # This would need to be implemented by parsing server output
        # For now, return a placeholder
        return "--"
    
    def broadcast_console_output(self, message):
        """Broadcast console output to web clients"""
        if self.web_server_running and hasattr(self, 'socketio'):
            try:
                self.socketio.emit('console_output', {'message': message})
            except:
                pass  # Silently handle errors

def main():
    root = tk.Tk()
    app = MinecraftServerWrapper(root)
    root.mainloop()

if __name__ == "__main__":    main()
