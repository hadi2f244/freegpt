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
   - No tokens in `data/api_tokens.json`
   - All requests allowed

2. **Environment variable only**
   - Set `FREEGPT_API_KEY` or `OPENAI_API_KEY`
   - Only that key will work

3. **Token file + Environment variable**
   - Both environment key AND tokens from file are valid
   - Any valid token will authenticate

## Security Best Practices

1. **Never commit tokens to git**
   - `data/api_tokens.json` is in `.gitignore`
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
mv data/api_tokens.json data/api_tokens.json.backup
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
# FreeGPT API Systemd Service

This guide explains how to run the FreeGPT API as a systemd service that starts automatically on system boot.

## Quick Installation

```bash
# Stop any running instance first
pkill -f "uvicorn api:app" || true

# Install the service
sudo ./install_service.sh
```

That's it! The API will now:
- ✅ Start automatically on system boot
- ✅ Restart automatically if it crashes
- ✅ Run in the background as a service
- ✅ Log to systemd journal

## Service Management

### Check Status
```bash
sudo systemctl status freegpt-api
```

### Start Service
```bash
sudo systemctl start freegpt-api
```

### Stop Service
```bash
sudo systemctl stop freegpt-api
```

### Restart Service
```bash
sudo systemctl restart freegpt-api
```

### View Logs
```bash
# View recent logs
sudo journalctl -u freegpt-api -n 50

# Follow logs in real-time
sudo journalctl -u freegpt-api -f

# View logs since today
sudo journalctl -u freegpt-api --since today
```

## Configuration

### Service File Location
- Service file: `/etc/systemd/system/freegpt-api.service`
- Working directory: `/home/h.azaddel@asax.local/code/asax/freegpt`

### Environment Variables

The service loads environment variables from `.env` file in the project directory.

Edit `.env` to configure:
```bash
nano /home/h.azaddel@asax.local/code/asax/freegpt/.env
```

Example `.env`:
```bash
FREEGPT_API_KEY=sk-your-token-here
# Or leave empty to disable authentication
```

After changing `.env`, restart the service:
```bash
sudo systemctl restart freegpt-api
```

### Change Port or Host

Edit the service file:
```bash
sudo nano /etc/systemd/system/freegpt-api.service
```

Find the line:
```ini
ExecStart=/usr/bin/python3 -m uvicorn api:app --host 0.0.0.0 --port 8000
```

Change to your desired host/port:
```ini
ExecStart=/usr/bin/python3 -m uvicorn api:app --host 127.0.0.1 --port 8080
```

Then reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart freegpt-api
```

## Troubleshooting

### Service won't start

Check the status and logs:
```bash
sudo systemctl status freegpt-api
sudo journalctl -u freegpt-api -n 100
```

Common issues:

1. **Port already in use**
   ```bash
   # Find what's using port 8000
   sudo lsof -i :8000

   # Kill it or change the service port
   ```

2. **Missing dependencies**
   ```bash
   cd /home/h.azaddel@asax.local/code/asax/freegpt
   pip install -r requirements.txt
   ```

3. **Permission issues**
   ```bash
   # Check file ownership
   ls -la /home/h.azaddel@asax.local/code/asax/freegpt

   # Fix if needed
   sudo chown -R h.azaddel@asax.local:h.azaddel@asax.local /home/h.azaddel@asax.local/code/asax/freegpt
   ```

### View detailed logs

```bash
# All logs with timestamps
sudo journalctl -u freegpt-api --no-pager

# Logs with errors only
sudo journalctl -u freegpt-api -p err

# Export logs to file
sudo journalctl -u freegpt-api > freegpt-api.log
```

### Service keeps restarting

Check for errors in the code:
```bash
# Run manually to see errors
cd /home/h.azaddel@asax.local/code/asax/freegpt
python3 -m uvicorn api:app --host 0.0.0.0 --port 8000
```

## Testing the Service

After installation, test the API:

```bash
# Get your API token
python token_manager.py list

# Test with curl
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR-TOKEN-HERE" \
  -d '{
    "model": "gpt-4.1",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

Or use the test script:
```bash
python test_openai_sdk.py
```

## Uninstallation

To remove the service:
```bash
sudo ./uninstall_service.sh
```

This will:
- Stop the service
- Disable it from starting on boot
- Remove the systemd service file

Your code and data will remain intact.

## Auto-start on Boot

The service is configured to start automatically on boot. To verify:

```bash
# Check if enabled
sudo systemctl is-enabled freegpt-api

# Should output: enabled
```

To disable auto-start:
```bash
sudo systemctl disable freegpt-api
```

To re-enable:
```bash
sudo systemctl enable freegpt-api
```

## Security Considerations

1. **API Tokens**: Keep your tokens in `.env` and ensure proper file permissions:
   ```bash
   chmod 600 /home/h.azaddel@asax.local/code/asax/freegpt/.env
   ```

2. **Firewall**: If exposing to network, consider firewall rules:
   ```bash
   # Allow only from localhost
   sudo ufw deny 8000

   # Or allow specific IPs
   sudo ufw allow from 192.168.1.0/24 to any port 8000
   ```

3. **HTTPS**: For production, use a reverse proxy (nginx/apache) with SSL:
   ```nginx
   # Example nginx config
   location /v1/ {
       proxy_pass http://localhost:8000/v1/;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
   }
   ```

## Advanced Configuration

### Run on Different User

Edit the service file:
```bash
sudo nano /etc/systemd/system/freegpt-api.service
```

Change:
```ini
User=your-username
Group=your-username
WorkingDirectory=/path/to/your/freegpt
```

### Add Resource Limits

Add to `[Service]` section:
```ini
# Limit memory usage
MemoryLimit=1G

# Limit CPU usage
CPUQuota=50%

# Limit file descriptors
LimitNOFILE=4096
```

### Custom Environment Variables

Add to `[Service]` section:
```ini
Environment="CUSTOM_VAR=value"
Environment="ANOTHER_VAR=value"
```

## Support

For issues, check:
1. Service logs: `sudo journalctl -u freegpt-api -f`
2. System logs: `sudo journalctl -xe`
3. Application test: `python test_openai_sdk.py`
