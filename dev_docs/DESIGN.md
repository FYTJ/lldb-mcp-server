# LLDB MCP Server - Architecture Design

## Overview

LLDB MCP Server is a debugging server that exposes LLDB functionality through the Model Context Protocol (MCP). It enables AI assistants to programmatically control LLDB for debugging C/C++ applications on macOS.

**Key Differentiator**: Multi-session architecture that allows concurrent debugging sessions with isolated state.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          AI Assistant                                │
│                    (Claude Desktop / Claude Code)                    │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ MCP Protocol (stdio/HTTP/SSE)
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        FastMCP Server Layer                          │
│                    (fastmcp_server.py)                               │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Tool Registration (9 modules, 40 tools)                     │    │
│  │  - session.py      - target.py       - breakpoints.py       │    │
│  │  - execution.py    - inspection.py   - memory.py            │    │
│  │  - watchpoints.py  - advanced.py     - security.py          │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       SessionManager                                 │
│                    (session/manager.py)                              │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Multi-Session Management                                    │    │
│  │  - Session lifecycle (create/terminate/list)                 │    │
│  │  - Thread-safe operations (RLock)                            │    │
│  │  - Event polling architecture                                │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       LLDB Python Bindings                           │
│                    (lldb.SBDebugger)                                 │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Session 1         Session 2         Session N              │    │
│  │  ┌──────────┐     ┌──────────┐      ┌──────────┐           │    │
│  │  │SBDebugger│     │SBDebugger│      │SBDebugger│           │    │
│  │  │SBTarget  │     │SBTarget  │      │SBTarget  │           │    │
│  │  │SBProcess │     │SBProcess │      │SBProcess │           │    │
│  │  │EventQueue│     │EventQueue│      │EventQueue│           │    │
│  │  └──────────┘     └──────────┘      └──────────┘           │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. FastMCP Server (`fastmcp_server.py`)

Entry point for the MCP server using the FastMCP framework.

**Responsibilities:**
- Initialize MCP server with tool registration
- Handle transport modes (stdio, HTTP, SSE)
- Provide custom HTTP routes for tool listing/calling
- Auto-configure LLDB environment

**Transport Modes:**
| Mode | Use Case | Command |
|------|----------|---------|
| stdio | Claude Desktop integration | `--transport stdio` (default) |
| HTTP | Testing and development | `--transport http --port 8765` |
| SSE | Server-sent events | `--transport sse` |

### 2. SessionManager (`session/manager.py`)

Central coordinator for all debugging operations.

**Key Features:**
- Multi-session isolation
- Thread-safe operations (RLock)
- Background event thread per session
- Transcript logging

**Session Data Structure:**
```python
@dataclass
class Session:
    session_id: str
    debugger: Any = None      # lldb.SBDebugger
    target: Any = None        # lldb.SBTarget
    process: Any = None       # lldb.SBProcess
    listener: Any = None      # lldb.SBListener
    event_thread: Any = None  # threading.Thread
    events: Any = None        # deque for event queue
    event_stop: Any = None    # threading.Event
```

### 3. Tool Modules (`tools/`)

9 modular tool registration files:

| Module | Tools | Purpose |
|--------|-------|---------|
| `session.py` | 3 | Session lifecycle management |
| `target.py` | 6 | Target/process control |
| `breakpoints.py` | 4 | Breakpoint management |
| `execution.py` | 5 | Execution control |
| `inspection.py` | 10 | Code/variable inspection |
| `memory.py` | 2 | Memory operations |
| `watchpoints.py` | 3 | Memory watchpoints |
| `advanced.py` | 4 | Events, commands, transcript |
| `security.py` | 2 | Crash analysis |

### 4. Exploitability Analysis (`analysis/`)

Security-focused crash analysis:
- Crash type detection
- Exploitability rating
- Suspicious function identification
- Register state analysis

---

## Design Patterns

### Interactive Debugging Support

The server is designed to support iterative, decision-based debugging workflows suitable for AI agents:

- **State Inspection**: Tools like `lldb_frames` and `lldb_threads` provide rich state information.
- **Error Guidance**: Tools return actionable error messages (e.g., "process not stopped") to guide the AI's next step.
- **Optional Parameters**: Tools have sensible defaults (e.g., current thread) to reduce friction.

See `skills/lldb-debugger/INTERACTIVE_DEBUGGING.md` for detailed workflows.

### Multi-Session Isolation

Each debugging session maintains complete isolation:

```
Session A                    Session B
┌────────────────────┐      ┌────────────────────┐
│ SBDebugger         │      │ SBDebugger         │
│ ├── SBTarget       │      │ ├── SBTarget       │
│ │   └── binary_a   │      │ │   └── binary_b   │
│ ├── SBProcess      │      │ ├── SBProcess      │
│ │   └── PID: 1234  │      │ │   └── PID: 5678  │
│ ├── EventThread    │      │ ├── EventThread    │
│ └── EventQueue     │      │ └── EventQueue     │
└────────────────────┘      └────────────────────┘
```

