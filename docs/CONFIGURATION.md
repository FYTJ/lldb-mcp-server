# LLDB MCP Server - Configuration Guide

**Language:** [English](CONFIGURATION.md) | [中文](CONFIGURATION.zh.md)

This guide provides detailed configuration instructions for LLDB MCP Server across different IDEs and platforms.

## Table of Contents

- [Environment Variables](#environment-variables)
- [Claude Code Configuration](#claude-code-configuration)
- [Claude Desktop Configuration](#claude-desktop-configuration)
- [Cursor IDE Configuration](#cursor-ide-configuration)
- [Codex Configuration](#codex-configuration)
- [Manual LLDB Path Configuration](#manual-lldb-path-configuration)

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `LLDB_MCP_ALLOW_LAUNCH=1` | Allow launching new processes | Disabled |
| `LLDB_MCP_ALLOW_ATTACH=1` | Allow attaching to existing processes | Disabled |
| `LLDB_PYTHON_PATH` | Override LLDB Python module path | Auto-detect |

**Security Note:** `LLDB_MCP_ALLOW_LAUNCH` and `LLDB_MCP_ALLOW_ATTACH` are required for launching and attaching operations. Without these, the server will reject such operations.

## Claude Code Configuration

### Global Configuration (Recommended)

**macOS - Intel (x86_64):**
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

**macOS - Apple Silicon (arm64):**
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
# First, get your LLDB Python path
LLDB_PATH=$(/usr/bin/lldb-19 -P)
echo "LLDB Python path: $LLDB_PATH"

# Then add MCP server configuration
claude mcp add-json --scope user lldb-debugger '{
  "type": "stdio",
  "command": "uvx",
  "args": ["--python", "/usr/bin/python3.12", "-q", "lldb-mcp-server", "--transport", "stdio"],
  "env": {
    "LLDB_MCP_ALLOW_LAUNCH": "1",
    "LLDB_MCP_ALLOW_ATTACH": "1",
    "LLDB_PYTHON_PATH": "'"$LLDB_PATH"'"
  }
}'
```
> **Important:**
> - Replace `/usr/bin/python3.12` with your system's Python 3.12 path if different
> - The `--python` argument must match the Python version LLDB was compiled for
> - Check LLDB's Python version: `lldb-19 -P | grep python3.`

### Project-Specific Configuration

Create `.mcp.json` in your project root directory:

**macOS - Intel (x86_64):**
```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "uvx",
      "args": ["--python", "/usr/local/opt/python@3.13/bin/python3.13", "lldb-mcp-server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1",
        "PYTHONPATH": "/usr/local/opt/llvm/lib/python3.13/site-packages"
      }
    }
  }
}
```

**macOS - Apple Silicon (arm64):**
```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "uvx",
      "args": ["--python", "/opt/homebrew/opt/python@3.13/bin/python3.13", "lldb-mcp-server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1",
        "PYTHONPATH": "/opt/homebrew/opt/llvm/lib/python3.13/site-packages"
      }
    }
  }
}
```

**Linux:**
```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "uvx",
      "args": ["--python", "/usr/bin/python3.12", "-q", "lldb-mcp-server", "--transport", "stdio"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1",
        "LLDB_PYTHON_PATH": "/usr/lib/llvm-19/lib/python3.12/site-packages"
      }
    }
  }
}
```

> **Linux Notes:**
> - Use `uvx` with `--python /usr/bin/python3.12` to match LLDB's Python version
> - Set `LLDB_PYTHON_PATH` to output from `lldb-19 -P`
> - Replace Python path if using different LLDB version (check with `lldb-19 -P | grep python3.`)

## Claude Desktop Configuration

### macOS

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

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
        "PYTHONPATH": "/usr/local/opt/llvm/lib/python3.13/site-packages"
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
        "PYTHONPATH": "/opt/homebrew/opt/llvm/lib/python3.13/site-packages"
      }
    }
  }
}
```

### Linux

