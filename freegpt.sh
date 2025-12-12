#!/usr/bin/env bash
# FreeGPT API - Unified Management Script

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Globals
COMPOSE_CMD=""
PORT="${PORT:-8000}"

# ============================================================================
# Common Functions
# ============================================================================

detect_compose() {
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        echo -e "${RED}❌ Docker Compose not found${NC}"
        echo ""
        echo "Please install Docker:"
        echo "  macOS:   brew install --cask docker"
        echo "  Linux:   https://docs.docker.com/engine/install/"
        exit 1
    fi
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not installed${NC}"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker daemon not running${NC}"
        echo "   Please start Docker Desktop"
        exit 1
    fi
}

load_env() {
    if [ -f .env ]; then
        set -a
        source .env
        set +a
        PORT="${PORT:-8000}"
    fi
}

prepare_files() {
    mkdir -p data
    [ ! -f "data/.copilot_token" ] && touch data/.copilot_token
    [ ! -f "api_tokens.json" ] && echo "{}" > api_tokens.json
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}📝 Created .env from .env.example${NC}"
    fi
}

# ============================================================================
# Command Functions
# ============================================================================

cmd_start() {
    local detach="" build=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--detach) detach="-d"; shift ;;
            --build) build="--build"; shift ;;
            *) shift ;;
        esac
    done

    echo "🚀 Starting FreeGPT API..."
    echo ""

    detect_compose
    check_docker
    load_env
    prepare_files

    echo -e "${BLUE}⚙️  Configuration:${NC}"
    echo "   Host: ${HOST:-0.0.0.0}"
    echo "   Port: $PORT"
    echo "   API Docs: http://localhost:$PORT/docs"
    echo ""

    if [ -n "$detach" ]; then
        echo "🔧 Starting in background mode..."
        echo "   View logs: $0 logs -f"
        echo "   Stop server: $0 stop"
        echo ""
        $COMPOSE_CMD up $build $detach
        echo ""
        echo -e "${GREEN}✅ Server started in background${NC}"
        echo "   Check status: $0 status"
    else
        echo "🔧 Starting in foreground mode..."
        echo "   Stop server: Ctrl+C"
        echo ""
        $COMPOSE_CMD up $build $detach
    fi
}

cmd_stop() {
    detect_compose
    echo "🛑 Stopping FreeGPT API..."
    $COMPOSE_CMD down
    echo -e "${GREEN}✅ Server stopped${NC}"
}

cmd_restart() {
    detect_compose
    echo "🔄 Restarting FreeGPT API..."
    $COMPOSE_CMD restart
    echo -e "${GREEN}✅ Server restarted${NC}"
}

cmd_logs() {
    detect_compose
    $COMPOSE_CMD logs "$@"
}

cmd_status() {
    detect_compose
    load_env
    echo "📊 FreeGPT API Status"
    echo "===================="
    $COMPOSE_CMD ps
    echo ""
    echo "API endpoint: http://localhost:$PORT"
}

cmd_build() {
    detect_compose
    check_docker
    echo "🔨 Building Docker image..."
    $COMPOSE_CMD build "$@"
    echo -e "${GREEN}✅ Build complete${NC}"
}

cmd_clean() {
    local images=false data=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--images) images=true; shift ;;
            -d|--data) data=true; shift ;;
            -a|--all) images=true; data=true; shift ;;
            *) shift ;;
        esac
    done

    detect_compose
    echo "🧹 Cleaning up..."
    $COMPOSE_CMD down

    if [ "$images" = true ]; then
        echo "   Removing Docker images..."
        docker rmi freegpt-freegpt-api freegpt-test 2>/dev/null || true
        echo -e "   ${GREEN}✅ Images removed${NC}"
    fi

    if [ "$data" = true ]; then
        echo -e "   ${YELLOW}⚠️  This will delete your authentication tokens!${NC}"
        read -p "   Are you sure? (y/N): " confirm
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            rm -rf data/.copilot_token api_tokens.json
            echo "   Data files removed"
        fi
    fi

    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

