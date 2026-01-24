# LLDB MCP Server - Features

## Overview

LLDB MCP Server provides 40 MCP tools for programmatic debugging of C/C++ applications on macOS.

---

## Feature Categories

| Category | Tools | Description | Documentation |
|----------|-------|-------------|---------------|
| Session Management | 3 | Debug session lifecycle | [01-session-management.md](features/01-session-management.md) |
| Target Control | 6 | Binary loading, process control | [02-target-control.md](features/02-target-control.md) |
| Breakpoints | 4 | Breakpoint CRUD operations | [03-breakpoints.md](features/03-breakpoints.md) |
| Execution Control | 5 | Step, continue, pause | [04-execution-control.md](features/04-execution-control.md) |
| Inspection | 6 | Threads, frames, stack trace | [05-inspection.md](features/05-inspection.md) |
| Memory Operations | 2 | Memory read/write | [06-memory-operations.md](features/06-memory-operations.md) |
| Watchpoints | 3 | Memory watchpoints | [07-watchpoints.md](features/07-watchpoints.md) |
| Advanced Tools | 4 | Events, commands, transcript | [08-advanced-tools.md](features/08-advanced-tools.md) |
| Security Analysis | 2 | Crash analysis, vulnerability detection | [09-security-analysis.md](features/09-security-analysis.md) |
| Register Operations | 2 | Register read/write | [10-register-operations.md](features/10-register-operations.md) |
| Symbol Search | 1 | Symbol lookup | [11-symbol-search.md](features/11-symbol-search.md) |
| Module Management | 1 | Loaded modules listing | [12-module-management.md](features/12-module-management.md) |
| Core Dump Support | 2 | Core dump load/create | [13-core-dump-support.md](features/13-core-dump-support.md) |

---

## Parameter Conventions

All tools follow these conventions for consistent usage:

### Required Parameters

1. **sessionId** - Always the first parameter for session-specific operations
   - Type: `string`
   - Format: UUID returned by `lldb_initialize`
   - Required for all tools except `lldb_initialize` and `lldb_listSessions`

### Optional Parameters with Defaults

Many tools provide sensible defaults when optional parameters are omitted:

| Tool | Optional Parameter | Default Behavior | Example |
|------|-------------------|------------------|---------|
| `lldb_frames` | `threadId` | Uses currently selected thread | `lldb_frames(sessionId)` |
| `lldb_stackTrace` | `threadId` | Uses currently selected thread | `lldb_stackTrace(sessionId)` |
| `lldb_evaluate` | `frameIndex` | Evaluates in current frame | `lldb_evaluate(sessionId, "x")` |
| `lldb_disassemble` | `address` | Disassembles at program counter | `lldb_disassemble(sessionId)` |
| `lldb_disassemble` | `count` | Disassembles 10 instructions | `lldb_disassemble(sessionId, count=5)` |
| `lldb_readRegisters` | `threadId` | Reads current thread's registers | `lldb_readRegisters(sessionId)` |
| `lldb_searchSymbol` | `module` | Searches all modules | `lldb_searchSymbol(sessionId, "main")` |

### ID-Based References

Tools use integer IDs returned by previous operations:

- **threadId** - Returned by `lldb_threads`, used by `lldb_frames`, `lldb_selectThread`
- **frameId/frameIndex** - Frame index (0 = current, 1 = caller), used by `lldb_evaluate`, `lldb_selectFrame`
- **breakpointId** - Returned by `lldb_setBreakpoint`, used by `lldb_deleteBreakpoint`, `lldb_updateBreakpoint`
- **watchpointId** - Returned by `lldb_setWatchpoint`, used by `lldb_deleteWatchpoint`

### Error Handling

All tools raise structured errors with actionable messages:

```python
# Example error from lldb_evaluate
{
  "code": 4001,
  "message": "Cannot evaluate: process is not stopped. Use lldb_pause() first."
}
```

Common error patterns:
- **Process state errors** - Suggest calling `lldb_pause()` or `lldb_continue()` first
- **Missing debug symbols** - Suggest using `lldb_readRegisters()` or `lldb_disassemble()` instead
- **Invalid session** - Session not found or terminated
- **Permission denied** - Environment variable not set (e.g., `LLDB_MCP_ALLOW_LAUNCH`)

### Parameter Type Reference

| Type | Format | Example |
|------|--------|---------|
| `sessionId` | UUID string | `"abc123-def456-..."` |
| `threadId` | Integer | `1`, `2`, `3` |
| `frameIndex` | Integer (0-based) | `0` (current), `1` (caller) |
| `breakpointId` | Integer | `1`, `2`, `3` |
| `address` | Hex string or integer | `"0x100000f50"`, `4294971216` |
| `signal` | Signal name | `"SIGTERM"`, `"SIGKILL"` |
| `expression` | C/C++ expression | `"x + 1"`, `"ptr->field"` |

---

## Tool Reference

### Session Management (3 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_initialize` | Create new debug session | - |
| `lldb_terminate` | End debug session | `sessionId` |
| `lldb_listSessions` | List active sessions | - |

### Target Control (6 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_createTarget` | Load executable | `sessionId`, `file` |
| `lldb_launch` | Start process | `sessionId`, `args`, `env` |
| `lldb_attach` | Attach to process | `sessionId`, `pid`/`name` |
| `lldb_restart` | Restart process | `sessionId` |
| `lldb_signal` | Send signal | `sessionId`, `signal` |
| `lldb_loadCore` | Load core dump | `sessionId`, `corePath`, `executablePath` |

