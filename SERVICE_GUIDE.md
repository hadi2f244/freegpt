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
