#!/bin/bash

echo "=== Ollama Activity Monitor ==="
echo "Press Ctrl+C to stop"
echo

while true; do
    clear
    echo "=== Ollama Activity Monitor ==="
    echo "Time: $(date '+%H:%M:%S')"
    echo
    
    echo "Running Models:"
    echo "---------------"
    response=$(curl -s http://127.0.0.1:11434/api/ps)
    
    if [ -n "$response" ]; then
        models=$(echo "$response" | jq -r '.models[]? | "\(.name) - Size: \(.size_vram // 0 | tonumber / 1024 / 1024 / 1024 | floor)GB"' 2>/dev/null)
        if [ -n "$models" ]; then
            echo "$models"
        else
            echo "(No models currently loaded)"
        fi
    else
        echo "❌ Cannot reach Ollama"
    fi
    
    echo
    echo "Network Connections to Ollama (port 11434):"
    echo "--------------------------------------------"
    connections=$(ss -tn | grep ':11434' | wc -l)
    if [ "$connections" -gt 0 ]; then
        echo "Active connections: $connections"
        ss -tn | grep ':11434' | head -5
    else
        echo "(No active connections)"
    fi
    
    echo
    echo "Recent log activity:"
    echo "--------------------"
    if [ -f ~/.opencode/logs/*.log ]; then
        tail -3 ~/.opencode/logs/*.log 2>/dev/null
    else
        echo "(No OpenCode logs yet)"
    fi
    
    sleep 2
done
