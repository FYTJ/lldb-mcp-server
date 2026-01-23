# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LLDB MCP Server is a debugging server that exposes LLDB functionality through the Model Context Protocol (MCP). It enables AI assistants to programmatically control LLDB for debugging C/C++ applications on macOS.

**Key differentiator**: Multi-session architecture that allows concurrent debugging sessions with isolated state.

## Development Commands

### Installation and Environment Setup

**Critical Compatibility Note:**

This project requires both **LLDB Python bindings** (for debugging) and **FastMCP** (for the MCP server). These have conflicting Python version requirements:
- **Xcode LLDB**: Only supports Python 3.9.6
- **FastMCP**: Requires Python ≥3.10

**Solution:** Use Homebrew's LLVM/LLDB which supports modern Python versions (3.10+).

---

### Recommended Setup (Homebrew LLVM + Python 3.13)

**Prerequisites:**
- macOS
- Homebrew (`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`)
- `uv` package manager: `pip install uv` or `brew install uv`

**Step 1: Install Homebrew LLVM and Python 3.13**

```bash
# Install LLVM (includes LLDB with Python 3.10+ support)
brew install llvm

# Install Python 3.13
brew install python@3.13

# Verify installations
/usr/local/opt/python@3.13/bin/python3.13 -V  # Should show Python 3.13.x
$(brew --prefix llvm)/bin/lldb --version      # Should show LLDB version
```

**Step 2: Configure Shell Environment**

Add to `~/.zshrc` (or `~/.bashrc` for bash):

```bash
# Add Homebrew LLVM to PATH (prioritize over system LLDB)
export PATH="$(brew --prefix llvm)/bin:$PATH"
```

Reload shell configuration:
```bash
source ~/.zshrc  # or source ~/.bashrc
hash -r          # Clear command hash
```

Verify LLDB is now from Homebrew:
```bash
which lldb
# Expected: /usr/local/opt/llvm/bin/lldb (NOT /usr/bin/lldb)

lldb --version
# Expected: LLDB from Homebrew

lldb -P
# Expected: Homebrew LLDB Python path
```

**Step 3: Create Virtual Environment with Python 3.13**

```bash
# Remove old venv if exists
deactivate 2>/dev/null || true
rm -rf .venv

# Create venv with Python 3.13
/usr/local/opt/python@3.13/bin/python3.13 -m venv .venv
source .venv/bin/activate

# Verify Python version
python -c "import sys; print(sys.executable); print(sys.version)"
# Expected: Python 3.13.x
```

**Step 4: Add LLDB Python Path to Virtual Environment**

This step makes LLDB module permanently available without `PYTHONPATH`:

```bash
# Get LLDB Python module path
LLDB_PY_PATH="$(lldb -P)"
echo "LLDB Python path: $LLDB_PY_PATH"

# Get venv site-packages directory
SITE_PKGS="$(python -c 'import site; print(site.getsitepackages()[0])')"
echo "Site packages: $SITE_PKGS"

# Write LLDB path to .pth file (permanent Python path configuration)
echo "$LLDB_PY_PATH" > "$SITE_PKGS/lldb.pth"
```

**Step 5: Verify LLDB Import (No PYTHONPATH Needed)**

```bash
python - <<'PY'
import lldb
print("lldb module:", lldb.__file__)
print("lldb version:", lldb.SBDebugger.GetVersionString())

# Verify internal module
import lldb._lldb as m
print("lldb._lldb:", m.__file__)
PY
```

Expected output:
```
lldb module: /usr/local/opt/llvm/lib/python3.13/site-packages/lldb/__init__.py
lldb version: lldb-<version>
lldb._lldb: /usr/local/opt/llvm/lib/python3.13/site-packages/lldb/_lldb.cpython-313-darwin.so
```

**Step 6: Install Project Dependencies**

```bash
# Install with uv (recommended)
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"

# Verify FastMCP installed (requires Python 3.10+)
python -c "import fastmcp; print('FastMCP:', fastmcp.__version__)"
```

**Step 7: Final Verification**

```bash
# Test imports
python -c "
import lldb
import fastmcp
print('✅ LLDB version:', lldb.SBDebugger.GetVersionString())
print('✅ FastMCP version:', fastmcp.__version__)
print('✅ Both modules working!')
"
```

### Why This Setup Works

**Problem Solved:**
- **Homebrew LLDB** compiles Python bindings for the installed Python version
- When you install Python 3.13, Homebrew LLDB automatically supports it
- No binary incompatibility between Python versions

