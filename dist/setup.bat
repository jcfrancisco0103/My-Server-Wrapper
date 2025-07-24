@echo off
title Minecraft Server Wrapper - Setup
color 0A

echo.
echo ========================================
echo   Minecraft Server Wrapper v1.0
echo ========================================
echo.
echo This will set up your Minecraft Server Wrapper.
echo.
echo Requirements:
echo - Minecraft Server JAR file
echo - Java installed on your system
echo.
echo The wrapper will:
echo - Provide a web interface at http://localhost:5000
echo - Monitor server performance (CPU, RAM, TPS)
echo - Allow file management and console access
echo - Enable easy server control
echo.
pause

echo.
echo Setting up directories...
if not exist "server_files" mkdir server_files
if not exist "logs" mkdir logs
if not exist "backups" mkdir backups

echo.
echo Setup complete!
echo.
echo To start the server wrapper:
echo 1. Place your Minecraft server JAR file in the server_files folder
echo 2. Run MinecraftServerWrapper.exe or run_server.bat
echo 3. Open http://localhost:5000 in your browser
echo.
echo Press any key to start the wrapper now...
pause > nul

echo.
echo Starting Minecraft Server Wrapper...
start "" "MinecraftServerWrapper.exe"

echo.
echo The wrapper is starting...
echo Open http://localhost:5000 in your browser
echo.
pause