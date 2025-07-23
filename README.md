# Minecraft Server Wrapper

A user-friendly Python GUI application for managing Minecraft servers.

## Features

- **Easy Server Management**: Start, stop, and restart your Minecraft server with simple buttons
- **Real-time Console**: View server logs and send commands directly from the GUI
- **Configuration Management**: Set memory allocation, server port, and JAR file location
- **User-friendly Interface**: Clean, modern dark theme interface
- **Auto-save Settings**: Your configuration is automatically saved and loaded

## Requirements

- Python 3.6 or higher
- Java (for running Minecraft server)
- Minecraft server JAR file

## Installation

1. Make sure you have Python installed on your system
2. Download or clone this project
3. Run the application:
   ```
   python minecraft_server_wrapper.py
   ```

## Usage

1. **First Setup**:
   - Click "Browse" to select your Minecraft server JAR file
   - Set your preferred memory allocation (Min/Max Memory)
   - Configure the server port (default: 25565)
   - Click "Save Config" to save your settings

2. **Starting the Server**:
   - Click "Start Server" to launch your Minecraft server
   - Monitor the console output for server status and player activity

3. **Managing the Server**:
   - Use "Stop Server" to gracefully shut down the server
   - Use "Restart Server" to quickly restart the server
   - Send commands using the command input field at the bottom

4. **Console Commands**:
   - Type commands in the command field and press Enter or click "Send"
   - Common commands: `list`, `say <message>`, `op <player>`, `stop`

## Configuration

The application saves your settings in `server_config.json`. You can manually edit this file if needed:

```json
{
    "server_jar": "path/to/your/server.jar",
    "java_path": "java",
    "memory_min": "1G",
    "memory_max": "2G",
    "server_port": "25565",
    "additional_args": ""
}
```

## Tips

- Make sure you have enough RAM allocated for your server
- The server JAR file should be in a dedicated folder with proper permissions
- Always use "Stop Server" instead of closing the application to properly shut down the server
- Check the console output for any error messages or important information

## Troubleshooting

- **Server won't start**: Check that Java is installed and the JAR file path is correct
- **Permission errors**: Make sure the application has write permissions in the server directory
- **Memory errors**: Reduce the memory allocation if you don't have enough RAM
- **Port conflicts**: Change the server port if 25565 is already in use

## License

This project is open source and available under the MIT License.