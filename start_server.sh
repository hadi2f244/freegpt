#!/usr/bin/env bash
# Quick start script for FreeGPT API server

echo "🚀 Starting FreeGPT API Server..."
echo ""

# Check if requirements are installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Check for .copilot_token
if [ ! -f ".copilot_token" ]; then
    echo "⚠️  No GitHub Copilot token found."
    echo "   You'll need to authenticate when the server starts."
    echo ""
fi

# Show configuration
echo "⚙️  Configuration:"
echo "   Host: ${HOST:-0.0.0.0}"
echo "   Port: ${PORT:-8000}"

if [ -n "$FREEGPT_API_KEY" ] || [ -n "$OPENAI_API_KEY" ]; then
    echo "   Auth: ENABLED ✅"
else
    echo "   Auth: DISABLED ⚠️  (Set FREEGPT_API_KEY to enable)"
fi

echo ""
echo "📚 API Documentation: http://localhost:${PORT:-8000}/docs"
echo ""

# Start the server
python3 api.py
