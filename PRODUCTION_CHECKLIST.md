# Production Deployment Checklist

## Pre-Deployment

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create API Token
```bash
python token_manager.py create production
# Save the generated token securely!
```

### 3. Configure Environment
```bash
cp .env.example .env
nano .env
# Add: FREEGPT_API_KEY=sk-your-token-here
```

### 4. Test Locally
```bash
# Start server
python -m uvicorn api:app --host 127.0.0.1 --port 8000

# In another terminal, test
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-token" \
  -d '{"model":"gpt-4","messages":[{"role":"user","content":"Hello"}]}'
```

## Production Deployment

### Option 1: Systemd Service (Recommended)

```bash
# Install service
sudo ./install_service.sh

# Verify it's running
sudo systemctl status freegpt-api

# Check logs
sudo journalctl -u freegpt-api -f
```

### Option 2: Manual with Screen/Tmux

```bash
# Using screen
screen -S freegpt
./start_server.sh
# Detach: Ctrl+A, D

# Using tmux
tmux new -s freegpt
./start_server.sh
# Detach: Ctrl+B, D
```

### Option 3: Docker (Optional)

```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Build and run
docker build -t freegpt-api .
docker run -d -p 8000:8000 --env-file .env freegpt-api
```

## Security Hardening

### 1. File Permissions
```bash
chmod 600 .env
chmod 600 api_tokens.json
chmod 600 .copilot_token
```

### 2. Firewall Rules
```bash
# Allow only from localhost
sudo ufw deny 8000

# Or allow specific network
sudo ufw allow from 192.168.1.0/24 to any port 8000
```

### 3. Reverse Proxy (Nginx)
```nginx
server {
    listen 443 ssl;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /v1/ {
        proxy_pass http://localhost:8000/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. Rate Limiting (Optional)
```bash
# Install nginx rate limiting or use fail2ban
sudo apt-get install fail2ban
```

## Monitoring

### 1. Service Health
```bash
# Check if service is running
systemctl is-active freegpt-api

# Check uptime
systemctl status freegpt-api
```

### 2. Logs
```bash
# Real-time logs
sudo journalctl -u freegpt-api -f

# Last 100 lines
sudo journalctl -u freegpt-api -n 100

# Since yesterday
sudo journalctl -u freegpt-api --since yesterday
```

### 3. API Health Check
```bash
# Simple health check
curl http://localhost:8000/health

# Add to cron for monitoring
*/5 * * * * curl -f http://localhost:8000/health || mail -s "FreeGPT API Down" admin@example.com
```

## Token Rotation

### Regular Token Rotation (Recommended every 90 days)

```bash
# 1. Create new token
python token_manager.py create "production-$(date +%Y%m%d)"

# 2. Update .env with new token
nano .env

# 3. Restart service
sudo systemctl restart freegpt-api

# 4. Verify new token works
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-new-token" \
  -d '{"model":"gpt-4","messages":[{"role":"user","content":"test"}]}'

# 5. Revoke old token
python token_manager.py revoke sk-old-token-prefix
```

## Backup Strategy

### Files to Backup
```bash
# Create backup
tar -czf freegpt-backup-$(date +%Y%m%d).tar.gz \
  .env \
  api_tokens.json \
  .copilot_token

# Store securely off-server
```

### Restore from Backup
```bash
# Extract backup
tar -xzf freegpt-backup-YYYYMMDD.tar.gz

# Restart service
sudo systemctl restart freegpt-api
```

## Troubleshooting Production Issues

### Service Won't Start
```bash
# Check service status
sudo systemctl status freegpt-api

# Check detailed logs
sudo journalctl -u freegpt-api -n 100 --no-pager

# Check file permissions
ls -la /path/to/freegpt

# Test manually
cd /path/to/freegpt
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

### High Memory Usage
```bash
# Check memory usage
ps aux | grep uvicorn

# Add memory limit to service
# Edit: /etc/systemd/system/freegpt-api.service
# Add under [Service]:
MemoryLimit=512M

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart freegpt-api
```

### High CPU Usage
```bash
# Check CPU usage
top -p $(pgrep -f "uvicorn api:app")

# Add CPU limit to service
# Edit: /etc/systemd/system/freegpt-api.service
# Add under [Service]:
CPUQuota=50%

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart freegpt-api
```

## Maintenance

### Weekly Tasks
- [ ] Check logs for errors
- [ ] Verify service is running
- [ ] Test API endpoints
- [ ] Check disk space

### Monthly Tasks
- [ ] Review token usage (list last_used)
- [ ] Update dependencies if needed
- [ ] Backup configuration files
- [ ] Check for security updates

### Quarterly Tasks
- [ ] Rotate API tokens
- [ ] Review and revoke unused tokens
- [ ] Update documentation
- [ ] Performance review

## Updates and Upgrades

### Update Application Code
```bash
# Stop service
sudo systemctl stop freegpt-api

# Backup current version
cp -r /path/to/freegpt /path/to/freegpt.backup

# Pull updates (if using git)
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Test
python test_openai_sdk.py

# Restart service
sudo systemctl start freegpt-api

# Verify
sudo systemctl status freegpt-api
```

### Rollback on Failure
```bash
# Stop service
sudo systemctl stop freegpt-api

# Restore backup
rm -rf /path/to/freegpt
mv /path/to/freegpt.backup /path/to/freegpt

# Restart service
sudo systemctl start freegpt-api
```

## Support Contacts

- Documentation: See README.md, TOKEN_GUIDE.md, SERVICE_GUIDE.md
- Logs: `sudo journalctl -u freegpt-api -f`
- GitHub Issues: [Repository URL]

## Emergency Procedures

### Complete Service Failure
1. Check if service is running: `systemctl status freegpt-api`
2. Check logs: `journalctl -u freegpt-api -n 100`
3. Try manual start: `python -m uvicorn api:app`
4. If authentication issues: Check .env and api_tokens.json
5. If copilot issues: Delete .copilot_token and re-authenticate

### Data Loss
1. Stop service
2. Restore from latest backup
3. Verify files: .env, api_tokens.json, .copilot_token
4. Restart service
5. Test with curl command

### Security Breach
1. Immediately revoke all tokens: `python token_manager.py revoke [prefix]`
2. Stop service: `sudo systemctl stop freegpt-api`
3. Generate new tokens: `python token_manager.py create emergency`
4. Update all clients with new tokens
5. Review logs for suspicious activity
6. Restart service with new configuration
