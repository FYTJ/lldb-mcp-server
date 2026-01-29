# LLDB MCP Server

**Language:** [English](README.md) | [中文](docs/README.zh.md)

[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](https://github.com/FYTJ/lldb-mcp-server)
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

**Key Capabilities:**
- 🔧 **40 Debugging Tools**: Session management, breakpoints, execution control, memory operations, security analysis, and more
- 🔄 **Multi-session Support**: Run multiple independent debugging sessions concurrently
- 📊 **Event-driven Architecture**: Non-blocking event collection for state changes, breakpoint hits, stdout/stderr
- 🛡️ **Security Analysis**: Crash exploitability classification and dangerous function detection
- 📝 **Session Recording**: Automatically records all commands and output with timestamps
- 💻 **Cross-platform**: Supports macOS (Intel & Apple Silicon) and Linux (Ubuntu, Fedora, Arch)

## Documentation

- **[Features](docs/FEATURES.md)** - Complete list of 40 tools and detailed capabilities
- **[Configuration](docs/CONFIGURATION.md)** - Detailed configuration for Claude Code, Claude Desktop, Cursor, and Codex
- **[Usage Guide](docs/USAGE.md)** - Usage examples, Claude Code Skill integration, and test programs
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions for all platforms
- **[Linux Installation](docs/LINUX_INSTALLATION.md)** - Detailed Linux installation guide

## Prerequisites

### System Requirements

- **Operating System**: macOS (Intel or Apple Silicon) **or** Linux (Ubuntu 22.04+, Fedora 38+, Arch Linux)
- **LLDB** with Python bindings (version 14+, 18+ recommended)
- **Python 3.10+**

### Platform-Specific Requirements

**macOS:**
- **Homebrew** ([Installation Guide](https://brew.sh/))
- **Homebrew LLVM** or Xcode Command Line Tools

**Linux:**
- **Package Manager**: apt (Ubuntu/Debian), dnf (Fedora/RHEL), or pacman (Arch)
- **LLDB**: Install via `sudo apt install lldb-18 python3-lldb-18` (Ubuntu) or equivalent

## Quick Start

### 1. Install Dependencies

#### macOS

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

#### Linux (Ubuntu/Debian)

```bash
# Install LLDB with Python bindings
sudo apt update
sudo apt install lldb-18 python3-lldb-18

# Install lldb-mcp-server (use pip, NOT uvx on Linux)
pip3 install --user lldb-mcp-server

# Find LLDB Python path
lldb-18 -P
# Example output: /usr/lib/llvm-18/lib/python3.12/site-packages

# Set LLDB_PYTHON_PATH (add to ~/.bashrc for persistence)
export LLDB_PYTHON_PATH="/usr/lib/llvm-18/lib/python3.12/site-packages"

# Verify installation
python3 -c "import lldb; print('LLDB Python bindings OK')"
lldb-mcp-server --help
```

> **⚠️ IMPORTANT - Linux Users:**
> - **DO NOT use `uvx` on Linux** - it creates isolated environments that cannot access system LLDB
> - **Use `pip3 install --user lldb-mcp-server`** instead
> - **Always set `LLDB_PYTHON_PATH`** in your configuration
> - Use `lldb-mcp-server` command directly (not `uvx lldb-mcp-server`)

**For other Linux distributions (Fedora, Arch, etc.)**, see the [Linux Installation Guide](docs/LINUX_INSTALLATION.md).

### 2. Configure MCP

Choose your IDE and follow the configuration instructions:

#### Claude Code

**macOS - Global Configuration (Recommended):**

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

**Linux:**
```bash
claude mcp add-json --scope user lldb-debugger '{
  "type": "stdio",
  "command": "lldb-mcp-server",
  "args": [],
  "env": {
    "LLDB_MCP_ALLOW_LAUNCH": "1",
    "LLDB_MCP_ALLOW_ATTACH": "1",
    "LLDB_PYTHON_PATH": "/usr/lib/llvm-18/lib/python3.12/site-packages"
  }
}'
```
> **Note:** Replace `/usr/lib/llvm-18/lib/python3.12/site-packages` with output from `lldb-18 -P`

#### Claude Desktop

**macOS:**
Edit `~/Library/Application Support/Claude/claude_desktop_config.json`

**Linux:**
Edit `~/.config/claude/claude_desktop_config.json`

See [Configuration Guide](docs/CONFIGURATION.md) for detailed configuration examples.

#### Cursor IDE

Create `.cursor/mcp.json` in your project root or `~/.cursor/mcp.json` for global configuration.

See [Configuration Guide](docs/CONFIGURATION.md) for platform-specific examples.

#### Codex (OpenAI)

Use `codex mcp add` command or edit `~/.codex/config.toml`.

See [Configuration Guide](docs/CONFIGURATION.md) for detailed instructions.

### 3. Start Using

**macOS:**
No manual installation required! When you configure the MCP server using `uvx`, it automatically installs and manages the package.

**Linux:**
After installing with `pip` and configuring environment variables, the server is ready to use.

Just configure your IDE and start Claude Code or restart Claude Desktop.

## Usage Examples

### Basic Debugging

```
User: "Debug the program at /path/to/my/app"

Claude automatically:
1. Creates a debugging session
2. Loads the binary
3. Sets breakpoints
4. Launches the process
5. Analyzes execution
```

### Crash Analysis

```
User: "This program crashed, help me analyze the cause"

Claude will:
1. Analyze the crash event
2. Show crash stack trace
3. Check register state
4. Detect dangerous functions
5. Provide repair suggestions
```

For more examples, see the [Usage Guide](docs/USAGE.md).

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `LLDB_MCP_ALLOW_LAUNCH=1` | Allow launching new processes | Disabled |
| `LLDB_MCP_ALLOW_ATTACH=1` | Allow attaching to existing processes | Disabled |
| `LLDB_PYTHON_PATH` | Override LLDB Python module path | Auto-detect |

## Troubleshooting

### macOS: `No module named lldb`

```bash
# Verify LLDB is from Homebrew
which lldb

# Add to PATH
echo 'export PATH="$(brew --prefix llvm)/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
hash -r
```

### Linux: `cannot import name '_lldb'`

```bash
# Install with pip (not uvx)
pip3 install --user lldb-mcp-server

# Set LLDB_PYTHON_PATH
lldb-18 -P
export LLDB_PYTHON_PATH="/usr/lib/llvm-18/lib/python3.12/site-packages"
```

For more issues and solutions, see the [Troubleshooting Guide](docs/TROUBLESHOOTING.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- **Documentation**: [Features](docs/FEATURES.md) | [Configuration](docs/CONFIGURATION.md) | [Usage](docs/USAGE.md) | [Troubleshooting](docs/TROUBLESHOOTING.md)
- **PyPI Package**: [https://pypi.org/project/lldb-mcp-server/](https://pypi.org/project/lldb-mcp-server/)
- **Source Code**: [https://github.com/FYTJ/lldb-mcp-server](https://github.com/FYTJ/lldb-mcp-server)
- **Issues**: [https://github.com/FYTJ/lldb-mcp-server/issues](https://github.com/FYTJ/lldb-mcp-server/issues)
- **MCP Documentation**: [https://modelcontextprotocol.io](https://modelcontextprotocol.io)
