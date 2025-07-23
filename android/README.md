# Cacasians Server Manager - Android App

A mobile Android application for managing your Minecraft server remotely using the existing web interface.

## Features

- **WebView Integration**: Loads the existing web interface of your Minecraft server wrapper
- **Modern Material Design**: Clean and intuitive user interface
- **Server Configuration**: Easy setup to connect to your server
- **Responsive Design**: Optimized for mobile devices
- **Offline Detection**: Handles network connectivity issues gracefully

## Setup Instructions

### Prerequisites

- Android Studio (latest version recommended)
- Android SDK with API level 21 or higher
- A running Minecraft server wrapper with web interface

### Installation

1. **Open the project in Android Studio**:
   - Launch Android Studio
   - Select "Open an existing project"
   - Navigate to the `android` folder and open it

2. **Configure your server**:
   - The app defaults to `http://192.168.1.100:5000`
   - You can change this in the Settings screen within the app
   - Make sure your server is accessible from your mobile device

3. **Build and run**:
   - Connect your Android device or start an emulator
   - Click "Run" in Android Studio
   - The app will install and launch on your device

### Server Configuration

1. **Find your server's IP address**:
   - On Windows: Run `ipconfig` in Command Prompt
   - Look for your local IP address (usually starts with 192.168.x.x)

2. **Update the app settings**:
   - Open the app
   - Tap the settings icon (⚙️) in the toolbar
   - Enter your server's IP address and port (e.g., `http://192.168.1.100:5000`)
   - Tap "Save Settings"

3. **Access your server**:
   - The app will load your server's web interface
   - You can now manage your Minecraft server from your mobile device

## App Structure

- **MainActivity**: Main screen with WebView displaying the server interface
- **SettingsActivity**: Configuration screen for server URL
- **Material Design**: Modern UI components and theming
- **Network Handling**: Automatic retry and error handling

## Troubleshooting

### Connection Issues

- Ensure your mobile device is on the same network as your server
- Check that the server wrapper is running and accessible
- Verify the IP address and port in the app settings
- Make sure your firewall allows connections on the server port

### App Issues

- Clear the app's cache and data if experiencing loading issues
- Restart the app if the WebView becomes unresponsive
- Check that JavaScript is enabled (it's enabled by default)

## Technical Details

- **Minimum Android Version**: Android 5.0 (API level 21)
- **Target Android Version**: Android 14 (API level 34)
- **Dependencies**: Material Design Components, WebView, SwipeRefreshLayout

## Building for Release

1. **Generate a signed APK**:
   - In Android Studio: Build → Generate Signed Bundle/APK
   - Choose APK and follow the signing wizard
   - Select "release" build variant

2. **Install on devices**:
   - Transfer the APK to your device
   - Enable "Install from unknown sources" in device settings
   - Install the APK

## Support

For issues related to the server wrapper itself, refer to the main project documentation. For Android app-specific issues, check the troubleshooting section above.