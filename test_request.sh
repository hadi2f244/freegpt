#!/bin/bash

# Load API key from .env file if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Use FREEGPT_API_KEY or OPENAI_API_KEY
API_KEY="${FREEGPT_API_KEY:-${OPENAI_API_KEY}}"

echo "Testing chat completion endpoint..."
echo "Using API key: ${API_KEY:0:10}..."
echo ""

# Non-streaming request
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{
    "model": "freegpt-4",
    "messages": [{"role": "user", "content": "Say hello in one sentence"}],
    "stream": false,
    "max_tokens": 100
  }'

echo -e "\n\nDone!"
