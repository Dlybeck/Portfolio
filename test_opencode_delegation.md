# OpenCode Delegation Test

## Overview
This test verifies that oh-my-opencode agents are properly delegating to local vs cloud models.

## Your Configuration

### Local Models (Ollama - http://127.0.0.1:11434)
- **librarian**: `ollama/qwen2.5-coder:7b-instruct-q8_0`
- **explore**: `ollama/qwen2.5-coder:7b-instruct-q8_0`
- **metis**: `ollama/deepseek-coder-v2:lite`
- **quick category**: `ollama/qwen2.5-coder:7b-instruct-q8_0`
- **unspecified-low**: `ollama/qwen2.5-coder:14b`

### Cloud Models
- **sisyphus**: `anthropic/claude-sonnet-4-5`
- **oracle**: `google/antigravity-gemini-3-pro`
- **prometheus**: `anthropic/claude-sonnet-4-5`
- **multimodal-looker**: `google/antigravity-gemini-3-pro`

## Pre-Test Verification

### ✅ Ollama Status
```bash
# Check Ollama is running
ps aux | grep ollama

# Verify models loaded
curl http://127.0.0.1:11434/api/tags

# Expected models:
# - qwen2.5-coder:7b-instruct-q8_0
# - qwen2.5-coder:14b
# - deepseek-coder-v2:lite
```

**Status**: ✅ All models present and Ollama running (PID 1437)

### Check Network Connectivity
```bash
# Test local Ollama
curl -s http://127.0.0.1:11434/v1/models

# Test if OpenCode can reach Ollama
# (OpenCode uses baseURL: http://127.0.0.1:11434/v1)
```

## Manual Delegation Tests

### Test 1: Local Agent - Explore
**Expected**: Uses `ollama/qwen2.5-coder:7b-instruct-q8_0` locally

```bash
# In OpenCode chat, run:
Hey explore agent, can you search for any Python files in this project?
```

**How to verify**:
1. Run `journalctl -u ollama -f` in another terminal while testing
2. You should see Ollama logs showing inference activity
3. Check OpenCode logs: `tail -f ~/.opencode/logs/*.log`
4. Look for requests to `127.0.0.1:11434`

**Success criteria**:
- Response comes from Explore agent
- Ollama logs show model loading/inference
- No external API calls made

---

### Test 2: Local Agent - Librarian
**Expected**: Uses `ollama/qwen2.5-coder:7b-instruct-q8_0` locally

```bash
# In OpenCode chat:
@librarian can you explain how FastAPI routing works?
```

**How to verify**:
- Same as Test 1
- Check Ollama activity during response

---

### Test 3: Cloud Agent - Sisyphus
**Expected**: Uses `anthropic/claude-sonnet-4-5` via API

```bash
# In OpenCode chat:
@sisyphus help me refactor this code to be more maintainable
```

**How to verify**:
- No Ollama activity during this request
- Check for network traffic to Anthropic API
- Response quality should be higher (Claude Sonnet 4)

---

### Test 4: Cloud Agent - Oracle
**Expected**: Uses `google/antigravity-gemini-3-pro` via Antigravity

```bash
# In OpenCode chat:
@oracle what's the best architecture for handling authentication in this project?
```

**How to verify**:
- No Ollama activity
- Network traffic to Google/Antigravity endpoint
- Response should be from Gemini 3 Pro

---

### Test 5: Category Delegation - Quick
**Expected**: Uses `ollama/qwen2.5-coder:7b-instruct-q8_0` locally

```bash
# Trigger quick category via delegate_task
# In OpenCode, ask Sisyphus to delegate a simple task:
@sisyphus please fix this typo in README.md (line 42)
```

**How to verify**:
- Sisyphus should delegate to quick category
- Quick uses local Qwen 7B
- Check Ollama logs for activity

---

## Automated Test Script

Save this as `test_delegation.sh`:

