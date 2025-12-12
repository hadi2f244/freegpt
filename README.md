# FreeGPT API

OpenAI-compatible API server powered by GitHub Copilot. Drop-in replacement for OpenAI API.

## Quick Start

### Docker Setup (Recommended)

#### 1. Install and Start

```bash
./install_service.sh
```

This will:
- Check Docker prerequisites
- Build the Docker image
- Start the container
- Run health checks

#### 2. GitHub Copilot Authentication (First Time Only)

```bash
docker compose run --rm freegpt-api python chat.py
```

- Follow the prompts to authenticate
- Visit the provided URL and enter the code
- After success, the token is saved automatically

#### 3. Configure Proxy (If Required)

If you need a proxy to access GitHub Copilot API:

```bash
# Edit .env file
nano .env

# Add proxy settings:
HTTP_PROXY=http://your-proxy-host:port
HTTPS_PROXY=http://your-proxy-host:port
```

Then restart:

```bash
docker compose restart
```

#### 4. Create API Token

```bash
docker compose exec freegpt-api python token_manager.py create my-app
# Save the generated token (starts with sk-)
```

#### 5. Test

```bash
./run_tests.sh
```

**Server runs at:** `http://localhost:8000`

---

### Local/Manual Setup

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2. GitHub Copilot Authentication (First Time Only)

```bash
python chat.py
```

- Follow the prompts to authenticate
- Visit the provided URL and enter the code
- After success, press Ctrl+C to exit

This creates `.copilot_token` file needed for API access.

#### 3. Configure Proxy (If Required)

```bash
# Set proxy environment variables
export HTTP_PROXY=http://your-proxy-host:port
export HTTPS_PROXY=http://your-proxy-host:port
```

#### 4. Create API Token

```bash
python token_manager.py create my-app
# Save the generated token (starts with sk-)
```

#### 5. Configure Environment

```bash
cp .env.example .env
nano .env  # Add your token: FREEGPT_API_KEY=sk-your-token
```

#### 6. Start Server

```bash
./start_server.sh
```

#### 7. Test

```bash
./run_tests.sh --local
```

**Server runs at:** `http://localhost:8000`

---

## Docker Commands

```bash
# Start/Stop
docker compose up -d              # Start in background
docker compose down               # Stop and remove containers
docker compose restart            # Restart containers

# Logs and Status
docker compose logs -f            # View live logs
docker compose ps                 # Check container status

# Execute Commands
docker compose exec freegpt-api python token_manager.py list
docker compose exec freegpt-api python chat.py

# Testing
./run_tests.sh                    # Run tests in Docker (default)
./run_tests.sh --local            # Run tests locally against Docker

# Cleanup
./uninstall_service.sh            # Remove containers
./uninstall_service.sh --images   # Also remove images
./uninstall_service.sh --all      # Remove everything
```

## Usage

### With OpenAI SDK

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
```

### With curl

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-your-token" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4","messages":[{"role":"user","content":"Hello"}]}'
```

## Commands

```bash
# Verification
./verify_setup.sh                    # Check setup status

# Token Management
python token_manager.py list         # List all tokens
python token_manager.py create name  # Create new token
python token_manager.py revoke sk-   # Revoke token

# Service Management (if installed)
sudo systemctl status freegpt-api    # Check status
sudo systemctl restart freegpt-api   # Restart
sudo journalctl -u freegpt-api -f    # View logs

# Testing
./run_tests.sh                       # Run all tests
```

## Supported Models

- `gpt-4`, `gpt-4.1`, `freegpt-4`
- `gpt-3.5-turbo`, `freegpt-3.5`

## Files & Scripts

| File | Purpose |
|------|---------|
| `chat.py` | CLI chat + Copilot authentication |
| `api.py` | OpenAI-compatible API server |
| `token_manager.py` | Manage API tokens |
| `start_server.sh` | Start server manually |
| `install_service.sh` | Install as systemd service |
| `verify_setup.sh` | Verify setup is correct |
| `run_tests.sh` | Run all tests |
| `tests/` | Test files |
| `DOCS.md` | Full documentation |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| No Copilot token | Run `python chat.py` to authenticate |
| Dependencies missing | `pip install -r requirements.txt` |
| Port already in use | `PORT=8001 ./start_server.sh` |
| Auth errors | Verify token in `.env` file |
| Server won't start | Check logs: `./verify_setup.sh` |

## License

Educational use only.