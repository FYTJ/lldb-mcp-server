## Linux Installation

This guide covers installing **LLDB MCP Server** on Linux distributions and configuring LLDB Python bindings so `import lldb` works.

## Requirements

- Python 3.10+
- LLDB 14+ (18+ recommended)
- LLDB Python bindings package (distribution-specific)

## Install LLDB + Python Bindings

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y lldb-19 python3-lldb-19 python3-pip

lldb-19 --version
# Expected: lldb version 19.x (or newer)

lldb-19 -P
# Expected: /usr/lib/llvm-19/lib/python3.12/site-packages (path may vary)

# Verify Python 3.12 is available (required for LLDB-19 bindings)
which python3.12
python3.12 --version
# Expected: Python 3.12.x
```

> **Note:** LLDB Python bindings are compiled for a specific Python version. LLDB-19 requires Python 3.12. If you have LLDB-18, it may require a different Python version - check with `lldb-18 -P | grep python3.`

### Fedora / RHEL-like

```bash
sudo dnf install -y lldb python3-lldb python3-pip

lldb --version
# Expected: lldb version 18.x (or newer)
```

### Arch Linux

```bash
sudo pacman -S --needed lldb python python-pip

lldb --version
# Expected: lldb version 18.x (or newer)
```

## Install uv (provides uvx)

Install `uv` which provides the `uvx` command for running Python tools:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reload shell to get uvx in PATH
source ~/.bashrc  # or source ~/.zshrc for zsh
```

## Verify LLDB Python Bindings

Test that LLDB Python bindings work with Python 3.12:

```bash
python3.12 -c "import sys; sys.path.insert(0, '$(/usr/bin/lldb-19 -P)'); import lldb; print('LLDB Python bindings OK')"
# Expected: LLDB Python bindings OK
```

## Configure MCP Server

### Get LLDB Python Path

```bash
LLDB_PATH=$(/usr/bin/lldb-19 -P)
echo "LLDB Python path: $LLDB_PATH"
# Expected: /usr/lib/llvm-19/lib/python3.12/site-packages
```

### Claude Code Configuration

```bash
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

### Claude Desktop Configuration

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

### Key Configuration Points

1. **`--python /usr/bin/python3.12`**: Forces uvx to use Python 3.12, matching LLDB-19 bindings
2. **`LLDB_PYTHON_PATH`**: Points to LLDB Python bindings (from `lldb-19 -P`)
3. **`LLDB_MCP_ALLOW_LAUNCH` and `LLDB_MCP_ALLOW_ATTACH`**: Security flags to enable debugging operations

## Critical: Python Version Matching

The most common issue on Linux is **Python version mismatch** between uvx and LLDB.

### Problem

- **LLDB Python bindings are compiled for a specific Python version** (e.g., LLDB-19 → Python 3.12)
- **uvx defaults to system Python**, which may be different (e.g., Python 3.14 from linuxbrew)
- **Mismatch causes `cannot import name '_lldb'` error**

### Solution

**Always specify the matching Python version with `--python`:**

```bash
# Check LLDB's Python version
lldb-19 -P
# Output: /usr/lib/llvm-19/lib/python3.12/site-packages
#         ^^^^^^^^ This shows Python 3.12

# Check uvx's default Python
uvx --python-preference system python --version
# If this shows 3.14, but LLDB needs 3.12, that's the problem

# Force uvx to use Python 3.12
# Add to MCP config: "--python", "/usr/bin/python3.12"
```

### Verification

Test the configuration before using with MCP:

```bash
LLDB_PYTHON_PATH=$(/usr/bin/lldb-19 -P) \
uvx --python /usr/bin/python3.12 -q lldb-mcp-server --help
# Expected: shows help output without import errors
```

## Troubleshooting

### Error: `cannot import name '_lldb'`

This means Python version mismatch. Check:

1. LLDB's Python version: `lldb-19 -P | grep -o 'python3\.[0-9]*'`
2. Update MCP config to use matching `--python /usr/bin/python3.XX`

### Error: `No module named 'lldb'`

This means `LLDB_PYTHON_PATH` is not set or incorrect:

1. Get correct path: `lldb-19 -P`
2. Update MCP config `env.LLDB_PYTHON_PATH` to that path

### Check Python Availability

If `/usr/bin/python3.12` doesn't exist:

```bash
# Find available Python versions
ls /usr/bin/python3.*

# Install Python 3.12 if needed (Ubuntu/Debian)
sudo apt install python3.12
```
