# OpenCode Testing Guide

## Quick Start

Run the comprehensive test suite to check infrastructure, model health, routing, and response quality:

```bash
./comprehensive_test_suite.sh all
```

You can also run specific layers:
```bash
./comprehensive_test_suite.sh 1  # Infrastructure only
./comprehensive_test_suite.sh 2  # Model Inference only
./comprehensive_test_suite.sh 3  # Routing only
./comprehensive_test_suite.sh 4  # Quality only
```

## What Gets Tested

### Layer 1: Infrastructure (Pass/Fail)
- Is the Ollama process running?
- Is the Ollama API responsive?
- Are the required models (`qwen2.5-coder:7b`, `qwen2.5-coder:14b`, `deepseek-coder-v2:lite`) loaded/available?
- Is the OpenCode configuration (`oh-my-opencode.json`) valid JSON?
- Are provider base URLs correct?

### Layer 2: Model Inference (Pass/Fail)
- Can each local model perform basic text completion ("Say hello")?
- **CRITICAL**: Can `qwen2.5-coder:7b` generate valid tool calls (JSON in `tool_calls` array)?
- Does the response format match OpenAI specifications (`finish_reason`, `usage`)?

### Layer 3: Agent Routing (Pass/Fail)
- Do local agents (`explore`, `metis`, `quick`) map to local models (starting with `ollama/`)?
- Do cloud agents (`sisyphus`, `oracle`, `ultrabrain`) map to cloud models?
- Do the configured local models actually exist in the running Ollama instance?

### Layer 4: Response Quality (Pass/Warn/Fail)
- **Code Search (explore)**: Does it generate a search tool call?
- **Analysis (metis)**: Does it provide specific, relevant analysis (not generic fluff)?
- **Refactoring (quick)**: Does it successfully propose code edits using the `Edit` tool?

## Interpreting Results

- ✅ **PASS**: The component is working correctly.
- ⚠️ **WARNING**: The component works but with issues (e.g., Qwen 7B putting tool calls in content string instead of the dedicated array).
- ❌ **FAIL**: The component is broken or performing below acceptable standards.

## Troubleshooting Failures

### Layer 1 Fails
- **Ollama process not found**: Run `ollama serve` or restart the service.
- **Connection refused**: Check if port 11434 is blocked or used by another service.
- **Missing models**: Run `ollama pull qwen2.5-coder:7b-instruct-q8_0` (or the missing model).

### Layer 2 Fails
- **Tool call generation failed**: This is a known issue with Qwen 7B in some environments. It may put JSON in `content` instead of `tool_calls`.
- **Empty response**: The model might be crashed or OOM. Check `journalctl -u ollama`.

### Layer 3 Fails
- **Mapping mismatch**: Edit `~/.config/opencode/oh-my-opencode.json` to fix agent-to-model mappings.
- **Model not found**: Ensure the model name in config matches `ollama list` exactly.

### Layer 4 Fails
- **Generic analysis**: DeepSeek V2 Lite might be too small for complex analysis. Consider upgrading to a larger model or using cloud.
- **No fix proposed**: The model failed to follow instructions. Try simplifying the prompt or using a stronger model.

## When to Run Tests
- Before starting a development session.
- After modifying `oh-my-opencode.json`.
- If you suspect silent failures (e.g., agents ignoring instructions).
- After updating Ollama or pulling new models.
