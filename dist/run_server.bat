@echo off
echo Starting Minecraft Server Wrapper...
echo.
echo The web interface will be available at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.
cd /d "%~dp0"
"MinecraftServerWrapper.exe"
pause