cmd_verify() {
    echo "🔍 FreeGPT API - Setup Verification"
    echo "===================================="
    echo ""

    local failed=0
    detect_compose
    load_env

    echo "1. Checking Docker..."
    if command -v docker &>/dev/null; then
        echo -e "   ${GREEN}✅ Docker installed: $(docker --version)${NC}"
    else
        echo -e "   ${RED}❌ Docker not installed${NC}"
        failed=1
    fi

    echo "2. Checking Docker daemon..."
    if docker info &>/dev/null; then
        echo -e "   ${GREEN}✅ Docker daemon running${NC}"
    else
        echo -e "   ${RED}❌ Docker daemon not running${NC}"
        failed=1
    fi

    echo "3. Checking GitHub Copilot authentication..."
    if [ -f ".copilot_token" ] && [ -s ".copilot_token" ]; then
        echo -e "   ${GREEN}✅ Copilot token found${NC}"
    else
        echo -e "   ${RED}❌ Copilot token missing${NC}"
        echo "      Run: $0 auth"
        failed=1
    fi

    echo "4. Checking API tokens..."
    if [ -f "api_tokens.json" ] && [ -s "api_tokens.json" ] && [ "$(cat api_tokens.json)" != "{}" ]; then
        echo -e "   ${GREEN}✅ API tokens configured${NC}"
    else
        echo -e "   ${YELLOW}⚠️  No API tokens configured${NC}"
        echo "      Run: $0 token create my-app"
    fi

    echo "5. Checking container status..."
    if $COMPOSE_CMD ps 2>/dev/null | grep -q "freegpt-api.*running\|Up"; then
        echo -e "   ${GREEN}✅ Container running${NC}"

        if curl -s "http://localhost:$PORT/health" >/dev/null 2>&1; then
            echo -e "   ${GREEN}✅ API responding on port $PORT${NC}"
        fi
    else
        echo -e "   ${YELLOW}ℹ️  Container not running${NC}"
        echo "      Run: $0 start -d"
    fi

    echo ""
    echo "===================================="
    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}✅ Verification passed!${NC}"
    else
        echo -e "${RED}❌ Please fix the issues above${NC}"
    fi
    echo "===================================="

    exit $failed
}

cmd_test() {
    detect_compose
    check_docker
    echo "🧪 Running tests..."
    echo ""
    $COMPOSE_CMD run --rm test "$@"
}

cmd_auth() {
    detect_compose
    check_docker
    prepare_files
    load_env

    echo "🔐 GitHub Copilot Authentication & Chat"
    echo "========================================"
    echo ""

    # Check if token already exists
    if [ -f "data/.copilot_token" ] && [ -s "data/.copilot_token" ]; then
        echo -e "${GREEN}✅ Existing token found${NC}"
        echo "   This will start a chat session using your existing token"
        echo "   To re-authenticate, delete data/.copilot_token first"
        echo ""
    else
        echo "No existing token found - will start OAuth authentication"
        echo ""
    fi

    # Check proxy configuration
    if [ -n "$HTTP_PROXY" ] || [ -n "$HTTPS_PROXY" ]; then
        echo "Proxy: ${HTTPS_PROXY:-$HTTP_PROXY}"
        echo -e "${YELLOW}⚠️  If you see connection errors, check your proxy is running${NC}"
    else
        echo "Direct connection (no proxy)"
        echo -e "${YELLOW}⚠️  If you see 403 errors, you may need to configure a proxy in .env${NC}"
    fi

    echo ""
    echo "Starting chat.py (use Ctrl+C to exit)..."
    echo "════════════════════════════════════════"
    echo ""

    $COMPOSE_CMD run --rm freegpt-api python chat.py

    echo ""
    if [ -s "data/.copilot_token" ]; then
        echo -e "${GREEN}✅ Token file exists${NC}"
        echo "   You can now start the API server: $0 start -d"
    else
        echo -e "${YELLOW}⚠️  No token file created${NC}"
        echo "   Authentication may not have completed successfully"
    fi
}

