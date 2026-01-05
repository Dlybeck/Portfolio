# Cloud Run Deployment Guide

## Architecture Overview

This application uses **Tailscale-in-Cloud-Run** to enable access to your Ubuntu-based VS Code (code-server) from anywhere.

### Flow Diagram
```
Any Device (no Tailscale app needed)
    ↓ HTTPS (Google-managed certificate)
Cloud Run Container
    ↓ SOCKS5 proxy (localhost:1055)
    ↓ Through Tailscale network
Ubuntu Server at 100.82.216.64
    ├─ code-server (port 8888) -> VS Code Interface
    └─ ttyd (port 7681) -> Persistent Terminal (tmux)
```

## Setup

### 1. Ubuntu Server (100.82.216.64)
- **code-server**: Running on port 8888 (bind: 0.0.0.0)
- **ttyd**: Running on port 7681 (bind: 0.0.0.0)
  - Systemd service: `ttyd-terminal`
  - Critical: Must use `--interface 0.0.0.0` to be accessible from Cloud Run via Tailscale
- **tmux**: Session `portfolio-dev` managed automatically

### 2. Cloud Run
- Connects to Ubuntu via Tailscale
- Proxies requests based on path:
  - `/dev/vscode-proxy/*` -> `100.82.216.64:8888`
  - `/dev/terminal-proxy/*` -> `100.82.216.64:7681`

## Security
- **Authentication**: TOTP (Time-based One-Time Password)
- **Tokens**: JWT access/refresh tokens stored in cookies
- **Transport**: HTTPS (Cloud Run) + WireGuard (Tailscale)

## Development
- **Local URL**: `http://100.82.216.64:8080/dev`
- **Cloud URL**: `https://portfolio-app-xxx.run.app/dev`

## Troubleshooting
- **Logs**: `journalctl --user -u ttyd-terminal`
- **Restart Terminal**: `systemctl --user restart ttyd-terminal`
- **Restart App**: `python main.py` or `touch .trigger_restart`
