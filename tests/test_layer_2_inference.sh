#!/bin/bash

# Source helper functions
source tests/lib/test_helpers.sh

print_header "Layer 2: Model Inference Tests"

FAILED=0

# Test 2.1 - 2.3: Basic Inference
for model in "qwen2.5-coder:7b-instruct-q8_0" "qwen2.5-coder:14b" "deepseek-coder-v2:lite"; do
    echo -n "Testing basic inference for $model... "
    
    RESPONSE=$(curl -s http://127.0.0.1:11434/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"$model\",
            \"messages\": [{\"role\": \"user\", \"content\": \"Say hello\"}],
            \"stream\": false
        }")
    
    CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content // empty')
    
    if [ -n "$CONTENT" ]; then
        print_test_result "Test 2.x: Basic inference ($model)" "pass"
    else
        print_test_result "Test 2.x: Basic inference ($model)" "fail" "Empty response or error"
        echo "Response: $RESPONSE"
        FAILED=1
    fi
done

# Test 2.4: Tool Call Generation (Critical)
echo -n "Testing tool call generation for qwen2.5-coder:7b-instruct-q8_0... "

TOOL_PROMPT='{
    "model": "qwen2.5-coder:7b-instruct-q8_0",
    "messages": [
        {"role": "system", "content": "You have access to a tool called search_code that takes a query parameter. You must respond with a tool call."},
        {"role": "user", "content": "Find all Python files that import FastAPI"}
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "search_code",
                "description": "Search code files",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                }
            }
        }
    ],
    "stream": false
}'

RESPONSE=$(curl -s http://127.0.0.1:11434/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d "$TOOL_PROMPT")

TOOL_CALLS=$(echo "$RESPONSE" | jq -r '.choices[0].message.tool_calls // empty')
TOOL_NAME=$(echo "$RESPONSE" | jq -r '.choices[0].message.tool_calls[0].function.name // empty')

if [ -n "$TOOL_CALLS" ] && [ "$TOOL_NAME" == "search_code" ]; then
    print_test_result "Test 2.4: Tool call generation" "pass"
else
    print_test_result "Test 2.4: Tool call generation" "fail" "No valid tool call found"
    echo "Response: $RESPONSE"
    FAILED=1
fi

# Test 2.5: Response Format
FINISH_REASON=$(echo "$RESPONSE" | jq -r '.choices[0].finish_reason // empty')
TOTAL_TOKENS=$(echo "$RESPONSE" | jq -r '.usage.total_tokens // 0')

if [ "$FINISH_REASON" == "tool_calls" ] && [ "$TOTAL_TOKENS" -gt 0 ]; then
    print_test_result "Test 2.5: Response format valid" "pass"
else
    print_test_result "Test 2.5: Response format valid" "fail" "Finish reason: $FINISH_REASON, Tokens: $TOTAL_TOKENS"
    FAILED=1
fi

exit $FAILED
