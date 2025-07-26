#!/bin/bash

# Quick Server Setup Script for Ubuntu ARM64
# This script helps you set up the Minecraft server directory and download server.jar

echo "🎮 Minecraft Server Setup for Ubuntu ARM64"
echo "=========================================="

# Create server directory if it doesn't exist
if [ ! -d "minecraft_server" ]; then
    echo "📁 Creating minecraft_server directory..."
    mkdir -p minecraft_server
fi

cd minecraft_server

echo ""
echo "📍 Current directory: $(pwd)"
echo ""
echo "🔽 Available Minecraft Server Versions:"
echo "1. Minecraft 1.20.4 (Latest Release)"
echo "2. Minecraft 1.20.1 (Stable)"
echo "3. Minecraft 1.19.4 (LTS)"
echo "4. Paper 1.20.4 (Optimized)"
echo "5. I'll download manually"
echo ""

read -p "Choose an option (1-5): " choice

case $choice in
    1)
        echo "📥 Downloading Minecraft 1.20.4..."
        wget -O server.jar "https://piston-data.mojang.com/v1/objects/8dd1a28015f51b1803213892b50b7b4fc76e594d/server.jar"
        ;;
    2)
        echo "📥 Downloading Minecraft 1.20.1..."
        wget -O server.jar "https://piston-data.mojang.com/v1/objects/84194a2f286ef7c14ed7ce0090dba59902951553/server.jar"
        ;;
    3)
        echo "📥 Downloading Minecraft 1.19.4..."
        wget -O server.jar "https://piston-data.mojang.com/v1/objects/8f3112a1049751cc472ec13e397eade5336ca7ae/server.jar"
        ;;
    4)
        echo "📥 Downloading Paper 1.20.4 (this may take a moment)..."
        # Get the latest Paper build
        PAPER_VERSION="1.20.4"
        BUILD=$(curl -s "https://api.papermc.io/v2/projects/paper/versions/${PAPER_VERSION}" | grep -o '"builds":\[[0-9,]*\]' | grep -o '[0-9]*' | tail -1)
        wget -O server.jar "https://api.papermc.io/v2/projects/paper/versions/${PAPER_VERSION}/builds/${BUILD}/downloads/paper-${PAPER_VERSION}-${BUILD}.jar"
        ;;
    5)
        echo "📝 Manual download instructions:"
        echo "   1. Download your preferred server.jar from:"
        echo "      - Vanilla: https://minecraft.net/download/server"
        echo "      - Paper: https://papermc.io/downloads"
        echo "      - Fabric: https://fabricmc.net/use/server/"
        echo "   2. Place it in: $(pwd)/server.jar"
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

if [ -f "server.jar" ]; then
    echo "✅ Server JAR downloaded successfully!"
    echo "📊 File size: $(du -h server.jar | cut -f1)"
    
    # Accept EULA automatically
    echo "📜 Creating eula.txt (accepting Minecraft EULA)..."
    echo "eula=true" > eula.txt
    
    # Create basic server.properties
    if [ ! -f "server.properties" ]; then
        echo "⚙️ Creating basic server.properties..."
        cat > server.properties << EOF
# Minecraft Server Properties (ARM64 Optimized)
server-port=25565
max-players=10
online-mode=false
white-list=false
spawn-protection=16
max-world-size=29999984
difficulty=easy
gamemode=survival
force-gamemode=false
hardcore=false
pvp=true
spawn-monsters=true
generate-structures=true
spawn-animals=true
snooper-enabled=false
level-name=world
level-seed=
level-type=default
view-distance=8
simulation-distance=8
EOF
    fi
    
    echo ""
    echo "🎯 Setup Complete!"
    echo "📁 Server files location: $(pwd)"
    echo "🎮 Server JAR: $(pwd)/server.jar"
    echo ""
    echo "🚀 Next steps:"
    echo "1. Go back to your wrapper directory: cd .."
    echo "2. In the web interface, set Server JAR path to: $(pwd)/server.jar"
    echo "3. Or use the full path: $(realpath server.jar)"
    echo ""
    echo "💡 Recommended settings for ARM64:"
    echo "   - Min Memory: 1G"
    echo "   - Max Memory: 2G (adjust based on your device)"
    echo "   - Enable Aikar's Flags: Yes"
    
else
    echo "❌ Server JAR not found. Please download manually."
fi