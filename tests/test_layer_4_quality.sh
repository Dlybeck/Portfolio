#!/bin/bash

# Source helper functions
source tests/lib/test_helpers.sh

print_header "Layer 4: Response Quality Tests"

FAILED=0

# --- Test 4.1: Code Search Quality (Qwen 7B) ---
echo -n "Test 4.1: Code Search Quality (explore)... "

PROMPT='{
    "model": "qwen2.5-coder:7b-instruct-q8_0",
    "messages": [
        {"role": "system", "content": "You have access to a tool called search_code. Use it."},
        {"role": "user", "content": "Find all Python files that import FastAPI"}
    ],
    "tools": [{
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Search code files",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
    }],
    "stream": false
}'

RESPONSE=$(curl -s http://127.0.0.1:11434/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d "$PROMPT")

TOOL_CALLS=$(echo "$RESPONSE" | jq -r '.choices[0].message.tool_calls // empty')
CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content // empty')

if [ -n "$TOOL_CALLS" ]; then
    echo "PASS (Valid tool call)"
    print_test_result "Test 4.1: Code Search" "pass"
elif echo "$CONTENT" | grep -q "search_code"; then
    echo "WARNING (Tool call in content string - known issue)"
    print_test_result "Test 4.1: Code Search" "warn" "Model put tool call in content string"
else
    echo "FAIL (No tool call)"
    print_test_result "Test 4.1: Code Search" "fail" "No tool call generated"
    FAILED=1
fi

# --- Test 4.2: Analysis Quality (DeepSeek) ---
echo -n "Test 4.2: Analysis Quality (metis)... "

CODE_CONTENT=$(cat tests/fixtures/sample_code.py | jq -sR .)
PROMPT="{
    \"model\": \"deepseek-coder-v2:lite\",
    \"messages\": [
        {\"role\": \"user\", \"content\": \"Analyze this code for issues:\\n$CODE_CONTENT\"}
    ],
    \"stream\": false
}"

RESPONSE=$(curl -s http://127.0.0.1:11434/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d "$PROMPT")

CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content // empty')

if echo "$CONTENT" | grep -qE "FastAPI|app|read_root"; then
    if [ ${#CONTENT} -gt 50 ]; then
        echo "PASS"
        print_test_result "Test 4.2: Analysis Quality" "pass"
    else
        echo "FAIL (Response too short)"
        print_test_result "Test 4.2: Analysis Quality" "fail" "Response too short"
        FAILED=1
    fi
else
    echo "FAIL (Generic response)"
    print_test_result "Test 4.2: Analysis Quality" "fail" "Response missed key concepts"
    FAILED=1
fi

# --- Test 4.3: Refactor Quality (Quick/Qwen 7B) ---
echo -n "Test 4.3: Refactor Quality (quick)... "

# We intentionally check for tool usage or code block with fix
PROMPT='{
    "model": "qwen2.5-coder:7b-instruct-q8_0",
    "messages": [
        {"role": "system", "content": "You have an Edit tool. Fix the typo."},
        {"role": "user", "content": "Fix typo \"Hellow\" to \"Hello\" in tests/fixtures/sample_code.py"}
    ],
    "stream": false
}'

RESPONSE=$(curl -s http://127.0.0.1:11434/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d "$PROMPT")

CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content // empty')

if echo "$CONTENT" | grep -qE "Edit|Hello"; then
    echo "PASS"
    print_test_result "Test 4.3: Refactor Quality" "pass"
else
    echo "FAIL"
    print_test_result "Test 4.3: Refactor Quality" "fail" "No fix proposed"
    FAILED=1
fi

exit $FAILED
