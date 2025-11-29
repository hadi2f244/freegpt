#!/bin/bash
# Quick Start Verification Script
# Checks if everything is properly set up

echo "🔍 FreeGPT API - Quick Start Verification"
echo "=========================================="
echo ""

FAILED=0

# 1. Check dependencies
echo "1. Checking dependencies..."
if python -c "import fastapi, uvicorn, openai" 2>/dev/null; then
    echo "   ✅ All dependencies installed"
else
    echo "   ❌ Missing dependencies"
    echo "   Run: pip install -r requirements.txt"
    FAILED=1
fi

# 2. Check Copilot token
echo "2. Checking GitHub Copilot authentication..."
if [ -s .copilot_token ]; then
    echo "   ✅ Copilot token found"
else
    echo "   ❌ Copilot token missing"
    echo "   Run: python chat.py (first time only)"
    FAILED=1
fi

# 3. Check API token
echo "3. Checking API tokens..."
if [ -f api_tokens.json ] && [ -s api_tokens.json ]; then
    TOKEN_COUNT=$(python -c "import json; print(len(json.load(open('api_tokens.json'))))" 2>/dev/null || echo "0")
    if [ "$TOKEN_COUNT" -gt 0 ]; then
        echo "   ✅ Found $TOKEN_COUNT API token(s)"
    else
        echo "   ❌ No API tokens"
        echo "   Run: python token_manager.py create my-app"
        FAILED=1
    fi
else
    echo "   ❌ No API tokens"
    echo "   Run: python token_manager.py create my-app"
    FAILED=1
fi

# 4. Check .env file
echo "4. Checking environment configuration..."
if [ -f .env ]; then
    if grep -q "FREEGPT_API_KEY=" .env && grep "FREEGPT_API_KEY=" .env | grep -v "^#" | grep -v "=$" > /dev/null; then
        echo "   ✅ API key configured in .env"
    else
        echo "   ⚠️  .env exists but no API key set"
        echo "   Edit .env and add: FREEGPT_API_KEY=sk-your-token"
    fi
else
    echo "   ⚠️  No .env file"
    echo "   Run: cp .env.example .env"
fi

# 5. Check if server is running
echo "5. Checking server status..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ Server is running on port 8000"
elif systemctl is-active --quiet freegpt-api 2>/dev/null; then
    echo "   ✅ Service is active"
else
    echo "   ℹ️  Server not running"
    echo "   Start with: ./start_server.sh"
    echo "   Or install service: sudo ./install_service.sh"
fi

echo ""
echo "=========================================="
if [ $FAILED -eq 0 ]; then
    echo "✅ Quick start verification passed!"
    echo ""
    echo "Next steps:"
    echo "  - Start server: ./start_server.sh"
    echo "  - Run tests: ./run_tests.sh"
    echo "  - Install service: sudo ./install_service.sh"
else
    echo "❌ Please fix the issues above before starting"
fi
echo "=========================================="

exit $FAILED