**Key Differences:**

| Aspect | Xcode LLDB | Homebrew LLDB |
|--------|------------|---------------|
| Python Version | Fixed at 3.9.6 | Matches installed Python (3.10+) |
| FastMCP Support | ❌ No | ✅ Yes |
| PYTHONPATH Required | ✅ Always | ❌ No (uses .pth) |
| Update Method | Xcode updates | `brew upgrade llvm` |
| Binary Location | `/Library/Developer/CommandLineTools` | `/usr/local/opt/llvm` |

**Technical Details:**
- `.pth` file in `site-packages` adds paths to `sys.path` automatically
- Homebrew LLDB's Python bindings are in: `/usr/local/opt/llvm/lib/python3.13/site-packages/lldb/`
- The `_lldb.cpython-313-darwin.so` binary extension matches Python 3.13's ABI

### Building and Testing

```bash
# Build the test binary (required for examples)
cd examples/client/c_test/hello && cc -g -O0 -Wall -Wextra -o hello hello.c

# Run tests (LLDB auto-imported via .pth file)
.venv/bin/python -m pytest tests/ -v

# Run tests with coverage
.venv/bin/python -m pytest tests/ --cov=lldb_mcp_server --cov-report=html

# Run specific test file
.venv/bin/python -m pytest tests/test_session.py -v

# Type checking
.venv/bin/python -m mypy src/lldb_mcp_server

# Linting and formatting
.venv/bin/python -m ruff check src/
.venv/bin/python -m ruff format --check src/
```

### Running the Server

```bash
# FastMCP Server - HTTP mode (for testing)
LLDB_MCP_ALLOW_LAUNCH=1 \
LLDB_MCP_ALLOW_ATTACH=1 \
  .venv/bin/python -m lldb_mcp_server.fastmcp_server \
  --transport http --host 127.0.0.1 --port 8765

# FastMCP Server - Stdio mode (for Claude Desktop)
LLDB_MCP_ALLOW_LAUNCH=1 \
LLDB_MCP_ALLOW_ATTACH=1 \
  .venv/bin/python -m lldb_mcp_server.fastmcp_server

# FastMCP Dev mode (with auto-reload)
LLDB_MCP_ALLOW_LAUNCH=1 \
  fastmcp dev src/lldb_mcp_server/fastmcp_server.py
```

## Architecture

### Multi-Session Design

Each debugging session is completely isolated with:
- Its own `lldb.SBDebugger` instance
- Dedicated background thread for event collection
- Independent event queue (deque) for `pollEvents`
- Separate transcript log file

**Thread Safety**: All session operations use `with self._lock:` (RLock) for synchronization.

### Event-Driven Model

The server uses a **polling architecture** rather than callbacks:
1. Each session spawns a background thread in `SessionManager.start_events()`
2. Thread continuously calls `listener.WaitForEvent(1, ev)` (1-second timeout)
3. Events are appended to session's deque
4. Clients retrieve events via `pollEvents` tool (non-blocking)

**Event types**: `processStateChanged`, `breakpointHit`, `stdout`, `stderr`, `targetCreated`, etc.

### LLDB Environment Setup

**Current Approach (FastMCP Server):**

The LLDB Python module requires explicit `PYTHONPATH` configuration at runtime:

```bash
# Set PYTHONPATH to LLDB's Python module location
export PYTHONPATH="$(/usr/bin/lldb -P)"

# Then run server
.venv/bin/python -m lldb_mcp_server.fastmcp_server
```

**Why PYTHONPATH is needed:**
- LLDB bindings are in Xcode frameworks, not standard site-packages
- Path: `/Library/Developer/CommandLineTools/Library/PrivateFrameworks/LLDB.framework/Resources/Python`
- Python cannot discover this path automatically

**Legacy TCP Server (mcp/server.py):**

The older TCP server has automatic LLDB environment setup:
1. Try `import lldb`
2. If fails, auto-configure from `config.json`:
   - Add Python paths from `lldb -P` or Xcode
   - Set `DYLD_FRAMEWORK_PATH` and `DYLD_LIBRARY_PATH`
   - Preload LLDB.framework
   - Can re-exec with correct Python executable if needed
3. Graceful degradation: server starts even if LLDB unavailable

**Note:** FastMCP server (recommended) requires manual `PYTHONPATH` setup as shown above.

## Key Components

### SessionManager (`session/manager.py`)

