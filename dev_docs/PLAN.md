# LLDB MCP Server - Phase 3 Development Plan

## Overview

This plan reorganizes the next development phase into three sequential stages:
1. **Phase 1: Real-World Testing** - 使用真实 C 程序测试 MCP 工具和 AI 调试效果
2. **Phase 2: Smithery Publishing** - 上架到 Smithery 市场
3. **Phase 3: Skills Integration** - 将 MCP 工具封装为 Skills

---

## Phase 1: Real-World Testing (Priority: Highest)

### Objective

Validate that the MCP server and its 40 tools work effectively for AI-driven debugging of real C programs with various bug types.

### Current Status

- ✅ Basic test infrastructure (pytest, 45 tests passing: 34 unit + 11 e2e)
- ✅ 8 test programs with different bug types created
- ✅ Build script (`build_all.sh`) created
- ✅ E2E test framework created
- ⚠️ Need manual AI testing with Claude Code/Desktop

### Test Programs (Already Created)

**Location:** `examples/client/c_test/`

| Program | Bug Type | Status |
|---------|----------|--------|
| `null_deref.c` | Null pointer dereference | ✅ Created |
| `buffer_overflow.c` | Stack buffer overflow | ✅ Created |
| `use_after_free.c` | Use after free | ✅ Created |
| `infinite_loop.c` | Infinite loop | ✅ Created |
| `divide_by_zero.c` | Division by zero | ✅ Created |
| `stack_overflow.c` | Stack overflow (recursion) | ✅ Created |
| `format_string.c` | Format string vulnerability | ✅ Created |
| `double_free.c` | Double free | ✅ Created |

### Implementation Steps

#### 1.1 Build Test Programs

```bash
cd examples/client/c_test
./build_all.sh
```

Verify all 8 programs compile with debug symbols.

#### 1.2 Run Automated E2E Tests

```bash
# Run all e2e tests
pytest tests/e2e/ -v

# Run specific test scenarios
pytest tests/e2e/test_ai_debugging.py::TestCrashDetection -v
pytest tests/e2e/test_ai_debugging.py::TestMemoryCorruptionDetection -v
```

**Expected Results:**
- All crash detection tests pass
- Stack traces are correctly retrieved
- Exploitability analysis works
- Register states are readable at crash

#### 1.3 Manual AI Testing with Claude Code

**Setup:**
```bash
# Configure Claude Desktop/Code MCP server
# Add to claude_desktop_config.json or mcp.json:
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "python3",
      "args": ["-m", "lldb_mcp_server.fastmcp_server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1"
      }
    }
  }
}
```

**Test Scenarios:**

1. **Scenario: Null Pointer Crash**
   - Prompt: "Debug the null_deref program at `examples/client/c_test/null_deref/null_deref` and identify the bug"
   - Expected AI workflow:
     - Initialize session
     - Load binary
     - Launch process
     - Detect crash
     - Analyze crash location
     - Report null pointer dereference at specific line

2. **Scenario: Buffer Overflow**
   - Prompt: "Debug buffer_overflow and explain the vulnerability with remediation"
   - Expected AI workflow:
     - Set breakpoint at main
     - Inspect buffer size
     - Identify strcpy overflow
     - Suggest strncpy/bounds checking

3. **Scenario: Memory Corruption**
   - Prompt: "Find the use-after-free bug in the program"
   - Expected AI workflow:
     - Set watchpoints on memory
     - Track allocation/deallocation
     - Identify UAF pattern

#### 1.4 Verification Mechanism (Ensure MCP Usage)

**Critical Requirement:** AI must use MCP tools for debugging, NOT source code analysis.

**Test Protocol:**

1. **Prevent Source Code Access**
   - ⚠️ **DO NOT** provide source code file paths in prompts
   - ⚠️ **DO NOT** allow AI to read `.c` files directly
   - ✅ **ONLY** provide compiled binary paths

   Example prompts:
   - ✅ Good: "Debug the binary at `examples/client/c_test/null_deref/null_deref`"
   - ❌ Bad: "Debug `examples/client/c_test/null_deref/null_deref.c`"

