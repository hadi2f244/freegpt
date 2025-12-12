#!/usr/bin/env bash
# Quick start script for FreeGPT API server
# This is now a wrapper for freegpt.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/freegpt.sh" start "$@"
