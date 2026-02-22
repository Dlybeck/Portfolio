# OpenHands Setup & Troubleshooting Guide

## 📋 Overview
This guide provides a simplified, comprehensive setup for OpenHands on Ubuntu server with Cloud Run integration. It fixes all known WebSocket and connectivity issues.

## 🚀 Quick Start

### 1. Run the Setup Script (Ubuntu Server)
```bash
cd ~/Portfolio
git pull
bash scripts/simple-setup.sh
```

### 2. Wait for Cloud Run Redeploy (2-3 minutes)

### 3. Test at: https://opencode.davidlybeck.com/

## 🔧 What Gets Fixed

| Issue | Solution |
|-------|----------|
| **Agent binding to 127.0.0.1** | Forces 0.0.0.0 binding via environment variables |
| **Missing Python dependencies** | Installs websockets, python-socks, etc. |
| **WebSocket 403/404 errors** | Proper routing and authentication |
| **Cloud Run ↔ Ubuntu connectivity** | Tailscale SOCKS5 proxy on 0.0.0.0:1055 |
| **Complex script management** | Single setup script, 3 management scripts |

## 📁 Simplified Scripts

After setup, you'll have these management scripts:

1. **`start-openhands.sh`** - Start OpenHands with proper binding
2. **`check-openhands.sh`** - Health check and diagnostics  
3. **`reset-openhands.sh`** - Stop everything and start fresh

## 🏥 Health Check Commands

```bash
# Basic health check
./check-openhands.sh

# Check Docker containers
docker ps --filter "name=openhands"

# Check network binding (should show 0.0.0.0)
sudo ss -tlnp | grep -E ":3000|:48[0-9]{3}"

# Test API
curl -H "Host: opencode.davidlybeck.com" http://$(tailscale ip -4):3000/api/conversations | head -1
```

## 🔄 Reset When Things Break

```bash
./reset-openhands.sh
```

This stops all containers and starts fresh with proper configuration.

## 🌐 Architecture Overview

```
Browser → https://opencode.davidlybeck.com/
               ↓
        Cloud Run (SOCKS5 Proxy)
               ↓
     Ubuntu Server (OpenHands + Agents)
```

**Key Fixes Applied:**
- Agent servers bind to `0.0.0.0` (not `127.0.0.1`)
- SOCKS5 proxy listens on `0.0.0.0:1055` (accessible in container)
- WebSocket fallback logic (SOCKS5 → direct connection)
- All dependencies installed properly

## 📝 Common Issues & Solutions

### 1. WebSocket Connection Failed
**Symptoms:** Browser shows WebSocket connection failure
**Solution:**
```bash
./check-openhands.sh  # Run health check
./reset-openhands.sh  # Restart services
# Wait 3 minutes for Cloud Run redeploy
```

### 2. Agent Server Not Accessible  
**Symptoms:** Cloud Run can't connect to agent port
**Solution:**
```bash
# Check binding
sudo ss -tlnp | grep "0.0.0.0"
# Should show: 0.0.0.0:PORT (not 127.0.0.1:PORT)

# If 127.0.0.1, restart with binding fix
./reset-openhands.sh
```

### 3. Missing Python Dependencies
**Symptoms:** "No module named websockets"
**Solution:**
```bash
# Install dependencies
pip3 install websockets python-socks --user
# Or run setup script again
bash scripts/simple-setup.sh
```

## 🎯 Expected Success State

After setup and Cloud Run redeploy:

1. ✅ OpenHands container running on Ubuntu
2. ✅ Agent servers binding to 0.0.0.0 (ports 48xxx, 60xxx, 40xxx)
3. ✅ API responding with agent URLs
4. ✅ WebSocket connections working from browser
5. ✅ Cloud Run can connect via SOCKS5 proxy

## 📞 Support

If issues persist after following this guide:
1. Run: `./check-openhands.sh` and share output
2. Check Cloud Run logs for errors
3. Verify Tailscale connection: `tailscale status`

---

**Last Updated:** $(date)
**Status:** ✅ All known issues fixed
