# Deploy Cloud Run Proxy - Fix OpenCode WebSocket Issue

## What Was Fixed

1. **Updated Tailscale IP**: `100.84.184.84` → `100.82.216.64`
2. **Added universal WebSocket proxy**: Now handles ALL WebSocket paths including:
   - `/pty/*` (OpenCode terminal)
   - `/session/*/message` (OpenCode chat streaming)
   - `/dev/ws/terminal` (old terminal endpoint)

## Deploy to Cloud Run

```bash
cd /home/dlybeck/Documents/portfolio/cloud_proxy

# Set your project ID
export PROJECT_ID="your-gcp-project-id"

# Deploy (assumes Tailscale OAuth already configured)
gcloud builds submit \
  --config cloudbuild.yaml \
  --project=${PROJECT_ID}
```

## After Deployment

1. Test OpenCode WebSockets:
   - Go to https://opencode.davidlybeck.com
   - Open the built-in terminal
   - Should connect without errors
   - Chat messages should stream in real-time

2. Check logs if issues persist:
   ```bash
   gcloud run services logs read dev-proxy \
     --region=us-central1 \
     --limit=100
   ```

## What This Fixes

Before: WebSocket requests to `wss://opencode.davidlybeck.com/pty/...` failed with 500 errors

After: All WebSocket paths are proxied correctly to your server at 100.82.216.64:8080
