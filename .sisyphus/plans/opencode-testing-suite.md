# OpenCode + OMO + Ollama Testing Suite

## Context

### Original Request
User experiences silent failures with local inference (Ollama) in OpenCode. Errors appear as "improper responses" or "tool call errors" from orchestrator, but only AFTER delegation completes. Need piece-by-piece testing to catch failures early and prove the whole system works reliably.

### Interview Summary
**Key Discussions**:
- Failure symptoms: Hard to diagnose because silenced; sees orchestrator complaints about tool calls
- Local agents affected: explore (code search), metis (analysis), quick category, unspecified-low category
- Desired verification: Infrastructure health, routing correctness, response quality, end-to-end workflows, automatic recovery
- Test requirements: All of the above ideally

**Design Decisions**:
- **Failure strategy**: Fail loudly (no silent fallbacks)
- **Implementation scope**: Phase 1-3 (Infrastructure + Routing + Quality tests)
- **Test execution**: Manual command only (no automation/cron for now)
- **Test framework**: Bash scripts with curl/jq (consistent with existing test_delegation.sh)

**Research Findings**:
- Existing tests: `test_delegation.sh` (basic connectivity), `monitor_ollama.sh` (realtime), `DELEGATION_TEST_QUICKSTART.md` (manual guide)
- Current config validated: explore & metis → Ollama; sisyphus, oracle, prometheus → Cloud
- Configuration files: `~/.config/opencode/oh-my-opencode.json`, `~/.config/opencode/opencode.json`
- Missing: Response quality tests, routing validation, end-to-end verification

### Metis Review
**Identified Gaps**: Metis returned no output (empty response) - this is actually demonstrating the exact problem we're solving! Local model may have failed silently or produced unparseable response. This reinforces the need for robust testing.

---

## Work Objectives

### Core Objective
Build a comprehensive, piece-by-piece testing suite that catches OpenCode + Ollama local inference failures BEFORE they affect development, eliminating silent failures and providing clear pass/fail signals for each component.

### Concrete Deliverables
1. Enhanced test script: `comprehensive_test_suite.sh` (Layers 1-4)
2. Updated: `test_delegation.sh` → include new Layer 1 & 2 tests
3. New test module: `test_layer_2_inference.sh` (model inference quality)
4. New test module: `test_layer_3_routing.sh` (agent routing validation)
5. New test module: `test_layer_4_quality.sh` (response quality evaluation)
6. Test report generator: Structured pass/fail output with actionable failures
7. Documentation: `TESTING_GUIDE.md` - How to run, interpret, debug failures

### Definition of Done
- [x] Run `./comprehensive_test_suite.sh` → Complete in <10 minutes
- [x] Report shows: ✅/⚠️/❌ for each test layer with clear failure messages
- [x] Can identify EXACTLY what's broken (e.g., "Qwen 7B tool call format invalid")
- [x] All tests pass on user's current setup OR identify specific issues to fix
- [x] User confidently knows: "Ollama is working" or "Here's why it's not"

### Must Have
- **Layer 1**: Infrastructure health checks (Ollama running, config valid, network ok)
- **Layer 2**: Model inference tests (direct Ollama queries, tool call validation)
- **Layer 3**: Agent routing tests (verify explore→Ollama, sisyphus→Cloud with 100% accuracy)
- **Layer 4**: Response quality tests (real tasks: code search, analysis, simple refactor)
- Clear pass/fail criteria for each test
- Actionable failure messages (not "something's wrong" but "Qwen 7B at http://127.0.0.1:11434 timeout after 30s")
- Test data using real portfolio codebase (not synthetic fixtures)

