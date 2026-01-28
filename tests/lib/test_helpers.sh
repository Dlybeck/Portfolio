#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print test result with standardized formatting
# Usage: print_test_result "Test Name" "status" "message"
# Status: pass, fail, warn
print_test_result() {
    local name="$1"
    local status="$2"
    local message="$3"
    
    case "$status" in
        "pass")
            echo -e "${GREEN}✅ ${name}: PASS${NC}"
            if [ -n "$message" ]; then echo "   $message"; fi
            return 0
            ;;
        "fail")
            echo -e "${RED}❌ ${name}: FAIL${NC}"
            if [ -n "$message" ]; then echo "   Error: $message"; fi
            return 1
            ;;
        "warn")
            echo -e "${YELLOW}⚠️  ${name}: WARNING${NC}"
            if [ -n "$message" ]; then echo "   Warning: $message"; fi
            return 0
            ;;
        *)
            echo "Unknown status: $status"
            return 2
            ;;
    esac
}

# Check if Ollama is running and accessible
# Usage: check_ollama_running [timeout_seconds]
check_ollama_running() {
    local timeout=${1:-5}
    local response
    
    response=$(curl -s --max-time "$timeout" http://127.0.0.1:11434/api/tags)
    if [ $? -eq 0 ] && [ -n "$response" ]; then
        return 0
    else
        return 1
    fi
}

# Verify JSON response contains expected keys
# Usage: verify_json_response "json_string" "key1" "key2" ...
verify_json_response() {
    local json="$1"
    shift
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        echo "Error: jq is not installed"
        return 2
    fi
    
    # Check for valid JSON
    if ! echo "$json" | jq empty &> /dev/null; then
        return 1
    fi
    
    # Check for required keys
    for key in "$@"; do
        local value
        value=$(echo "$json" | jq -r ".$key // empty")
        if [ -z "$value" ]; then
            return 1
        fi
    done
    
    return 0
}

# Compare actual vs expected value
# Usage: compare_expected "actual" "expected" "label"
compare_expected() {
    local actual="$1"
    local expected="$2"
    local label="$3"
    
    if [ "$actual" == "$expected" ]; then
        return 0
    else
        echo "   Mismatch for $label:"
        echo "     Expected: $expected"
        echo "     Actual:   $actual"
        return 1
    fi
}

# Print section header
print_header() {
    echo
    echo -e "${BLUE}=== $1 ===${NC}"
    echo
}