```bash
#!/bin/bash

echo "=== OpenCode Delegation Test ==="
echo

# Test 1: Ollama accessibility
echo "Test 1: Can OpenCode reach Ollama?"
curl -s http://127.0.0.1:11434/v1/models | jq -r '.data[].id' 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Ollama reachable at 127.0.0.1:11434"
else
    echo "❌ Cannot reach Ollama"
fi
echo

# Test 2: Check OpenCode config
echo "Test 2: OpenCode Configuration"
cat ~/.config/opencode/oh-my-opencode.json | jq -r '.agents.explore.model'
if [[ $(cat ~/.config/opencode/oh-my-opencode.json | jq -r '.agents.explore.model') == "ollama/"* ]]; then
    echo "✅ Explore agent configured for local Ollama"
else
    echo "❌ Explore agent NOT using Ollama"
fi
echo

# Test 3: Ollama model inference test
echo "Test 3: Direct Ollama inference test"
curl -s http://127.0.0.1:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-coder:7b-instruct-q8_0",
    "messages": [{"role": "user", "content": "Say hello"}],
    "stream": false
  }' | jq -r '.choices[0].message.content'

if [ $? -eq 0 ]; then
    echo "✅ Ollama can run inference"
else
    echo "❌ Ollama inference failed"
fi
echo

# Test 4: Check OpenCode logs for delegation
echo "Test 4: Recent OpenCode delegation activity"
echo "Looking for Ollama usage in logs..."
grep -r "ollama" ~/.opencode/logs/*.log 2>/dev/null | tail -5
echo

echo "=== Test Complete ==="
echo
echo "Next steps:"
echo "1. Run the manual tests in OpenCode chat"
echo "2. Monitor Ollama logs: journalctl -u ollama -f (or: tail -f /var/log/ollama.log)"
echo "3. Check OpenCode logs: tail -f ~/.opencode/logs/*.log"
echo "4. Watch network traffic: sudo tcpdump -i any port 11434"
```

Make it executable:
```bash
chmod +x test_delegation.sh
./test_delegation.sh
```

## Monitoring During Tests

### Terminal 1: Ollama Logs
```bash
# If Ollama runs as systemd service:
journalctl -u ollama -f

# Or if logging to file:
tail -f /var/log/ollama.log

# Or process logs:
tail -f ~/.ollama/logs/*.log
```

### Terminal 2: OpenCode Logs
```bash
tail -f ~/.opencode/logs/*.log
```

### Terminal 3: Network Traffic
```bash
# Monitor Ollama port (11434)
sudo tcpdump -i any port 11434 -A

# Monitor Anthropic API traffic (port 443)
sudo tcpdump -i any host api.anthropic.com
```

## Expected Results

### When Local Delegation Works ✅
- Ollama logs show model loading
- Network traffic on port 11434
- Fast responses (local inference)
- No external API calls for local agents
- OpenCode logs show `ollama/qwen2.5-coder:7b-instruct-q8_0`

### When Local Delegation Fails ❌
- No Ollama activity for agents configured as local
- Network calls to cloud APIs instead
- Slower responses (cloud round-trip)
- OpenCode errors about Ollama connection

## Common Issues

### Issue 1: Ollama Not Reachable
**Symptom**: OpenCode falls back to cloud models for local agents

**Fix**:
```bash
# Check Ollama is listening on 127.0.0.1:11434
ss -tlnp | grep 11434

# Verify OpenCode can reach it
curl http://127.0.0.1:11434/api/tags

# Check firewall
sudo ufw status
```

### Issue 2: Models Not Loaded
**Symptom**: Ollama returns 404 for model

**Fix**:
```bash
# List loaded models
ollama list

# Pull missing model
ollama pull qwen2.5-coder:7b-instruct-q8_0

# Verify in config
cat ~/.config/opencode/oh-my-opencode.json | jq '.agents.explore'
```

### Issue 3: Wrong Model Format
**Symptom**: OpenCode config has wrong model name

**Expected format**: `ollama/qwen2.5-coder:7b-instruct-q8_0`

