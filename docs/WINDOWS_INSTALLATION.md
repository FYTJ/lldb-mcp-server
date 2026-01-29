## Windows Installation

This guide covers installing **LLDB MCP Server** on Windows and configuring LLDB Python bindings so `import lldb` works.

## Requirements

- Windows 10+ / Windows 11
- Python 3.10+
- LLVM/LLDB distribution that includes Python bindings

## Install LLVM (LLDB) and Python

### Option A (Recommended): Chocolatey

Open an **Administrator PowerShell** and run:

```powershell
choco install -y llvm python
```

Verify:

```powershell
lldb --version
# Expected: lldb version X.Y.Z

python --version
# Expected: Python 3.10+ (for example: Python 3.12.x)
```

## Verify LLDB Python Bindings

```powershell
python -c "import lldb; print(lldb.__file__)"
```

Expected output: a path to the `lldb` Python package (location varies by LLVM distribution).

If this fails, you likely need to set `LLDB_PYTHON_PATH` (next section).

## Configure LLDB_PYTHON_PATH

`LLDB_PYTHON_PATH` should point to a directory that contains the `lldb` Python package.

Common Chocolatey LLVM locations:
- `C:\Program Files\LLVM\lib\site-packages`
- `C:\Program Files\LLVM\lib\python3.12\site-packages` (Python version may vary)

Example (PowerShell, current session):

```powershell
$env:LLDB_PYTHON_PATH = "C:\Program Files\LLVM\lib\site-packages"
python -c "import lldb; print('LLDB Python bindings OK')"
# Expected: LLDB Python bindings OK
```

To persist it (PowerShell):

```powershell
[Environment]::SetEnvironmentVariable("LLDB_PYTHON_PATH", "C:\Program Files\LLVM\lib\site-packages", "User")
```

Restart your terminal and verify again:

```powershell
python -c "import lldb; print('LLDB Python bindings OK')"
```

## Install LLDB MCP Server

```powershell
pip install -U lldb-mcp-server
lldb-mcp-server --help
# Expected: shows CLI help output
```

## Configure MCP

If your MCP configuration supports environment variables, set at least:
- `LLDB_MCP_ALLOW_LAUNCH=1`
- `LLDB_MCP_ALLOW_ATTACH=1`
- `LLDB_PYTHON_PATH` (if auto-detection fails)

Example `.mcp.json` snippet:

```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "lldb-mcp-server",
      "args": [],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1",
        "LLDB_PYTHON_PATH": "C:\\Program Files\\LLVM\\lib\\site-packages"
      }
    }
  }
}
```

## Notes

- If `lldb --version` works but `import lldb` fails, the most common fix is adding the correct `LLDB_PYTHON_PATH`.
- Some LLVM distributions require the directory containing `liblldb.dll` to be on `PATH`. The server attempts to prepend likely DLL directories automatically, but you can also add `C:\Program Files\LLVM\bin` to your user PATH.
