# OpenCode Remote UI Message Display Issue

## Issue Summary

**Status**: Root cause identified - upstream OpenCode bug  
**Severity**: Medium (workaround available)  
**Affected**: Remote access via opencode.davidlybeck.com  
**Local Access**: Works correctly  

---

## Symptoms

- ✅ Messages send successfully (backend processes them)
- ✅ User receives "request complete" notifications  
- ❌ Messages do not appear in UI chat window
- ❌ Error toast shows "Failed to send prompt" or similar
- ✅ Refreshing page shows messages were actually sent

---

## Root Cause

**OpenCode Issue #12453** - Frontend fetch handling bug in version 1.1.53

### Technical Details

The `/session/{id}/message` endpoint behavior changed in 1.1.53:

1. **Immediate Response**: POST returns 200 OK immediately with **empty body**
2. **Delayed Content**: Response body not written until AI completes (minutes)
3. **Browser Timeout**: Fetch API sees "success" but no body content → triggers error
4. **SSE Works**: Backend correctly sends results via `/global/event` stream
5. **UI Failure**: Frontend fetch handler already errored, doesn't process SSE updates

### Why It Appears to Work Locally

Local access (localhost:4096) uses a different code path or timing that masks the issue. The bug specifically affects:
- Remote proxy access (Cloud Run → Tailscale → Ubuntu)
- Version 1.1.53 specifically
- The streaming POST response handling

---

## Investigation Evidence

### Infrastructure Verification (All ✅)

| Component | Status | Evidence |
|-----------|--------|----------|
| Local OpenCode (:4096) | ✅ Working | `/tmp/sse_baseline_local.txt` |
| Portfolio Proxy (:8080) | ✅ Working | `/tmp/sse_proxy_local.txt` |
| SSE Streaming | ✅ Working | Events captured in all layers |
| Cloud Run | ✅ Working | Remote access succeeds |
| Tailscale | ✅ Working | Connection established |
| Browser SSE | ✅ Working | EventSource to /global/event (200 OK) |

### Browser Console Analysis

**CSP Violation** (Non-critical):
```
[ERROR] Loading a manifest from 'https://davidlybeck.com/manifest.json' has been blocked...
```

- Manifest.json redirect triggers CSP block
- Does NOT affect message sending/receiving
- Minor cosmetic issue only

**SSE Connection**: ✅ Established successfully (200 OK)

### Key Finding

**Infrastructure is NOT the problem.** All proxy layers work correctly. The issue is entirely within OpenCode's bundled frontend JavaScript (version 1.1.53).

---

## Workarounds

### Option 1: Refresh Page (Recommended)

1. Send message (you'll see error toast)
2. Wait for "request complete" notification
3. Refresh browser page (F5 or Ctrl+R)
4. Messages will appear in chat history

### Option 2: Use Desktop CLI

Instead of web interface, use OpenCode CLI directly:
```bash
opencode chat
```

### Option 3: Downgrade to 1.1.48

**Warning**: Only if you need immediate fix and can accept older version

```bash
# Backup current config
cp -r ~/.config/opencode ~/.config/opencode.backup

# Stop current
pkill -f "opencode web"

# Install 1.1.48
curl -fsSL https://opencode.ai/install | bash -s -- --version 1.1.48

# Start
~/.opencode/bin/opencode web --port 4096 --hostname 0.0.0.0

# Test - if works, stay on 1.1.48
# To restore 1.1.53:
# pkill -f "opencode web"
# curl -fsSL https://opencode.ai/install | bash -s -- --version 1.1.53
# mv ~/.config/opencode.backup ~/.config/opencode
```

### Option 4: Wait for Upstream Fix

Monitor OpenCode Issue #12453 for resolution.

---

## Investigation Files

### Evidence Location
- `/tmp/sse_baseline_local.txt` - Local SSE baseline
- `/tmp/sse_proxy_local.txt` - SSE through proxy
- `/tmp/console_errors.txt` - Browser console output
- `/tmp/investigation_path.txt` - Analysis decision
- `.sisyphus/evidence/task-2-console.png` - Console screenshot
- `.sisyphus/evidence/task-2-network.png` - Network tab screenshot

### Documentation Location
- `.sisyphus/notepads/debug-opencode-remote-ui/FINAL_REPORT.md`
- `.sisyphus/notepads/debug-opencode-remote-ui/COMPLETION_SUMMARY.md`
- `.sisyphus/notepads/debug-opencode-remote-ui/TASK_STATUS_REPORT.md`
- `docs/OPENCODE_REMOTE_UI_FIX.md` (this file)

---

## Architecture Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│  Cloud Run  │────▶│  Tailscale  │────▶│   Ubuntu    │
│  (Remote)   │     │   (Proxy)   │     │  (Network)  │     │  (Server)   │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                    │
                                                                    ▼
                                                            ┌─────────────┐
                                                            │  OpenCode   │
                                                            │  (:4096)    │
                                                            └─────────────┘

Status: All layers ✅ working
Issue:  OpenCode frontend ❌ bug
```

---

## Related Issues

- **OpenCode #12453**: Web UI: "Failed to send prompt" false alarm
  - Status: Open (as of Feb 2026)
  - Affects: Version 1.1.53
  - Workaround: Use async endpoint or refresh page

---

## Conclusion

**No infrastructure changes required.** 

Your proxy configuration, Cloud Run setup, and Tailscale network are all functioning correctly. The issue is confirmed to be an upstream bug in OpenCode's frontend JavaScript.

**Recommended Action**: Use workaround (refresh page after sending) until OpenCode releases fix for Issue #12453.

---

*Investigation completed: 2026-02-09*  
*Investigator: Atlas (Orchestrator)*  
*Plan: debug-opencode-remote-ui*
