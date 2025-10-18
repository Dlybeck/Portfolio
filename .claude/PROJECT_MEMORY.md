# Project Memory

## Deployment Process

**IMPORTANT**: This project uses **automatic CI/CD deployment**.

- **When code is pushed to `main` branch**, it automatically triggers a rebuild and deployment to Cloud Run
- **DO NOT manually deploy** using `gcloud run deploy` from local environment
- **Workflow**:
  1. Make changes locally
  2. Commit and push to `main`
  3. Cloud Run automatically rebuilds and deploys

## Cloud Run Configuration

- **Service Name**: `portfolio-app`
- **Region**: `us-central1`
- **Project**: `portfolio-446922`
- **Environment Variables**: Already configured in Cloud Run, including:
  - `TAILSCALE_OAUTH_CLIENT_ID`
  - `TAILSCALE_OAUTH_CLIENT_SECRET` (stored as secret)
  - Security credentials (SECRET_KEY, DASHBOARD_USERNAME, etc.)

## Tailscale Setup

- **Mac Tailscale IP**: `100.84.184.84`
- **code-server port**: `8888` (localhost only)
- **Tailscale domain**: `davids-macbook-pro.tail1e7db.ts.net`
- **OAuth credentials**: Already configured in Cloud Run environment

## Architecture

```
Any Device (no Tailscale app needed)
    ↓ HTTPS via Cloud Run URL
Cloud Run (has Tailscale via OAuth)
    ↓ SOCKS5 proxy (localhost:1055)
    ↓ Through Tailscale network
Mac at 100.84.184.84 (code-server on port 8888)
    ↓ Full VS Code with Claude Code extension
```

## Local Development

- **Main app**: `python main.py` (auto-detects HTTPS certificates)
- **code-server**: `code-server --bind-addr 0.0.0.0:8888` (**IMPORTANT**: Must bind to 0.0.0.0, NOT 127.0.0.1, so Cloud Run can reach it via Tailscale)
- **Local access**: `https://localhost:8443/dev` or `https://100.84.184.84:8443/dev`
- **Environment detection**: Uses `K_SERVICE` env var to detect Cloud Run vs local
- **Security Note**: code-server on 0.0.0.0:8888 is only accessible via Tailscale network (100.84.184.84), not public internet

## Key Files

- `Dockerfile`: Already configured with Tailscale userspace networking and SOCKS5
- `services/code_server_proxy.py`: Auto-detects environment, uses SOCKS5 in Cloud Run
- `apis/route_dev.py`: Unified routing for both environments
- `DEPLOYMENT.md`: Complete deployment guide

## Git Workflow

- **Branch**: `main`
- **Remote**: `origin` (GitHub: Dlybeck/Portfolio)
- **Commit**: Always include detailed messages with architecture changes
- **Push**: Triggers automatic Cloud Run deployment

## Security

- JWT tokens with 2FA (TOTP)
- bcrypt password hashing
- Rate limiting with account lockout
- Session management (1 hour idle timeout)
- All credentials stored in .env (not in repo)