### Breakpoints (4 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_setBreakpoint` | Set breakpoint | `sessionId`, `symbol`/`file:line`/`address` |
| `lldb_deleteBreakpoint` | Delete breakpoint | `sessionId`, `breakpointId` |
| `lldb_listBreakpoints` | List breakpoints | `sessionId` |
| `lldb_updateBreakpoint` | Modify breakpoint | `sessionId`, `breakpointId`, `enabled`, `condition` |

### Execution Control (5 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_continue` | Continue execution | `sessionId` |
| `lldb_pause` | Pause execution | `sessionId` |
| `lldb_stepIn` | Step into function | `sessionId` |
| `lldb_stepOver` | Step over function | `sessionId` |
| `lldb_stepOut` | Step out of function | `sessionId` |

### Inspection (6 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_threads` | List threads | `sessionId` |
| `lldb_frames` | List stack frames | `sessionId`, `threadId` (optional) |
| `lldb_stackTrace` | Get stack trace | `sessionId`, `threadId` (optional) |
| `lldb_selectThread` | Select thread | `sessionId`, `threadId` |
| `lldb_selectFrame` | Select frame | `sessionId`, `frameIndex` |
| `lldb_evaluate` | Evaluate expression | `sessionId`, `expression`, `frameIndex` (optional) |

### Memory Operations (2 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_readMemory` | Read memory | `sessionId`, `address`, `size` |
| `lldb_writeMemory` | Write memory | `sessionId`, `address`, `data` |

### Watchpoints (3 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_setWatchpoint` | Set watchpoint | `sessionId`, `address`, `size`, `read`, `write` |
| `lldb_deleteWatchpoint` | Delete watchpoint | `sessionId`, `watchpointId` |
| `lldb_listWatchpoints` | List watchpoints | `sessionId` |

### Advanced Tools (4 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_pollEvents` | Poll debug events | `sessionId`, `limit` |
| `lldb_command` | Execute LLDB command | `sessionId`, `command` |
| `lldb_getTranscript` | Get session transcript | `sessionId` |
| `lldb_disassemble` | Disassemble code | `sessionId`, `address`, `count` |

### Security Analysis (2 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_analyzeCrash` | Analyze crash | `sessionId` |
| `lldb_getSuspiciousFunctions` | Find suspicious calls | `sessionId` |

### Register Operations (2 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_readRegisters` | Read registers | `sessionId` |
| `lldb_writeRegister` | Write register | `sessionId`, `name`, `value` |

### Symbol Search (1 tool)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_searchSymbol` | Search symbols | `sessionId`, `pattern` |

### Module Management (1 tool)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_listModules` | List loaded modules | `sessionId` |

### Core Dump Support (2 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_loadCore` | Load core dump | `sessionId`, `corePath`, `executablePath` |
| `lldb_createCoredump` | Create core dump | `sessionId`, `path` |

---

## Key Capabilities

### 1. Multi-Session Debugging

- Create multiple independent debug sessions
- Each session has isolated state (debugger, target, process)
- Sessions can run concurrently
- Clean session termination with resource cleanup

### 2. Event-Driven Architecture

- Background event collection per session
- Non-blocking event polling
- Event types: state changes, breakpoint hits, stdout/stderr
- Configurable event limits

### 3. Security Analysis

- Crash exploitability analysis
- Suspicious function detection (strcpy, sprintf, etc.)
- Register state at crash
- Crash type classification

### 4. Transcript Logging

- Automatic command logging
- Timestamped entries
- Full output capture
- Retrievable via `lldb_getTranscript`

### 5. Flexible Breakpoints

- Symbol-based breakpoints
- File:line breakpoints
- Address breakpoints
- Conditional breakpoints
- Enable/disable without deletion

### 6. Memory Debugging

- Memory read with hex and ASCII view
- Memory write with hex data
- Watchpoints for memory access monitoring
- Support for read/write watchpoints

---

## Environment Requirements

| Requirement | Version | Purpose |
|-------------|---------|---------|
| macOS | Any | Operating system |
| Python | ≥3.10 | Runtime |
| Homebrew LLVM | Latest | LLDB with Python bindings |
| FastMCP | ≥2.0 | MCP framework |

---

## Security Configuration

| Variable | Effect | Default |
|----------|--------|---------|
| `LLDB_MCP_ALLOW_LAUNCH=1` | Enable process launch | Disabled |
| `LLDB_MCP_ALLOW_ATTACH=1` | Enable process attach | Disabled |

---

## Integration Points

### Claude Desktop

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

### HTTP Mode (Testing)

```bash
LLDB_MCP_ALLOW_LAUNCH=1 \
  python3 -m lldb_mcp_server.fastmcp_server \
  --transport http --port 8765
```

---

## Feature Documentation

Detailed documentation for each feature category is available in `dev_docs/features/`:

```
dev_docs/features/
├── 01-session-management.md
├── 02-target-control.md
├── 03-breakpoints.md
├── 04-execution-control.md
├── 05-inspection.md
├── 06-memory-operations.md
├── 07-watchpoints.md
├── 08-advanced-tools.md
├── 09-security-analysis.md
├── 10-register-operations.md
├── 11-symbol-search.md
├── 12-module-management.md
└── 13-core-dump-support.md
```

Each document includes:
- Tool descriptions and parameters
- Return value schemas
- Usage examples
- Error codes
- Implementation notes