Edit `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "uvx",
      "args": ["--python", "/usr/bin/python3.12", "-q", "lldb-mcp-server", "--transport", "stdio"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1",
        "LLDB_PYTHON_PATH": "/usr/lib/llvm-19/lib/python3.12/site-packages"
      }
    }
  }
}
```

> **Important:**
> - Replace `/usr/bin/python3.12` with your Python 3.12 path
> - Replace `/usr/lib/llvm-19/lib/python3.12/site-packages` with output from `lldb-19 -P`
> - The Python version in both paths must match LLDB's Python version

> **Note:** Replace `/usr/lib/llvm-18/lib/python3.12/site-packages` with output from `lldb-18 -P`, and `YOUR_USERNAME` with your actual username.

After editing, restart Claude Desktop.

## Cursor IDE Configuration

### Option 1: Project-Specific Configuration (Recommended)

Create `.cursor/mcp.json` in your project root:

**macOS - Intel (x86_64):**
```bash
mkdir -p .cursor
cat > .cursor/mcp.json << 'EOF'
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "uvx",
      "args": ["--python", "/usr/local/opt/python@3.13/bin/python3.13", "lldb-mcp-server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1",
        "PYTHONPATH": "/usr/local/opt/llvm/lib/python3.13/site-packages"
      }
    }
  }
}
EOF
```

**macOS - Apple Silicon (arm64):**
```bash
mkdir -p .cursor
cat > .cursor/mcp.json << 'EOF'
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "uvx",
      "args": ["--python", "/opt/homebrew/opt/python@3.13/bin/python3.13", "lldb-mcp-server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1",
        "PYTHONPATH": "/opt/homebrew/opt/llvm/lib/python3.13/site-packages"
      }
    }
  }
}
EOF
```

**Linux:**
```bash
mkdir -p .cursor
cat > .cursor/mcp.json << 'EOF'
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "lldb-mcp-server",
      "args": [],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1",
        "LLDB_PYTHON_PATH": "/usr/lib/llvm-18/lib/python3.12/site-packages",
        "PATH": "/home/YOUR_USERNAME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
      }
    }
  }
}
EOF
```
> **Note:** Replace `/usr/lib/llvm-18/lib/python3.12/site-packages` with output from `lldb-18 -P`, and `YOUR_USERNAME` with your actual username.

### Option 2: Global Configuration

Create `~/.cursor/mcp.json` in your home directory using the same JSON structure as above. This makes the LLDB debugger available across all your Cursor projects.

After configuration, restart Cursor to load the MCP server.

## Codex Configuration

### macOS

**Intel (x86_64) - CLI:**
```bash
codex mcp add lldb-debugger \
  --env LLDB_MCP_ALLOW_LAUNCH=1 \
  --env LLDB_MCP_ALLOW_ATTACH=1 \
  --env PYTHONPATH=/usr/local/opt/llvm/lib/python3.13/site-packages \
  -- uvx --python /usr/local/opt/python@3.13/bin/python3.13 lldb-mcp-server
```

**Apple Silicon (arm64) - CLI:**
```bash
codex mcp add lldb-debugger \
  --env LLDB_MCP_ALLOW_LAUNCH=1 \
  --env LLDB_MCP_ALLOW_ATTACH=1 \
  --env PYTHONPATH=/opt/homebrew/opt/llvm/lib/python3.13/site-packages \
  -- uvx --python /opt/homebrew/opt/python@3.13/bin/python3.13 lldb-mcp-server
```

**Manual - Edit `~/.codex/config.toml` (Intel):**
```toml
[mcp_servers.lldb-debugger]
command = "uvx"
args = ["--python", "/usr/local/opt/python@3.13/bin/python3.13", "lldb-mcp-server"]

[mcp_servers.lldb-debugger.env]
LLDB_MCP_ALLOW_LAUNCH = "1"
LLDB_MCP_ALLOW_ATTACH = "1"
PYTHONPATH = "/usr/local/opt/llvm/lib/python3.13/site-packages"
```

