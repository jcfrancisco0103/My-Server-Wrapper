# Minecraft Server Wrapper

A user-friendly Python GUI application for managing Minecraft servers.

## Features

- **Easy Server Management**: Start, stop, and restart your Minecraft server with simple buttons
- **Real-time Console**: View server logs and send commands directly through the interface
- **Enhanced Command Input**: Dedicated command field supporting both server commands and chat messages
- **Memory Configuration**: Set minimum and maximum RAM allocation for optimal performance
- **Port Management**: Configure server port settings
- **Server Properties Editor**: Edit server.properties file directly within the application
- **JAR File Selection**: Browse and select your Minecraft server JAR file
- **Auto-save Configuration**: All settings are automatically saved and restored
- **Auto-start Server**: Option to automatically start the server when the application opens
- **Windows Startup Integration**: Option to automatically start the wrapper with Windows
- **Aikar's Flags Support**: Enable optimized JVM arguments for better server performance
- **Real-time Performance Monitor**: Monitor CPU, RAM, and TPS in real-time

## Performance Monitor Feature

The wrapper includes a comprehensive real-time performance monitoring system that tracks your server's vital statistics:

### Monitored Metrics

- **TPS (Ticks Per Second)**: Shows server performance with color-coded indicators
  - Green (19.5+ TPS): Excellent performance
  - Orange (18-19.4 TPS): Good performance with minor lag
  - Red (<18 TPS): Poor performance, significant lag
- **CPU Usage**: Real-time CPU usage of the server process
- **Server RAM**: Memory usage of the Minecraft server process
- **System RAM**: Overall system memory usage with percentage

### Features

- **Real-time Updates**: Metrics update every 2 seconds
- **Color-coded Indicators**: Visual feedback for performance levels
- **Automatic TPS Detection**: Parses TPS from server output (works with Paper, Spigot, and TPS plugins)
- **Smart Resource Monitoring**: Only monitors when server is running
- **Historical Tracking**: Maintains recent performance history for accurate averages

### Usage

The performance monitor automatically starts when you launch the application and displays live metrics when your server is running. No additional configuration is required - it works out of the box with most Minecraft server types.

## Windows Startup Integration

The wrapper can automatically start with Windows, ensuring your server is always ready when your computer boots up:

### Features

- **Registry Integration**: Safely adds/removes entries from Windows startup registry
- **Smart Detection**: Automatically detects current startup status and syncs with configuration
- **User Control**: Easy checkbox toggle to enable/disable startup functionality
- **Error Handling**: Graceful error handling with user feedback
- **Persistent Setting**: Startup preference is saved and restored across sessions

### How to Use

1. **Enable Startup**: Check the "Start with Windows (Run at startup)" checkbox
2. **Automatic Registration**: The application automatically registers itself in Windows startup
3. **Boot Integration**: The wrapper will now start automatically when Windows boots
4. **Disable Anytime**: Uncheck the box to remove from startup

## Enhanced Console Features

The wrapper includes an improved console system with dedicated command input and read-only output:

### Console Output

- **Read-only Display**: Server output cannot be accidentally modified
- **Real-time Updates**: Live server logs and messages
- **Formatted Timestamps**: Clear time-stamped entries
- **Scroll Support**: Easy navigation through server history

### Command Input System

- **Dual Functionality**: Supports both server commands and chat messages
- **Server Commands**: Prefix with `/` for server commands (e.g., `/stop`, `/list`, `/tp player`)
- **Chat Messages**: Type without `/` to send chat messages as `[ADMIN]`
- **Enter Key Support**: Press Enter to send commands quickly
- **Visual Feedback**: Clear indication of command type in console

### Usage Examples

- **Server Command**: Type `/list` to see online players
- **Chat Message**: Type `Hello everyone!` to broadcast as admin
- **Stop Server**: Type `/stop` to gracefully stop the server
- **Teleport**: Type `/tp player1 player2` to teleport players

## New Server Properties Features

- **Open server.properties**: Opens the file in your default text editor
- **Edit in Wrapper**: Built-in editor window for editing properties without leaving the application
- **Reload Properties**: Send reload command to running server to apply changes
- **Auto-create Properties**: Automatically creates a default server.properties file if none exists

## Aikar's Flags Feature

- **Performance Optimization**: Enable Aikar's Flags for optimized JVM arguments
- **Reduced Lag**: Specially tuned garbage collection settings to minimize server lag
- **Easy Toggle**: Simple checkbox to enable/disable optimized flags
- **Information Panel**: Built-in guide explaining what Aikar's Flags do and their benefits
- **Automatic Integration**: Seamlessly replaces standard JVM arguments when enabled

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

5. **Server Properties Management**:
   - **Open server.properties**: Click to open the file in your default text editor (Notepad, VS Code, etc.)
   - **Edit in Wrapper**: Opens a built-in editor window for convenient editing without leaving the application
   - **Reload Properties**: Sends a reload command to the running server to apply property changes
   - If no server.properties file exists, the wrapper will create a default one with common settings

6. **Aikar's Flags (Performance Optimization)**:
   - Check the "Use Aikar's Flags (Optimized JVM)" checkbox to enable performance optimization
   - Click the "ℹ️ Info" button to learn more about what Aikar's Flags do
   - Recommended for servers with 2GB+ RAM and multiple players
   - Automatically replaces standard JVM arguments with optimized ones when enabled

## Configuration

The application saves your settings in `server_config.json`. You can manually edit this file if needed:

```json
{
    "server_jar": "path/to/your/server.jar",
    "java_path": "java",
    "memory_min": "1G",
    "memory_max": "2G",
    "server_port": "25565",
    "additional_args": "",
    "use_aikars_flags": false,
    "auto_start_server": true,
    "startup_enabled": false
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