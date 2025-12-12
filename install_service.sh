#!/bin/bash
# FreeGPT API Docker Installation Script
# This is now a wrapper for freegpt.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/freegpt.sh" install "$@"