cmd_token() {
    detect_compose
    prepare_files

    if $COMPOSE_CMD ps 2>/dev/null | grep -q "freegpt-api.*running\|Up"; then
        $COMPOSE_CMD exec freegpt-api python token_manager.py "$@"
    else
        $COMPOSE_CMD run --rm freegpt-api python token_manager.py "$@"
    fi
}

cmd_install() {
    echo "=========================================="
    echo "FreeGPT API Docker Installation"
    echo "=========================================="
    echo ""

    detect_compose
    check_docker
    load_env
    prepare_files

    echo "🔨 Building Docker image..."
    $COMPOSE_CMD build
    echo ""

    echo "🚀 Starting container..."
    $COMPOSE_CMD up -d
    echo ""

    echo "⏳ Waiting for service to be healthy..."
    for i in {1..30}; do
        if $COMPOSE_CMD ps | grep -q "healthy"; then
            echo -e "${GREEN}✅ Service is healthy${NC}"
            break
        elif [ $i -eq 30 ]; then
            echo -e "${YELLOW}⚠️  Health check timeout${NC}"
        else
            sleep 1
            printf "."
        fi
    done
    echo ""

    echo "=========================================="
    echo -e "${GREEN}✅ Installation Complete!${NC}"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "  1. Authenticate with GitHub Copilot:"
    echo "     $0 auth"
    echo ""
    echo "  2. Create an API token:"
    echo "     $0 token create my-app"
    echo ""
    echo "  3. Run tests:"
    echo "     $0 test"
    echo ""
    echo "API server: http://localhost:$PORT"
    echo "API docs:   http://localhost:$PORT/docs"
    echo ""
}

cmd_help() {
    cat << 'EOF'
FreeGPT API - Unified Management Script

Usage: ./freegpt.sh <command> [options]

Commands:
  start [-d] [--build]   Start server (-d=background)
  stop                   Stop server
  restart                Restart server
  logs [-f]              View logs
  status                 Show container status

  build                  Build Docker image
  install                Full install (build + start)
  clean [-i|-d|-a]       Cleanup (-i=images, -d=data, -a=all)

  verify                 Verify setup
  test                   Run tests

  auth                   GitHub Copilot authentication
  token [args]           Manage API tokens
                         token create <name>
                         token list
                         token delete <key>

  help                   This help

Examples:
  ./freegpt.sh start -d              # Start background
  ./freegpt.sh logs -f               # Follow logs
  ./freegpt.sh auth                  # Setup Copilot
  ./freegpt.sh token create myapp    # Create token
  ./freegpt.sh test                  # Run tests
  ./freegpt.sh clean --all           # Remove everything
EOF
}

# ============================================================================
# Main Entry Point
# ============================================================================

COMMAND="${1:-help}"
shift || true

case "$COMMAND" in
    start) cmd_start "$@" ;;
    stop) cmd_stop "$@" ;;
    restart) cmd_restart "$@" ;;
    logs) cmd_logs "$@" ;;
    status|ps) cmd_status "$@" ;;
    build) cmd_build "$@" ;;
    install) cmd_install "$@" ;;
    clean) cmd_clean "$@" ;;
    verify) cmd_verify "$@" ;;
    test) cmd_test "$@" ;;
    auth) cmd_auth "$@" ;;
    token) cmd_token "$@" ;;
    help|--help|-h) cmd_help ;;
    up|down|exec|run) detect_compose; $COMPOSE_CMD "$COMMAND" "$@" ;;
    *) echo -e "${RED}Unknown command: $COMMAND${NC}"; echo ""; cmd_help; exit 1 ;;
esac
