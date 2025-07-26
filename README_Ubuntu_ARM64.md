# Minecraft Server Wrapper for Ubuntu ARM64 (Termux)

A powerful, web-based Minecraft server management tool optimized for Ubuntu ARM64 environments, including Android Termux with GUI support.

## 🚀 Features

- **Headless Operation**: Runs without GUI requirements, perfect for Termux
- **Web Interface**: Modern, responsive web UI accessible from any device
- **ARM64 Optimized**: Specifically designed for ARM64 Ubuntu environments
- **Real-time Monitoring**: Live server status, player count, and console output
- **Command & Chat Modes**: Easy switching between server commands and chat
- **Auto-save**: Automatic configuration and console history saving
- **Signal Handling**: Graceful shutdown on system signals
- **Systemd Integration**: Optional system service installation

## 📋 Requirements

- Ubuntu ARM64 (including Termux)
- Python 3.8+
- Java 17+ (OpenJDK recommended)
- Internet connection for initial setup

## 🛠️ Installation

### Quick Setup (Recommended)

1. **Download the files to your Ubuntu ARM64 system:**
   ```bash
   # Create directory
   mkdir minecraft-wrapper
   cd minecraft-wrapper
   
   # Download files (replace with your actual download method)
   # Copy minecraft_server_wrapper_ubuntu.py, setup_ubuntu.sh, requirements_ubuntu.txt
   ```

2. **Run the setup script:**
   ```bash
   chmod +x setup_ubuntu.sh
   ./setup_ubuntu.sh
   ```

3. **Activate the virtual environment:**
   ```bash
   source minecraft_wrapper_env/bin/activate
   ```

### Manual Setup

1. **Install system dependencies:**
   ```bash
   apt update
   apt install -y python3 python3-pip python3-venv openjdk-17-jdk
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv minecraft_wrapper_env
   source minecraft_wrapper_env/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements_ubuntu.txt
   ```

## 🎮 Usage

### Running the Wrapper

**Headless Mode (Recommended for Termux):**
```bash
python3 minecraft_server_wrapper_ubuntu.py --headless
```

**GUI Mode (if display available):**
```bash
python3 minecraft_server_wrapper_ubuntu.py
```

**Custom Port:**
```bash
python3 minecraft_server_wrapper_ubuntu.py --headless --port 8080
```

### Accessing the Web Interface

Once running, open your web browser and navigate to:
- Local access: `http://localhost:5000`
- Network access: `http://[your-ip]:5000`

### Setting Up Your Minecraft Server

1. **Download a Minecraft server JAR:**
   ```bash
   mkdir minecraft_server
   cd minecraft_server
   
   # Example for Minecraft 1.20.4
   wget https://piston-data.mojang.com/v1/objects/8dd1a28015f51b1803213892b50b7b4fc76e594d/server.jar
   ```

2. **Configure through the web interface:**
   - Navigate to the web interface
   - Set the server JAR path
   - Configure memory settings (recommended: min 1G, max 2G for ARM64)
   - Start the server

## 🔧 Configuration

### Memory Recommendations for ARM64

- **Minimum**: 1GB RAM for basic server
- **Recommended**: 2-4GB RAM for optimal performance
- **Heavy modded**: 4-8GB RAM

### Java Optimization

The wrapper includes ARM64-optimized JVM flags when "Use Aikar's Flags" is enabled:
- G1 Garbage Collector optimizations
- Reduced GC pause times
- ARM64-specific performance tuning

## 🌐 Web Interface Features

- **Real-time Status**: Server status, player count, uptime
- **Live Console**: Real-time server console output
- **Command Interface**: Send commands or chat messages
- **Server Controls**: Start, stop, restart server
- **Responsive Design**: Works on desktop and mobile devices

## 🔄 Running as a System Service

To run the wrapper automatically on system boot:

1. **Install the service:**
   ```bash
   sudo cp minecraft-wrapper.service /etc/systemd/system/
   sudo systemctl enable minecraft-wrapper
   ```

2. **Start the service:**
   ```bash
   sudo systemctl start minecraft-wrapper
   ```

3. **Check status:**
   ```bash
   sudo systemctl status minecraft-wrapper
   ```

## 📱 Termux-Specific Notes

### Installation in Termux

1. **Update Termux packages:**
   ```bash
   pkg update && pkg upgrade
   ```

2. **Install required packages:**
   ```bash
   pkg install python openjdk-17 wget curl
   ```

3. **Follow the standard installation steps above**

### Network Access in Termux

To access the web interface from other devices on your network:

1. **Find your device's IP:**
   ```bash
   ip addr show
   ```

2. **Access from other devices:**
   ```
   http://[termux-device-ip]:5000
   ```

## 🛡️ Security Considerations

- The web interface runs without authentication by default
- For production use, consider:
  - Running behind a reverse proxy with authentication
  - Using firewall rules to restrict access
  - Enabling HTTPS with SSL certificates

## 🐛 Troubleshooting

### Common Issues

1. **Permission Denied:**
   ```bash
   chmod +x minecraft_server_wrapper_ubuntu.py
   ```

2. **Port Already in Use:**
   ```bash
   python3 minecraft_server_wrapper_ubuntu.py --headless --port 8080
   ```

3. **Java Not Found:**
   ```bash
   # Install OpenJDK
   apt install openjdk-17-jdk
   
   # Or specify Java path in config
   export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64
   ```

4. **Memory Issues on ARM64:**
   - Reduce max memory allocation
   - Enable swap if available
   - Close unnecessary applications

### Logs and Debugging

- Console output is saved to `console_history.json`
- Configuration is stored in `server_config.json`
- Check system logs: `journalctl -u minecraft-wrapper`

## 📊 Performance Tips for ARM64

1. **Memory Management:**
   - Use appropriate heap sizes for your device
   - Enable G1GC for better performance
   - Monitor memory usage regularly

2. **CPU Optimization:**
   - Limit concurrent players based on CPU cores
   - Use server optimization mods (Fabric/Paper)
   - Regular server restarts for memory cleanup

3. **Storage:**
   - Use fast storage (SSD if available)
   - Regular world backups
   - Optimize world generation settings

## 🤝 Contributing

This wrapper is designed specifically for ARM64 Ubuntu environments. Contributions and improvements are welcome!

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

For issues specific to ARM64 Ubuntu or Termux environments, please provide:
- Device specifications
- Ubuntu/Termux version
- Python version
- Error messages and logs

---

**Happy Minecraft server hosting on ARM64! 🎮🚀**