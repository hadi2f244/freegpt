#!/usr/bin/env bash
# Quick start script for FreeGPT API server using Docker Compose

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Parse arguments early for help
for arg in "$@"; do
    case $arg in
        --help|-h)
            echo "Usage: ./start_server.sh [options]"
            echo ""
            echo "Options:"
            echo "  -d, --detach    Run in background (detached mode)"
            echo "  --build         Rebuild the Docker image before starting"
            echo "  --help, -h      Show this help message"
            echo ""
            exit 0
            ;;
    esac
done

echo "🚀 Starting FreeGPT API Server (Docker)..."
echo ""

# Determine compose command
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Docker Compose not found"
    echo ""
    echo "Please install Docker and Docker Compose:"
    echo "  macOS:   brew install --cask docker"
    echo "  Linux:   https://docs.docker.com/engine/install/"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running"
    echo "   Please start Docker Desktop or the Docker service"
    exit 1
fi

# Load .env file if it exists (silently)
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Create placeholder files if they don't exist
if [ ! -f ".copilot_token" ] || [ ! -s ".copilot_token" ]; then
    touch .copilot_token
    echo "⚠️  No GitHub Copilot token found."
    echo "   Run: $COMPOSE_CMD run --rm freegpt-api python chat.py"
    echo ""
fi

if [ ! -f "api_tokens.json" ]; then
    echo "{}" > api_tokens.json
fi

# Check for API token
HAS_TOKEN=0
if [ -n "$FREEGPT_API_KEY" ] || [ -n "$OPENAI_API_KEY" ]; then
    HAS_TOKEN=1
elif [ -f "api_tokens.json" ] && [ -s "api_tokens.json" ] && [ "$(cat api_tokens.json)" != "{}" ]; then
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
    echo "   1. $COMPOSE_CMD exec freegpt-api python token_manager.py create my-app"
    echo "   2. Add token to .env file"
fi

echo ""
echo "📚 API Documentation: http://localhost:${PORT:-8000}/docs"
echo ""

# Parse arguments
DETACH=""
BUILD=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--detach)
            DETACH="-d"
            shift
            ;;
        --build)
            BUILD="--build"
            shift
            ;;
        *)
            shift
            ;;
    esac
done

if [ -n "$DETACH" ]; then
    echo "🔧 Starting in background mode..."
    echo "   View logs: $COMPOSE_CMD logs -f"
    echo "   Stop server: $COMPOSE_CMD down"
else
    echo "🔧 Starting in foreground mode..."
    echo "   Stop server: Ctrl+C"
fi
echo ""

# Start the server
$COMPOSE_CMD up $BUILD $DETACH
