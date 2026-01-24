# MCP Usage Verification Scripts

This directory contains scripts to verify that AI assistants use LLDB MCP tools for debugging rather than analyzing source code directly.

## Purpose

When testing AI-driven debugging with the LLDB MCP server, we need to ensure the AI:
- ✅ Uses MCP tools (lldb_initialize, lldb_createTarget, etc.)
- ❌ Does NOT read source code files (.c, .cpp, etc.)

This verification prevents false positives where AI "debugs" by reading source code instead of using the debugger.

## Scripts

### `verify_mcp_usage.py`

Analyzes debugging transcripts to verify proper MCP tool usage.

**Usage:**
```bash
python scripts/verify_mcp_usage.py <transcript_file> <scenario>
```

**Scenarios:**
- `crash` - Crash detection and analysis (requires: stackTrace, analyzeCrash)
- `breakpoint` - Breakpoint-based debugging (requires: setBreakpoint, evaluate)
- `memory` - Memory inspection (requires: readMemory, setWatchpoint)

**Example:**
```bash
# Verify a crash debugging session
python scripts/verify_mcp_usage.py logs/session_abc123.txt crash

# Output:
# ============================================================
# MCP Usage Verification Results - Scenario: crash
# ============================================================
# Tool Coverage: 6/6 (100%)
# ✅ Found MCP Tool Calls:
#   - lldb_initialize
#   - lldb_createTarget
#   - lldb_launch
#   ...
# ✅ PASS: AI used MCP tools correctly
```

**Exit Codes:**
- `0` - Verification passed (AI used MCP tools correctly)
- `1` - Verification failed (AI read source code or insufficient tool usage)

**Output Files:**
- `<transcript>.verification.json` - Detailed results in JSON format

## Test Files

### `test_transcript_valid.txt`

Example of a valid debugging session where AI uses MCP tools correctly.

### `test_transcript_invalid.txt`

Example of an invalid session where AI reads source code instead.

## Running Tests

Test the verification script:

```bash
# Test with valid transcript (should PASS)
python scripts/verify_mcp_usage.py scripts/test_transcript_valid.txt crash

# Test with invalid transcript (should FAIL)
python scripts/verify_mcp_usage.py scripts/test_transcript_invalid.txt crash
```

## Integration with AI Testing

### Step 1: Configure Test Environment

Ensure AI cannot access source files:
```bash
# Only provide binary path, not source path
BINARY="/path/to/examples/client/c_test/null_deref/null_deref"
```

### Step 2: Run AI Debugging Session

Use this prompt template:
```
Debug the binary at /path/to/binary

REQUIREMENTS:
1. You MUST use LLDB MCP tools for debugging
2. You DO NOT have access to source code files
3. You can ONLY use the compiled binary
4. After finding the bug, use lldb_getTranscript to show your debugging process
```

### Step 3: Extract Transcript

After AI completes debugging:
```bash
# Get transcript from MCP server logs or AI response
# Save to file, e.g., logs/test_session.txt
```

### Step 4: Verify MCP Usage

```bash
python scripts/verify_mcp_usage.py logs/test_session.txt crash
```

### Step 5: Check Results

- Exit code 0 = Test passed (AI used MCP tools)
- Exit code 1 = Test failed (AI cheated by reading source)

## Verification Criteria

### Required Base Tools (All Scenarios)
- `lldb_initialize` - Session creation
- `lldb_createTarget` - Binary loading
- `lldb_launch` - Process execution
- `lldb_pollEvents` - Event monitoring

### Scenario-Specific Tools

**Crash Scenario:**
- `lldb_stackTrace` - Crash location
- `lldb_analyzeCrash` - Exploitability analysis

**Breakpoint Scenario:**
- `lldb_setBreakpoint` - Set breakpoint
- `lldb_evaluate` - Inspect variables

**Memory Scenario:**
- `lldb_readMemory` - Memory inspection
- `lldb_setWatchpoint` - Memory watchpoints

### Validation Rules

1. **Tool Coverage**: Must find ≥70% of required tools
2. **No Source Reads**: Zero source file reads allowed
3. **Both Must Pass**: Coverage AND no-reads must both be true

## Troubleshooting

### False Negatives

If verification fails but AI did use MCP:
- Check transcript format matches expected patterns
- Ensure tool names are exact (case-sensitive)
- Verify transcript contains complete session

### False Positives

If verification passes but AI read source:
- Check for alternative read patterns (vim, less, etc.)
- Update regex patterns in verify_mcp_usage.py
- Review actual transcript manually

## Extending the Verifier

To add new scenarios:

1. Edit `verify_mcp_usage.py`
2. Add to `scenario_tools` dictionary:
   ```python
   scenario_tools = {
       "crash": ["lldb_stackTrace", "lldb_analyzeCrash"],
       "your_scenario": ["lldb_toolA", "lldb_toolB"],
   }
   ```
3. Update help text and documentation

## See Also

- `dev_docs/PLAN.md` - Full testing plan with verification protocol
- `examples/client/c_test/README.md` - Test programs documentation
- `tests/e2e/` - End-to-end automated tests
