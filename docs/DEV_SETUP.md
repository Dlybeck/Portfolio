# Portfolio Dev Environment Setup Guide

This guide explains how to run the Portfolio dev environment locally and deploy to Google Cloud Run.

## Architecture Overview

The dev environment consists of three main components:

1. **FastAPI Server** (port 8080/8443) - Main backend server
   - Serves authentication, API endpoints, and dev dashboard
   - Proxies requests to code-server and Agor
   - Runs locally or in Google Cloud Run

2. **code-server** (port 8888) - VS Code in browser
   - Full VS Code experience with all extensions
   - Managed by macOS LaunchAgent for auto-start
   - Accessible via FastAPI proxy at `/dev/vscode`

3. **Agor** (port 3030) - AI-powered collaborative coding
   - Multi-agent AI coding environment
   - Spatial canvas for parallel development tasks
   - Accessible via FastAPI proxy at `/dev/agor`

## Quick Start (Local Development)

### Prerequisites

1. **Python 3.13+** - Check: `python3 --version`
2. **code-server** - Install: `brew install code-server`
3. **Agor** - Install: `npm install -g agor-live`
4. **Node.js** - Required for Agor

### Starting Everything

Simply run:

```bash
./start-local-dev.sh
```

This script will:
- ✓ Activate Python virtual environment
- ✓ Install dependencies if needed
- ✓ Configure code-server on port 8888
- ✓ Initialize and start Agor on port 3030
- ✓ Start FastAPI server on port 8080 (HTTP) or 8443 (HTTPS)

**Access Points:**
- Dev Dashboard: http://localhost:8080/dev (or https://localhost:8443/dev)
- VS Code Direct: http://localhost:8888
- Agor Direct: http://localhost:3030

### Stopping Everything

```bash
./stop-local-dev.sh
```

To also stop code-server LaunchAgent:
```bash
launchctl unload ~/Library/LaunchAgents/com.coder.code-server.plist
```

## Manual Setup (if needed)

### 1. Python Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Security Configuration

```bash
# Generate JWT secrets and create admin user
python setup_security.py
```

Follow the prompts to set up your admin credentials.

### 3. code-server Setup

The startup script handles this, but manually:

```bash
# Create config
mkdir -p ~/.config/code-server
cat > ~/.config/code-server/config.yaml << EOF
bind-addr: 0.0.0.0:8888
auth: none
cert: false
EOF

# Start code-server
code-server --bind-addr 0.0.0.0:8888 --auth none
```

### 4. Agor Setup

```bash
# Initialize Agor database
agor init

# Start daemon
agor daemon start

# Open UI (optional, usually accessed via proxy)
agor open
```

### 5. Start FastAPI Server

```bash
# HTTP mode
python main.py

# The server auto-detects SSL certificates in ~/.ssl/
# and switches to HTTPS on port 8443
```

## HTTPS Setup (Optional)

Generate self-signed certificates for local HTTPS:

```bash
mkdir -p ~/.ssl
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout ~/.ssl/key.pem \
  -out ~/.ssl/cert.pem \
  -days 365 \
  -subj "/CN=localhost"
```

The server will automatically use HTTPS on port 8443.

## Cloud Deployment (Google Cloud Run)

### Prerequisites

1. **Google Cloud SDK** - Install: `brew install --cask google-cloud-sdk`
2. **Tailscale OAuth Credentials** - For connecting Cloud Run to your Mac
   - Go to https://login.tailscale.com/admin/settings/oauth
   - Create OAuth client
   - Set as environment variables

### Deploy to Cloud Run

```bash
# Set Tailscale OAuth credentials
export TAILSCALE_OAUTH_CLIENT_ID="your-client-id"
export TAILSCALE_OAUTH_CLIENT_SECRET="your-client-secret"

# Deploy
gcloud run deploy portfolio \
  --source . \
  --region us-west1 \
  --allow-unauthenticated \
  --set-env-vars="TAILSCALE_OAUTH_CLIENT_ID=$TAILSCALE_OAUTH_CLIENT_ID,TAILSCALE_OAUTH_CLIENT_SECRET=$TAILSCALE_OAUTH_CLIENT_SECRET"
```

The Dockerfile handles:
- Installing Tailscale
- Generating ephemeral auth keys
- Starting SOCKS5 proxy
- Connecting to your Tailscale network
- Starting FastAPI server

### How Cloud Proxy Works

When deployed to Cloud Run:

