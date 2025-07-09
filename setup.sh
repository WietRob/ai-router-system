#!/bin/bash
# AI Router Quick Setup Script
echo "🚀 AI Router System Setup"

# Create directory structure
mkdir -p ~/ai-config ~/projects/{features,architecture,documentation}
cd ~/ai-config

# Download all scripts
echo "📥 Lade Scripts herunter..."
wget https://raw.githubusercontent.com/WietRob/ai-router-system/main/smart_router.py
wget https://raw.githubusercontent.com/WietRob/ai-router-system/main/file_router.py
wget https://raw.githubusercontent.com/WietRob/ai-router-system/main/cursor_integration.py

# Make executable
chmod +x *.py

echo ""
echo "✅ Scripts erfolgreich heruntergeladen!"
echo "📁 Verzeichnis: ~/ai-config/"
echo ""
echo "🔧 Nächste Schritte:"
echo "1. Claude API Key bei console.anthropic.com holen ($5 kaufen)"
echo "2. python smart_router.py setup YOUR_CLAUDE_API_KEY"
echo "3. python smart_router.py prompt 'Hello World'"
echo ""
echo "🔗 Cursor Integration:"
echo "4. python cursor_integration.py &"
echo "5. Cursor AI Provider: http://localhost:8000/v1/chat/completions"