2. **Require Explicit Tool Usage**

   Add to each test prompt:
   ```
   IMPORTANT: You must use the LLDB MCP tools to debug this binary.
   DO NOT read the source code. You only have access to the compiled binary.
   After debugging, retrieve the full transcript using lldb_getTranscript
   to show your debugging process.
   ```

3. **Verify Tool Call Sequence**

   After AI completes debugging, check the transcript contains these calls:

   **Required MCP calls (minimum):**
   ```
   ✅ lldb_initialize          # Session creation
   ✅ lldb_createTarget        # Binary loading
   ✅ lldb_launch              # Process execution
   ✅ lldb_pollEvents          # Event monitoring
   ✅ lldb_getTranscript       # Debugging log retrieval
   ```

   **Scenario-specific calls:**

   For crash detection:
   ```
   ✅ lldb_stackTrace          # Crash location
   ✅ lldb_analyzeCrash        # Exploitability analysis
   ✅ lldb_readRegisters       # CPU state
   ```

   For breakpoint debugging:
   ```
   ✅ lldb_setBreakpoint       # Set breakpoint
   ✅ lldb_evaluate            # Inspect variables
   ✅ lldb_stepOver/stepIn     # Code stepping
   ```

4. **Automated Verification Script**

   Create `scripts/verify_mcp_usage.py`:

   ```python
   #!/usr/bin/env python3
   """Verify AI used MCP tools instead of source code analysis."""

   import json
   import re
   from pathlib import Path

   def verify_transcript(transcript_text: str, scenario: str) -> dict:
       """Verify transcript contains required MCP tool calls."""

       # Parse transcript for tool calls
       required_base = [
           "lldb_initialize",
           "lldb_createTarget",
           "lldb_launch",
           "lldb_pollEvents",
       ]

       scenario_tools = {
           "crash": ["lldb_stackTrace", "lldb_analyzeCrash"],
           "breakpoint": ["lldb_setBreakpoint", "lldb_evaluate"],
           "memory": ["lldb_readMemory", "lldb_setWatchpoint"],
       }

       required = required_base + scenario_tools.get(scenario, [])

       found_tools = []
       for tool in required:
           if tool in transcript_text:
               found_tools.append(tool)

       # Check for source code file reads (should NOT happen)
       source_read_pattern = r'(Read|cat|open).*\.c\b'
       source_reads = re.findall(source_read_pattern, transcript_text)

       return {
           "required_tools": required,
           "found_tools": found_tools,
           "missing_tools": list(set(required) - set(found_tools)),
           "source_reads": source_reads,
           "valid": len(found_tools) >= len(required) * 0.7 and not source_reads
       }

   if __name__ == "__main__":
       import sys
       if len(sys.argv) != 3:
           print("Usage: verify_mcp_usage.py <transcript_file> <scenario>")
           sys.exit(1)

       transcript = Path(sys.argv[1]).read_text()
       scenario = sys.argv[2]

       result = verify_transcript(transcript, scenario)
       print(json.dumps(result, indent=2))

       if result["valid"]:
           print("\n✅ PASS: AI used MCP tools correctly")
           sys.exit(0)
       else:
           print("\n❌ FAIL: AI did not use MCP tools correctly")
           if result["source_reads"]:
               print(f"  - Found source code reads: {result['source_reads']}")
           if result["missing_tools"]:
               print(f"  - Missing tool calls: {result['missing_tools']}")
           sys.exit(1)
   ```

5. **Test Execution Checklist**

   For each test scenario:

   - [ ] Start with clean session (no source files open in editor)
   - [ ] Provide ONLY binary path in prompt
   - [ ] Include explicit "no source code" instruction
   - [ ] Wait for AI to complete debugging
   - [ ] Request transcript: "Show me the debugging transcript using lldb_getTranscript"
   - [ ] Save transcript to file
   - [ ] Run verification script: `python scripts/verify_mcp_usage.py transcript.txt <scenario>`
   - [ ] Check verification passes
   - [ ] Document results

