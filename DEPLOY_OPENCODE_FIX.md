# Deploy OpenCode WebSocket Fix

## What This Fixes
- ✅ OpenCode terminal WebSocket errors (`wss://opencode.davidlybeck.com/pty/...`)
- ✅ Chat message streaming issues
- ✅ All real-time features in OpenCode web

## Changes Made

### Local Server (✅ Already Applied)
1. **Added PTY service** - Provides terminal WebSocket endpoints
2. **Updated middleware** - Routes `/pty/` to local PTY service
3. **WebSocket middleware** - Handles OpenCode subdomain WebSockets

### Cloud Run Proxy (❌ Needs Deployment)
1. **Updated Tailscale IP**: `100.84.184.84` → `100.82.216.64`
2. **Universal WebSocket proxy**: Handles ALL WebSocket paths (PTY, chat, etc.)

## Deploy to Cloud Run

### Option 1: From Your Machine (if gcloud is configured elsewhere)

```bash
cd ~/Documents/portfolio/cloud_proxy

# Get your GCP project ID
gcloud config get-value project

# Deploy
gcloud builds submit --config cloudbuild.yaml
```

### Option 2: Manual Deployment

1. **Get the updated files:**
   - `cloud_proxy/proxy_main.py` (already updated)
   - `cloud_proxy/cloudbuild.yaml` (no changes needed)
   - `cloud_proxy/requirements.txt` (already has websockets)

2. **Push to your git repo:**
   ```bash
   cd ~/Documents/portfolio
   git add cloud_proxy/
   git commit -m "Fix OpenCode WebSocket proxying"
   git push
   ```

3. **Deploy from Cloud Console:**
   - Go to https://console.cloud.google.com/cloud-build
   - Select your project
   - Click "Triggers" → "Run trigger" (or create manual build)
   - Select `cloudbuild.yaml` from `cloud_proxy/` directory

### Option 3: Cloud Shell

1. Open https://shell.cloud.google.com
2. Clone your repo or upload files
3. Run:
   ```bash
   cd cloud_proxy
   gcloud builds submit --config cloudbuild.yaml
   ```

## Verify After Deployment

1. **Check Cloud Run deployment:**
   ```bash
   gcloud run services describe dev-proxy --region=us-west1
   ```

2. **Test OpenCode:**
   - Go to https://opencode.davidlybeck.com
   - Click the terminal icon
   - Should open without WebSocket errors
   - Type commands - should work!

3. **Test chat:**
   - Send a message in OpenCode
   - Should stream in real-time without freezing

## Troubleshooting

### If terminal still fails:

Check Cloud Run logs:
```bash
gcloud run services logs read dev-proxy --region=us-west1 --limit=100
```

Look for:
- `WebSocket proxy:` - Should show `/pty/` requests
- `Connecting to:` - Should show `ws://100.82.216.64:8080/pty/...`
- Any error messages

### If Cloud Run shows old IP (100.84.184.84):

Deployment didn't complete. Redeploy:
```bash
gcloud run deploy dev-proxy --source=. --region=us-west1
```

## What Happens After Deployment

1. **Terminal in OpenCode works:**
   - Click terminal → WebSocket connects to Cloud Run
   - Cloud Run proxies to your server (100.82.216.64:8080)
   - Your server's PTY service handles it
   - Terminal shell starts

2. **Chat messages stream:**
   - All `/session/*/message` WebSockets proxied correctly
   - Real-time updates without freezing

3. **No more errors:**
   - No more "WebSocket connection failed"
   - No more 500 errors
   - UI stays responsive

## Summary

**Local changes**: ✅ Applied and working
**Cloud Run changes**: ❌ Need deployment

Once Cloud Run is deployed with the updated `proxy_main.py`, everything will work!