### Event-Driven Polling

Non-blocking event collection with background threads:

```
┌─────────────────────────────────────────────────────────────┐
│                     Background Thread                        │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │ LLDB Listener   │───▶│  Event Queue    │                 │
│  │ WaitForEvent(1) │    │  (deque)        │                 │
│  └─────────────────┘    └────────┬────────┘                 │
│                                  │                          │
└──────────────────────────────────┼──────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────┐
│                      Client                                  │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │ pollEvents()    │───▶│  Process Events │                 │
│  │ (non-blocking)  │    │                 │                 │
│  └─────────────────┘    └─────────────────┘                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Event Types:**
- `processStateChanged` - Process state transitions
- `breakpointHit` - Breakpoint triggered
- `stdout` / `stderr` - Process output
- `targetCreated` - Target loaded

### Thread Safety

All session operations use reentrant lock:

```python
def operation(self, session_id: str, ...):
    with self._lock:  # RLock for thread safety
        sess = self._sessions.get(session_id)
        if not sess:
            raise LLDBError(1002, "Session not found")
        if sess.debugger is None:
            raise LLDBError(2000, "LLDB unavailable")
        # Perform operation
        return result
```

---

## Security Model

### Permission Controls

Dangerous operations require explicit environment variables:

| Variable | Operation | Default |
|----------|-----------|---------|
| `LLDB_MCP_ALLOW_LAUNCH` | Process launch | `0` (disabled) |
| `LLDB_MCP_ALLOW_ATTACH` | Process attach | `0` (disabled) |

### Localhost Only

Server designed for local use:
- Default bind: `127.0.0.1`
- No authentication on TCP socket
- Trust boundary at localhost

---

## File Structure

```
lldb-mcp-server/
├── src/lldb_mcp_server/
│   ├── fastmcp_server.py     # FastMCP entry point
│   ├── session/
│   │   ├── manager.py        # SessionManager (1200+ lines)
│   │   └── types.py          # Session data structures
│   ├── tools/                # 9 tool modules
│   │   ├── session.py
│   │   ├── target.py
│   │   ├── breakpoints.py
│   │   ├── execution.py
│   │   ├── inspection.py
│   │   ├── memory.py
│   │   ├── watchpoints.py
│   │   ├── advanced.py
│   │   └── security.py
│   ├── analysis/
│   │   └── exploitability.py # Crash analysis
│   ├── mcp/
│   │   └── server.py         # Legacy TCP server
│   └── utils/
│       ├── config.py         # Configuration
│       ├── errors.py         # Error codes
│       └── logging.py        # Logging utilities
├── tests/                    # Unit tests (34 tests)
│   └── e2e/                  # E2E tests (11 tests)
├── examples/
│   └── client/
│       ├── c_test/           # Test C programs
│       └── run_debug_flow.py # Example workflow
├── skills/
│   └── lldb-debugger/        # Claude Code skill
├── dev_docs/
│   ├── DESIGN.md             # This file
│   ├── FEATURES.md           # Feature summary
│   ├── PLAN.md               # Development plan
│   └── features/             # Detailed feature docs
├── config.json               # LLDB configuration
├── smithery.yaml             # Smithery marketplace config
└── pyproject.toml            # Python package config
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| MCP Framework | FastMCP 2.x | Tool registration, transport handling |
| Debugger | LLDB (Homebrew) | Debugging engine |
| Python Bindings | lldb module | LLDB API access |
| HTTP Server | Starlette | HTTP transport mode |
| Configuration | JSON | LLDB path configuration |
| Testing | pytest | Unit and E2E testing |

---

## Design Decisions

### Why Multi-Session?

- **Concurrent debugging**: Debug multiple targets simultaneously
- **Session isolation**: Bugs in one session don't affect others
- **Resource management**: Clean session termination

### Why Polling vs Callbacks?

- **Simplicity**: No callback registration complexity
- **Reliability**: No missed events in async scenarios
- **Flexibility**: Client controls event processing rate

### Why FastMCP?

- **Modern protocol**: MCP standard compliance
- **Multiple transports**: stdio, HTTP, SSE support
- **Tool registration**: Declarative tool definition
- **Claude integration**: Native Claude Desktop support

---

## Comparison with Other LLDB Wrappers

| Feature | This Project | Others (lisa.py, etc.) |
|---------|--------------|------------------------|
| Multi-session | ✅ Yes | ❌ Single session |
| Event polling | ✅ Non-blocking | ❌ Blocking callbacks |
| Environment auto-config | ✅ Yes | ❌ Manual setup |
| Transcript logging | ✅ Built-in | ❌ Not available |
| Security analysis | ✅ Exploitability | ❌ Basic only |
| MCP integration | ✅ FastMCP | ❌ Custom protocols |
