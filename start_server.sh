#!/usr/bin/env bash
# Quick start script for FreeGPT API server

set -e

echo "🚀 Starting FreeGPT API Server..."
echo ""

# Load .env file if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

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

# Check for API token
HAS_TOKEN=0
if [ -n "$FREEGPT_API_KEY" ] || [ -n "$OPENAI_API_KEY" ]; then
    HAS_TOKEN=1
elif [ -f "api_tokens.json" ] && [ -s "api_tokens.json" ]; then
    HAS_TOKEN=1
fi

# Show configuration
echo "⚙️  Configuration:"
echo "   Host: ${HOST:-0.0.0.0}"
echo "   Port: ${PORT:-8000}"

if [ $HAS_TOKEN -eq 1 ]; then
    echo "   Auth: ENABLED ✅"
else
    echo "   Auth: DISABLED ⚠️"
    echo ""
    echo "   To enable authentication:"
    echo "   1. python token_manager.py create my-app"
    echo "   2. Add token to .env file"
fi

echo ""
echo "📚 API Documentation: http://localhost:${PORT:-8000}/docs"
echo "🔧 Stop server: Ctrl+C"
echo ""

# Start the server
python3 -m uvicorn api:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000}