Central coordinator for all debugging operations:
- **Session lifecycle**: `create_session()`, `terminate_session()`, `list_sessions()`
- **Target/Process control**: `create_target()`, `launch()`, `attach()`, `restart()`
- **Breakpoints**: `set_breakpoint()`, `delete_breakpoint()`, `list_breakpoints()`, `update_breakpoint()`
- **Execution**: `continue_process()`, `pause_process()`, `step_in()`, `step_over()`, `step_out()`
- **Inspection**: `threads()`, `frames()`, `stack_trace()`, `evaluate()`
- **Memory**: `read_memory()`, `write_memory()`
- **Watchpoints**: `set_watchpoint()`, `delete_watchpoint()`, `list_watchpoints()`
- **Advanced**: `disassemble()`, `command()`, `poll_events()`, `get_transcript()`

### MCP Server (`mcp/server.py`)

TCP server with JSON-RPC dispatcher:
- Listens on configured host:port
- Routes 33 tool calls to SessionManager methods
- Tool naming convention: `lldb.<operation>` (e.g., `lldb.initialize`, `lldb.setBreakpoint`)
- Returns structured JSON responses via `make_response()` or `make_error()`

### Configuration (`utils/config.py` + `config.json`)

Configuration sources (priority order):
1. Environment variable `LLDB_MCP_CONFIG=/path/to/config.json`
2. Default `config.json` in project root

