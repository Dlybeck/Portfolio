# Cloud Run Deployment Guide

## Architecture Overview

This application uses **Tailscale-in-Cloud-Run** to enable access to your Mac-based VS Code (code-server) from anywhere, without requiring Tailscale on client devices.

### Flow Diagram
```
Any Device (no Tailscale app needed)
    ↓ HTTPS (Google-managed certificate)
Cloud Run Container (has Tailscale in userspace mode)
    ↓ SOCKS5 proxy (localhost:1055)
    ↓ Through Tailscale network
Mac at 100.84.184.84 (code-server on port 8888)
    ↓
Full VS Code with Claude Code extension
```

### Key Features
- **No Tailscale required on client devices** - Access from phone, tablet, or any browser
- **Google-managed HTTPS certificates** - No security warnings
- **SOCKS5 proxy through Tailscale** - Secure connection to your Mac
- **Full VS Code in browser** - Including Claude Code extension with webviews

---

## Prerequisites

### 1. Mac Setup (Development Server)
Your Mac must be running:
- **Tailscale** with IP `100.84.184.84` on your tailnet
- **code-server** on port `8888`
- **This FastAPI app** on port `8080` (HTTP) or `8443` (HTTPS)

Start code-server:
```bash
code-server --bind-addr 127.0.0.1:8888
```

Start local FastAPI app:
```bash
python main.py
```

### 2. Tailscale OAuth Credentials
You need Tailscale OAuth credentials to allow Cloud Run to join your tailnet.

