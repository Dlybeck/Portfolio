#!/bin/bash

# Source helper functions
source tests/lib/test_helpers.sh

print_header "Layer 3: Agent Routing Tests (Configuration Audit)"

FAILED=0
CONFIG_FILE=~/.config/opencode/oh-my-opencode.json

if [ ! -f "$CONFIG_FILE" ]; then
    print_test_result "Config file exists" "fail" "File $CONFIG_FILE not found"
    exit 1
fi

# Test 3.1: Verify Local Agent Mapping
echo "Checking Local Agent Mappings..."
LOCAL_AGENTS=("agents.explore" "agents.metis" "categories.quick" "categories.\"unspecified-low\"")

for agent in "${LOCAL_AGENTS[@]}"; do
    MODEL=$(jq -r ".$agent.model // empty" "$CONFIG_FILE")
    if [[ "$MODEL" == ollama/* ]]; then
        print_test_result "Test 3.1: $agent -> Local" "pass"
    else
        print_test_result "Test 3.1: $agent -> Local" "fail" "Expected ollama/..., got $MODEL"
        FAILED=1
    fi
done

# Test 3.2: Verify Cloud Agent Mapping
echo "Checking Cloud Agent Mappings..."
CLOUD_AGENTS=("agents.sisyphus" "agents.oracle" "categories.ultrabrain")

for agent in "${CLOUD_AGENTS[@]}"; do
    MODEL=$(jq -r ".$agent.model // empty" "$CONFIG_FILE")
    if [[ "$MODEL" != ollama/* ]] && [ -n "$MODEL" ]; then
        print_test_result "Test 3.2: $agent -> Cloud" "pass"
    else
        print_test_result "Test 3.2: $agent -> Cloud" "fail" "Expected cloud model, got $MODEL"
        FAILED=1
    fi
done

# Test 3.3: Routing Audit Simulation (Verify local models exist)
echo "Auditing Local Model Availability..."
AVAILABLE_MODELS=$(curl -s http://127.0.0.1:11434/api/tags | jq -r '.models[].name')

for agent in "${LOCAL_AGENTS[@]}"; do
    CONFIGURED_MODEL=$(jq -r ".$agent.model // empty" "$CONFIG_FILE" | sed 's/^ollama\///')
    
    # Check for exact match or substring match (ignoring tags if needed)
    if echo "$AVAILABLE_MODELS" | grep -q "$CONFIGURED_MODEL"; then
         print_test_result "Test 3.3: Model for $agent exists ($CONFIGURED_MODEL)" "pass"
    else
         print_test_result "Test 3.3: Model for $agent exists ($CONFIGURED_MODEL)" "fail" "Model not found in Ollama"
         FAILED=1
    fi
done

exit $FAILED