**Critical settings**:
- `lldb.python_paths`: Paths for `import lldb` (from `lldb -P`)
- `lldb.framework_paths`: LLDB.framework locations (from `xcode-select -p`)
- `lldb.python_executable`: Preferred Python binary (Xcode's Python)
- `log_dir`: Where transcript logs are written

**Finding LLDB paths**:
```bash
# Get Python path for lldb module
lldb -P

# Get developer root (contains frameworks)
xcode-select -p
```

## Important Patterns

### LLDB Import Handling

Always wrap LLDB imports with exception handling:

```python
try:
    import lldb
    # Use LLDB functionality
except Exception as e:
    logger.warning("lldb.unavailable %s", str(e))
    # Graceful degradation
```

### Session Operations

All session methods follow this pattern:

```python
def operation(self, session_id: str, ...):
    with self._lock:
        sess = self._sessions.get(session_id)
        if not sess:
            raise LLDBError(1002, "Session not found", {"sessionId": session_id})
        if sess.debugger is None:
            raise LLDBError(2000, "LLDB unavailable")
        # Perform operation
        return result
```

### Event Polling (Non-Blocking)

```python
# Client calls this periodically
events = client.call_tool("lldb.pollEvents", {
    "sessionId": sid,
    "limit": 32  # Max events to retrieve
})
# Events are removed from deque after retrieval
```

### Transcript Logging

Every LLDB command/output is automatically logged to `logs/<session_id>.txt`:
- Timestamped entries
- Command echoing
- Output capture
- Retrievable via `lldb.getTranscript` tool

## Security Model

**Dangerous operations require explicit opt-in**:

```bash
# Allow process launch
export LLDB_MCP_ALLOW_LAUNCH=1

# Allow attaching to running processes
export LLDB_MCP_ALLOW_ATTACH=1
```

These are checked in `mcp/server.py:handle_tools_call()` before calling SessionManager.

**Note**: No authentication on TCP socket. Designed for localhost use only (127.0.0.1).

## Environment Requirements

### Recommended Configuration (Homebrew LLDB)

- **OS**: macOS
- **Python**: 3.10+ (3.13 recommended)
- **LLDB**: Homebrew LLVM (`brew install llvm`)
- **Package Manager**: `uv` (recommended) or `pip`
- **FastMCP**: ✅ Supported (requires Python ≥3.10)

**Advantages:**
- ✅ FastMCP server available
- ✅ Modern Python versions (3.10+)
- ✅ No PYTHONPATH needed
- ✅ Simple `.pth` configuration
- ✅ Actively maintained


## File Structure

**Critical files**:
- `src/lldb_mcp_server/fastmcp_server.py` - FastMCP server entry point (recommended)
- `src/lldb_mcp_server/mcp/server.py` - Legacy TCP server with auto-configuration
- `src/lldb_mcp_server/session/manager.py` - Session management, event system (1227 lines)
- `src/lldb_mcp_server/session/types.py` - Session data structures
- `src/lldb_mcp_server/tools/` - Tool registration modules (9 modules)
- `src/lldb_mcp_server/analysis/` - Crash and exploitability analysis
- `src/lldb_mcp_server/utils/config.py` - Configuration loader
- `config.json` - LLDB environment configuration
- `pyproject.toml` - Python dependencies (requires-python = ">=3.9")

**Examples**:
- `examples/client/run_debug_flow.py` - Complete debug workflow example
- `examples/client/c_test/hello/` - Test C program for debugging

## Tool Categories (40 Total)

**Session Management (3 tools)**: `lldb_initialize`, `lldb_terminate`, `lldb_listSessions`

**Target/Process (5 tools)**: `lldb_createTarget`, `lldb_launch`, `lldb_attach`, `lldb_restart`, `lldb_signal`

**Breakpoints (4 tools)**: `lldb_setBreakpoint`, `lldb_deleteBreakpoint`, `lldb_listBreakpoints`, `lldb_updateBreakpoint`

**Execution Control (5 tools)**: `lldb_continue`, `lldb_pause`, `lldb_stepIn`, `lldb_stepOver`, `lldb_stepOut`

**Inspection (5 tools)**: `lldb_threads`, `lldb_frames`, `lldb_stackTrace`, `lldb_selectThread`, `lldb_selectFrame`

**Expressions (1 tool)**: `lldb_evaluate`

**Memory Operations (2 tools)**: `lldb_readMemory`, `lldb_writeMemory`

**Watchpoints (4 tools)**: `lldb_setWatchpoint`, `lldb_deleteWatchpoint`, `lldb_listWatchpoints`, `lldb_updateWatchpoint`

**Register Operations (2 tools)**: `lldb_readRegisters`, `lldb_writeRegister`

**Symbol Search (1 tool)**: `lldb_searchSymbol`

**Module Management (1 tool)**: `lldb_listModules`

**Core Dump Support (2 tools)**: `lldb_loadCore`, `lldb_createCoredump`

**Security Analysis (2 tools)**: `lldb_analyzeCrash`, `lldb_getSuspiciousFunctions`

**Advanced (3 tools)**: `lldb_disassemble`, `lldb_command`, `lldb_pollEvents`, `lldb_getTranscript`

**Tool Naming:** All tools use `lldb_` prefix (e.g., `lldb_initialize`, not `lldb.initialize`) in FastMCP server.

## Common Debugging Workflow

**Using FastMCP Server (recommended):**

```python
# 1. Initialize session
response = client.call_tool("lldb_initialize", {})
session_id = response["sessionId"]

# 2. Create target (load executable)
client.call_tool("lldb_createTarget", {
    "sessionId": session_id,
    "file": "/path/to/binary"
})

# 3. Set breakpoint at main
client.call_tool("lldb_setBreakpoint", {
    "sessionId": session_id,
    "symbol": "main"
})

# 4. Launch process
client.call_tool("lldb_launch", {
    "sessionId": session_id,
    "args": [],
    "env": {}
})

# 5. Poll for events (breakpoint hit)
events = client.call_tool("lldb_pollEvents", {
    "sessionId": session_id,
    "limit": 10
})

# 6. Inspect variables at breakpoint
result = client.call_tool("lldb_evaluate", {
    "sessionId": session_id,
    "expression": "argc"
})

# 7. Step through code
client.call_tool("lldb_stepOver", {"sessionId": session_id})

# 8. Read registers
registers = client.call_tool("lldb_readRegisters", {"sessionId": session_id})

# 9. Analyze crash (if process crashed)
crash_info = client.call_tool("lldb_analyzeCrash", {"sessionId": session_id})

# 10. Continue execution
client.call_tool("lldb_continue", {"sessionId": session_id})

# 11. Retrieve full transcript
transcript = client.call_tool("lldb_getTranscript", {
    "sessionId": session_id
})
```

**Using Legacy TCP Server:**

Tool names use dot notation: `lldb.initialize`, `lldb.createTarget`, etc.

## Comparison with Other LLDB MCP Projects

This project differs from `lisa.py` and similar tools:
- **Multi-session support**: Most wrappers are single-session
- **Event polling architecture**: More flexible than callback-based
- **Automatic environment setup**: Self-configuring LLDB paths
- **Transcript logging**: Built-in capture of debugging history
- **Future roadmap**: Plans for exploit analysis (security-focused debugging)

See `LLDB_MCP_项目分析与改进规划.md` for detailed comparison and 3-phase improvement plan.
