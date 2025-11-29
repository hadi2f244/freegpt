#!/bin/bash
# Simple test runner for FreeGPT API

echo "🧪 Running FreeGPT API Tests"
echo ""

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Server not running on port 8000"
    echo "Start server first: ./start_server.sh"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Run Python tests
python tests/run_tests.py

exit $?