6. **Example Complete Test Prompt**

   ```
   Debug the binary at /path/to/examples/client/c_test/null_deref/null_deref

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

7. **Success Criteria**

   A test is considered valid ONLY if:
   - ✅ AI made at least 5 MCP tool calls
   - ✅ AI used lldb_initialize, lldb_createTarget, lldb_launch
   - ✅ AI used scenario-appropriate tools (stackTrace, evaluate, etc.)
   - ✅ AI did NOT read any `.c` source files
   - ✅ AI correctly identified the bug type and location
   - ✅ Transcript shows complete debugging workflow

#### 1.5 Document Test Results

Create `examples/client/c_test/TEST_RESULTS.md` documenting:
- Which test programs AI successfully debugged
- Debugging workflow used
- Tools that were most effective
- Any limitations discovered

### Verification Checklist

**Automated Tests:**
- [x] All 8 programs compile
- [x] Each program exhibits expected bug
- [x] Build script works
- [x] E2E tests pass (11 tests)

**MCP Usage Verification:**
- [x] Verification script created (`scripts/verify_mcp_usage.py`)
- [x] Test prompts documented (see section 1.4.6)
- [x] Test result template created (`TEST_RESULTS.template.md`)
- [x] Binary check script created (`scripts/check_test_binaries.sh`)
- [ ] Claude Code can connect to MCP server
- [ ] AI uses MCP tools (not source analysis) for null_deref
- [ ] AI uses MCP tools (not source analysis) for buffer_overflow
- [ ] AI uses MCP tools (not source analysis) for use_after_free
- [ ] All transcripts contain required MCP tool calls
- [ ] No source file reads detected in any test
- [ ] Test results documented with verification proof

---

## Phase 2: Smithery Publishing (Priority: High)

### Objective

Publish the MCP server to Smithery marketplace for easy installation and discovery.

### Current Status

- ✅ `smithery.yaml` exists and is configured
- ✅ 40 tools documented
- ✅ Version 0.2.0 in pyproject.toml and smithery.yaml
- ✅ MIT license
- ⚠️ GitHub repo visibility (need to confirm public)
- ⚠️ Smithery CLI not installed

### Implementation Steps

#### 2.1 Pre-publish Verification

```bash
# Verify entry point works
python3 -m lldb_mcp_server.fastmcp_server --transport stdio --help

# Check GitHub repo visibility
gh repo view FYTJ/lldb-mcp-server --json visibility

# If private, make it public:
gh repo edit FYTJ/lldb-mcp-server --visibility public
```

#### 2.2 Install Smithery CLI

```bash
# Install Smithery CLI globally
npm install -g @anthropic-ai/smithery

# Login to Smithery (requires Anthropic account)
smithery login

# Verify authentication
smithery whoami
```

#### 2.3 Validate Configuration

```bash
# Validate smithery.yaml
smithery publish --dry-run
```

Fix any validation errors in `smithery.yaml`.

#### 2.4 Publish to Smithery

```bash
# Publish
smithery publish

