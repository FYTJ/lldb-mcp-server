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
sudo apt install -y lldb-18 python3-lldb-18 python3-pip

lldb-18 --version
# Expected: lldb version 18.x (or newer)

lldb-18 -P
# Expected: /usr/lib/llvm-18/lib/python3.12/site-packages (path may vary)
```

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

## Install LLDB MCP Server

On Linux, install with `pip` so the server runs in the system Python environment that can access system LLDB bindings.

```bash
python3 -m pip install --user -U lldb-mcp-server

lldb-mcp-server --help
# Expected: shows CLI help output
```

## Configure LLDB Python Import

### Option A (Recommended): Set LLDB_PYTHON_PATH

Use `lldb -P` to find the correct path, then export it.

```bash
LLDB_PYTHON_PATH="$(lldb -P 2>/dev/null || true)"
echo "$LLDB_PYTHON_PATH"
```

If your distro uses versioned commands (Ubuntu/Debian):

```bash
LLDB_PYTHON_PATH="$(lldb-18 -P)"
echo "$LLDB_PYTHON_PATH"
# Expected: /usr/lib/llvm-18/lib/python3.12/site-packages (path may vary)
```

Make it persistent (bash):

```bash
echo "export LLDB_PYTHON_PATH=\"$LLDB_PYTHON_PATH\"" >> ~/.bashrc
```

Verify:

```bash
python3 -c "import lldb; print('LLDB Python bindings OK')"
# Expected: LLDB Python bindings OK
```

### Option B: Configure via MCP env

If you configure your MCP server via `.mcp.json`, set `LLDB_PYTHON_PATH` there.

Example (Claude Code / stdio):

```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "lldb-mcp-server",
      "args": [],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1",
        "LLDB_PYTHON_PATH": "/usr/lib/llvm-18/lib/python3.12/site-packages"
      }
    }
  }
}
```

## Common Pitfall: Do Not Use uvx on Linux

Tools like `uvx` typically run in an isolated environment that cannot see system-installed LLDB bindings.

If you see import errors like `No module named lldb` or `cannot import name '_lldb'`, use:

```bash
python3 -m pip install --user -U lldb-mcp-server
```

and set `LLDB_PYTHON_PATH` as shown above.
