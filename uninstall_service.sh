#!/bin/bash

# FreeGPT API Docker Uninstallation Script
# This script stops and removes the Docker containers

set -e

echo "=========================================="
echo "FreeGPT API Docker Uninstallation"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Determine compose command
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Docker Compose not found"
    exit 1
fi

# Parse arguments
REMOVE_IMAGES=false
REMOVE_DATA=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --images|-i)
            REMOVE_IMAGES=true
            shift
            ;;
        --data|-d)
            REMOVE_DATA=true
            shift
            ;;
        --all|-a)
            REMOVE_IMAGES=true
            REMOVE_DATA=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./uninstall_service.sh [options]"
            echo ""
            echo "Options:"
            echo "  --images, -i    Also remove Docker images"
            echo "  --data, -d      Also remove data files (tokens)"
            echo "  --all, -a       Remove everything (images + data)"
            echo "  --help, -h      Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "Uninstalling FreeGPT API Docker service..."
echo ""

# Stop and remove containers
echo "1. Stopping and removing containers..."
$COMPOSE_CMD down || true
echo ""

# Remove images if requested
if [ "$REMOVE_IMAGES" = true ]; then
    echo "2. Removing Docker images..."
    docker rmi freegpt-freegpt-api freegpt-test 2>/dev/null || true
    docker rmi $(docker images -q "freegpt*" 2>/dev/null) 2>/dev/null || true
    echo "   ✅ Images removed"
    echo ""
fi

# Remove data if requested
if [ "$REMOVE_DATA" = true ]; then
    echo "3. Removing data files..."
    echo "   ⚠️  This will delete your authentication tokens!"
    read -p "   Are you sure? (y/N): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        rm -f .copilot_token api_tokens.json
        echo "   ✅ Data files removed"
    else
        echo "   ⏭️  Skipped data removal"
    fi
    echo ""
fi

echo "=========================================="
echo "✅ Uninstallation Complete!"
echo "=========================================="
echo ""
echo "The FreeGPT API Docker service has been removed."
if [ "$REMOVE_DATA" = false ]; then
    echo "Your data files are preserved in: $SCRIPT_DIR"
    echo "  - .copilot_token"
    echo "  - api_tokens.json"
fi
echo ""
echo "To reinstall, run: ./install_service.sh"
echo ""
