#!/usr/bin/env python3
"""
Web-only version of the Minecraft Server Wrapper
This version runs only the web interface without the GUI
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main class
from minecraft_server_wrapper import MinecraftServerWrapper

class WebOnlyServerWrapper(MinecraftServerWrapper):
    """Web-only version that doesn't start the GUI"""
    
    def __init__(self):
        # Initialize everything except the GUI
        self.server_running = False
        self.server_process = None
        self.monitoring_active = True
        self.console_history = []
        self.performance_data = []
        
        # Configuration
        self.config_file = 'server_config.json'
        self.console_history_file = 'console_history.json'
        self.users_file = 'users.json'
        self.pending_registrations_file = 'pending_registrations.json'
        
        # Server settings
        self.server_jar = ''
        self.min_memory = '1G'
        self.max_memory = '2G'
        
        # Update system
        self.current_version = "1.0.0"
        self.github_repo = "jcfrancisco0103/My-Server-Wrapper"
        self.github_api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
        self.update_available = False
        self.latest_version = None
        self.update_download_url = None
        self.update_check_interval = 3600  # 1 hour
        
        # Authentication
        self.users = {}
        self.pending_registrations = {}
        
        # Load data
        self.load_config()
        self.load_console_history()
        self.load_users()
        self.load_pending_registrations()
        
        # Initialize web components
        self.init_web_server()
        self.setup_web_routes()
        
        # Start performance monitoring
        self.start_performance_monitoring()
        
        print("🌐 Starting web-only server...")
        print("📍 Web interface will be available at:")
        print("   • http://localhost:5000")
        print("   • http://127.0.0.1:5000")
        print("🔐 Default login: admin / admin123")
        print("🛑 Press Ctrl+C to stop the server")
    
    def run_web_only(self):
        """Run only the web server without GUI"""
        try:
            # Start the web server directly (blocking)
            self.socketio.run(
                self.web_server, 
                host='0.0.0.0', 
                port=5000, 
                debug=False, 
                use_reloader=False,
                allow_unsafe_werkzeug=True
            )
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
        except Exception as e:
            print(f"❌ Web server error: {e}")
    
    def add_console_message(self, message):
        """Add message to console history"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.console_history.append(log_entry)
        
        # Keep only last 1000 messages
        if len(self.console_history) > 1000:
            self.console_history = self.console_history[-1000:]
        
        # Print to console
        print(log_entry)
        
        # Save to file
        self.save_console_history()
        
        # Emit to web clients if socketio is available
        try:
            self.socketio.emit('console_update', {'message': log_entry})
        except:
            pass

def main():
    """Main function for web-only server"""
    try:
        app = WebOnlyServerWrapper()
        app.run_web_only()
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()