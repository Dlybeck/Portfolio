#!/bin/bash

# Source helper functions
if [ -f "tests/lib/test_helpers.sh" ]; then
    source tests/lib/test_helpers.sh
else
    echo "Error: Helper library not found at tests/lib/test_helpers.sh"
    exit 1
fi

print_header "Comprehensive OpenCode Testing Suite"

# Initialize counters
TOTAL_PASSED=0
TOTAL_FAILED=0
TOTAL_WARNINGS=0

run_layer() {
    local layer=$1
    local script="tests/test_layer_${layer}_*.sh"
    
    # Resolve wildcard to actual file
    script=$(ls $script 2>/dev/null | head -1)
    
    if [ -z "$script" ]; then
        echo "Error: Test script for Layer $layer not found"
        return 1
    fi
    
    echo
    echo "----------------------------------------"
    echo "Running Layer $layer..."
    echo "----------------------------------------"
    
    bash "$script"
    local status=$?
    
    if [ $status -eq 0 ]; then
        ((TOTAL_PASSED++))
    else
        ((TOTAL_FAILED++))
    fi
    
    return $status
}

run_all() {
    run_layer 1
    run_layer 2
    run_layer 3
    run_layer 4
}

case "$1" in
    1) run_layer 1 ;;
    2) run_layer 2 ;;
    3) run_layer 3 ;;
    4) run_layer 4 ;;
    all) run_all ;;
    *)
        echo "Usage: $0 {1|2|3|4|all}"
        exit 1
        ;;
esac

echo
print_header "Test Summary Report"
echo "Layers Passed: $TOTAL_PASSED"
echo "Layers Failed: $TOTAL_FAILED"

if [ $TOTAL_FAILED -eq 0 ]; then
    echo -e "${GREEN}OVERALL STATUS: PASS${NC}"
    exit 0
else
    echo -e "${RED}OVERALL STATUS: FAIL${NC}"
    exit 1
fi