# Expected output:
# ✓ Published lldb-mcp-server@0.2.0
# ✓ https://smithery.ai/server/lldb-mcp-server
```

#### 2.5 Post-publish Verification

- Visit https://smithery.ai/server/lldb-mcp-server
- Verify:
  - All 40 tools are listed
  - Tool documentation displays correctly
  - Installation instructions work
  - README renders properly

#### 2.6 Update README with Smithery Badge

Add to `README.md`:

```markdown
[![Smithery](https://smithery.ai/badge/lldb-mcp-server)](https://smithery.ai/server/lldb-mcp-server)

## Installation

Install via Smithery:
```bash
npx @anthropic-ai/smithery install lldb-mcp-server
```

Or add manually to your MCP configuration:
```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "python3",
      "args": ["-m", "lldb_mcp_server.fastmcp_server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1"
      }
    }
  }
}
```
```

### Files to Modify

- `README.md` - Add Smithery badge and installation instructions
- `smithery.yaml` - Minor updates if validation fails

### Verification Checklist

- [ ] Server entry point verified
- [ ] GitHub repo is public
- [ ] Smithery CLI installed
- [ ] `smithery publish --dry-run` passes
- [ ] Successfully published to Smithery
- [ ] Server listed on smithery.ai
- [ ] All 40 tools visible on marketplace
- [ ] Installation instructions work
- [ ] README updated with badge

---

## Phase 3: Skills Integration (Priority: Medium)

### Objective

Create a Claude Code skill that provides guided debugging workflows using the MCP server.

### Current Status

- ✅ 40 MCP tools organized in 9 modules
- ✅ Skill template created (`skills/lldb-debugger/skill.md`)
- ✅ Example scenarios created (debug_crash.md, find_vulnerability.md)
- ⚠️ Not tested with Claude Code skill system

### Implementation Steps

#### 3.1 Verify Skill Template

Review `skills/lldb-debugger/skill.md` and ensure it includes:
- Tool categories overview
- Standard debugging workflow
- Important rules and best practices
- Example prompts

#### 3.2 Test Skill with Claude Code

**Setup:**
```bash
# Configure Claude Code to load the skill
# Add skill directory to Claude Code configuration
```

**Test Workflow:**
- Ask Claude to use the lldb-debugger skill
- Verify it follows the documented workflow
- Test with null_deref example
- Verify session management (initialize/terminate)

#### 3.3 Create Additional Example Scenarios

**File:** `skills/lldb-debugger/examples/debug_logic_bug.md`

Example: Debugging an infinite loop without crash
- Set breakpoint in suspected function
- Step through loop iterations
- Identify incorrect loop condition

**File:** `skills/lldb-debugger/examples/analyze_coredump.md`

Example: Post-mortem debugging
- Load core dump with lldb_loadCore
- Analyze crash with lldb_analyzeCrash
- Generate security report

#### 3.4 Update MCP Configuration

Ensure `mcp.json` includes skill-aware configuration:

```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "python3",
      "args": ["-m", "lldb_mcp_server.fastmcp_server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1"
      }
    }
  },
  "skills": {
    "lldb-debugger": {
      "path": "./skills/lldb-debugger",
      "enabled": true
    }
  }
}
```

#### 3.5 Document Skill Usage

Update `README.md` with skill usage section:

```markdown
## Using as a Claude Code Skill

Load the LLDB debugger skill in Claude Code:

1. Configure MCP server (see Installation)
2. Load skill: `/skill lldb-debugger`
3. Ask Claude to debug a program

Example prompts:
- "Debug the crash in my program at /path/to/binary"
- "Find the buffer overflow vulnerability"
- "Analyze this core dump for exploitability"
```

### Files to Modify

- `skills/lldb-debugger/skill.md` - Refine if needed
- `skills/lldb-debugger/examples/` - Add more scenarios
- `mcp.json` - Add skill configuration
- `README.md` - Document skill usage

### Verification Checklist

- [x] Skill prompt template created
- [x] Example scenarios created
- [ ] Skill tested with Claude Code
- [ ] Debugging workflow works end-to-end via skill
- [ ] Multiple example scenarios documented
- [ ] README updated with skill usage

---

## Implementation Timeline

### Immediate (Phase 1)
1. ✅ Build all test programs
2. ✅ Run e2e tests
3. 🔄 Manual AI testing with Claude Code
4. 🔄 Document test results

### Next (Phase 2)
1. Verify GitHub repo is public
2. Install Smithery CLI
3. Validate and publish to Smithery
4. Update README with installation instructions

### Future (Phase 3)
1. Test skill with Claude Code
2. Add more example scenarios
3. Document skill usage
4. Gather user feedback

---

## Success Metrics

### Phase 1 Success
- ✅ All 45 automated tests pass
- AI successfully debugs 6/8 test programs
- Test results documented with workflow examples

### Phase 2 Success
- Server published on Smithery marketplace
- Installation via `npx @anthropic-ai/smithery install` works
- 40 tools visible and documented

### Phase 3 Success
- Skill loads successfully in Claude Code
- Skill-guided debugging completes full workflow
- 3+ documented example scenarios
- Positive user feedback

---

## Notes

### Why This Order?

1. **Phase 1 First**: Validate that the core MCP functionality actually works for real debugging tasks before publishing
2. **Phase 2 Second**: Once validated, publish to make it easily discoverable and installable
3. **Phase 3 Third**: Add skill layer for enhanced UX after core functionality is proven and published

### Current Progress

- **Phase 1**: 80% complete (automated tests done, manual testing pending)
- **Phase 2**: 70% complete (config ready, publishing pending)
- **Phase 3**: 60% complete (templates created, testing pending)