**Check**:
```bash
cat ~/.config/opencode/oh-my-opencode.json | jq '.agents.explore.model'
# Should output: "ollama/qwen2.5-coder:7b-instruct-q8_0"
```

### Issue 4: Delegation Not Triggering
**Symptom**: Sisyphus doesn't delegate to specialized agents

**Possible causes**:
1. Agent names spelled wrong in prompt
2. oh-my-opencode plugin not loaded
3. Delegation disabled in settings

**Fix**:
```bash
# Verify plugin loaded
cat ~/.config/opencode/opencode.json | jq '.plugin'
# Should include: "oh-my-opencode@latest"

# Check oh-my-opencode config exists
ls -la ~/.config/opencode/oh-my-opencode.json
```

## Advanced Debugging

### Enable Verbose Logging
Edit `~/.config/opencode/opencode.json`:
```json
{
  "log": {
    "level": "debug",
    "file": "~/.opencode/logs/debug.log"
  }
}
```

Restart OpenCode:
```bash
pkill opencode
opencode web --port 4096 --hostname 0.0.0.0
```

### Inspect Request/Response
Add logging proxy between OpenCode and Ollama:

```bash
# Install mitmproxy
pip install mitmproxy

# Run proxy on port 11435, forwarding to Ollama 11434
mitmdump -p 11435 --mode reverse:http://127.0.0.1:11434

# Update OpenCode config to use proxy
# Change baseURL to: http://127.0.0.1:11435/v1
```

Watch mitmproxy output to see exact requests OpenCode sends.

## Quick Reference

### Agent → Model Mapping
| Agent | Model | Location |
|-------|-------|----------|
| sisyphus | Claude Sonnet 4 | Cloud (Anthropic) |
| oracle | Gemini 3 Pro | Cloud (Antigravity) |
| prometheus | Claude Sonnet 4 | Cloud (Anthropic) |
| librarian | Qwen 7B Q8 | Local (Ollama) |
| explore | Qwen 7B Q8 | Local (Ollama) |
| metis | DeepSeek V2 Lite | Local (Ollama) |
| multimodal-looker | Gemini 3 Pro | Cloud (Antigravity) |

### Category → Model Mapping
| Category | Model | Location |
|----------|-------|----------|
| visual-engineering | Gemini 3 Pro | Cloud |
| ultrabrain | Gemini 3 Pro | Cloud |
| artistry | Gemini 3 Pro | Cloud |
| quick | Qwen 7B Q8 | Local |
| unspecified-low | Qwen 14B | Local |
| unspecified-high | Claude Sonnet 4 | Cloud |
| writing | Gemini 3 Flash | Cloud |

## Success Checklist

- [ ] Ollama running and accessible at 127.0.0.1:11434
- [ ] All required models loaded in Ollama
- [ ] OpenCode config points to correct Ollama URL
- [ ] oh-my-opencode plugin loaded
- [ ] oh-my-opencode.json has correct agent → model mappings
- [ ] Local agents (explore, librarian) trigger Ollama activity
- [ ] Cloud agents (sisyphus, oracle) do NOT trigger Ollama
- [ ] Category delegation works (quick → local, ultrabrain → cloud)
- [ ] No errors in OpenCode logs about missing models

## Report Template

After testing, fill this out:

```markdown
### Test Results (Date: _________)

**Environment:**
- OpenCode version: ___________
- oh-my-opencode version: ___________
- Ollama version: ___________

**Tests Performed:**
1. Explore agent (local): [ ] Pass [ ] Fail
2. Librarian agent (local): [ ] Pass [ ] Fail
3. Sisyphus agent (cloud): [ ] Pass [ ] Fail
4. Oracle agent (cloud): [ ] Pass [ ] Fail
5. Quick category (local): [ ] Pass [ ] Fail

**Issues Found:**
- 

**Logs Captured:**
- Ollama logs: 
- OpenCode logs: 
- Network traffic: 

**Conclusion:**
Delegation is working: [ ] Yes [ ] No [ ] Partially

**Action Items:**
- 
```

---

**Good luck with testing! Let me know your results.**