### Must NOT Have (Guardrails)
- ❌ No auto-fallback to cloud (fail loudly per user choice)
- ❌ No automation/cron jobs (manual execution only for now)
- ❌ No Layer 5 (end-to-end workflows) or Layer 6 (error handling) - out of scope for Phase 1-3
- ❌ No monitoring dashboard or real-time alerts (future enhancement)
- ❌ No changes to OpenCode configuration (test existing setup, don't modify it)
- ❌ No external dependencies beyond curl, jq, bash (keep it simple)

---

## Verification Strategy

### Manual QA Only

**CRITICAL**: Each test must verify EXECUTION, not just "it should work".

Tests use bash scripts with curl/jq to query Ollama and OpenCode directly, then verify responses match expected formats.

**By Deliverable Type:**

| Type | Verification Tool | Procedure |
|------|------------------|-----------|
| **Ollama Health** | curl + jq | Query /api/tags, /api/ps, /v1/chat/completions |
| **Config Validation** | jq | Parse JSON, verify model references exist |
| **Routing Verification** | tcpdump or ss | Monitor network traffic to port 11434 during test requests |
| **Response Quality** | curl + grep/jq | Send test prompts, parse responses, verify tool call format |

**Evidence Required:**
- [x] Command output captured (copy-paste actual terminal output)
- [x] Test report showing pass/fail for each layer
- [x] Clear error messages for any failures

---

## Task Flow

```
Task 0 (Setup)
├─ Task 1 (Layer 1: Infrastructure) → Parallel
├─ Task 2 (Layer 2: Model Inference) → Depends on Task 1
└─ Task 3 (Layer 3: Routing) → Depends on Task 1, Parallel with Task 2
    └─ Task 4 (Layer 4: Quality) → Depends on Tasks 2 & 3
        └─ Task 5 (Integration & Docs) → Depends on all previous
```

## Parallelization

| Group | Tasks | Reason |
|-------|-------|--------|
| A | 1 | Independent (just creates test structure) |
| B | 2, 3 | Both depend on Task 1 but independent of each other |

| Task | Depends On | Reason |
|------|------------|--------|
| 0 | - | Setup task |
| 1 | 0 | Needs test structure |
| 2 | 1 | Needs Layer 1 passing to validate models work |
| 3 | 1 | Needs Layer 1 passing to validate routing |
| 4 | 2, 3 | Needs models working AND routing correct |
| 5 | 0, 1, 2, 3, 4 | Integrates all test modules |

---

## TODOs

- [x] 0. Create Test Infrastructure

  **What to do**:
  - Create directory structure: `tests/`, `tests/lib/`, `tests/fixtures/`
  - Create shared test library: `tests/lib/test_helpers.sh` with common functions:
    - `print_test_result()` - Standardized pass/fail/warn output
    - `check_ollama_running()` - Reusable Ollama health check
    - `verify_json_response()` - JSON validation helper
    - `compare_expected()` - Compare actual vs expected output
  - Create test fixtures: `tests/fixtures/sample_code.py` (for code search tests)
  - Create `.gitignore` entries: `tests/results/`, `tests/*.log`

  **Must NOT do**:
  - Don't create automated test runners (no GitHub Actions, no cron)
  - Don't modify existing test scripts yet (will enhance in later tasks)
  - Don't add external dependencies (stick to curl, jq, bash)

  **Parallelizable**: N/A (first task, others depend on this)

  **References**:
  **Existing Test Patterns**:
  - `test_delegation.sh` - Current test structure and output format to maintain consistency
  - `monitor_ollama.sh` - Example of curl-based Ollama queries

  **Test Library Patterns** (reference standard bash test frameworks):
  - BATS (Bash Automated Testing System) structure - for inspiration on test organization
  - https://github.com/sstephenson/bats - Common patterns for bash test helpers

  **Fixture Approach**:
  - Use actual project files as test fixtures (e.g., `services/pty_service.py`, `apis/route_general.py`)
  - Alternative: Create minimal synthetic fixtures in `tests/fixtures/`

  **Acceptance Criteria**:

  **Manual Execution Verification**:
  - [x] Directory structure created:
    ```bash
    ls -la tests/
    # Expected: lib/, fixtures/ directories exist
    ```
  - [x] Test library has core functions:
    ```bash
    grep -E "print_test_result|check_ollama_running|verify_json_response" tests/lib/test_helpers.sh
    # Expected: All three functions defined
    ```
  - [x] Can source library without errors:
    ```bash
    source tests/lib/test_helpers.sh && echo "Library loaded successfully"
    # Expected output: "Library loaded successfully"
    # Exit code: 0
    ```
  - [x] Fixture file exists and is valid Python:
    ```bash
    python3 -m py_compile tests/fixtures/sample_code.py
    # Expected: No syntax errors, exit code 0
    ```

  **Commit**: YES
  - Message: `test(opencode): add test infrastructure and helper library`
  - Files: `tests/lib/test_helpers.sh`, `tests/fixtures/sample_code.py`, `.gitignore`
  - Pre-commit: `bash -n tests/lib/test_helpers.sh` (syntax check)

---

- [x] 1. Implement Layer 1: Infrastructure Tests

  **What to do**:
  - Create `tests/test_layer_1_infrastructure.sh`:
    - Test 1.1: Ollama process running (`pgrep ollama` or `systemctl status ollama`)
    - Test 1.2: Ollama API responsive (`curl http://127.0.0.1:11434/api/tags`)
    - Test 1.3: Models available (`jq '.models[].name'` from /api/tags, verify qwen2.5-coder:7b-instruct-q8_0, qwen2.5-coder:14b, deepseek-coder-v2:lite exist)
    - Test 1.4: oh-my-opencode.json valid (`jq empty ~/.config/opencode/oh-my-opencode.json`)
    - Test 1.5: Agent model references exist (check .agents.explore.model, .agents.metis.model point to valid Ollama models)
    - Test 1.6: opencode.json valid and baseURL correct (`jq '.provider.ollama.options.baseURL'` == "http://127.0.0.1:11434/v1")
  - Enhance existing `test_delegation.sh` to call Layer 1 tests (or merge relevant tests)
  - Output format: `✅ Test 1.1: Ollama process running` or `❌ Test 1.2: API not responsive (connection refused)`

  **Must NOT do**:
  - Don't test actual inference yet (that's Layer 2)
  - Don't test routing (that's Layer 3)
  - Don't modify configuration files (only read and validate)

  **Parallelizable**: YES (with Task 0 complete, Task 1 is independent)

  **References**:
  **Configuration Files**:
  - `~/.config/opencode/oh-my-opencode.json` - Agent configuration to validate
  - `~/.config/opencode/opencode.json` - Provider configuration to validate

  **Existing Test Logic**:
  - `test_delegation.sh` lines 7-15 - Ollama health check pattern
  - `test_delegation.sh` lines 19-44 - Config validation pattern
  - `test_delegation.sh` lines 86-93 - BaseURL check pattern

  **Expected Model List** (from oh-my-opencode.json):
  - qwen2.5-coder:7b-instruct-q8_0 (explore agent)
  - qwen2.5-coder:14b (unspecified-low category)
  - deepseek-coder-v2:lite (metis agent)

  **Test Output Format** (maintain consistency):
  - Use `echo "✅ ..."` for pass
  - Use `echo "❌ ..."` for fail
  - Use `echo "⚠️  ..."` for warnings

  **Acceptance Criteria**:

  **Manual Execution Verification**:
  - [x] Test script runs without errors:
    ```bash
    bash tests/test_layer_1_infrastructure.sh
    # Expected: 6 tests execute, each with ✅/❌/⚠️ output
    # Exit code: 0 if all pass, 1 if any fail
    ```
  - [x] Ollama health check works:
    ```bash
    bash tests/test_layer_1_infrastructure.sh | grep "Test 1.2"
    # Expected output contains: "✅ Test 1.2: Ollama API responsive"
    ```
  - [x] Configuration validation works:
    ```bash
    bash tests/test_layer_1_infrastructure.sh | grep "Test 1.5"
    # Expected output: "✅ Test 1.5: Agent model references valid" OR specific error
    ```
  - [x] All 3 required models found:
    ```bash
    bash tests/test_layer_1_infrastructure.sh | grep "Test 1.3"
    # Expected output mentions: qwen2.5-coder:7b-instruct-q8_0, qwen2.5-coder:14b, deepseek-coder-v2:lite
    ```

  **Commit**: YES
  - Message: `test(opencode): implement Layer 1 infrastructure tests`
  - Files: `tests/test_layer_1_infrastructure.sh`, `test_delegation.sh` (if enhanced)
  - Pre-commit: `bash tests/test_layer_1_infrastructure.sh` (should pass or show specific failures)

