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

**Cause:** `uvx` creates isolated environments that cannot access system LLDB Python bindings.

**Solution:**

```bash
# 1. Uninstall if installed with uvx
# (No action needed, uvx uses temporary environments)

# 2. Install with pip instead
pip3 install --user lldb-mcp-server

# 3. Find LLDB Python path
lldb-18 -P
# Output: /usr/lib/llvm-18/lib/python3.12/site-packages

# 4. Set environment variable permanently
echo 'export LLDB_PYTHON_PATH="/usr/lib/llvm-18/lib/python3.12/site-packages"' >> ~/.bashrc
source ~/.bashrc

# 5. Update configuration to use lldb-mcp-server command
# In .mcp.json or claude_desktop_config.json:
{
  "command": "lldb-mcp-server",  # NOT "uvx"
  "args": [],
  "env": {
    "LLDB_PYTHON_PATH": "/usr/lib/llvm-18/lib/python3.12/site-packages"
  }
}
```

### Issue: `lldb-mcp-server: command not found` on Linux

**Cause:** `~/.local/bin` is not in PATH.

**Solution:**

```bash
# 1. Add to PATH permanently
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 2. Or use full path in configuration
{
  "command": "/home/YOUR_USERNAME/.local/bin/lldb-mcp-server",
  "env": {
    "PATH": "/home/YOUR_USERNAME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
  }
}
```

### Issue: Python version mismatch on Linux

**Cause:** LLDB Python bindings built for different Python version than system default.

**Solution:**

```bash
# 1. Check Python versions
python3 --version  # System Python
lldb-18 -P | grep python  # LLDB Python version

# 2. If mismatch, ensure LLDB_PYTHON_PATH is set correctly
# Example: If LLDB uses Python 3.12 but system is 3.14:
export LLDB_PYTHON_PATH="/usr/lib/llvm-18/lib/python3.12/site-packages"

# 3. Verify import works
python3 -c "import sys; sys.path.insert(0, '/usr/lib/llvm-18/lib/python3.12/site-packages'); import lldb; print('OK')"
```

### Issue: LLDB Python module not found on Ubuntu/Debian

**Cause:** LLDB Python bindings not installed.

**Solution:**

```bash
# Install LLDB with Python bindings
sudo apt update
sudo apt install lldb-18 python3-lldb-18

# Verify installation
lldb-18 -P
python3 -c "import sys; sys.path.insert(0, '$(lldb-18 -P)'); import lldb; print('OK')"
```

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
   lldb-mcp-server

   # Should output: "LLDB MCP Server starting..." and wait for input
   # Press Ctrl+C to exit
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
lldb-18 --version
lldb-18 -P
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
