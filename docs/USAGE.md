# LLDB MCP Server - Usage Guide

**Language:** [English](USAGE.md) | [中文](USAGE.zh.md)

This guide provides usage examples and instructions for using LLDB MCP Server with AI assistants like Claude Code.

## Table of Contents

- [Usage Examples](#usage-examples)
- [Claude Code Skill Integration](#claude-code-skill-integration)
- [Test Programs](#test-programs)
- [Project Structure](#project-structure)

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

### Example 4: Core Dump Analysis

```
User: "Analyze this core dump at /path/to/core"

Claude will:
1. Call lldb_initialize to create a session
2. Call lldb_loadCore to load the core dump
3. Call lldb_stackTrace to show the crash stack
4. Call lldb_analyzeCrash to determine crash type
5. Call lldb_readMemory to inspect memory state
6. Provide root cause analysis
```

### Example 5: Multi-threaded Debugging

```
User: "Debug this multi-threaded program that has a race condition"

Claude will:
1. Call lldb_initialize and lldb_createTarget
2. Call lldb_setBreakpoint on critical sections
3. Call lldb_launch to start the program
4. Call lldb_threads to list all threads
5. Call lldb_stackTrace for each thread
6. Analyze thread interactions and identify race conditions
```

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

### Skill Documentation

Full debugging guide is available in the skill file:
- **Location**: `skills/lldb-debug/SKILL.md`
- **Content**: 700+ lines of comprehensive debugging methodologies
- **Coverage**: Mindset, workflows, error types, strategies, decision trees, reference tables

## Test Programs

The project includes test programs with intentional bugs for skill validation and testing:

### Building Test Programs

```bash
# Build all test programs
cd examples/client/c_test
./build_all.sh

# Or build individual programs
cd examples/client/c_test/null_deref
gcc -g null_deref.c -o null_deref
```

### Available Test Programs

Located in `examples/client/c_test/`:

| Program | Bug Type | Description |
|---------|----------|-------------|
| `null_deref/` | Null pointer dereference | Dereferencing a NULL pointer |
| `buffer_overflow/` | Stack buffer overflow | Writing beyond buffer bounds using strcpy |
| `use_after_free/` | Use-after-free | Accessing memory after it's been freed |
| `divide_by_zero/` | Division by zero | Integer division by zero |
| `stack_overflow/` | Stack overflow | Infinite recursion causing stack exhaustion |
| `format_string/` | Format string vulnerability | Unsafe use of printf with user input |
| `double_free/` | Double free | Freeing the same memory twice |
| `infinite_loop/` | Infinite loop | Loop that never terminates |

### Running Test Programs

**Method 1: Direct debugging with Claude Code**
```
# In Claude Code, after MCP is configured:
User: "Debug the null pointer dereference program at examples/client/c_test/null_deref/null_deref"
```

**Method 2: Using Python debug flow**
```bash
cd examples/client
TARGET_BIN=./c_test/null_deref/null_deref python3 run_debug_flow.py
```

**Method 3: Manual MCP tool invocation**
```python
# Example: Debug null_deref program
import json

# 1. Initialize session
lldb_initialize()
# Returns: {"sessionId": "session-123"}

# 2. Create target
lldb_createTarget("session-123", "examples/client/c_test/null_deref/null_deref")

# 3. Set breakpoint
lldb_setBreakpoint("session-123", symbol="main")

# 4. Launch
lldb_launch("session-123")

# 5. Poll events
lldb_pollEvents("session-123")

# 6. Continue execution
lldb_continue("session-123")

# 7. Get crash info
lldb_analyzeCrash("session-123")
lldb_stackTrace("session-123")
```

## Project Structure

```
lldb-mcp-server/
├── src/lldb_mcp_server/
│   ├── fastmcp_server.py      # MCP entry point
│   ├── platform/               # Platform abstraction layer
│   │   ├── __init__.py
│   │   ├── detector.py         # OS/distro detection
│   │   ├── provider.py         # Abstract platform provider
│   │   ├── macos.py            # macOS-specific paths
│   │   └── linux.py            # Linux-specific paths
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
│   ├── analysis/
│   │   └── exploitability.py   # Crash analysis
│   └── utils/
│       ├── config.py           # Configuration loading
│       └── errors.py           # Error handling
├── skills/
│   └── lldb-debug/             # Claude Code debugging skill
│       └── SKILL.md            # 700+ line debugging guide
├── examples/
│   └── client/
│       ├── c_test/             # Test programs with bugs
│       │   ├── null_deref/
│       │   ├── buffer_overflow/
│       │   ├── use_after_free/
│       │   └── ...
│       └── run_debug_flow.py   # Example debugging script
├── docs/
│   ├── FEATURES.md             # Feature documentation
│   ├── CONFIGURATION.md        # Configuration guide
│   ├── TROUBLESHOOTING.md      # Troubleshooting guide
│   ├── USAGE.md                # This file
│   └── LINUX_INSTALLATION.md   # Linux installation guide
├── scripts/
│   └── diagnose_lldb_linux.sh  # Linux diagnostic script
├── .mcp.json.uvx               # MCP config template
├── pyproject.toml              # Package configuration
├── LICENSE                     # MIT License
└── README.md                   # Main documentation
```

### Key Components

**SessionManager (`src/lldb_mcp_server/session/manager.py`)**
- Central state management for all debugging sessions
- Owns all session lifecycle (create, terminate, list)
- Implements all MCP tool operations
- Thread-safe with background event collection

**Platform Abstraction (`src/lldb_mcp_server/platform/`)**
- Auto-detects OS and Linux distribution
- Provides platform-specific LLDB paths
- Handles macOS Homebrew and Linux package manager installations

**Tool Registration (`src/lldb_mcp_server/tools/`)**
- Each module registers a category of MCP tools
- Clean separation of concerns
- Easy to extend with new tools

## See Also

- [Features](FEATURES.md) - Complete list of 40 tools and capabilities
- [Configuration Guide](CONFIGURATION.md) - Detailed configuration for all IDEs
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
- [Main README](../README.md) - Quick start guide