---

- [x] 2. Implement Layer 2: Model Inference Tests

  **What to do**:
  - Create `tests/test_layer_2_inference.sh`:
    - Test 2.1: Qwen 7B basic inference
      - Query: `curl -s http://127.0.0.1:11434/v1/chat/completions -H "Content-Type: application/json" -d '{"model": "qwen2.5-coder:7b-instruct-q8_0", "messages": [{"role": "user", "content": "Say hello"}], "stream": false}'`
      - Verify: Response contains `.choices[0].message.content` with non-empty string
    - Test 2.2: Qwen 14B basic inference (same pattern)
    - Test 2.3: DeepSeek V2 Lite basic inference (same pattern)
    - Test 2.4: **CRITICAL** - Tool call generation test (Qwen 7B)
      - System prompt: "You have access to a tool called 'search_code' that takes a 'query' parameter. Use it to find Python files."
      - User prompt: "Find all Python files that import FastAPI"
      - Verify: Response contains tool call with name="search_code" and arguments include "query"
      - Verify: JSON structure matches OpenAI tool call format
    - Test 2.5: Response format validation
      - Verify: `.choices[0].finish_reason` is "stop" or "tool_calls"
      - Verify: `.usage.total_tokens` > 0
      - Verify: No truncated responses (check for incomplete JSON)

  **Must NOT do**:
  - Don't test via OpenCode delegation yet (direct Ollama queries only)
  - Don't test actual code search functionality (just verify tool call format)
  - Don't test response quality/correctness (that's Layer 4)

  **Parallelizable**: NO (depends on Task 1 passing)

  **References**:
  **Ollama API**:
  - OpenAI-compatible endpoint: `http://127.0.0.1:11434/v1/chat/completions`
  - API docs: https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-chat-completion

  **Tool Call Format** (OpenAI spec):
  ```json
  {
    "choices": [{
      "message": {
        "role": "assistant",
        "tool_calls": [{
          "id": "call_abc123",
          "type": "function",
          "function": {
            "name": "search_code",
            "arguments": "{\"query\":\"import FastAPI\"}"
          }
        }]
      },
      "finish_reason": "tool_calls"
    }]
  }
  ```

  **System Prompt for Tool Test**:
  ```json
  {
    "model": "qwen2.5-coder:7b-instruct-q8_0",
    "messages": [
      {"role": "system", "content": "You have access to a tool called 'search_code' that takes a 'query' parameter. You must respond with a tool call."},
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
    ]
  }
  ```

  **Existing Test Pattern**:
  - `test_delegation.sh` lines 63-82 - Direct Ollama inference pattern

  **Acceptance Criteria**:

  **Manual Execution Verification**:
  - [x] All 5 tests execute:
    ```bash
    bash tests/test_layer_2_inference.sh
    # Expected: Tests 2.1-2.5 run with ✅/❌ output
    # Exit code: 0 if all pass, 1 if any fail
    ```
  - [x] Basic inference works for all models:
    ```bash
    bash tests/test_layer_2_inference.sh | grep -E "Test 2\.[1-3]"
    # Expected: ✅ for Qwen 7B, Qwen 14B, DeepSeek V2
    ```
  - [x] Tool call test (CRITICAL):
    ```bash
    bash tests/test_layer_2_inference.sh | grep "Test 2.4"
    # Expected: ✅ Tool call generation successful
    # OR: ❌ with specific error (e.g., "Invalid JSON", "Missing tool_calls field")
    ```
  - [x] Response format valid:
    ```bash
    bash tests/test_layer_2_inference.sh | grep "Test 2.5"
    # Expected: ✅ Response format valid (finish_reason present, tokens counted)
    ```
  - [x] Capture actual tool call response:
    ```bash
    curl -s http://127.0.0.1:11434/v1/chat/completions -H "Content-Type: application/json" -d '...' | jq '.choices[0].message'
    # Manual verification: Check if tool_calls array exists and has valid structure
    ```

  **Commit**: YES
  - Message: `test(opencode): implement Layer 2 model inference tests with tool call validation`
  - Files: `tests/test_layer_2_inference.sh`
  - Pre-commit: `bash tests/test_layer_2_inference.sh` (may fail - that's ok, we're discovering issues)

