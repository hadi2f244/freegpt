# Quick Start: Token Management

## Creating Your First Token

```bash
# Create a new API token
python token_manager.py create my-app

# Output:
# ✓ New token created: sk-abc123...
# Save this token - you won't see it again!
```

## Using the Token

### Option 1: In .env file (recommended for local development)

```bash
echo "FREEGPT_API_KEY=sk-abc123..." >> .env
```

### Option 2: Direct in requests

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-abc123..." \
  -H "Content-Type: application/json" \
  -d '{"model":"freegpt-4","messages":[{"role":"user","content":"Hello!"}]}'
```

### Option 3: Python client

```python
import openai
openai.api_key = "sk-abc123..."
openai.api_base = "http://localhost:8000/v1"

response = openai.ChatCompletion.create(
    model="freegpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Managing Tokens

```bash
# List all tokens
python token_manager.py list

# Revoke a token (disable it)
python token_manager.py revoke sk-abc123

# Delete a token permanently
python token_manager.py delete sk-abc123
```

## Disable Authentication (for testing)

```bash
# Remove API keys from environment
unset FREEGPT_API_KEY
unset OPENAI_API_KEY

# Remove or rename token file
mv api_tokens.json api_tokens.json.backup

# Restart server - now accepts requests without auth
```

## Testing

```bash
# Run the example client
python example_client.py

# Or use the test script
./test_request.sh
```

## Troubleshooting

**Error: "Invalid API key provided"**

Solution:
```bash
# Check what keys are configured
echo "ENV: $FREEGPT_API_KEY"
python token_manager.py list

# Create a new token
python token_manager.py create test

# Use the new token in your request
```

**Want to disable auth completely?**

```bash
unset FREEGPT_API_KEY
unset OPENAI_API_KEY
rm api_tokens.json
# Restart server
```

For more details, see `TOKEN_GUIDE.md`
