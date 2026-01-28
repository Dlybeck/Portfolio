#!/bin/bash

# Source helper functions
source tests/lib/test_helpers.sh

print_header "Layer 1: Infrastructure Tests"

FAILED=0

# Test 1.1: Ollama process running
if pgrep -x "ollama" > /dev/null || pgrep -x "ollama_llama_server" > /dev/null; then
    print_test_result "Test 1.1: Ollama process running" "pass"
else
    print_test_result "Test 1.1: Ollama process running" "fail" "Process not found"
    FAILED=1
fi

# Test 1.2: Ollama API responsive
if check_ollama_running 2; then
    print_test_result "Test 1.2: Ollama API responsive" "pass"
else
    print_test_result "Test 1.2: Ollama API responsive" "fail" "Connection refused or timeout"
    FAILED=1
fi

# Test 1.3: Models available
MODELS_JSON=$(curl -s http://127.0.0.1:11434/api/tags)
MISSING_MODELS=""
for model in "qwen2.5-coder:7b-instruct-q8_0" "qwen2.5-coder:14b" "deepseek-coder-v2:lite"; do
    if ! echo "$MODELS_JSON" | grep -q "$model"; then
        MISSING_MODELS="$MISSING_MODELS $model"
    fi
done

if [ -z "$MISSING_MODELS" ]; then
    print_test_result "Test 1.3: Required models available" "pass"
else
    print_test_result "Test 1.3: Required models available" "fail" "Missing:$MISSING_MODELS"
    FAILED=1
fi

# Test 1.4: Config file validity
if [ -f ~/.config/opencode/oh-my-opencode.json ] && jq empty ~/.config/opencode/oh-my-opencode.json > /dev/null 2>&1; then
    print_test_result "Test 1.4: oh-my-opencode.json valid" "pass"
else
    print_test_result "Test 1.4: oh-my-opencode.json valid" "fail" "File missing or invalid JSON"
    FAILED=1
fi

# Test 1.5: Agent model references
EXPLORE_MODEL=$(jq -r '.agents.explore.model // empty' ~/.config/opencode/oh-my-opencode.json 2>/dev/null)
METIS_MODEL=$(jq -r '.agents.metis.model // empty' ~/.config/opencode/oh-my-opencode.json 2>/dev/null)

if [[ "$EXPLORE_MODEL" == ollama/* ]] && [[ "$METIS_MODEL" == ollama/* ]]; then
    print_test_result "Test 1.5: Agent model references valid" "pass"
else
    print_test_result "Test 1.5: Agent model references valid" "fail" "Explore: $EXPLORE_MODEL, Metis: $METIS_MODEL"
    FAILED=1
fi

# Test 1.6: Provider BaseURL
BASE_URL=$(jq -r '.provider.ollama.options.baseURL // empty' ~/.config/opencode/opencode.json 2>/dev/null)
EXPECTED="http://127.0.0.1:11434/v1"

if [ "$BASE_URL" == "$EXPECTED" ]; then
    print_test_result "Test 1.6: Provider BaseURL correct" "pass"
else
    print_test_result "Test 1.6: Provider BaseURL correct" "fail" "Expected $EXPECTED, got $BASE_URL"
    FAILED=1
fi

exit $FAILED
