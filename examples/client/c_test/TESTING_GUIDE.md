# AI Debugging Testing Guide

This guide explains how to test AI debugging capabilities with LLDB MCP Server using the verification system.

## Quick Start

### 1. Build Test Programs

```bash
cd examples/client/c_test
./build_all.sh
```

Verify all binaries are ready:
```bash
../../scripts/check_test_binaries.sh
```

Expected output:
```
✅ All 8 test binaries are ready
```

### 2. Start MCP Server

#### Option A: Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "python3",
      "args": [
        "-m",
        "lldb_mcp_server.fastmcp_server"
      ],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1"
      }
    }
  }
}
```

Restart Claude Desktop.

#### Option B: HTTP Mode (for testing)

```bash
cd /path/to/lldb-mcp-server
source .venv/bin/activate
LLDB_MCP_ALLOW_LAUNCH=1 python -m lldb_mcp_server.fastmcp_server \
  --transport http --port 8765
```

### 3. Run a Test Debugging Session

Start a new conversation with Claude and use this prompt:

```
Debug the binary at /absolute/path/to/examples/client/c_test/null_deref/null_deref

REQUIREMENTS:
1. You MUST use LLDB MCP tools for debugging
2. You DO NOT have access to source code files
3. You can ONLY use the compiled binary
4. After finding the bug, use lldb_getTranscript to show your debugging process

Please identify:
- What type of bug causes the crash
- The exact location (function name and approximate instruction)
- The root cause of the bug
- How to fix it
```

**Important:**
- Use **absolute paths** to binaries
- Do NOT mention `.c` source files
- Explicitly state "no source code access"

### 4. Extract Debugging Transcript

After AI completes debugging, ask:

```
Please use lldb_getTranscript to show me the complete debugging transcript.
```

Save the transcript to a file:
```bash
# Copy AI's transcript response to a file
cat > logs/test_null_deref_$(date +%Y%m%d_%H%M%S).txt
# Paste transcript, then Ctrl+D
```

### 5. Verify MCP Tool Usage

Run the verification script:

```bash
python scripts/verify_mcp_usage.py \
  logs/test_null_deref_20260124_103000.txt \
  crash
```

Expected output for valid test:
```
============================================================
MCP Usage Verification Results - Scenario: crash
============================================================
Tool Coverage: 6/6 (100%)
✅ Found MCP Tool Calls:
  - lldb_initialize
  - lldb_createTarget
  - lldb_launch
  - lldb_pollEvents
  - lldb_stackTrace
  - lldb_analyzeCrash
✅ No source code reads detected
✅ PASS: AI used MCP tools correctly
```

### 6. Document Results

Copy the test results template:
```bash
cp TEST_RESULTS.template.md TEST_RESULTS_$(date +%Y%m%d).md
```

Fill in:
- AI's diagnosis
- Verification results
- Your observations
- Tool usage analysis

## Test Scenarios

### Scenario 1: Crash Detection (null_deref, divide_by_zero)

**Goal:** AI detects crash and identifies root cause

**Verification scenario:** `crash`

**Expected tools:**
- lldb_initialize
- lldb_createTarget
- lldb_launch
- lldb_pollEvents
- lldb_stackTrace
- lldb_analyzeCrash

**Prompt template:** See section 3 above

### Scenario 2: Breakpoint Debugging (buffer_overflow, format_string)

**Goal:** AI sets breakpoints and inspects variables

**Verification scenario:** `breakpoint`

**Expected tools:**
- lldb_initialize
- lldb_createTarget
- lldb_setBreakpoint
- lldb_launch
- lldb_evaluate
- lldb_stepOver/stepIn

**Prompt template:**
```
Debug the binary at /path/to/buffer_overflow/buffer_overflow

REQUIREMENTS:
1. Use LLDB MCP tools only (no source code)
2. Set a breakpoint at main
3. Inspect variables and identify the buffer overflow
4. After debugging, use lldb_getTranscript

Identify the vulnerability and suggest a fix.
```

### Scenario 3: Memory Analysis (use_after_free, double_free)

**Goal:** AI analyzes memory operations

**Verification scenario:** `memory`

**Expected tools:**
- lldb_initialize
- lldb_createTarget
- lldb_launch
- lldb_readMemory
- lldb_setWatchpoint (optional)

**Prompt template:**
```
Debug the binary at /path/to/use_after_free/use_after_free

REQUIREMENTS:
1. Use LLDB MCP tools only (no source code)
2. Track memory allocations and accesses
3. Identify the use-after-free bug
4. After debugging, use lldb_getTranscript
```

## Common Issues

### Issue: AI Reads Source Code

**Symptom:** Verification fails with "Source code reads detected"

**Solution:**
- Ensure prompt explicitly forbids source access
- Don't mention `.c` file paths in prompts
- Use absolute paths to binaries only

### Issue: Insufficient Tool Usage

**Symptom:** Verification fails with "Insufficient tool usage"

**Solution:**
- Check if MCP server is running
- Verify MCP tools are available to AI
- Check Claude Desktop config is correct
- Try more explicit instructions in prompt

### Issue: Transcript Not Available

**Symptom:** AI doesn't show transcript

**Solution:**
- Explicitly ask for transcript: "Use lldb_getTranscript"
- Check if session is still active
- Verify lldb_getTranscript tool is available

## Verification Script Reference

### Usage

```bash
python scripts/verify_mcp_usage.py <transcript_file> <scenario>
```

### Scenarios

| Scenario | Use Case | Required Tools |
|----------|----------|----------------|
| `crash` | Crash detection | stackTrace, analyzeCrash |
| `breakpoint` | Variable inspection | setBreakpoint, evaluate |
| `memory` | Memory operations | readMemory, setWatchpoint |

### Exit Codes

- `0` - PASS: AI used MCP tools correctly
- `1` - FAIL: Source code read or insufficient tool usage

### Output Files

- `<transcript>.verification.json` - Detailed JSON results

## Test Programs Reference

| Program | Bug Type | Expected Behavior | Difficulty |
|---------|----------|-------------------|------------|
| null_deref | Null pointer dereference | Immediate SIGSEGV crash | Easy |
| buffer_overflow | Stack buffer overflow | Crash or undefined behavior | Medium |
| use_after_free | Use after free | Crash or corruption | Hard |
| divide_by_zero | Integer division by zero | SIGFPE crash | Easy |
| stack_overflow | Stack overflow (recursion) | SIGSEGV from stack exhaustion | Easy |
| infinite_loop | Infinite loop | Hangs (requires pause/interrupt) | Medium |
| format_string | Format string vulnerability | Crash or information leak | Medium |
| double_free | Double free | Crash in malloc | Medium |

## Tips for Effective Testing

### Do's
- ✅ Use absolute paths to binaries
- ✅ Explicitly state "no source code access"
- ✅ Ask for transcript at the end
- ✅ Run verification script on every test
- ✅ Document both successes and failures

### Don'ts
- ❌ Don't mention `.c` source file paths
- ❌ Don't have source files open in editor during test
- ❌ Don't assume AI used MCP without verification
- ❌ Don't skip transcript collection
- ❌ Don't test with debug symbols stripped binaries

## Next Steps

After completing tests:

1. Fill out `TEST_RESULTS_[date].md` with findings
2. Update `dev_docs/PLAN.md` verification checklist
3. Report any MCP server issues to GitHub
4. Share results with development team

## See Also

- `scripts/README.md` - Verification script documentation
- `dev_docs/PLAN.md` - Complete testing plan
- `README.md` - Project overview and setup
