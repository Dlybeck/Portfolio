# Dev Server Auto-Start Setup

This folder contains scripts to easily start your dev server (code-server + FastAPI) and optionally auto-start it on Mac login.

## 📁 Files Created

1. **`start-dev-server.command`** - Double-click launcher (opens Terminal window)
2. **`start-dev-server.sh`** - Background launcher (used by auto-start)
3. **`manage-autostart.command`** - Auto-start management tool
4. **`~/Library/LaunchAgents/com.dlybeck.portfolio-dev.plist`** - Auto-start configuration

---

## 🚀 Quick Start

### Option 1: Manual Start (Double-Click)

1. In Finder, navigate to: `/Users/dlybeck/Documents/Portfolio/`
2. Double-click **`start-dev-server.command`**
3. Terminal window opens and starts both servers
4. Access at: **https://localhost:8443/dev**

### Option 2: Auto-Start on Login

1. In Finder, navigate to: `/Users/dlybeck/Documents/Portfolio/`
2. Double-click **`manage-autostart.command`**
3. Select option **1** to enable auto-start
4. Server will start automatically every time you log in

---

## 🛠️ Managing Auto-Start

Double-click **`manage-autostart.command`** and choose:

- **1) Enable auto-start** - Start server automatically on login
- **2) Disable auto-start** - Stop auto-start and stop service
- **3) Check service status** - See if servers are running
- **4) View service logs** - Debug issues
- **5) Restart service now** - Restart without rebooting

---

## 📍 Access Points

After starting the server:

- **Local HTTP**: http://localhost:8080/dev (or https://localhost:8443/dev if certs installed)
- **Tailscale IP**: http://100.84.184.84:8080/dev (or https if certs)
- **code-server**: http://localhost:8888 (local only)

**Note**: The app auto-detects HTTPS certificates in `~/certs/`. If not found, it runs on HTTP port 8080.

---

## 📋 Service Details

**What runs automatically:**
- `code-server` on port 8888 (bound to 0.0.0.0 for Tailscale access)
- FastAPI app on port 8443 (HTTPS)

**Logs stored at:**
- `/tmp/code-server.log` - code-server output
- `/tmp/portfolio-app.log` - FastAPI output
- `/tmp/portfolio-dev-stdout.log` - Auto-start service output
- `/tmp/portfolio-dev-stderr.log` - Auto-start service errors

---

## 🔧 Manual Commands (Terminal)

```bash
# Start servers manually
./start-dev-server.sh

# Check if running
lsof -ti :8888  # code-server
lsof -ti :8443  # FastAPI

# Stop servers
kill $(lsof -ti :8888) $(lsof -ti :8443)

# Enable auto-start
launchctl load ~/Library/LaunchAgents/com.dlybeck.portfolio-dev.plist

# Disable auto-start
launchctl unload ~/Library/LaunchAgents/com.dlybeck.portfolio-dev.plist

# Check auto-start status
launchctl list | grep com.dlybeck.portfolio-dev
```

---

## ⚠️ Troubleshooting

### Server won't start
```bash
# Check logs
tail -f /tmp/portfolio-dev-stderr.log
tail -f /tmp/portfolio-app.log
```

### Port already in use
```bash
# Find what's using the port
lsof -ti :8888
lsof -ti :8443

# Kill processes
kill $(lsof -ti :8888)
kill $(lsof -ti :8443)
```

### Auto-start not working
```bash
# Reload the LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.dlybeck.portfolio-dev.plist
launchctl load ~/Library/LaunchAgents/com.dlybeck.portfolio-dev.plist
```

---

## 🔐 Security Notes

- code-server binds to `0.0.0.0:8888` but is only accessible via Tailscale network (100.84.184.84)
- FastAPI uses HTTPS with self-signed certificates
- All services require authentication (JWT + 2FA)
- Services are only accessible from Tailscale network or localhost

---

## 🎯 Recommended Setup

For daily development work:

1. **Enable auto-start** (double-click `manage-autostart.command` → option 1)
2. Server starts automatically when you log in to your Mac
3. Access from any device via Cloud Run: https://portfolio-q6j7ikwabq-uw.a.run.app/dev
4. Or locally: https://localhost:8443/dev
5. Stay logged in for 7 days with automatic token refresh
