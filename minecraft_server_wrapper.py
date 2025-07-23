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

class MinecraftServerWrapper:
    def __init__(self, root):
        self.root = root
        self.root.title("Minecraft Server Wrapper")
        self.root.geometry("800x600")
        self.root.configure(bg="#2c3e50")
        
        # Server process
        self.server_process = None
        self.server_running = False
        
        # Configuration
        self.config_file = "server_config.json"
        self.load_config()
        
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
            "use_aikars_flags": False
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
            messagebox.showerror("Error", f"Failed to save config: {str(e)}")
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = tk.Frame(self.root, bg="#2c3e50")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="Minecraft Server Wrapper", 
                              font=("Arial", 16, "bold"), fg="#ecf0f1", bg="#2c3e50")
        title_label.pack(pady=(0, 20))
        
        # Server controls frame
        controls_frame = tk.Frame(main_frame, bg="#34495e", relief=tk.RAISED, bd=2)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        controls_title = tk.Label(controls_frame, text="Server Controls", 
                                 font=("Arial", 12, "bold"), fg="#ecf0f1", bg="#34495e")
        controls_title.pack(pady=5)
        
        # Buttons frame
        buttons_frame = tk.Frame(controls_frame, bg="#34495e")
        buttons_frame.pack(pady=10)
        
        self.start_button = tk.Button(buttons_frame, text="Start Server", 
                                     command=self.start_server, bg="#27ae60", fg="white",
                                     font=("Arial", 10, "bold"), width=12)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(buttons_frame, text="Stop Server", 
                                    command=self.stop_server, bg="#e74c3c", fg="white",
                                    font=("Arial", 10, "bold"), width=12, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.restart_button = tk.Button(buttons_frame, text="Restart Server", 
                                       command=self.restart_server, bg="#f39c12", fg="white",
                                       font=("Arial", 10, "bold"), width=12, state=tk.DISABLED)
        self.restart_button.pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = tk.Label(controls_frame, text="Status: Stopped", 
                                    fg="#e74c3c", bg="#34495e", font=("Arial", 10, "bold"))
        self.status_label.pack(pady=5)
        
        # Configuration frame
        config_frame = tk.Frame(main_frame, bg="#34495e", relief=tk.RAISED, bd=2)
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        config_title = tk.Label(config_frame, text="Server Configuration", 
                               font=("Arial", 12, "bold"), fg="#ecf0f1", bg="#34495e")
        config_title.pack(pady=5)
        
        # Config grid
        config_grid = tk.Frame(config_frame, bg="#34495e")
        config_grid.pack(padx=10, pady=10)
        
        # Server JAR
        tk.Label(config_grid, text="Server JAR:", fg="#ecf0f1", bg="#34495e").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        jar_frame = tk.Frame(config_grid, bg="#34495e")
        jar_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        self.jar_entry = tk.Entry(jar_frame, width=40)
        self.jar_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.jar_entry.insert(0, self.config.get("server_jar", ""))
        self.jar_entry.bind('<FocusOut>', self.auto_save_config)
        self.jar_entry.bind('<KeyRelease>', self.schedule_auto_save)
        
        browse_button = tk.Button(jar_frame, text="Browse", command=self.browse_jar, bg="#3498db", fg="white")
        browse_button.pack(side=tk.LEFT)
        
        # Memory settings
        tk.Label(config_grid, text="Min Memory:", fg="#ecf0f1", bg="#34495e").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.min_memory_entry = tk.Entry(config_grid, width=10)
        self.min_memory_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        self.min_memory_entry.insert(0, self.config.get("memory_min", "1G"))
        self.min_memory_entry.bind('<FocusOut>', self.auto_save_config)
        self.min_memory_entry.bind('<KeyRelease>', self.schedule_auto_save)
        
        tk.Label(config_grid, text="Max Memory:", fg="#ecf0f1", bg="#34495e").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.max_memory_entry = tk.Entry(config_grid, width=10)
        self.max_memory_entry.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        self.max_memory_entry.insert(0, self.config.get("memory_max", "2G"))
        self.max_memory_entry.bind('<FocusOut>', self.auto_save_config)
        self.max_memory_entry.bind('<KeyRelease>', self.schedule_auto_save)
        
        # Port
        tk.Label(config_grid, text="Server Port:", fg="#ecf0f1", bg="#34495e").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.port_entry = tk.Entry(config_grid, width=10)
        self.port_entry.grid(row=3, column=1, sticky="w", padx=5, pady=2)
        self.port_entry.insert(0, self.config.get("server_port", "25565"))
        self.port_entry.bind('<FocusOut>', self.auto_save_config)
        self.port_entry.bind('<KeyRelease>', self.schedule_auto_save)
        
        # Aikar's Flags
        self.aikars_flags_var = tk.BooleanVar()
        self.aikars_flags_var.set(self.config.get("use_aikars_flags", False))
        self.aikars_flags_var.trace('w', self.auto_save_config_trace)
        aikars_checkbox = tk.Checkbutton(config_grid, text="Use Aikar's Flags (Optimized JVM)", 
                                        variable=self.aikars_flags_var, fg="#ecf0f1", bg="#34495e",
                                        selectcolor="#2c3e50", activebackground="#34495e",
                                        activeforeground="#ecf0f1", font=("Arial", 9))
        aikars_checkbox.grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        # Info button for Aikar's Flags
        info_button = tk.Button(config_grid, text="ℹ️ Info", command=self.show_aikars_info,
                               bg="#3498db", fg="white", font=("Arial", 8), width=8)
        info_button.grid(row=4, column=1, sticky="e", padx=5, pady=5)
        
        # Save config button
        save_config_button = tk.Button(config_grid, text="Save Config", command=self.save_config_ui,
                                      bg="#9b59b6", fg="white", font=("Arial", 9, "bold"))
        save_config_button.grid(row=5, column=0, columnspan=2, pady=10)
        
        # Server properties management
        properties_frame = tk.Frame(config_frame, bg="#34495e")
        properties_frame.pack(pady=10)
        
        properties_label = tk.Label(properties_frame, text="Server Properties Management:", 
                                   fg="#ecf0f1", bg="#34495e", font=("Arial", 10, "bold"))
        properties_label.pack(pady=(0, 5))
        
        properties_buttons_frame = tk.Frame(properties_frame, bg="#34495e")
        properties_buttons_frame.pack()
        
        self.open_properties_button = tk.Button(properties_buttons_frame, text="Open server.properties", 
                                               command=self.open_server_properties, bg="#e67e22", fg="white",
                                               font=("Arial", 9, "bold"), width=18)
        self.open_properties_button.pack(side=tk.LEFT, padx=5)
        
        self.edit_properties_button = tk.Button(properties_buttons_frame, text="Edit in Wrapper", 
                                               command=self.edit_server_properties, bg="#16a085", fg="white",
                                               font=("Arial", 9, "bold"), width=15)
        self.edit_properties_button.pack(side=tk.LEFT, padx=5)
        
        self.reload_properties_button = tk.Button(properties_buttons_frame, text="Reload Properties", 
                                                 command=self.reload_server_properties, bg="#8e44ad", fg="white",
                                                 font=("Arial", 9, "bold"), width=15)
        self.reload_properties_button.pack(side=tk.LEFT, padx=5)
        
        # Console frame
        console_frame = tk.Frame(main_frame, bg="#34495e", relief=tk.RAISED, bd=2)
        console_frame.pack(fill=tk.BOTH, expand=True)
        
        console_title = tk.Label(console_frame, text="Server Console", 
                                font=("Arial", 12, "bold"), fg="#ecf0f1", bg="#34495e")
        console_title.pack(pady=5)
        
        # Console output
        self.console_output = scrolledtext.ScrolledText(console_frame, height=15, 
                                                       bg="#1e1e1e", fg="#00ff00", 
                                                       font=("Consolas", 9))
        self.console_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Command input
        command_frame = tk.Frame(console_frame, bg="#34495e")
        command_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(command_frame, text="Command:", fg="#ecf0f1", bg="#34495e").pack(side=tk.LEFT)
        self.command_entry = tk.Entry(command_frame, bg="#ecf0f1")
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.command_entry.bind("<Return>", self.send_command)
        
        send_button = tk.Button(command_frame, text="Send", command=self.send_command,
                               bg="#3498db", fg="white")
        send_button.pack(side=tk.RIGHT)
        
        # Initial console message
        self.log_message("Minecraft Server Wrapper initialized. Configure your server and click 'Start Server'.")
    
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
        
        self.save_config()
        self.log_message("Configuration saved successfully!")
    
    def log_message(self, message):
        """Add message to console with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.console_output.insert(tk.END, formatted_message)
        self.console_output.see(tk.END)
    
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
            self.update_ui_state()
            
            # Start output reader thread
            threading.Thread(target=self.read_server_output, daemon=True).start()
            
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
        self.update_ui_state()
        self.log_message("Server stopped.")
    
    def restart_server(self):
        """Restart the Minecraft server"""
        self.log_message("Restarting server...")
        self.stop_server()
        time.sleep(2)  # Wait a moment
        self.start_server()
    
    def send_command(self, event=None):
        """Send command to server"""
        if not self.server_running or not self.server_process:
            self.log_message("Server is not running!")
            return
        
        command = self.command_entry.get().strip()
        if not command:
            return
        
        try:
            self.server_process.stdin.write(f"{command}\n")
            self.server_process.stdin.flush()
            self.log_message(f"Command sent: {command}")
            self.command_entry.delete(0, tk.END)
        except Exception as e:
            self.log_message(f"Failed to send command: {str(e)}")
    
    def read_server_output(self):
        """Read server output in a separate thread"""
        try:
            while self.server_running and self.server_process:
                line = self.server_process.stdout.readline()
                if line:
                    # Schedule UI update in main thread
                    self.root.after(0, lambda: self.log_message(f"[SERVER] {line.strip()}"))
                elif self.server_process.poll() is not None:
                    break
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"Error reading server output: {str(e)}"))
        
        # Server process ended
        self.server_running = False
        self.server_process = None
        self.root.after(0, self.update_ui_state)
        self.root.after(0, lambda: self.log_message("Server process ended."))
    
    def update_ui_state(self):
        """Update UI based on server state"""
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

def main():
    root = tk.Tk()
    app = MinecraftServerWrapper(root)
    root.mainloop()

if __name__ == "__main__":
    main()