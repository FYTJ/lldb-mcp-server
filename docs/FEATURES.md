# LLDB MCP Server - Features

**Language:** [English](FEATURES.md) | [中文](FEATURES.zh.md)

## 🔧 40 Debugging Tools

| Category | Count | Function |
|----------|-------|----------|
| **Session Management** | 3 | Create, terminate, and list debugging sessions |
| **Target Control** | 6 | Load binary, launch/attach process, restart, send signal, load core dump |
| **Breakpoints** | 4 | Set, delete, list, update breakpoints (supports symbol, file:line, address, condition) |
| **Execution Control** | 5 | Continue, pause, step in/over/out |
| **Inspection** | 6 | Threads, stack frames, stack trace, expression evaluation |
| **Memory Operations** | 2 | Read/write memory (supports Hex and ASCII views) |
| **Watchpoints** | 3 | Set, delete, list memory watchpoints |
| **Registers** | 2 | Read, write CPU registers |
| **Symbols & Modules** | 2 | Symbol search, list loaded modules |
| **Advanced Tools** | 4 | Event polling, raw LLDB command, disassemble, session transcript |
| **Security Analysis** | 2 | Crash exploitability analysis, suspicious function detection |
| **Core Dump** | 2 | Load/Create core dump |

## ✨ Key Capabilities

- **Multi-session Debugging**: Run multiple independent debugging sessions concurrently, with isolated state for each session.
- **Event-driven Architecture**: Background event collection with non-blocking polling (state changes, breakpoint hits, stdout/stderr).
- **Security Analysis**: Crash exploitability classification, dangerous function detection (strcpy, sprintf, etc.).
- **Session Recording**: Automatically records all commands and output with timestamps.
- **Flexible Breakpoints**: Supports symbol, file:line, and address breakpoints, as well as conditional breakpoints.
- **Memory Debugging**: Memory read/write, watchpoint monitoring (read/write access).

## Tool Reference

### Session Management (3 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_initialize` | Create a new debug session | - |
| `lldb_terminate` | Terminate a debug session | `sessionId` |
| `lldb_listSessions` | List all active sessions | - |

### Target Control (6 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_createTarget` | Load executable file | `sessionId`, `file` |
| `lldb_launch` | Launch process | `sessionId`, `args`, `env` |
| `lldb_attach` | Attach to running process | `sessionId`, `pid`/`name` |
| `lldb_restart` | Restart process | `sessionId` |
| `lldb_signal` | Send signal to process | `sessionId`, `signal` |
| `lldb_loadCore` | Load core dump | `sessionId`, `corePath`, `executablePath` |

### Breakpoints (4 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_setBreakpoint` | Set breakpoint | `sessionId`, `symbol`/`file:line`/`address` |
| `lldb_deleteBreakpoint` | Delete breakpoint | `sessionId`, `breakpointId` |
| `lldb_listBreakpoints` | List all breakpoints | `sessionId` |
| `lldb_updateBreakpoint` | Modify breakpoint properties | `sessionId`, `breakpointId`, `enabled`, `condition` |

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
| `lldb_stackTrace` | Get formatted stack trace | `sessionId`, `threadId` (optional) |
| `lldb_selectThread` | Select thread | `sessionId`, `threadId` |
| `lldb_selectFrame` | Select stack frame | `sessionId`, `frameIndex` |
| `lldb_evaluate` | Evaluate expression | `sessionId`, `expression`, `frameIndex` (optional) |

### Memory Operations (2 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_readMemory` | Read memory content | `sessionId`, `address`, `size` |
| `lldb_writeMemory` | Write memory | `sessionId`, `address`, `data` |

### Watchpoints (3 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_setWatchpoint` | Set memory watchpoint | `sessionId`, `address`, `size`, `read`, `write` |
| `lldb_deleteWatchpoint` | Delete watchpoint | `sessionId`, `watchpointId` |
| `lldb_listWatchpoints` | List all watchpoints | `sessionId` |

### Registers (2 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_readRegisters` | Read CPU registers | `sessionId`, `threadId` (optional) |
| `lldb_writeRegister` | Write register | `sessionId`, `name`, `value` |

### Symbols & Modules (2 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_searchSymbol` | Search symbols | `sessionId`, `pattern`, `module` (optional) |
| `lldb_listModules` | List loaded modules | `sessionId` |

### Advanced Tools (4 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_pollEvents` | Poll debug events | `sessionId`, `limit` |
| `lldb_command` | Execute raw LLDB command | `sessionId`, `command` |
| `lldb_getTranscript` | Get session transcript | `sessionId` |
| `lldb_disassemble` | Disassemble code | `sessionId`, `address`, `count` |

### Security Analysis (2 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_analyzeCrash` | Analyze crash exploitability | `sessionId` |
| `lldb_getSuspiciousFunctions` | Find suspicious functions | `sessionId` |

### Core Dump (2 tools)

| Tool | Description | Parameters |
|------|-------------|------------|
| `lldb_loadCore` | Load core dump | `sessionId`, `corePath`, `executablePath` |
| `lldb_createCoredump` | Create core dump | `sessionId`, `path` |

## Event Types

Events obtained via `lldb_pollEvents`:

| Event Type | Description |
|------------|-------------|
| `targetCreated` | Target created |
| `processLaunched` | Process launched |
| `processAttached` | Attached to process |
| `processStateChanged` | Process state changed (running/stopped/exited) |
| `breakpointSet` | Breakpoint set |
| `breakpointHit` | Breakpoint hit (includes thread/frame info) |
| `stdout` | Process standard output |
| `stderr` | Process standard error output |

## See Also

- [Configuration Guide](CONFIGURATION.md) - Detailed MCP configuration
- [Usage Guide](USAGE.md) - Usage examples and Claude Code Skill integration
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
- [Main README](../README.md) - Quick start guide