1. **Tailscale Connection**
   - Cloud Run instance connects to your Tailscale network
   - Creates SOCKS5 proxy on localhost:1055
   - Allows Cloud Run to reach your Mac at 100.84.184.84

2. **Service Discovery**
   - FastAPI detects Cloud Run via `K_SERVICE` env variable
   - Switches to proxy mode automatically
   - All requests to code-server/Agor go through SOCKS5

3. **Request Flow**
   ```
   Browser → Cloud Run (FastAPI) → SOCKS5 Proxy → Tailscale → Mac (code-server/Agor)
   ```

### Environment-Specific Behavior

The code auto-detects environment via `IS_CLOUD_RUN = os.environ.get("K_SERVICE") is not None`:

**Local Mode:**
- Direct connections to localhost:8888 (code-server) and localhost:3030 (Agor)
- No SOCKS5 proxy
- Fast, low-latency

**Cloud Run Mode:**
- Proxies through Tailscale SOCKS5
- Connects to Mac at 100.84.184.84
- Handles connection pooling and retries

## Troubleshooting

### code-server not accessible

```bash
# Check if running
lsof -i :8888

# Check config
cat ~/.config/code-server/config.yaml

# Restart via LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.coder.code-server.plist
launchctl load ~/Library/LaunchAgents/com.coder.code-server.plist

# Or start manually
code-server --bind-addr 0.0.0.0:8888 --auth none
```

### Agor not starting

```bash
# Check if initialized
ls -la ~/.local/share/agor/

# Initialize if needed
agor init

# Start daemon
agor daemon start

# Check logs
tail -f /tmp/agor-daemon.log
```

### FastAPI server issues

```bash
# Check if port is in use
lsof -i :8080  # or :8443 for HTTPS

# Check .env configuration
cat .env

# Run security setup if needed
python setup_security.py

# Check logs when starting
python main.py
```

### Port conflicts

If ports 8080, 8443, 8888, or 3030 are in use:

```bash
# Find what's using the port
lsof -i :8888

# Kill process
kill -9 <PID>
```

## Development Workflow

### Typical Local Development

1. Start everything: `./start-local-dev.sh`
2. Open browser: http://localhost:8080/dev
3. Switch between VS Code, Agor, and Terminal tabs
4. Make changes, test locally
5. Stop when done: `./stop-local-dev.sh`

### Testing Cloud Deployment

1. Make changes locally
2. Test locally first
3. Commit changes
4. Deploy to Cloud Run
5. Test at Cloud Run URL

## File Structure

```
Portfolio/
├── main.py                    # FastAPI application entry point
├── start-local-dev.sh         # 🆕 One-command startup
├── stop-local-dev.sh          # 🆕 Stop all services
├── start-dev-server.sh        # Legacy code-server script
├── Dockerfile                 # Cloud Run deployment
├── requirements.txt           # Python dependencies
├── .env                       # Security configuration (not committed)
│
├── apis/
│   ├── route_dev.py          # Dev dashboard routes & proxies
│   ├── route_auth.py         # Authentication
│   └── ...
│
├── services/
│   ├── code_server_proxy.py  # VS Code proxy
│   ├── agor_proxy.py         # Agor proxy
│   ├── session_manager.py    # Terminal sessions
│   └── socks5_connection_manager.py  # Cloud Run SOCKS5
│
├── templates/dev/
│   ├── dev_dashboard.html    # Main dashboard with tabs
│   ├── dashboard_old.html    # Terminal view
│   └── login.html            # Auth page
│
└── core/
    ├── security.py           # JWT authentication
    └── config.py             # App configuration
```

## Security Notes

- **Local Development**: No authentication on code-server/Agor for convenience
- **Production**: All endpoints require JWT authentication
- **Tokens**: Auto-refresh every 6 days (7-day expiry)
- **Sessions**: WebSocket connections require token validation
- **CORS**: Restricted to same-origin requests

## Next Steps

After starting the dev environment:

1. **First Time**: Run `python setup_security.py` to create admin user
2. **Login**: Go to http://localhost:8080/dev/login
3. **Explore**: Switch between VS Code, Agor, and Terminal
4. **Develop**: Make changes and test
5. **Deploy**: Push to Cloud Run when ready

## Support

For issues:
1. Check service status: `ps aux | grep -E "uvicorn|code-server|agor"`
2. Check logs: `/tmp/code-server.log`, `/tmp/agor-daemon.log`
3. Restart services: `./stop-local-dev.sh && ./start-local-dev.sh`
4. Review this guide: `DEV_SETUP.md`
