import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import subprocess
import threading
import os
import json
import time
from datetime import datetime

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
        
    def load_config(self):
        """Load server configuration from file"""
        default_config = {
            "server_jar": "",
            "java_path": "java",
            "memory_min": "1G",
            "memory_max": "2G",
            "server_port": "25565",
            "additional_args": ""
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
        
        browse_button = tk.Button(jar_frame, text="Browse", command=self.browse_jar, bg="#3498db", fg="white")
        browse_button.pack(side=tk.LEFT)
        
        # Memory settings
        tk.Label(config_grid, text="Min Memory:", fg="#ecf0f1", bg="#34495e").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.min_memory_entry = tk.Entry(config_grid, width=10)
        self.min_memory_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        self.min_memory_entry.insert(0, self.config.get("memory_min", "1G"))
        
        tk.Label(config_grid, text="Max Memory:", fg="#ecf0f1", bg="#34495e").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.max_memory_entry = tk.Entry(config_grid, width=10)
        self.max_memory_entry.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        self.max_memory_entry.insert(0, self.config.get("memory_max", "2G"))
        
        # Port
        tk.Label(config_grid, text="Server Port:", fg="#ecf0f1", bg="#34495e").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.port_entry = tk.Entry(config_grid, width=10)
        self.port_entry.grid(row=3, column=1, sticky="w", padx=5, pady=2)
        self.port_entry.insert(0, self.config.get("server_port", "25565"))
        
        # Save config button
        save_config_button = tk.Button(config_grid, text="Save Config", command=self.save_config_ui,
                                      bg="#9b59b6", fg="white", font=("Arial", 9, "bold"))
        save_config_button.grid(row=4, column=0, columnspan=2, pady=10)
        
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
    
    def save_config_ui(self):
        """Save configuration from UI"""
        self.config["server_jar"] = self.jar_entry.get()
        self.config["memory_min"] = self.min_memory_entry.get()
        self.config["memory_max"] = self.max_memory_entry.get()
        self.config["server_port"] = self.port_entry.get()
        
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
            
            command = [
                java_path,
                f"-Xms{min_mem}",
                f"-Xmx{max_mem}",
                "-jar",
                jar_path,
                "nogui"
            ]
            
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

def main():
    root = tk.Tk()
    app = MinecraftServerWrapper(root)
    
    # Handle window closing
    def on_closing():
        if app.server_running:
            if messagebox.askokcancel("Quit", "Server is running. Stop server and quit?"):
                app.stop_server()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()