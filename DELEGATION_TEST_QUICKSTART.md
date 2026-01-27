# OpenCode Delegation Test - Quick Start

## Current Status

✅ **Your configuration is correct!**

The automated test shows:
- Ollama is running and accessible
- All required models are loaded
- Local agents (explore, librarian) → Ollama
- Cloud agents (sisyphus, oracle) → Anthropic/Google
- oh-my-opencode plugin is loaded

## Quick Test (2 minutes)

### Step 1: Start monitoring (Terminal 1)
```bash
cd ~/Documents/portfolio
./monitor_ollama.sh
```

This shows real-time Ollama activity.

### Step 2: Start OpenCode Web (Terminal 2)
```bash
opencode web --port 4096 --hostname 0.0.0.0
```

### Step 3: Test delegation (Browser)
Open http://localhost:4096

Try these commands:

**Test Local Agent (should show Ollama activity in monitor):**
```
@explore can you find all Python files in this project?
```

**Test Cloud Agent (Ollama should stay idle):**
```
@sisyphus help me understand this codebase architecture
```

### Expected Results

#### When you use @explore or @librarian:
- Monitor shows model loading in Ollama
- Response uses local Qwen 7B model
- Fast response (local inference)
- Monitor shows "Running Models: qwen2.5-coder:7b-instruct-q8_0"

#### When you use @sisyphus, @oracle, or @prometheus:
- Monitor shows NO Ollama activity
- Response from cloud (Claude/Gemini)
- Slightly slower (API round-trip)
- Monitor shows "(No models currently loaded)"

## Troubleshooting

### Problem: Local agents NOT using Ollama

**Check 1: Is OpenCode using the right config?**
```bash
cat ~/.config/opencode/oh-my-opencode.json | jq '.agents.explore'
```
Should show: `"model": "ollama/qwen2.5-coder:7b-instruct-q8_0"`

**Check 2: Can OpenCode reach Ollama?**
```bash
curl http://127.0.0.1:11434/api/tags
```
Should show list of models.

**Check 3: Check OpenCode logs**
```bash
tail -f ~/.opencode/logs/*.log
```
Look for errors about Ollama connection.

### Problem: Monitor shows no activity

**Solution**: Make sure you're using agent names with @:
- ✅ `@explore find Python files`
- ❌ `explore find Python files` (won't trigger agent)

### Problem: All agents using cloud models

**Check baseURL**:
```bash
cat ~/.config/opencode/opencode.json | jq '.provider.ollama.options.baseURL'
```
Should be: `"http://127.0.0.1:11434/v1"`

## Configuration Summary

Your current setup:

| Agent/Category | Model | Backend |
|----------------|-------|---------|
| sisyphus | Claude Sonnet 4 | Anthropic Cloud |
| oracle | Gemini 3 Pro | Google Cloud |
| prometheus | Claude Sonnet 4 | Anthropic Cloud |
| **explore** | **Qwen 7B Q8** | **Local Ollama** |
| **librarian** | **Qwen 7B Q8** | **Local Ollama** |
| **metis** | **DeepSeek V2 Lite** | **Local Ollama** |
| multimodal-looker | Gemini 3 Pro | Google Cloud |
| **quick category** | **Qwen 7B Q8** | **Local Ollama** |
| **unspecified-low** | **Qwen 14B** | **Local Ollama** |
| unspecified-high | Claude Sonnet 4 | Anthropic Cloud |

**Bold** = Uses local Ollama

## Files Created

1. `test_delegation.sh` - Run once to verify config
2. `monitor_ollama.sh` - Live monitoring during tests
3. `test_opencode_delegation.md` - Detailed test documentation

## Next Steps

If delegation is working correctly:
- ✅ Mark this as resolved
- Use local agents for quick tasks (explore, librarian)
- Use cloud agents for complex reasoning (sisyphus, oracle)
- Monitor costs (cloud) vs speed (local)

If delegation is NOT working:
- Share OpenCode logs: `~/.opencode/logs/*.log`
- Share test script output: `./test_delegation.sh`
- Check network: `sudo tcpdump -i any port 11434`

## Advanced: Category-Based Delegation

When Sisyphus delegates tasks, it uses categories:

```bash
# This will use LOCAL Qwen 7B (quick category):
@sisyphus fix this typo in line 42

# This will use CLOUD Gemini 3 Pro (ultrabrain category):
@sisyphus design a new microservices architecture

# This will use CLOUD Gemini 3 Pro (visual-engineering category):
@sisyphus improve the UI/UX of this component
```

Watch the monitor to confirm which backend is used.
