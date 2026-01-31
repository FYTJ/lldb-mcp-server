# LLDB MCP Server - Troubleshooting Guide

**Language:** [English](TROUBLESHOOTING.md) | [中文](TROUBLESHOOTING.zh.md)

This guide covers common issues and solutions for LLDB MCP Server across different platforms.

## Table of Contents

- [macOS Issues](#macos-issues)
- [Linux Issues](#linux-issues)
- [General Issues](#general-issues)
- [Diagnostic Tools](#diagnostic-tools)

## macOS Issues

### Issue: `No module named lldb`

**Cause:** LLDB Python bindings are not configured correctly.

**Solution:**

```bash
# 1. Verify LLDB is from Homebrew
which lldb
# Should output: /usr/local/opt/llvm/bin/lldb or /opt/homebrew/opt/llvm/bin/lldb

# 2. If not, check PATH configuration
cat ~/.zshrc | grep llvm

# 3. If missing, add to PATH
echo 'export PATH="$(brew --prefix llvm)/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
hash -r

# 4. Set LLDB_PYTHON_PATH in .mcp.json (see Configuration Guide)
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
# Should show LLVM version, not "lldb-1500" (Xcode version)
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

## Linux Issues

### Issue: `cannot import name '_lldb'` on Linux

**Cause:** Python version mismatch between `uvx` and LLDB Python bindings.

- LLDB Python bindings are compiled for a specific Python version (e.g., LLDB-19 → Python 3.12)
- `uvx` defaults to system Python, which may be different (e.g., Python 3.14 from linuxbrew)

**Solution:**

```bash
# 1. Check LLDB's Python version
lldb-19 -P
# Output: /usr/lib/llvm-19/lib/python3.12/site-packages
#         ^^^^^^^^ This shows Python 3.12

# 2. Check uvx's default Python
uvx --python-preference system python --version
# If this shows 3.14, but LLDB needs 3.12, that's the problem

# 3. Check if Python 3.12 is available
which python3.12
python3.12 --version

# 4. Update MCP configuration to force Python 3.12
# Get LLDB path
LLDB_PATH=$(/usr/bin/lldb-19 -P)

# Update configuration (Claude Code)
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

# 5. Verify the fix
LLDB_PYTHON_PATH=$(/usr/bin/lldb-19 -P) \
uvx --python /usr/bin/python3.12 -q lldb-mcp-server --help
# Expected: shows help output without import errors
```

**Key Points:**
- The `--python /usr/bin/python3.12` argument forces uvx to use Python 3.12
- Replace `lldb-19` with your LLDB version (e.g., `lldb-18`)
- Replace `/usr/bin/python3.12` with the path matching your LLDB's Python version

### Issue: `uvx: command not found` on Linux

**Cause:** `uv` is not installed or not in PATH.

**Solution:**

```bash
# 1. Install uv (provides uvx command)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Reload shell to update PATH
source ~/.bashrc  # or source ~/.zshrc for zsh

# 3. Verify installation
which uvx
uvx --version
```

### Issue: Python version mismatch on Linux

**Cause:** LLDB Python bindings built for different Python version than what uvx uses.

**Solution:**

```bash
# 1. Check Python versions
lldb-19 -P | grep -o 'python3\.[0-9]*'  # LLDB Python version (e.g., python3.12)
uvx --python-preference system python --version  # uvx's default Python

# 2. Force uvx to use matching Python version
# If LLDB needs Python 3.12, update MCP config to include:
{
  "command": "uvx",
  "args": ["--python", "/usr/bin/python3.12", "-q", "lldb-mcp-server", "--transport", "stdio"]
}

# 3. Verify the fix
LLDB_PYTHON_PATH=$(/usr/bin/lldb-19 -P) \
uvx --python /usr/bin/python3.12 -c "import lldb; print('OK')"
```

### Issue: LLDB Python module not found on Ubuntu/Debian

**Cause:** LLDB Python bindings not installed.

**Solution:**

```bash
# Install LLDB with Python bindings
sudo apt update
sudo apt install lldb-19 python3-lldb-19

# Verify installation
lldb-19 -P
# Expected: /usr/lib/llvm-19/lib/python3.12/site-packages

# Verify Python 3.12 is available
which python3.12
python3.12 --version

# Test import
python3.12 -c "import sys; sys.path.insert(0, '$(/usr/bin/lldb-19 -P)'); import lldb; print('OK')"
```

> **Note:** If LLDB-19 is not available on your Ubuntu version, you can use LLDB-18 or another available version. Just make sure to match the Python version accordingly.

### Issue: LLDB Python module not found on Fedora/RHEL

**Cause:** LLDB Python bindings not installed.

**Solution:**

```bash
# Install LLDB with Python bindings
sudo dnf install lldb lldb-devel python3-lldb

# Verify installation
lldb -P
python3 -c "import lldb; print('OK')"
```

### Issue: LLDB Python module not found on Arch Linux

**Cause:** LLDB Python bindings not installed.

**Solution:**

```bash
# Install LLDB
sudo pacman -S lldb

# Python bindings should be in /usr/lib/python3.X/site-packages
python3 -c "import lldb; print('OK')"
```

## General Issues

### Issue: MCP server not responding

**Cause:** Server crashed or configuration error.

**Debugging steps:**

1. **Check server logs** (if running in Claude Desktop):
   ```bash
   # macOS
   tail -f ~/Library/Logs/Claude/mcp*.log

   # Linux
   tail -f ~/.config/Claude/logs/mcp*.log
   ```

2. **Test server manually:**
   ```bash
   # macOS
   uvx --python /opt/homebrew/opt/python@3.13/bin/python3.13 lldb-mcp-server

   # Linux
   LLDB_PYTHON_PATH=$(/usr/bin/lldb-19 -P) \
   uvx --python /usr/bin/python3.12 -q lldb-mcp-server --help

   # Should output help information without errors
   # Press Ctrl+C to exit if it starts waiting for input
   ```

3. **Verify LLDB import:**
   ```bash
   python3 -c "import lldb; print('LLDB imported successfully')"
   ```

### Issue: Breakpoints not hitting

**Possible causes:**

1. **Binary not compiled with debug symbols:**
   ```bash
   # Recompile with -g flag
   gcc -g myprogram.c -o myprogram
   ```

2. **Optimization removing code:**
   ```bash
   # Compile without optimization
   gcc -g -O0 myprogram.c -o myprogram
   ```

3. **Wrong file path in breakpoint:**
   - Use absolute paths for file:line breakpoints
   - Or use function names: `lldb_setBreakpoint(sessionId, symbol="main")`

### Issue: Cannot evaluate expressions

**Possible causes:**

1. **Process not stopped:**
   - Expressions can only be evaluated when process is stopped (at breakpoint or after pause)

2. **Variables optimized away:**
   - Compile with `-O0` to prevent optimization

3. **Wrong frame selected:**
   - Use `lldb_selectFrame` to select the correct stack frame

### Issue: Core dump not loading

**Possible causes:**

1. **Mismatched binary:**
   ```bash
   # Ensure the binary matches the core dump
   lldb_loadCore(sessionId, corePath="/path/to/core", executablePath="/path/to/exact/binary")
   ```

2. **Core dump generation disabled:**
   ```bash
   # Enable core dumps (Linux)
   ulimit -c unlimited

   # Generate core dump
   ./myprogram
   # After crash: core file created
   ```

3. **Core dump format not supported:**
   - LLDB supports ELF core dumps (Linux) and Mach-O core dumps (macOS)

## Diagnostic Tools

### Linux Diagnostic Script

For Linux users, we provide an automated diagnostic script:

```bash
# Download and run diagnostic script
curl -sSL https://raw.githubusercontent.com/FYTJ/lldb-mcp-server/main/scripts/diagnose_lldb_linux.sh | bash

# Or if you have the repository cloned
./scripts/diagnose_lldb_linux.sh
```

This script checks:
- Operating system and version
- Python version
- LLDB installation
- LLDB Python path
- Python LLDB import
- Environment variables
- lldb-mcp-server installation

And provides recommended fixes based on detected issues.

### Manual Diagnostics

**Check LLDB installation:**
```bash
# macOS
which lldb
lldb --version
lldb -P

# Linux
which lldb lldb-18 lldb-19
lldb-19 --version  # or lldb-18 if using LLDB-18
lldb-19 -P
# Check Python version in path
lldb-19 -P | grep -o 'python3\.[0-9]*'
```

**Check Python LLDB import:**
```bash
python3 -c "import lldb; print('LLDB file:', lldb.__file__); print('LLDB version:', lldb.SBDebugger.GetVersionString())"
```

**Check lldb-mcp-server installation:**
```bash
which lldb-mcp-server
lldb-mcp-server --help
```

**Check environment variables:**
```bash
echo $LLDB_PYTHON_PATH
echo $LLDB_MCP_ALLOW_LAUNCH
echo $LLDB_MCP_ALLOW_ATTACH
echo $PATH | grep -o "[^:]*local/bin[^:]*"
```

## Still Having Issues?

If you're still experiencing problems:

1. **Check existing issues:** [GitHub Issues](https://github.com/FYTJ/lldb-mcp-server/issues)

2. **File a new issue** with the following information:
   - Operating system and version
   - Python version (`python3 --version`)
   - LLDB version (`lldb --version` or `lldb-18 --version`)
   - Output of `lldb -P` or `lldb-18 -P`
   - Full error messages
   - Configuration file contents (`.mcp.json`)

3. **Check platform-specific installation guides:**
   - [Linux Installation Guide](LINUX_INSTALLATION.md)
   - [Main README](../README.md)

## See Also

- [Configuration Guide](CONFIGURATION.md) - Detailed configuration instructions
- [Features](FEATURES.md) - Complete list of 40 tools
- [Usage Guide](USAGE.md) - Usage examples
- [Main README](../README.md) - Quick start guide
