#!/bin/bash

echo "=== OpenCode Delegation Test ==="
echo

# Test 1: Ollama accessibility
echo "Test 1: Can OpenCode reach Ollama?"
response=$(curl -s http://127.0.0.1:11434/api/tags)
if [ -n "$response" ]; then
    echo "✅ Ollama reachable at 127.0.0.1:11434"
    echo "Available models:"
    echo "$response" | jq -r '.models[].name' 2>/dev/null || echo "$response" | grep -o '"name":"[^"]*"' | cut -d'"' -f4
else
    echo "❌ Cannot reach Ollama"
fi
echo

# Test 2: Check OpenCode config
echo "Test 2: OpenCode Configuration"
if [ -f ~/.config/opencode/oh-my-opencode.json ]; then
    echo "✅ oh-my-opencode.json found"
    
    explore_model=$(cat ~/.config/opencode/oh-my-opencode.json | jq -r '.agents.explore.model' 2>/dev/null)
    librarian_model=$(cat ~/.config/opencode/oh-my-opencode.json | jq -r '.agents.librarian.model' 2>/dev/null)
    sisyphus_model=$(cat ~/.config/opencode/oh-my-opencode.json | jq -r '.agents.sisyphus.model' 2>/dev/null)
    
    echo "  - explore: $explore_model"
    echo "  - librarian: $librarian_model"
    echo "  - sisyphus: $sisyphus_model"
    
    if [[ "$explore_model" == "ollama/"* ]]; then
        echo "✅ Explore agent configured for local Ollama"
    else
        echo "❌ Explore agent NOT using Ollama"
    fi
    
    if [[ "$librarian_model" == "ollama/"* ]]; then
        echo "✅ Librarian agent configured for local Ollama"
    else
        echo "❌ Librarian agent NOT using Ollama"
    fi
else
    echo "❌ oh-my-opencode.json not found"
fi
echo

# Test 3: Verify OpenCode plugin
echo "Test 3: oh-my-opencode plugin status"
if [ -f ~/.config/opencode/opencode.json ]; then
    plugin=$(cat ~/.config/opencode/opencode.json | jq -r '.plugin[]' 2>/dev/null | grep oh-my-opencode)
    if [ -n "$plugin" ]; then
        echo "✅ Plugin loaded: $plugin"
    else
        echo "❌ oh-my-opencode plugin NOT loaded"
    fi
else
    echo "❌ opencode.json not found"
fi
echo

# Test 4: Ollama model inference test
echo "Test 4: Direct Ollama inference test"
inference_response=$(curl -s http://127.0.0.1:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-coder:7b-instruct-q8_0",
    "messages": [{"role": "user", "content": "Say hello"}],
    "stream": false
  }')

if [ -n "$inference_response" ]; then
    content=$(echo "$inference_response" | jq -r '.choices[0].message.content' 2>/dev/null)
    if [ -n "$content" ] && [ "$content" != "null" ]; then
        echo "✅ Ollama can run inference"
        echo "Response: $content"
    else
        echo "⚠️  Ollama responded but content is empty or invalid"
        echo "Raw response: $inference_response"
    fi
else
    echo "❌ Ollama inference failed"
fi
echo

# Test 5: Check OpenCode baseURL
echo "Test 5: Ollama provider configuration"
baseURL=$(cat ~/.config/opencode/opencode.json | jq -r '.provider.ollama.options.baseURL' 2>/dev/null)
echo "BaseURL: $baseURL"
if [ "$baseURL" == "http://127.0.0.1:11434/v1" ]; then
    echo "✅ Correct Ollama baseURL configured"
else
    echo "⚠️  BaseURL might be incorrect (expected: http://127.0.0.1:11434/v1)"
fi
echo

# Test 6: Check for recent Ollama usage
echo "Test 6: Recent OpenCode activity"
if [ -d ~/.opencode/logs ]; then
    echo "OpenCode log directory found. Recent log files:"
    ls -lht ~/.opencode/logs/*.log 2>/dev/null | head -3
    echo
    echo "Searching for Ollama references in logs..."
    grep -i "ollama" ~/.opencode/logs/*.log 2>/dev/null | tail -5
else
    echo "⚠️  No OpenCode logs directory found"
fi
echo

echo "=== Test Complete ==="
echo
echo "Summary:"
echo "--------"
echo "If all tests passed ✅, delegation should be working correctly."
echo
echo "Next steps for manual verification:"
echo "1. Start OpenCode web: opencode web --port 4096"
echo "2. In OpenCode chat, try:"
echo "   - '@explore can you find Python files in this project?'"
echo "   - '@librarian explain how FastAPI works'"
echo "   - '@sisyphus help me refactor this code'"
echo "3. Monitor Ollama in another terminal:"
echo "   watch -n1 'curl -s http://127.0.0.1:11434/api/ps'"
echo "4. For local agents (explore, librarian), you should see Ollama activity"
echo "5. For cloud agents (sisyphus, oracle), Ollama should stay idle"
echo
echo "For detailed monitoring:"
echo "  - Ollama processes: curl -s http://127.0.0.1:11434/api/ps | jq"
echo "  - Network traffic: sudo tcpdump -i any port 11434 -nn"
echo "  - OpenCode logs: tail -f ~/.opencode/logs/*.log"
