# Token Management Guide

## Creating API Tokens

### 1. Create a new token

```bash
python token_manager.py create my-application
```

This will generate a secure token like: `sk-a1b2c3d4e5f6...`

**⚠️ Important:** Save this token immediately! It won't be shown again.

### 2. View all tokens

```bash
python token_manager.py list
```

Example output:
```
Found 2 token(s):

1. sk-a1b2c3d4e5f...
   Name: my-application
   Status: ✓ Active
   Created: 2025-11-26T10:30:00
   Last used: 2025-11-26T11:45:23

2. sk-x9y8z7w6v5u...
   Name: mobile-app
   Status: ✓ Active
   Created: 2025-11-25T15:20:00
   Last used: Never
```

### 3. Revoke a token (disable without deleting)

```bash
python token_manager.py revoke sk-a1b2c3d4e5f
```

### 4. Delete a token permanently

```bash
python token_manager.py delete sk-a1b2c3d4e5f
```

## Using Tokens

### Method 1: Environment Variable

Add to your `.env` file:
```bash
FREEGPT_API_KEY=sk-a1b2c3d4e5f6...
```

### Method 2: Direct API Request

Include in the Authorization header:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-a1b2c3d4e5f6..." \
  -d '{
    "model": "freegpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Method 3: Python Client

```python
import openai

openai.api_key = "sk-a1b2c3d4e5f6..."
openai.api_base = "http://localhost:8000/v1"

response = openai.ChatCompletion.create(
    model="freegpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Authentication Modes

The API supports three authentication modes:

1. **No authentication** (default if no keys configured)
   - No API key in environment
   - No tokens in `api_tokens.json`
   - All requests allowed

2. **Environment variable only**
   - Set `FREEGPT_API_KEY` or `OPENAI_API_KEY`
   - Only that key will work

3. **Token file + Environment variable**
   - Both environment key AND tokens from file are valid
   - Any valid token will authenticate

## Security Best Practices

1. **Never commit tokens to git**
   - `api_tokens.json` is in `.gitignore`
   - `.env` is in `.gitignore`

2. **Rotate tokens regularly**
   - Create new token
   - Update clients
   - Revoke old token

3. **Use descriptive names**
   ```bash
   python token_manager.py create "production-web-app"
   python token_manager.py create "staging-mobile-app"
   python token_manager.py create "john-dev-testing"
   ```

4. **Revoke unused tokens**
   - Check `list` output for "Never" used tokens
   - Revoke tokens when no longer needed

## Troubleshooting

### "Invalid API key provided" error

1. Check if authentication is enabled:
   ```bash
   echo $FREEGPT_API_KEY
   echo $OPENAI_API_KEY
   ```

2. List available tokens:
   ```bash
   python token_manager.py list
   ```

3. Create a new token if needed:
   ```bash
   python token_manager.py create test
   ```

### Disable authentication completely

```bash
unset FREEGPT_API_KEY
unset OPENAI_API_KEY
# Delete or rename api_tokens.json
mv api_tokens.json api_tokens.json.backup
# Restart server
```

### Check token validity

The API automatically tracks when tokens are used. Check the "Last used" timestamp:
```bash
python token_manager.py list
```

## Examples

### Creating tokens for different clients

```bash
# Web application
python token_manager.py create "webapp-production"

# Mobile app
python token_manager.py create "mobile-ios"

# Development/testing
python token_manager.py create "dev-testing"

# CI/CD pipeline
python token_manager.py create "github-actions"
```

### Revoking compromised token

```bash
# List to find the token prefix
python token_manager.py list

# Revoke it
python token_manager.py revoke sk-compromised-token-prefix

# Or delete it entirely
python token_manager.py delete sk-compromised-token-prefix
```
