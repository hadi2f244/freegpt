#!/bin/bash

# FreeGPT API Docker Installation Script
# This script builds and starts the FreeGPT API using Docker Compose

set -e

echo "=========================================="
echo "FreeGPT API Docker Installation"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for Docker
echo "1. Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo ""
    echo "Please install Docker:"
    echo "  macOS:   brew install --cask docker"
    echo "  Linux:   https://docs.docker.com/engine/install/"
    echo "  Windows: https://docs.docker.com/desktop/install/windows/"
    exit 1
fi

# Check for docker-compose (V2 is built into docker)
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Docker Compose is not available"
    echo ""
    echo "Please ensure Docker Compose is installed:"
    echo "  Modern Docker includes 'docker compose' command"
    echo "  Or install standalone: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "   ✅ Docker found: $(docker --version)"
echo "   ✅ Docker Compose found: $($COMPOSE_CMD version --short 2>/dev/null || echo 'available')"
echo ""

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running"
    echo "   Please start Docker Desktop or the Docker service"
    exit 1
fi
echo "   ✅ Docker daemon is running"
echo ""

# Create placeholder files if they don't exist (for volume mounting)
echo "2. Preparing configuration files..."
if [ ! -f ".copilot_token" ]; then
    touch .copilot_token
    echo "   📝 Created empty .copilot_token"
    echo "   ⚠️  You'll need to authenticate with GitHub Copilot"
fi

if [ ! -f "api_tokens.json" ]; then
    echo "{}" > api_tokens.json
    echo "   📝 Created empty api_tokens.json"
fi

# Check for .env file
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "   📝 Created .env from .env.example"
    fi
fi
echo ""

# Build the Docker image
echo "3. Building Docker image..."
$COMPOSE_CMD build
echo ""

# Start the container
echo "4. Starting the container..."
$COMPOSE_CMD up -d
echo ""

# Wait for health check
echo "5. Waiting for service to be healthy..."
for i in {1..30}; do
    if $COMPOSE_CMD ps | grep -q "healthy"; then
        echo "   ✅ Service is healthy"
        break
    elif [ $i -eq 30 ]; then
        echo "   ⚠️  Health check timeout (service may still be starting)"
    else
        sleep 1
        printf "."
    fi
done
echo ""

# Check status
echo ""
echo "=========================================="
echo "Container Status:"
echo "=========================================="
$COMPOSE_CMD ps
echo ""

echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "Docker Compose commands:"
echo "  $COMPOSE_CMD up -d          - Start the service (background)"
echo "  $COMPOSE_CMD down           - Stop the service"
echo "  $COMPOSE_CMD restart        - Restart the service"
echo "  $COMPOSE_CMD ps             - Check service status"
echo "  $COMPOSE_CMD logs -f        - View live logs"
echo ""
echo "First-time setup (GitHub Copilot auth):"
echo "  $COMPOSE_CMD run --rm freegpt-api python chat.py"
echo ""
echo "Run tests:"
echo "  ./run_tests.sh"
echo ""
echo "The API server is now running at: http://localhost:${PORT:-8000}"
echo ""
