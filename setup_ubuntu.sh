#!/bin/bash

# Minecraft Server Wrapper Setup Script for Ubuntu ARM64 (Termux)
# This script sets up the environment and dependencies

echo "🚀 Setting up Minecraft Server Wrapper for Ubuntu ARM64..."

# Update package lists
echo "📦 Updating package lists..."
apt update

# Install required packages
echo "🔧 Installing required packages..."
apt install -y python3 python3-pip python3-venv openjdk-17-jdk wget curl

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv minecraft_wrapper_env

# Activate virtual environment
source minecraft_wrapper_env/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install flask flask-socketio

# Create directories
echo "📁 Creating directories..."
mkdir -p minecraft_server
mkdir -p backups
mkdir -p logs

# Set permissions
chmod +x minecraft_server_wrapper_ubuntu.py

# Create systemd service file (optional)
echo "⚙️ Creating systemd service file..."
cat > minecraft-wrapper.service << EOF
[Unit]
Description=Minecraft Server Wrapper
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/minecraft_wrapper_env/bin
ExecStart=$(pwd)/minecraft_wrapper_env/bin/python $(pwd)/minecraft_server_wrapper_ubuntu.py --headless
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Setup complete!"
echo ""
echo "🎮 To run the Minecraft Server Wrapper:"
echo "1. Activate the virtual environment:"
echo "   source minecraft_wrapper_env/bin/activate"
echo ""
echo "2. Run in GUI mode (if display available):"
echo "   python3 minecraft_server_wrapper_ubuntu.py"
echo ""
echo "3. Run in headless mode (recommended for Termux):"
echo "   python3 minecraft_server_wrapper_ubuntu.py --headless"
echo ""
echo "4. Run on custom port:"
echo "   python3 minecraft_server_wrapper_ubuntu.py --headless --port 8080"
echo ""
echo "🌐 Web interface will be available at:"
echo "   http://localhost:5000 (or your custom port)"
echo ""
echo "📋 To install as a system service:"
echo "   sudo cp minecraft-wrapper.service /etc/systemd/system/"
echo "   sudo systemctl enable minecraft-wrapper"
echo "   sudo systemctl start minecraft-wrapper"
echo ""
echo "📥 Download Minecraft server JAR files to the minecraft_server directory"
echo "   Example: wget -O minecraft_server/server.jar https://launcher.mojang.com/v1/objects/[hash]/server.jar"