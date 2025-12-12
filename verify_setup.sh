#!/bin/bash
# Quick Start Verification Script for Docker deployment
# Checks if everything is properly set up

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔍 FreeGPT API - Docker Setup Verification"
echo "=========================================="
echo ""

FAILED=0

# Determine compose command
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD=""
fi

# 1. Check Docker
echo "1. Checking Docker installation..."
if command -v docker &> /dev/null; then
    echo "   ✅ Docker installed: $(docker --version)"
else
    echo "   ❌ Docker not installed"
    echo "   Install: https://docs.docker.com/get-docker/"
    FAILED=1
fi

# 2. Check Docker Compose
echo "2. Checking Docker Compose..."
if [ -n "$COMPOSE_CMD" ]; then
    echo "   ✅ Docker Compose available"
else
    echo "   ❌ Docker Compose not found"
    FAILED=1
fi

# 3. Check Docker daemon
echo "3. Checking Docker daemon..."
if docker info &> /dev/null; then
    echo "   ✅ Docker daemon is running"
else
    echo "   ❌ Docker daemon not running"
    echo "   Start Docker Desktop or run: sudo systemctl start docker"
    FAILED=1
fi

# 4. Check Copilot token
echo "4. Checking GitHub Copilot authentication..."
if [ -f ".copilot_token" ] && [ -s ".copilot_token" ]; then
    echo "   ✅ Copilot token found"
else
    echo "   ❌ Copilot token missing or empty"
    echo "   Run: $COMPOSE_CMD run --rm freegpt-api python chat.py"
    FAILED=1
fi

# 5. Check API tokens
echo "5. Checking API tokens..."
if [ -f "api_tokens.json" ] && [ -s "api_tokens.json" ] && [ "$(cat api_tokens.json)" != "{}" ]; then
    TOKEN_COUNT=$(python3 -c "import json; print(len(json.load(open('api_tokens.json'))))" 2>/dev/null || echo "0")
    if [ "$TOKEN_COUNT" -gt 0 ]; then
        echo "   ✅ Found $TOKEN_COUNT API token(s)"
    else
        echo "   ❌ No API tokens configured"
        echo "   Run: $COMPOSE_CMD exec freegpt-api python token_manager.py create my-app"
        FAILED=1
    fi
else
    echo "   ❌ No API tokens configured"
    echo "   Run: $COMPOSE_CMD exec freegpt-api python token_manager.py create my-app"
    FAILED=1
fi

# 6. Check .env file
echo "6. Checking environment configuration..."
if [ -f ".env" ]; then
    if grep -q "FREEGPT_API_KEY=" .env && grep "FREEGPT_API_KEY=" .env | grep -v "^#" | grep -v "=$" > /dev/null; then
        echo "   ✅ API key configured in .env"
    else
        echo "   ⚠️  .env exists but no API key set"
        echo "   Edit .env and add: FREEGPT_API_KEY=sk-your-token"
    fi
else
    echo "   ⚠️  No .env file"
    if [ -f ".env.example" ]; then
        echo "   Run: cp .env.example .env"
    fi
fi

# 7. Check Docker image
echo "7. Checking Docker image..."
if docker images | grep -q "freegpt"; then
    echo "   ✅ Docker image built"
else
    echo "   ℹ️  Docker image not built yet"
    echo "   Run: ./install_service.sh"
fi

# 8. Check if container is running
echo "8. Checking container status..."
if [ -n "$COMPOSE_CMD" ]; then
    if $COMPOSE_CMD ps 2>/dev/null | grep -q "freegpt-api.*running\|freegpt-api.*Up"; then
        echo "   ✅ Container is running"

        # Check health
        if $COMPOSE_CMD ps 2>/dev/null | grep -q "healthy"; then
            echo "   ✅ Container is healthy"
        else
            echo "   ⚠️  Container not yet healthy (may still be starting)"
        fi
    else
        echo "   ℹ️  Container not running"
        echo "   Start with: ./start_server.sh -d"
    fi
fi

# 9. Check API endpoint
echo "9. Checking API endpoint..."
PORT="${PORT:-8000}"
if curl -s "http://localhost:$PORT/health" > /dev/null 2>&1; then
    echo "   ✅ API responding on port $PORT"
else
    echo "   ℹ️  API not responding on port $PORT"
    echo "   Start with: ./start_server.sh -d"
fi

echo ""
echo "=========================================="
if [ $FAILED -eq 0 ]; then
    echo "✅ Setup verification passed!"
    echo ""
    echo "Quick commands:"
    echo "  Start server:     ./start_server.sh -d"
    echo "  View logs:        $COMPOSE_CMD logs -f"
    echo "  Run tests:        ./run_tests.sh"
    echo "  Stop server:      $COMPOSE_CMD down"
else
    echo "❌ Please fix the issues above"
    echo ""
    echo "Quick setup:"
    echo "  1. ./install_service.sh"
    echo "  2. $COMPOSE_CMD run --rm freegpt-api python chat.py  # Auth with GitHub"
    echo "  3. $COMPOSE_CMD exec freegpt-api python token_manager.py create my-app"
fi
echo "=========================================="

exit $FAILED
