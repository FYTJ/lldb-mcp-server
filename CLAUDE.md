# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

LLDB MCP Server exposes LLDB functionality through MCP (Model Context Protocol) for AI-driven debugging of C/C++ applications on macOS.

**Key feature**: Multi-session architecture with isolated debugging sessions.

## Quick Setup

**Requirements**: macOS, Homebrew, Python 3.10+

```bash
# 1. Install dependencies
brew install llvm python@3.13 uv

# 2. Add Homebrew LLVM to PATH (add to ~/.zshrc)
export PATH="$(brew --prefix llvm)/bin:$PATH"

# 3. Create venv and configure LLDB path
python3.13 -m venv .venv && source .venv/bin/activate
echo "$(lldb -P)" > "$(.venv/bin/python -c 'import site; print(site.getsitepackages()[0])')/lldb.pth"

# 4. Install project
uv pip install -e ".[dev]"

# 5. Verify
python -c "import lldb, fastmcp; print('OK')"
```

## MCP Configuration

### Method 1: Using uvx (Recommended - Published Package)

Install from PyPI and run with `uvx`:

```bash
# Generate .mcp.json with correct LLDB path
./scripts/generate_mcp_config.sh
```

This creates `.mcp.json`:
```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "uvx",
      "args": ["--python", "/usr/local/opt/python@3.13/bin/python3.13", "lldb-mcp-server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1",
        "PYTHONPATH": "/path/to/lldb/python/site-packages"
      }
    }
  }
}
```

**Benefits:**
- ✅ Automatic package installation from PyPI
- ✅ Version management built-in
- ✅ No manual virtual environment setup needed

### Method 2: Local Development (Virtual Environment)

For local development with editable install:

```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "/absolute/path/to/project/.venv/bin/python",
      "args": ["-m", "lldb_mcp_server.fastmcp_server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1"
      }
    }
  }
}
```

**⚠️ IMPORTANT:**
- Use the **absolute path** to your virtual environment's Python
- Do NOT use `python3` (system Python cannot access venv packages)
- Example: `/Users/yourname/Projects/lldb-mcp-server/.venv/bin/python`

### Development Mode (HTTP)

For testing or manual inspection:
File: `.mcp.json.http`

## Troubleshooting

**Issue: "ModuleNotFoundError: No module named 'lldb_mcp_server'"**

This means `.mcp.json` is using system Python instead of the virtual environment Python.

**Solution:** Update `.mcp.json` to use the absolute path to `.venv/bin/python`

See `dev_docs/TROUBLESHOOTING.md` for detailed solutions to common issues.

## Development Commands

```bash
# Run tests
pytest tests/ -v

# Run server (HTTP mode for testing)
LLDB_MCP_ALLOW_LAUNCH=1 python -m lldb_mcp_server.fastmcp_server --transport http --port 8765

# Run server (stdio mode for Claude Desktop)
LLDB_MCP_ALLOW_LAUNCH=1 python -m lldb_mcp_server.fastmcp_server

# Build test programs
cd examples/client/c_test && ./build_all.sh

# Linting
ruff check src/ && ruff format --check src/
```

## Architecture

### Core Design

- **Multi-session**: Each session has isolated `SBDebugger`, `SBTarget`, `SBProcess`
- **Event polling**: Background thread collects events, clients poll via `lldb_pollEvents`
- **Thread safety**: All operations use `RLock` for synchronization

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| FastMCP Server | `fastmcp_server.py` | MCP entry point, tool registration |
| SessionManager | `session/manager.py` | Session lifecycle, all debug operations |
| Tools | `tools/*.py` | 9 modules with 40 tools |
| Analysis | `analysis/exploitability.py` | Crash analysis |

## Tool Categories (40 tools)

| Category | Tools |
|----------|-------|
| Session | `lldb_initialize`, `lldb_terminate`, `lldb_listSessions` |
| Target | `lldb_createTarget`, `lldb_launch`, `lldb_attach`, `lldb_restart`, `lldb_signal` |
| Breakpoints | `lldb_setBreakpoint`, `lldb_deleteBreakpoint`, `lldb_listBreakpoints`, `lldb_updateBreakpoint` |
| Execution | `lldb_continue`, `lldb_pause`, `lldb_stepIn`, `lldb_stepOver`, `lldb_stepOut` |
| Inspection | `lldb_threads`, `lldb_frames`, `lldb_stackTrace`, `lldb_selectThread`, `lldb_selectFrame`, `lldb_evaluate` |
| Memory | `lldb_readMemory`, `lldb_writeMemory` |
| Watchpoints | `lldb_setWatchpoint`, `lldb_deleteWatchpoint`, `lldb_listWatchpoints` |
| Registers | `lldb_readRegisters`, `lldb_writeRegister` |
| Advanced | `lldb_disassemble`, `lldb_command`, `lldb_pollEvents`, `lldb_getTranscript` |
| Security | `lldb_analyzeCrash`, `lldb_getSuspiciousFunctions` |
| Symbols | `lldb_searchSymbol`, `lldb_listModules` |
| Core Dump | `lldb_loadCore`, `lldb_createCoredump` |

## Interactive Debugging

See `skills/lldb-debugger/INTERACTIVE_DEBUGGING.md` for comprehensive decision-based debugging workflows (crash analysis, variable inspection, etc.).

## Security Model

Dangerous operations require explicit opt-in:

```bash
export LLDB_MCP_ALLOW_LAUNCH=1  # Allow process launch
export LLDB_MCP_ALLOW_ATTACH=1  # Allow process attach
```

## Code Patterns

### Session Operations

```python
def operation(self, session_id: str, ...):
    with self._lock:
        sess = self._sessions.get(session_id)
        if not sess:
            raise LLDBError(1002, "Session not found")
        # Perform operation
```

### LLDB Import

```python
try:
    import lldb
except Exception as e:
    logger.warning("lldb unavailable: %s", e)
```

## File Structure

```
src/lldb_mcp_server/
├── fastmcp_server.py      # Entry point
├── session/manager.py     # SessionManager (core)
├── tools/                 # 9 tool modules
└── analysis/              # Crash analysis

examples/client/c_test/    # Test programs (8 bug types)
tests/                     # Unit tests
tests/e2e/                 # End-to-end tests
skills/lldb-debugger/      # Claude Code skill (includes INTERACTIVE_DEBUGGING.md)
dev_docs/                  # Design & feature docs
.mcp.json                  # Stdio config (Production)
.mcp.json.http             # HTTP config (Development)
```

## Documentation Rules

When adding new features:

1. Update `dev_docs/FEATURES.md` with tool summary
2. Add detailed docs to `dev_docs/features/<category>.md`

See `dev_docs/DESIGN.md` for architecture details.
