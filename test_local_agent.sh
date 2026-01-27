#!/bin/bash

echo "Testing local agent delegation..."
echo

echo "Step 1: Current Ollama status"
echo "=============================="
curl -s http://127.0.0.1:11434/api/ps | jq -r '.models[]? | "Loaded: \(.name)"'
echo

echo "Step 2: Checking connections before test"
echo "========================================="
connections_before=$(ss -tn | grep ':11434' | wc -l)
echo "Active connections to Ollama: $connections_before"
echo

echo "Step 3: Sending test message to trigger local agent"
echo "===================================================="
echo "This will take a moment..."

# Use opencode attach to send a message that should trigger explore/librarian
# Note: This might need authentication or specific session handling
cd /home/dlybeck/Documents/portfolio

# Try using explore agent explicitly via delegate_task
echo "Testing with a simple file search that might trigger local models..."
timeout 45 opencode run "@explore find all JSON config files in this repo" 2>&1 | head -30 &
OPENCODE_PID=$!

# Wait a bit for processing to start
sleep 3

echo
echo "Step 4: Checking Ollama activity during processing"
echo "==================================================="
for i in {1..5}; do
    echo "Check $i:"
    curl -s http://127.0.0.1:11434/api/ps | jq -r '.models[]? | "  Model: \(.name), VRAM: \(.size_vram / 1024 / 1024 / 1024 | floor)GB"'
    connections_now=$(ss -tn | grep ':11434' | wc -l)
    echo "  Active connections: $connections_now"
    sleep 2
done

# Wait for opencode to finish
wait $OPENCODE_PID 2>/dev/null

echo
echo "Step 5: Final status"
echo "===================="
curl -s http://127.0.0.1:11434/api/ps | jq -r '.models[]? | "Still loaded: \(.name)"'

echo
echo "Test complete. If you saw connection count increase or model activity, delegation is working!"
