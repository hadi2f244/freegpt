# FreeGPT API

OpenAI-compatible API server powered by GitHub Copilot. Drop-in replacement for OpenAI API endpoints.

## Features

- 🌐 **OpenAI-compatible** - Works with any OpenAI SDK/client
- 🔄 **Streaming & Non-streaming** - Full SSE support
- 🔐 **Token Management** - Built-in authentication system
- 🚀 **Systemd Service** - Auto-start on boot
- 📝 **Full Test Suite** - Validated compatibility

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create API Token

```bash
python token_manager.py create my-app
```

Save the generated token (starts with `sk-`).

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your token:
# FREEGPT_API_KEY=sk-your-token-here
```

### 4. Start Server

**Manual:**
```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

**As System Service:**
```bash
sudo ./install_service.sh
```

Server runs at `http://localhost:8000`

## API Usage

### Authentication

Include your token in the Authorization header:

```bash
Authorization: Bearer sk-your-token-here
```

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat/completions` | POST | Chat with streaming/non-streaming |
| `/v1/completions` | POST | Text completions |
| `/v1/models` | GET | List available models |
| `/v1/models/{id}` | GET | Get model details |
| `/health` | GET | Health check |

### Models

- `gpt-4` / `gpt-4.1` / `freegpt-4`
- `gpt-3.5-turbo` / `freegpt-3.5`

### Example: Chat Completion

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-token" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Example: Streaming

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-token" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Count to 5"}],
    "stream": true
  }'
```

## OpenAI SDK Integration

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="sk-your-token"
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

## Token Management

```bash
# Create new token
python token_manager.py create my-app

# List all tokens
python token_manager.py list

# Revoke token
python token_manager.py revoke sk-abc123

# Delete token
python token_manager.py delete sk-abc123
```

## Systemd Service

Install as a system service (auto-starts on boot):

```bash
sudo ./install_service.sh
```

### Service Commands

```bash
sudo systemctl status freegpt-api    # Check status
sudo systemctl restart freegpt-api   # Restart
sudo systemctl stop freegpt-api      # Stop
sudo journalctl -u freegpt-api -f    # View logs
```

Uninstall:

```bash
sudo ./uninstall_service.sh
```

## Testing

```bash
# Run full test suite
python test_openai_sdk.py

# Or use pytest
pytest tests/test_api.py -v
```

## Configuration Files

- `.env` - Environment variables (API keys)
- `api_tokens.json` - Token database (auto-generated)
- `freegpt-api.service` - Systemd service template

## Documentation

- `TOKEN_GUIDE.md` - Complete token management guide
- `SERVICE_GUIDE.md` - Systemd service documentation
- `QUICKSTART_TOKENS.md` - Quick token reference

## Troubleshooting

**Authentication errors:**
- Ensure token is set: `python token_manager.py list`
- Check `.env` file has correct token

**Port in use:**
- Change port in service file or use: `PORT=8001 uvicorn api:app`

**Module not found:**
- Install dependencies: `pip install -r requirements.txt`

## License

Educational purposes only. Respect GitHub's terms of service.