---

- [x] 3. Implement Layer 3: Agent Routing Tests

  **What to do**:
  - Create `tests/test_layer_3_routing.sh`:
    - Test 3.1: Explicit agent invocation routing
      - Start OpenCode web in background (or use existing instance)
      - Monitor network traffic: `ss -tn | grep ':11434'` OR `tcpdump -i any port 11434 -c 10 -nn` (if sudo available)
      - Trigger local agent: Send API request to OpenCode simulating "@explore find Python files"
      - Verify: Network traffic shows connection to 127.0.0.1:11434 during request
      - Trigger cloud agent: Send API request simulating "@sisyphus analyze architecture"
      - Verify: NO network traffic to 127.0.0.1:11434
    - Test 3.2: Category-based delegation routing
      - Simulate delegate_task with category="quick" (should use Ollama)
      - Simulate delegate_task with category="ultrabrain" (should use cloud)
      - Verify routing via network monitoring
    - Test 3.3: Routing audit (100 test requests)
      - Send 50 local agent requests, 50 cloud agent requests
      - Log which backend responded for each (check response headers, timing, or network traffic)
      - Report: "100/100 routed correctly" or "3 misrouted: ..."

  **Must NOT do**:
  - Don't test response quality yet (that's Layer 4)
  - Don't modify OpenCode configuration
  - Don't test actual functionality, just routing

  **Parallelizable**: YES (with Task 1 complete, parallel with Task 2)

  **References**:
  **OpenCode API** (for sending test requests):
  - OpenCode web runs on port 4096 (per user's setup: `opencode web --port 4096 --hostname 0.0.0.0`)
  - WebSocket endpoint: `ws://localhost:4096/` (for chat interface)
  - May need to inspect browser network traffic or use OpenCode CLI to trigger delegation

  **Network Monitoring**:
  - `ss -tn | grep ':11434'` - Check active connections to Ollama
  - `tcpdump -i any port 11434 -nn` - Capture packets to Ollama (requires sudo)
  - Alternative: Check Ollama `/api/ps` before/after request to see if model loaded

  **Existing Monitoring Tool**:
  - `monitor_ollama.sh` - Real-time monitoring pattern
  - Shows running models via `curl -s http://127.0.0.1:11434/api/ps | jq '.models[]'`

  **Agent/Category Routing** (from oh-my-opencode.json):
  - Local: explore, metis, quick, unspecified-low
  - Cloud: sisyphus, oracle, prometheus, librarian, ultrabrain, unspecified-high

  **Test Approach**:
  - **Option A**: Use OpenCode CLI if available to trigger agents programmatically
  - **Option B**: Monitor `/api/ps` endpoint - if model loads, Ollama was used
  - **Option C**: Parse OpenCode logs for delegation events (if logs exist)

  **Acceptance Criteria**:

  **Manual Execution Verification**:
  - [x] Routing test script runs:
    ```bash
    bash tests/test_layer_3_routing.sh
    # Expected: Tests 3.1-3.3 run with ✅/❌ output
    # May require OpenCode web running: opencode web --port 4096
    ```
  - [x] Local agent routes to Ollama:
    ```bash
    # Before test: Check baseline
    curl -s http://127.0.0.1:11434/api/ps | jq '.models'
    # Run test that triggers explore agent
    bash tests/test_layer_3_routing.sh | grep "Test 3.1"
    # After: Check if model loaded
    curl -s http://127.0.0.1:11434/api/ps | jq '.models'
    # Expected: qwen2.5-coder:7b-instruct-q8_0 appears in loaded models
    ```
  - [x] Cloud agent does NOT route to Ollama:
    ```bash
    # Before test: Check baseline (no models loaded)
    curl -s http://127.0.0.1:11434/api/ps | jq '.models | length'
    # Expected: 0
    # Run test that triggers sisyphus agent
    # After: Check models still empty
    curl -s http://127.0.0.1:11434/api/ps | jq '.models | length'
    # Expected: Still 0 (no Ollama activity)
    ```
  - [x] Routing audit complete:
    ```bash
    bash tests/test_layer_3_routing.sh | grep "Test 3.3"
    # Expected output: "✅ 100/100 routed correctly" OR "⚠️ X/100 misrouted"
    ```

  **Commit**: YES
  - Message: `test(opencode): implement Layer 3 agent routing validation tests`
  - Files: `tests/test_layer_3_routing.sh`
  - Pre-commit: `bash -n tests/test_layer_3_routing.sh` (syntax check only; actual test may require OpenCode running)

---

- [x] 4. Implement Layer 4: Response Quality Tests

  **What to do**:
  - Create `tests/test_layer_4_quality.sh`:
    - Test 4.1: Code search task quality (explore agent)
      - Send request via OpenCode: "@explore find all Python files that import FastAPI"
      - Verify: Response contains file paths (e.g., `main.py`, `route_*.py`)
      - Verify: File paths actually exist in project
      - Verify: Listed files DO import FastAPI (grep verification)
      - Compare: Local (explore) vs cloud response (if running librarian for same task)
    - Test 4.2: Analysis task quality (metis agent)
      - Send request: "@metis analyze this code for potential issues" (provide sample code)
      - Verify: Response is NOT generic (check for specific line numbers, code references)
      - Verify: No hallucinated file references (check mentioned files exist)
      - Flag: If response is vague ("looks good", "consider refactoring") → WARN
    - Test 4.3: Simple refactor task (quick category)
      - Send delegate_task(category="quick", prompt="Fix typo 'connexion' → 'connection' in test.py line 42")
      - Verify: Tool call is Edit with oldString containing "connexion", newString containing "connection"
      - Verify: File reference is correct (test.py exists)
      - Verify: No AI slop (e.g., doesn't also refactor unrelated code)

  **Must NOT do**:
  - Don't test complex workflows (single-task tests only)
  - Don't test edge cases (stick to common use cases)
  - Don't compare models extensively (brief quality check, not benchmarking)

  **Parallelizable**: NO (depends on Tasks 2 & 3 passing)

  **References**:
  **Test Files** (use actual project files as test subjects):
  - `main.py` - Imports FastAPI (Test 4.1)
  - `services/pty_service.py` - Sample code for analysis (Test 4.2)
  - Create `tests/fixtures/test_typo.py` with intentional typo for Test 4.3

  **Quality Criteria**:
  - **Good response**: Specific file paths, line numbers, concrete suggestions
  - **Bad response**: Generic advice, hallucinated files, vague statements
  - **AI slop patterns**: Over-engineering, unnecessary abstractions, unrelated changes

  **OpenCode Interaction**:
  - If OpenCode CLI supports programmatic requests: Use that
  - Alternative: Simulate requests via API or parse session logs
  - Fallback: Manual testing with documented steps

  **Expected Outcomes**:
  - Local models (Qwen 7B) may have lower quality than cloud models
  - Goal: Identify WHEN local is acceptable vs when cloud is needed
  - Document: "Use local for quick searches, cloud for complex analysis"

  **Acceptance Criteria**:

  **Manual Execution Verification**:
  - [x] Code search test (Test 4.1):
    ```bash
    bash tests/test_layer_4_quality.sh | grep "Test 4.1"
    # Expected: ✅ Code search successful: found N files
    # OR: ❌ Search failed: no results / incorrect results
    ```
  - [x] Verify search results are correct:
    ```bash
    # Test should output found files
    bash tests/test_layer_4_quality.sh | grep -A 10 "Test 4.1"
    # Manually check: Do listed files actually import FastAPI?
    grep -l "from fastapi import\|import fastapi" $(bash tests/test_layer_4_quality.sh | grep "Found:" | cut -d: -f2)
    ```
  - [x] Analysis quality test (Test 4.2):
    ```bash
    bash tests/test_layer_4_quality.sh | grep "Test 4.2"
    # Expected: ✅ Analysis quality: specific OR ⚠️ Analysis quality: generic (warning)
    # Check response for specificity (line numbers, variable names)
    ```
  - [x] Refactor test (Test 4.3):
    ```bash
    bash tests/test_layer_4_quality.sh | grep "Test 4.3"
    # Expected: ✅ Refactor task: correct tool call
    # OR: ❌ Tool call malformed / incorrect parameters
    ```
  - [x] Evidence of tool call format:
    ```bash
    # Test should log actual tool call received
    bash tests/test_layer_4_quality.sh | grep -A 5 "Tool call:"
    # Verify JSON structure matches: {"name": "Edit", "arguments": {"filePath": "...", "oldString": "connexion", "newString": "connection"}}
    ```

  **Commit**: YES
  - Message: `test(opencode): implement Layer 4 response quality tests`
  - Files: `tests/test_layer_4_quality.sh`, `tests/fixtures/test_typo.py`
  - Pre-commit: `bash -n tests/test_layer_4_quality.sh` (syntax check; actual test may require OpenCode running)

---

- [x] 5. Create Comprehensive Test Runner and Documentation

  **What to do**:
  - Create `comprehensive_test_suite.sh`:
    - Main runner that calls: Layer 1, Layer 2, Layer 3, Layer 4 in sequence
    - Aggregate results: Count total ✅, ⚠️, ❌ across all layers
    - Generate test report:
      ```
      OpenCode + OMO Test Report
      ===========================
      Run Date: YYYY-MM-DD HH:MM:SS
      Duration: Xs
      
      Layer 1: Infrastructure - PASS (6/6 tests)
      Layer 2: Model Inference - PASS with WARNINGS (4/5 tests, 1 warning)
      Layer 3: Agent Routing - PASS (3/3 tests)
      Layer 4: Response Quality - FAIL (2/3 tests)
      
      OVERALL: 3/4 layers passing
      BLOCKING ISSUES:
        - Test 4.2: metis analysis quality too generic
      WARNINGS:
        - Test 2.4: Qwen 7B tool call format occasionally inconsistent
      ```
    - Support layer selection: `./comprehensive_test_suite.sh 1` (run Layer 1 only) or `./comprehensive_test_suite.sh all`
  - Create `TESTING_GUIDE.md`:
    - How to run tests: `./comprehensive_test_suite.sh all`
    - How to interpret results: What each layer tests, what failures mean
    - How to debug failures:
      - ❌ Layer 1: Check Ollama service, config files
      - ❌ Layer 2: Try model manually, check Ollama logs
      - ❌ Layer 3: Verify oh-my-opencode.json routing config
      - ❌ Layer 4: Review response quality, consider switching agent to cloud
    - When to run tests: Before starting work, after config changes, when seeing silent failures
  - Update `DELEGATION_TEST_QUICKSTART.md`:
    - Add section: "Running Comprehensive Tests"
    - Link to new `TESTING_GUIDE.md`

  **Must NOT do**:
  - Don't create automated CI/CD pipeline (manual execution only)
  - Don't add monitoring/alerting (future enhancement)
  - Don't implement Layer 5/6 (out of scope)

  **Parallelizable**: NO (depends on all previous tasks)

  **References**:
  **Report Format Inspiration**:
  - pytest output format - Clear pass/fail with summary
  - Jest test reports - Color-coded results
  - Keep it simple: bash echo with ✅/⚠️/❌ emojis

  **Existing Documentation**:
  - `DELEGATION_TEST_QUICKSTART.md` - Current manual test guide
  - `test_delegation.sh` - Existing test script to integrate with

  **Documentation Structure**:
  ```markdown
  # OpenCode Testing Guide
  
  ## Quick Start
  ./comprehensive_test_suite.sh all
  
  ## What Gets Tested
  - Layer 1: Is Ollama healthy?
  - Layer 2: Do models produce valid output?
  - Layer 3: Are requests routed correctly?
  - Layer 4: Is output quality acceptable?
  
  ## Interpreting Results
  ✅ PASS: Everything working as expected
  ⚠️ WARN: Working but suboptimal (e.g., low quality)
  ❌ FAIL: Not working, needs fixing
  
  ## Debugging Failures
  [Specific troubleshooting for each layer]
  
  ## When to Run Tests
  - Before starting development session
  - After changing OpenCode/OMO config
  - When seeing "improper responses" errors
  - Weekly as maintenance check
  ```

  **Acceptance Criteria**:

  **Manual Execution Verification**:
  - [x] Main test runner executes all layers:
    ```bash
    ./comprehensive_test_suite.sh all
    # Expected: Runs Layer 1 → 2 → 3 → 4 in sequence
    # Duration: <10 minutes
    # Exit code: 0 if all pass, 1 if any fail
    ```
  - [x] Test report generated:
    ```bash
    ./comprehensive_test_suite.sh all | tail -20
    # Expected: See "OVERALL: X/4 layers passing" summary
    # See: BLOCKING ISSUES section if any fails
    # See: WARNINGS section if any warnings
    ```
  - [x] Layer selection works:
    ```bash
    ./comprehensive_test_suite.sh 1
    # Expected: Only Layer 1 tests run
    ./comprehensive_test_suite.sh 2
    # Expected: Only Layer 2 tests run
    ```
  - [x] Documentation complete and accurate:
    ```bash
    cat TESTING_GUIDE.md
    # Verify: Covers all 4 layers
    # Verify: Includes debugging steps
    # Verify: Examples are correct
    ```
  - [x] Integration with existing docs:
    ```bash
    grep -i "comprehensive_test_suite" DELEGATION_TEST_QUICKSTART.md
    # Expected: Reference to new comprehensive tests added
    ```

  **Commit**: YES
  - Message: `test(opencode): create comprehensive test runner and documentation`
  - Files: `comprehensive_test_suite.sh`, `TESTING_GUIDE.md`, `DELEGATION_TEST_QUICKSTART.md` (updated)
  - Pre-commit: `bash comprehensive_test_suite.sh all` (full test run to verify integration)

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 0 | `test(opencode): add test infrastructure and helper library` | tests/lib/test_helpers.sh, tests/fixtures/sample_code.py, .gitignore | bash -n tests/lib/test_helpers.sh |
| 1 | `test(opencode): implement Layer 1 infrastructure tests` | tests/test_layer_1_infrastructure.sh, test_delegation.sh | bash tests/test_layer_1_infrastructure.sh |
| 2 | `test(opencode): implement Layer 2 model inference tests with tool call validation` | tests/test_layer_2_inference.sh | bash tests/test_layer_2_inference.sh |
| 3 | `test(opencode): implement Layer 3 agent routing validation tests` | tests/test_layer_3_routing.sh | bash -n tests/test_layer_3_routing.sh |
| 4 | `test(opencode): implement Layer 4 response quality tests` | tests/test_layer_4_quality.sh, tests/fixtures/test_typo.py | bash -n tests/test_layer_4_quality.sh |
| 5 | `test(opencode): create comprehensive test runner and documentation` | comprehensive_test_suite.sh, TESTING_GUIDE.md, DELEGATION_TEST_QUICKSTART.md | bash comprehensive_test_suite.sh all |

---

## Success Criteria

### Verification Commands
```bash
# Run comprehensive test suite
./comprehensive_test_suite.sh all

# Expected output: Test report with clear pass/fail/warn for each layer
# Expected duration: <10 minutes
# Expected: Identifies any specific issues (e.g., "Qwen 7B tool call format invalid")
```

### Final Checklist
- [x] All "Must Have" present:
  - [x] Layer 1: Infrastructure tests implemented
  - [x] Layer 2: Model inference tests implemented (including tool call validation)
  - [x] Layer 3: Agent routing tests implemented
  - [x] Layer 4: Response quality tests implemented
  - [x] Test runner creates clear reports
  - [x] Documentation explains how to run and debug
- [x] All "Must NOT Have" absent:
  - [x] No auto-fallback to cloud (tests fail loudly)
  - [x] No automation/cron (manual execution only)
  - [x] No Layer 5/6 implementation (out of scope)
  - [x] No monitoring dashboard (future enhancement)
  - [x] No config changes (tests only read existing config)
  - [x] No external dependencies beyond curl/jq/bash
- [x] User can confidently say:
  - [x] "I know Ollama is working (or why it's not)"
  - [x] "Requests route to correct backends 100% of the time"
  - [x] "Local models produce acceptable quality for quick tasks"
  - [x] "I'll immediately see failures instead of discovering them silently"