#### Generate OAuth Client:
1. Go to [Tailscale Admin Console](https://login.tailscale.com/admin/settings/oauth)
2. Click "Generate OAuth Client"
3. Set description: "Cloud Run Portfolio App"
4. Select scopes:
   - `devices:write` (to create auth keys)
5. Save the **Client ID** and **Client Secret**

#### Set as Environment Variables:
You'll need these for Cloud Run deployment:
- `TAILSCALE_OAUTH_CLIENT_ID=tsoc-client-...`
- `TAILSCALE_OAUTH_CLIENT_SECRET=tsoc-...`

---

## Deployment Steps

### 1. Set Environment Variables

The Dockerfile expects these environment variables in Cloud Run:

```bash
# Required: Tailscale OAuth
TAILSCALE_OAUTH_CLIENT_ID=tsoc-client-...
TAILSCALE_OAUTH_CLIENT_SECRET=tsoc-...

# Required: Security Configuration (from .env)
SECRET_KEY=<your-secret-key>
DASHBOARD_USERNAME=<your-username>
DASHBOARD_PASSWORD_HASH=<bcrypt-hash>
TOTP_SECRET=<your-totp-secret>

# Optional: Configuration
ACCESS_TOKEN_EXPIRE_MINUTES=720
REFRESH_TOKEN_EXPIRE_DAYS=7
MAX_LOGIN_ATTEMPTS=20
LOCKOUT_DURATION_MINUTES=15
```

### 2. Build and Deploy to Cloud Run

#### Using gcloud CLI:

```bash
# Build and deploy in one command
gcloud run deploy portfolio \
  --source . \
  --region us-west1 \
  --allow-unauthenticated \
  --set-env-vars "TAILSCALE_OAUTH_CLIENT_ID=tsoc-client-...,TAILSCALE_OAUTH_CLIENT_SECRET=tsoc-...,SECRET_KEY=...,DASHBOARD_USERNAME=...,DASHBOARD_PASSWORD_HASH=...,TOTP_SECRET=..." \
  --memory 1Gi \
  --cpu 1 \
  --timeout 3600
```

#### Using Cloud Console:
1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click "Create Service"
3. Select "Deploy one revision from an existing container image" or "Continuously deploy from a repository"
4. Configure:
   - **Region**: `us-west1`
   - **Authentication**: Allow unauthenticated invocations
   - **Container**: Use Dockerfile from this repo
   - **Environment Variables**: Set all required variables above
   - **Resources**: 1 CPU, 1 GiB memory
   - **Request timeout**: 3600 seconds (1 hour)

### 3. Verify Tailscale Connection

After deployment, check Cloud Run logs:

```bash
gcloud run services logs read portfolio --region us-west1 --limit 50
```

Look for:
```
✅ Connected to Tailscale
[CodeServerProxy] Cloud Run mode: proxying to http://100.84.184.84:8888 via SOCKS5
```

---

## How It Works

### Dockerfile Setup
The `Dockerfile` (already configured):
1. Installs Tailscale in the container
2. Runs `tailscaled` in **userspace networking mode** with SOCKS5 proxy on `localhost:1055`
3. Generates ephemeral auth keys using OAuth credentials
4. Connects to your Tailscale network with hostname `portfolio-app`
5. Starts FastAPI app

### Code-Server Proxy
The `services/code_server_proxy.py` (already configured):
- **Local mode** (Mac): Connects directly to `http://127.0.0.1:8888`
- **Cloud Run mode**: Connects to `http://100.84.184.84:8888` via SOCKS5 proxy

Automatically detects environment using `K_SERVICE` environment variable.

### Authentication Flow
1. User visits Cloud Run URL (e.g., `https://portfolio-app-xxx.run.app/dev`)
2. Redirects to `/dev/login`
3. User logs in with username, password, and 2FA code
4. JWT token stored in session cookie
5. User redirected to `/dev/terminal` → `/dev/vscode/`
6. All HTTP and WebSocket requests proxied through SOCKS5 to Mac

---

## Testing

### 1. Test Login
```bash
# Get your Cloud Run URL
gcloud run services describe portfolio --region us-west1 --format='value(status.url)'

# Visit in browser
https://portfolio-xxx.run.app/dev/login
```

### 2. Test Code-Server Access
After logging in, you should see VS Code in your browser with:
- File explorer
- Terminal access
- Claude Code extension (if installed on Mac)
- Full syntax highlighting and IntelliSense

### 3. Debug Connectivity
Visit the debug endpoint (requires authentication):
```
https://portfolio-app-xxx.run.app/dev/debug/connectivity
```

Should return:
```json
{
  "mac_ip": "100.84.184.84",
  "mac_port": 8888,
  "mac_url": "http://100.84.184.84:8888",
  "socket_test": {"success": true, "error_code": 0},
  "http_test": {"status": 200, "success": true},
  "is_available": true
}
```

---

## Troubleshooting

### Issue: "Tailscale connection failed"
**Cause**: OAuth credentials invalid or expired.

**Fix**:
1. Regenerate OAuth client in Tailscale Admin Console
2. Update Cloud Run environment variables
3. Redeploy

### Issue: "Mac server unavailable"
**Cause**: Mac is offline or code-server not running.

**Fix**:
1. Ensure Mac is online and connected to Tailscale
2. Check Mac's Tailscale IP: `tailscale ip -4`
3. Ensure code-server is running: `ps aux | grep code-server`
4. Update `MAC_SERVER_IP` in `apis/route_dev.py` if IP changed

### Issue: "WebSocket connection failed"
**Cause**: SOCKS5 proxy not working or firewall blocking.

**Fix**:
1. Check Cloud Run logs for SOCKS5 errors
2. Verify Mac allows incoming connections on port 8888
3. Test with `curl` from Cloud Run container

### Issue: "Authentication loop"
**Cause**: Cookie not being set or token expired.

**Fix**:
1. Clear browser cookies
2. Check `ACCESS_TOKEN_EXPIRE_MINUTES` is set correctly
3. Verify time sync on Mac and Cloud Run

---

## Updating Mac IP Address

If your Mac's Tailscale IP changes:

1. Update `MAC_SERVER_IP` in:
   - `apis/route_dev.py` (line 21)
   - `services/code_server_proxy.py` (line 20)

2. Redeploy to Cloud Run:
```bash
gcloud run deploy portfolio --source . --region us-west1
```

---

## Security Notes

### Authentication
- **JWT tokens** with configurable expiration
- **2FA required** using TOTP (Google Authenticator)
- **bcrypt password hashing**
- **Rate limiting** with account lockout after failed attempts

### Network Security
- **Tailscale encryption** for all traffic between Cloud Run and Mac
- **HTTPS by default** with Google-managed certificates
- **No public ports exposed** on Mac (code-server only listens on localhost)

### Session Management
- **Automatic session cleanup** after 1 hour of inactivity
- **Multiple device support** with session sharing
- **WebSocket keepalive** to prevent timeout

---

## Cost Estimation

### Cloud Run Costs
- **CPU**: 1 vCPU @ $0.00002400/vCPU-second
- **Memory**: 1 GiB @ $0.00000250/GiB-second
- **Requests**: First 2 million free, then $0.40/million

**Estimated monthly cost**: $5-15 depending on usage

### Tailscale Costs
- **Free tier**: Up to 3 users, 100 devices
- **Personal Pro**: $48/year for more devices

---

## Local Testing (Simulating Cloud Run)

Test Cloud Run mode locally:

```bash
# Set Cloud Run environment variable
export K_SERVICE=local-test

# Set Tailscale OAuth (use your actual credentials)
export TAILSCALE_OAUTH_CLIENT_ID=tsoc-client-...
export TAILSCALE_OAUTH_CLIENT_SECRET=tsoc-...

# Run app
python main.py
```

The app will:
1. Use SOCKS5 proxy for all connections
2. Connect to Mac at `100.84.184.84` instead of localhost
3. Behave exactly like Cloud Run environment

---

## Files Modified

### Core Changes
- `Dockerfile` - Tailscale installation and SOCKS5 setup
- `services/code_server_proxy.py` - SOCKS5 proxy support for HTTP and WebSocket
- `apis/route_dev.py` - Removed temporary redirects, unified routing
- `main.py` - Environment detection and HTTPS support

### Configuration
- `requirements.txt` - Already includes `aiohttp` and `aiohttp-socks`
- `.env` - Security credentials (not in repo)

---

## Next Steps

1. ✅ Deploy to Cloud Run with Tailscale OAuth credentials
2. ✅ Test login and authentication
3. ✅ Verify code-server access through Cloud Run URL
4. 📱 Access from phone/tablet without Tailscale app
5. 🚀 Share Cloud Run URL with team (optional)

---

## Support

For issues:
1. Check Cloud Run logs: `gcloud run services logs read portfolio`
2. Check Mac logs: `tail -f /tmp/portfolio.log`
3. Visit debug endpoint: `/dev/debug/connectivity`
4. Review Tailscale status: `tailscale status`
