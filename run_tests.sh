#!/bin/bash
# Test runner for FreeGPT API using Docker Compose

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Unset proxy settings to avoid issues with localhost connections
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy NO_PROXY

echo "🧪 Running FreeGPT API Tests"
echo ""

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
RUN_MODE="docker"  # docker or local
VERBOSE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --local|-l)
            RUN_MODE="local"
            shift
            ;;
        --verbose|-v)
            VERBOSE="-v"
            shift
            ;;
        --help|-h)
            echo "Usage: ./run_tests.sh [options]"
            echo ""
            echo "Options:"
            echo "  --local, -l     Run tests locally (requires Python env)"
            echo "  --verbose, -v   Verbose output"
            echo "  --help, -h      Show this help message"
            echo ""
            echo "By default, tests run inside Docker containers."
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

if [ "$RUN_MODE" = "local" ]; then
    # Local mode: check if server is running and run tests locally
    echo "📍 Running tests locally..."
    echo ""

    # Check if server is running (either Docker or local)
    if curl -s http://localhost:${PORT:-8000}/health > /dev/null 2>&1; then
        echo "✅ Server is running"
    else
        echo "❌ Server not running on port ${PORT:-8000}"
        echo ""
        echo "Start server first:"
        echo "  ./start_server.sh -d"
        exit 1
    fi
    echo ""

    # Run Python tests
    python tests/run_tests.py
    exit $?
fi

# Docker mode
echo "🐳 Running tests in Docker..."
echo ""

# Check if server container is running
if ! $COMPOSE_CMD ps | grep -q "freegpt-api.*running\|freegpt-api.*Up"; then
    echo "⚠️  Server container not running. Starting it first..."
    $COMPOSE_CMD up -d freegpt-api

    # Wait for health check
    echo "⏳ Waiting for server to be healthy..."
    for i in {1..30}; do
        if $COMPOSE_CMD ps | grep -q "healthy"; then
            echo "✅ Server is healthy"
            break
        elif [ $i -eq 30 ]; then
            echo "❌ Server health check timeout"
            $COMPOSE_CMD logs freegpt-api
            exit 1
        else
            sleep 1
            printf "."
        fi
    done
    echo ""
fi

# Run the test service
echo "🧪 Running test suite..."
echo ""

$COMPOSE_CMD run --rm test python tests/run_tests.py $VERBOSE

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed"
fi

exit $TEST_EXIT_CODE
