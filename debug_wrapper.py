import sys
import os
import traceback

def main():
    try:
        print("Starting Minecraft Server Wrapper...")
        print(f"Python version: {sys.version}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Script location: {__file__}")
        
        # Import and run the main application
        print("Importing main application...")
        
        # Add the current directory to Python path
        if hasattr(sys, '_MEIPASS'):
            # Running in PyInstaller bundle
            bundle_dir = sys._MEIPASS
            print(f"Running from PyInstaller bundle: {bundle_dir}")
        else:
            # Running in normal Python environment
            bundle_dir = os.path.dirname(os.path.abspath(__file__))
            print(f"Running from normal Python: {bundle_dir}")
        
        sys.path.insert(0, bundle_dir)
        
        # Import the original script components
        print("Importing Flask and other dependencies...")
        from flask import Flask
        from flask_socketio import SocketIO
        
        print("Creating Flask app...")
        
        # Read and execute the main script
        script_path = os.path.join(bundle_dir, 'minecraft_server_wrapper.py')
        if not os.path.exists(script_path):
            print(f"Script not found at: {script_path}")
            print("Available files:")
            for file in os.listdir(bundle_dir):
                print(f"  - {file}")
        else:
            print(f"Executing main script: {script_path}")
            # Execute the main script in the current namespace
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # Execute the script
            exec(script_content, globals())
        
    except Exception as e:
        print(f"Error starting application: {e}")
        print("Traceback:")
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()