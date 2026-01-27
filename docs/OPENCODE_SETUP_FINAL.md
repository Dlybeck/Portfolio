# OpenCode Setup Guide (Updated for 2026)

Complete setup for OpenCode with free Gemini API + local DeepSeek R1 (Distill) model.

## Overview

This setup provides a hybrid AI coding assistant:
- **Gemini 2.0 Flash** (free API) - Planning, architecture, large context analysis (1M tokens)
- **DeepSeek R1 Distill Qwen 14B** (local GPU) - "Reasoning" model for high-IQ implementation

**Benefits:**
- Completely free (Gemini free tier + local model)
- Persistent via tmux sessions
- Web-accessible through code-server
- Privacy: sensitive code stays local
- Fast: local GPU inference, no API latency for coding

## System Requirements

- Linux server with GPU (RTX 3060 12GB or similar)
- ~10GB disk space for model (fits in 12GB VRAM with 4-bit quantization)
- CUDA support (auto-detected by Ollama)
- tmux for persistent sessions

## Directory Structure

```
System-wide:
/usr/local/bin/ollama              # Ollama binary (system install)

User-level:
~/.local/bin/opencode              # OpenCode CLI binary
~/.config/opencode/opencode.json   # Configuration file
~/.ollama/models/                  # Local model storage
~/.cache/opencode/                 # Cache files

Shell config:
~/.bashrc                          # Add ~/.local/bin to PATH
```

## Installation Steps

### 1. Clean Up Old Installation (if exists)

```bash
# Remove old OpenCode installation
rm -rf ~/.opencode
rm -rf ~/.config/opencode

# Remove old install scripts
rm ~/install-opencode.sh

# Clean up old PATH entries in ~/.bashrc
# (Look for lines with .opencode and remove them)
nano ~/.bashrc
```

### 2. Install Ollama (System-wide)

```bash
# Official installer - auto-detects CUDA/GPU
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version

# Check GPU detection
nvidia-smi  # Should show your RTX GPU
```

### 3. Download Local Model

```bash
# Pull DeepSeek R1 Distill Qwen 14B (~9GB download, fits in 12GB VRAM)
ollama pull deepseek-r1:14b

# Test the model
ollama run deepseek-r1:14b "write a hello world in python"

# Exit test: Ctrl+D or type /bye
```

### 4. Install OpenCode

```bash
# Official Linux installer
curl -fsSL https://opencode.ai/install | bash

# Verify installation (creates ~/.local/bin/opencode)
ls -la ~/.local/bin/opencode
```

### 5. Configure PATH

```bash
# Add to ~/.bashrc
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# Reload shell config
source ~/.bashrc

# Verify OpenCode is in PATH
which opencode
opencode --version
```

### 6. Get Gemini API Key (Free)

1. Visit: https://aistudio.google.com/apikey
2. Click "Get API key" → "Create API key"
3. Copy the key (starts with `AI...`)

**Free tier limits:**
- 15 requests/minute
- 1,500 requests/day
- 1M token context window
- Completely free, no credit card required

### 7. Configure OpenCode

```bash
# Set Gemini API key
opencode config set google.apiKey YOUR_API_KEY_HERE

# Set orchestrator model (free Gemini)
opencode config set model google/gemini-2.0-flash-exp

# Set implementation model (local)
opencode config set implementationModel ollama/deepseek-r1:14b

# Verify configuration
cat ~/.config/opencode/opencode.json
```

### 8. Set Up Persistent tmux Session

```bash
# Create named session for OpenCode
tmux new-session -s opencode

# Inside tmux, start OpenCode
opencode

# Detach from tmux (keep session running)
# Press: Ctrl+B, then D

# Reattach anytime
tmux attach -t opencode

# List all sessions
tmux ls
```

## Usage

### Local Terminal Access

```bash
# Attach to persistent session
tmux attach -t opencode

# Detach without closing
Ctrl+B, then D
```

### Web Access via code-server

1. Open your portfolio dev environment: `/dev/vscode`
2. Open integrated terminal in VS Code
3. Run: `tmux attach -t opencode`
4. Full OpenCode experience with cursor navigation

### Web Access via ttyd

1. Open terminal page: `/dev/terminal`
2. Run: `tmux attach -t opencode`
3. Works but less ideal for interactive chat
