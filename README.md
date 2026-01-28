# LLDB MCP Server

**Language:** [English](README.md) | [中文](docs/README.zh.md)

[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://github.com/FYTJ/lldb-mcp-server)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/lldb-mcp-server)](https://pypi.org/project/lldb-mcp-server/)

## Overview

LLDB MCP Server is a debugging server based on the [Model Context Protocol (MCP)](https://modelcontextprotocol.io). It exposes LLDB debugging capabilities to AI assistants like Claude Code and Claude Desktop through 40 specialized tools, enabling AI-driven interactive debugging of C/C++ applications.

**Core Architecture:** Multi-session design where each debugging session has isolated `SBDebugger`, `SBTarget`, and `SBProcess` instances, supporting concurrent debugging workflows.

**Use Cases:**
- AI-assisted debugging with Claude Code / Claude Desktop
- Automated debugging scripts and workflows
- Crash analysis and security vulnerability detection
- Remote debugging and core dump analysis

## Core Features

### 🔧 40 Debugging Tools

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

### ✨ Key Capabilities

- **Multi-session Debugging**: Run multiple independent debugging sessions concurrently, with isolated state for each session.
- **Event-driven Architecture**: Background event collection with non-blocking polling (state changes, breakpoint hits, stdout/stderr).
- **Security Analysis**: Crash exploitability classification, dangerous function detection (strcpy, sprintf, etc.).
- **Session Recording**: Automatically records all commands and output with timestamps.
- **Flexible Breakpoints**: Supports symbol, file:line, and address breakpoints, as well as conditional breakpoints.
- **Memory Debugging**: Memory read/write, watchpoint monitoring (read/write access).

## Prerequisites

### System Requirements

- **macOS**
- **Homebrew** ([Installation Guide](https://brew.sh/))
- **Homebrew LLVM**
- **Python 3.10+** (Installed via Homebrew)


## Quick Start

### 1. Install Dependencies

```bash
# Install Homebrew LLVM (includes LLDB)
brew install llvm

# Install uv (provides uvx command)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add Homebrew LLVM to PATH (add to ~/.zshrc)
export PATH="$(brew --prefix llvm)/bin:$PATH"

# Reload shell configuration
source ~/.zshrc
hash -r

# Verify LLDB installation
which lldb
lldb --version
```

### 2. Configure MCP

#### Claude Code

**Option 1: Command-line configuration (Global, recommended)**

Intel (x86_64):
```bash
claude mcp add-json --scope user lldb-debugger '{
  "type": "stdio",
  "command": "uvx",
  "args": ["--python", "/usr/local/opt/python@3.13/bin/python3.13", "lldb-mcp-server"],
  "env": {
    "LLDB_MCP_ALLOW_LAUNCH": "1",
    "LLDB_MCP_ALLOW_ATTACH": "1",
    "PYTHONPATH": "/usr/local/opt/llvm/lib/python3.13/site-packages"
  }
}'
```

Apple Silicon (arm64):
```bash
claude mcp add-json --scope user lldb-debugger '{
  "type": "stdio",
  "command": "uvx",
  "args": ["--python", "/opt/homebrew/opt/python@3.13/bin/python3.13", "lldb-mcp-server"],
  "env": {
    "LLDB_MCP_ALLOW_LAUNCH": "1",
    "LLDB_MCP_ALLOW_ATTACH": "1",
    "PYTHONPATH": "/opt/homebrew/opt/llvm/lib/python3.13/site-packages"
  }
}'
```

**Option 2: Manual configuration (Project-specific)**

Create `.mcp.json` in your project root (see [MCP Configuration](#mcp-configuration)).

#### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS (see [MCP Configuration](#mcp-configuration)).

### 3. Start Using

No manual installation required! When you configure the MCP server using `uvx`, it automatically:
- Installs the package from PyPI
- Manages dependencies
- Runs the server in an isolated environment

Just configure `.mcp.json` and start Claude Code or restart Claude Desktop.

## MCP Configuration

### Intel (x86_64)

Create `.mcp.json` (Claude Code) in your project root or edit Claude Desktop configuration:

```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "uvx",
      "args": ["--python", "/usr/local/opt/python@3.13/bin/python3.13", "lldb-mcp-server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1"
      }
    }
  }
}
```

### Apple Silicon (arm64)

```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "uvx",
      "args": ["--python", "/opt/homebrew/opt/python@3.13/bin/python3.13", "lldb-mcp-server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1"
      }
    }
  }
}
```

**Important:** The `--python` argument specifies the full path to Homebrew Python 3.13, ensuring `uvx` does not use the system Python 3.9.

### If LLDB Auto-detection Fails

If the server cannot automatically find LLDB Python bindings, add `LLDB_PYTHON_PATH`:

**Intel (x86_64):**
```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "uvx",
      "args": ["--python", "/usr/local/opt/python@3.13/bin/python3.13", "lldb-mcp-server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1",
        "LLDB_PYTHON_PATH": "/usr/local/opt/llvm/lib/python3.13/site-packages"
      }
    }
  }
}
```

**Apple Silicon (arm64):**
```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "uvx",
      "args": ["--python", "/opt/homebrew/opt/python@3.13/bin/python3.13", "lldb-mcp-server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1",
        "LLDB_PYTHON_PATH": "/opt/homebrew/opt/llvm/lib/python3.13/site-packages"
      }
    }
  }
}
```

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `LLDB_MCP_ALLOW_LAUNCH=1` | Allow launching new processes | Disabled |
| `LLDB_MCP_ALLOW_ATTACH=1` | Allow attaching to existing processes | Disabled |
| `LLDB_PYTHON_PATH` | Override LLDB Python module path | Auto-detect |

## Tool Reference

Full list of 40 MCP tools:

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

## Claude Code Skill Integration

This project includes a pre-built **debugging skill** for Claude Code that provides AI-guided debugging workflows. The skill teaches Claude when and how to use LLDB debugging tools effectively.

### Installing the Skill

The skill is located in `skills/lldb-debug/` directory. To install it:

**Option 1: Project-specific (recommended for testing)**
```bash
# The skill is already in the project's .claude/skills/ directory
# Claude Code will automatically detect it when working in this project
```

**Option 2: Global installation (for all projects)**
```bash
# Copy to your personal skills directory
cp -r skills/lldb-debug ~/.claude/skills/
```

### Using the Skill

Once the MCP server is configured, you can invoke the skill:

**Manual invocation:**
```bash
/lldb-debug path/to/binary
```

**Automatic invocation:**
Claude will automatically use debugging tools when appropriate if you describe debugging tasks like:
- "Debug this crashed program"
- "Find the buffer overflow in this binary"
- "Analyze this core dump"

### When the Skill Activates

The skill is designed to activate **ONLY** when direct code analysis is insufficient:

1. **Project complexity** makes static analysis unreliable
2. **Error logs are missing** or don't indicate root cause
3. **Multiple code fixes have failed**
4. **Runtime behavior analysis** is required (memory corruption, crashes, etc.)

The skill will **NOT** activate for simple issues that can be solved through code review alone.

### Skill Capabilities

The debugging skill provides:

- **Debugging mindset**: Scientific method, binary search localization, minimal reproduction
- **Error type classification**: Null pointer, buffer overflow, use-after-free, etc.
- **Assembly-level debugging**: Compiler optimization issues, ABI mismatches, binary-only debugging
- **Multi-session strategy**: Iterative debugging with session limits and structured logging
- **Decision trees**: Automated workflows for common debugging patterns
- **Quick reference**: Scenario-based tool combinations and troubleshooting guides

### Test Programs

The project includes test programs with intentional bugs for skill validation:

```bash
# Build all test programs
cd examples/client/c_test
./build_all.sh

# Test programs available:
examples/client/c_test/
├── null_deref/          # Null pointer dereference
├── buffer_overflow/     # Stack buffer overflow
├── use_after_free/      # Use-after-free
├── divide_by_zero/      # Division by zero
├── stack_overflow/      # Stack overflow via recursion
├── format_string/       # Format string vulnerability
├── double_free/         # Double free
└── infinite_loop/       # Infinite loop
```

### Skill Documentation

Full debugging guide is available in the skill file:
- **Location**: `skills/lldb-debug/SKILL.md`
- **Content**: 700+ lines of comprehensive debugging methodologies
- **Coverage**: Mindset, workflows, error types, strategies, decision trees, reference tables

## Usage Examples

### Example 1: Basic Debugging with Claude Code

After configuring MCP, you can debug naturally in Claude Code:

```
User: "Debug the program at /path/to/my/app"

Claude automatically executes:
1. Calls lldb_initialize to create a session
2. Calls lldb_createTarget to load the binary
3. Calls lldb_setBreakpoint to set a breakpoint at main
4. Calls lldb_launch to start the process
5. Calls lldb_pollEvents to check for breakpoint hits
6. Calls lldb_stackTrace to show the stack
```

### Example 2: Crash Analysis

```
User: "This program crashed, help me analyze the cause"

Claude will:
1. Call lldb_pollEvents to get the crash event
2. Call lldb_analyzeCrash to classify the crash type
3. Call lldb_stackTrace to show the crash stack
4. Call lldb_readRegisters to check register state
5. Call lldb_getSuspiciousFunctions to detect dangerous functions
6. Provide repair suggestions
```

### Example 3: Memory Debugging

```
User: "Check if there is a buffer overflow at address 0x100000"

Claude will:
1. Call lldb_readMemory to check memory content
2. Call lldb_setWatchpoint to monitor memory access
3. Call lldb_continue to resume execution
4. Call lldb_pollEvents to detect watchpoint hits
5. Analyze memory access patterns
```

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

## Troubleshooting

### Issue: `No module named lldb`

**Cause:** LLDB Python bindings are not configured correctly.

**Solution:**

```bash
# 1. Verify LLDB is from Homebrew
which lldb

# 2. If not, check PATH configuration
cat ~/.zshrc | grep llvm

# 3. If missing, add to PATH
echo 'export PATH="$(brew --prefix llvm)/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
hash -r

# 4. Set LLDB_PYTHON_PATH in .mcp.json (see MCP Configuration section)
```

### Issue: LLDB still uses system version

**Cause:** PATH configuration incorrect or terminal not restarted.

**Solution:**

```bash
# 1. Reload shell configuration
source ~/.zshrc
hash -r

# 2. Fully restart terminal

# 3. Verify LLDB path
which lldb
lldb --version
```

### Issue: `uvx` command not found

**Cause:** `uv` is not installed.

**Solution:**

```bash
# Install uv (provides uvx)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
which uvx
uvx --version
```

### Issue: Permission denied when launching/attaching

**Cause:** Security environment variables not set.

**Solution:**

Ensure `.mcp.json` contains:
```json
"env": {
  "LLDB_MCP_ALLOW_LAUNCH": "1",
  "LLDB_MCP_ALLOW_ATTACH": "1"
}
```

## Project Structure

```
lldb-mcp-server/
├── src/lldb_mcp_server/
│   ├── fastmcp_server.py      # MCP entry point
│   ├── session/
│   │   └── manager.py          # SessionManager (core)
│   ├── tools/                  # 9 tool modules
│   │   ├── session.py          # Session management
│   │   ├── target.py           # Target control
│   │   ├── breakpoints.py      # Breakpoints
│   │   ├── execution.py        # Execution control
│   │   ├── inspection.py       # Inspection
│   │   ├── memory.py           # Memory operations
│   │   ├── watchpoints.py      # Watchpoints
│   │   ├── registers.py        # Registers
│   │   └── advanced.py         # Advanced tools
│   └── analysis/
│       └── exploitability.py   # Crash analysis
├── .mcp.json.uvx               # MCP config template
├── pyproject.toml              # Package config
├── LICENSE                     # MIT License
└── README.md                   # English documentation
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- **PyPI Package**: [https://pypi.org/project/lldb-mcp-server/](https://pypi.org/project/lldb-mcp-server/)
- **Source Code**: [https://github.com/FYTJ/lldb-mcp-server](https://github.com/FYTJ/lldb-mcp-server)
- **Issues**: [https://github.com/FYTJ/lldb-mcp-server/issues](https://github.com/FYTJ/lldb-mcp-server/issues)
- **MCP Documentation**: [https://modelcontextprotocol.io](https://modelcontextprotocol.io)