**Manual - Edit `~/.codex/config.toml` (Apple Silicon):**
```toml
[mcp_servers.lldb-debugger]
command = "uvx"
args = ["--python", "/opt/homebrew/opt/python@3.13/bin/python3.13", "lldb-mcp-server"]

[mcp_servers.lldb-debugger.env]
LLDB_MCP_ALLOW_LAUNCH = "1"
LLDB_MCP_ALLOW_ATTACH = "1"
PYTHONPATH = "/opt/homebrew/opt/llvm/lib/python3.13/site-packages"
```

### Linux

**CLI:**
```bash
# Get LLDB Python path
LLDB_PATH=$(/usr/bin/lldb-19 -P)

codex mcp add lldb-debugger \
  --env LLDB_MCP_ALLOW_LAUNCH=1 \
  --env LLDB_MCP_ALLOW_ATTACH=1 \
  --env LLDB_PYTHON_PATH="$LLDB_PATH" \
  -- uvx --python /usr/bin/python3.12 -q lldb-mcp-server --transport stdio
```

**Manual - Edit `~/.codex/config.toml`:**
```toml
[mcp_servers.lldb-debugger]
command = "uvx"
args = ["--python", "/usr/bin/python3.12", "-q", "lldb-mcp-server", "--transport", "stdio"]

[mcp_servers.lldb-debugger.env]
LLDB_MCP_ALLOW_LAUNCH = "1"
LLDB_MCP_ALLOW_ATTACH = "1"
LLDB_PYTHON_PATH = "/usr/lib/llvm-19/lib/python3.12/site-packages"
```
> **Important:**
> - Replace `/usr/bin/python3.12` with your Python 3.12 path
> - Replace `/usr/lib/llvm-19/lib/python3.12/site-packages` with output from `lldb-19 -P`
> - Python version must match LLDB's Python version

**Note:** You can also create project-scoped `.codex/config.toml` in your project root (trusted projects only).

## Manual LLDB Path Configuration

If the server cannot automatically find LLDB Python bindings, you need to explicitly set `LLDB_PYTHON_PATH`:

### Finding LLDB Path

**macOS:**
```bash
# Method 1: Check Homebrew LLVM path
brew --prefix llvm
# Output: /usr/local/opt/llvm (Intel) or /opt/homebrew/opt/llvm (ARM)

# Add Python version: /usr/local/opt/llvm/lib/python3.13/site-packages

# Method 2: Use lldb -P command
lldb -P
```

**Linux:**
```bash
# Use lldb -P command with version-specific binary
lldb-18 -P
# Example output: /usr/lib/llvm-18/lib/python3.12/site-packages

# Or check manually
ls /usr/lib/llvm-*/lib/python*/site-packages/lldb
```

### Adding to Configuration

Once you have the LLDB Python path, add it to the `env` section of your configuration:

**macOS Example:**
```json
{
  "env": {
    "LLDB_MCP_ALLOW_LAUNCH": "1",
    "LLDB_MCP_ALLOW_ATTACH": "1",
    "LLDB_PYTHON_PATH": "/opt/homebrew/opt/llvm/lib/python3.13/site-packages"
  }
}
```

**Linux Example:**
```json
{
  "env": {
    "LLDB_MCP_ALLOW_LAUNCH": "1",
    "LLDB_MCP_ALLOW_ATTACH": "1",
    "LLDB_PYTHON_PATH": "/usr/lib/llvm-18/lib/python3.12/site-packages"
  }
}
```

## Verifying Configuration

After configuration, verify the setup:

**Test LLDB import:**
```bash
python3 -c "import lldb; print('LLDB version:', lldb.SBDebugger.GetVersionString())"
```

**Test MCP server (if installed globally):**
```bash
lldb-mcp-server --help
```

## See Also

- [Features](FEATURES.md) - Complete list of 40 tools
- [Usage Guide](USAGE.md) - Usage examples and skill integration
- [Troubleshooting](TROUBLESHOOTING.md) - Common configuration issues
- [Main README](../README.md) - Quick start guide
