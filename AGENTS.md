# Portfolio Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-02

**Constitution**: All development must comply with the 6 core principles defined in `.specify/memory/constitution.md`:
- I. Simplicity & Code Cleanliness
- II. Test-First Development (MANDATORY)
- III. DRY (Don't Repeat Yourself)
- IV. Observability
- V. Documentation
- VI. Security & Public Exposure

## Active Technologies

- Python 3.11+ + FastAPI, aiohttp, websockets, httpx, python-socks (002-codebase-cleanup)

## Project Structure

```text
src/
tests/
```

## Commands

```bash
# Run tests
pytest

# Lint code
ruff check .

# Run type checking
mypy .
```

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes

- 002-codebase-cleanup: Added Python 3.11+ + FastAPI, aiohttp, websockets, httpx, python-socks

<!-- MANUAL ADDITIONS START -->

## Lessons Learned: OpenHands WebSocket & Cloud Run Integration

### Critical Issues & Solutions

1. **Agent Server Binding** (Root Cause of 403/404)
   - **Problem**: OpenHands agent servers bind to `127.0.0.1` by default
   - **Solution**: Set ALL binding environment variables to `0.0.0.0`:
     ```bash
     -e BIND_ADDRESS=0.0.0.0 \
     -e HOST=0.0.0.0 \
     -e LISTEN_HOST=0.0.0.0 \
     -e AGENT_SERVER_BIND_ADDRESS=0.0.0.0 \
     -e AGENT_SERVER_HOST=0.0.0.0 \
     -e AGENT_ENV_BIND_ADDRESS=0.0.0.0 \
     -e AGENT_ENV_HOST=0.0.0.0
     ```

2. **Cloud Run ↔ Ubuntu Connectivity**
   - **Problem**: Cloud Run container can't reach `127.0.0.1` on Ubuntu
   - **Solution**: Tailscale SOCKS5 proxy listening on `0.0.0.0:1055` (not `localhost`)
   - **Fix in `cloud_run_entrypoint.sh`**: `tailscaled --socks5-server=0.0.0.0:1055`

3. **WebSocket Authentication**
   - **Problem**: Agent server rejects WebSocket with 403
   - **Solution**: Ensure `session_api_key` is passed in query params
   - **Path**: `/sockets/events/{id}?session_api_key={key}`

4. **Python Dependencies for Diagnostics**
   - **Problem**: "No module named websockets" when running diagnostics
   - **Solution**: Install with `pip3 install websockets python-socks --user`
   - **Better**: Use Ubuntu package: `sudo apt install python3-websockets`

### Simplified Management Scripts

After debugging, created minimal management scripts:

| Script | Purpose |
|--------|---------|
| `simple-setup.sh` | One-command fix for all issues |
| `start-openhands.sh` | Start with proper binding |
| `check-openhands.sh` | Health check and diagnostics |
| `reset-openhands.sh` | Stop everything and start fresh |

### Key Commands for Troubleshooting

```bash
# Check binding (MUST show 0.0.0.0)
sudo ss -tlnp | grep -E ":3000|:48[0-9]{3}"

# Test API
curl -H "Host: opencode.davidlybeck.com" http://$(tailscale ip -4):3000/api/conversations

# View logs
docker logs openhands-app
```

### Success Checklist
- [ ] OpenHands container running (`docker ps | grep openhands`)
- [ ] Port 3000 binding to `0.0.0.0` (not `127.0.0.1`)
- [ ] Agent ports (48xxx, 60xxx, 40xxx) binding to `0.0.0.0`
- [ ] API returns agent URLs with `localhost:PORT`
- [ ] Cloud Run logs show successful SOCKS5 connection
- [ ] Browser WebSocket connects at `opencode.davidlybeck.com`

### Additional Fixes (2026-02-22)
- **Python dependency installation**: Added fallback to Ubuntu packages (`python3-websockets`) and better error handling
- **Container cleanup**: Changed to `docker rm -f` to force remove existing containers
- **Docker permissions**: Added warning when user not in docker group
- **Health checks**: Improved diagnostics and reset scripts

**Last Debugged**: 2026-02-22 (WebSocket 403/404 issues resolved)
<!-- MANUAL ADDITIONS END -->
