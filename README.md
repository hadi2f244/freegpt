# FreeGPT

Free access to GPT-4, using only a Github Copilot subscription.

Now with an **OpenAI-compatible API server** for seamless integration with any service that uses the OpenAI API!

## Features

- 🔓 Free GPT-4 access via GitHub Copilot
- 🌐 OpenAI-compatible REST API
- 🔄 Streaming and non-streaming support
- 🔐 Optional API key authentication
- 🧪 Full test suite
- 💬 Both CLI and API server modes

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### CLI Usage (Original)

Interactive chat interface:

```bash
python3 chat.py
```

### API Server Usage

Start the OpenAI-compatible API server:

```bash
python3 api.py
```

Or with uvicorn:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

The server will start on `http://localhost:8000` by default.

## API Documentation

### Authentication

Set an API key for secure access (optional):

```bash
export FREEGPT_API_KEY="your-secret-key"
# OR
export OPENAI_API_KEY="your-secret-key"
```

If no key is set, authentication is disabled and all requests are allowed.

### Available Endpoints

- `POST /v1/chat/completions` - Chat completions (streaming & non-streaming)
- `POST /v1/completions` - Text completions
- `GET /v1/models` - List available models
- `GET /v1/models/{model}` - Get specific model info
- `POST /v1/moderations` - Content moderation (stub)
- `GET /health` - Health check

### Available Models

- `freegpt-4` - GPT-4 (default)
- `freegpt-3.5` - GPT-3.5 Turbo
- `gpt-4` - Alias for freegpt-4
- `gpt-3.5-turbo` - Alias for freegpt-3.5

### Examples

#### Non-Streaming Chat Completion

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "freegpt-4",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "Write a haiku about programming"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 150
  }'
```

Response:

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1699564800,
  "model": "freegpt-4",
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 35,
    "total_tokens": 60
  },
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Code flows like water\nBugs emerge, then disappear\nPeace in the debugger"
      },
      "finish_reason": "stop"
    }
  ]
}
```

#### Streaming Chat Completion

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "freegpt-4",
    "messages": [
      {
        "role": "user",
        "content": "Count from 1 to 5"
      }
    ],
    "stream": true
  }'
```

Response (Server-Sent Events):

```
data: {"id":"chatcmpl-xyz789","object":"chat.completion.chunk","created":1699564800,"model":"freegpt-4","choices":[{"index":0,"delta":{"content":"1"},"finish_reason":null}]}

data: {"id":"chatcmpl-xyz789","object":"chat.completion.chunk","created":1699564800,"model":"freegpt-4","choices":[{"index":0,"delta":{"content":","},"finish_reason":null}]}

data: {"id":"chatcmpl-xyz789","object":"chat.completion.chunk","created":1699564800,"model":"freegpt-4","choices":[{"index":0,"delta":{"content":" 2"},"finish_reason":null}]}

...

data: [DONE]
```

#### Text Completion

```bash
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "freegpt-4",
    "prompt": "Once upon a time",
    "max_tokens": 50,
    "temperature": 0.8
  }'
```

#### List Models

```bash
curl http://localhost:8000/v1/models \
  -H "Authorization: Bearer your-api-key"
```

Response:

```json
{
  "object": "list",
  "data": [
    {
      "id": "freegpt-4",
      "object": "model",
      "created": 1686935002,
      "owned_by": "freegpt"
    },
    {
      "id": "freegpt-3.5",
      "object": "model",
      "created": 1686935002,
      "owned_by": "freegpt"
    }
  ]
}
```

## Using with OpenAI SDK

The API is fully compatible with the OpenAI Python SDK:

```python
from openai import OpenAI

# Point to your local FreeGPT server
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="your-api-key"  # Optional if FREEGPT_API_KEY not set
)

# Use just like the official OpenAI API
response = client.chat.completions.create(
    model="freegpt-4",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)

# Streaming example
stream = client.chat.completions.create(
    model="freegpt-4",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## Configuration

### Environment Variables

- `FREEGPT_API_KEY` or `OPENAI_API_KEY` - API key for authentication (optional)
- `PORT` - Server port (default: 8000)
- `HOST` - Server host (default: 0.0.0.0)

### Example with Custom Port

```bash
PORT=3000 python3 api.py
```

## Testing

Run the test suite:

```bash
pytest tests/test_api.py -v
```

Run with coverage:

```bash
pytest tests/test_api.py -v --cov=api --cov-report=html
```

## Architecture

```
┌─────────────┐
│   Client    │ (OpenAI SDK, curl, etc.)
└──────┬──────┘
       │ HTTP/JSON
       ▼
┌─────────────────┐
│   api.py        │ (FastAPI server)
│   - /v1/chat/   │
│   - /v1/models  │
│   - Auth        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   chat.py       │ (Core logic)
│   - GitHub      │
│     Copilot API │
│   - Token mgmt  │
└─────────────────┘
```

## Drop-in Replacement

This server can be used as a drop-in replacement for OpenAI's API in any application:

1. Start the FreeGPT API server
2. Update your application's `base_url` to point to `http://localhost:8000/v1`
3. Use your preferred model names (`freegpt-4`, `freegpt-3.5`)
4. Everything else works the same!

## License

This project is for educational purposes. Please respect GitHub's terms of service.

## Troubleshooting

### Authentication Issues

If you see authentication errors with GitHub Copilot:

1. Delete `.copilot_token` file
2. Run `python3 chat.py` to re-authenticate
3. Follow the device code flow
4. Restart the API server

### Module Not Found

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

### Port Already in Use

Change the port:

```bash
PORT=8001 python3 api.py
```

## Contributing

Contributions welcome! Please ensure tests pass before submitting PRs.

```bash
pytest tests/test_api.py -v
```