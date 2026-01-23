# LLDB MCP Server

Language: [English](README.en.md) | [中文](../README.md)

## Overview

A local MCP server that exposes LLDB debugging capabilities through tools for:
- session management
- target and process control
- breakpoints and execution control
- inspection (threads, frames, registers)
- memory read/write and watchpoints
- advanced operations (modules, symbols, core dumps)
- security analysis (crash analysis, suspicious functions)

## Requirements

### Recommended setup (Homebrew LLVM + Python 3.13)

Apple LLDB Python bindings are tied to the system Python, while FastMCP requires Python >=3.10. Homebrew LLVM provides LLDB bindings compatible with modern Python.

1) Install LLVM and Python 3.13

```bash
brew install llvm python@3.13
$(brew --prefix python@3.13)/bin/python3.13 -V
$(brew --prefix llvm)/bin/lldb --version
```

2) Add Homebrew LLVM to PATH

```bash
export PATH="$(brew --prefix llvm)/bin:$PATH"
```

3) Create a Python 3.13 virtual environment

```bash
$(brew --prefix python@3.13)/bin/python3.13 -m venv .venv
source .venv/bin/activate
python --version
```

4) Add the LLDB Python path to the venv

```bash
LLDB_PY_PATH="$(lldb -P)"
SITE_PKGS="$(python -c 'import site; print(site.getsitepackages()[0])')"
echo "$LLDB_PY_PATH" > "$SITE_PKGS/lldb.pth"
```

5) Install project dependencies and verify imports

```bash
pip install -e ".[dev]"
python -c "import lldb, fastmcp; print(lldb.SBDebugger.GetVersionString())"
```

## Configure `config.json`

- Location: project root `config.json`; auto-loaded at runtime. You can also specify `LLDB_MCP_CONFIG=/path/to/config.json`.
- Key fields:
  - `log_dir`: logs directory, default `logs` (auto-created if missing).
  - `server_host`/`server_port`: HTTP/SSE address/port (for `--transport http|sse`).
  - `lldb.python_executable`: preferred Python executable.
  - `lldb.python_paths`: Python paths required for `import lldb` (use `lldb -P` output).
  - `lldb.framework_paths`: directories containing `LLDB.framework` for `DYLD_*` setup.
  - `project_root`: absolute project root path (e.g., `$(pwd)`).
  - `src_path`: source path (usually `<project_root>/src`).
  - `client.target_bin`: default target executable for the example client; overridable via `TARGET_BIN`.

## Security

- `LLDB_MCP_ALLOW_LAUNCH=1` allow `launch`
- `LLDB_MCP_ALLOW_ATTACH=1` allow `attach`

## Run (FastMCP)

Start server (HTTP):

```bash
LLDB_MCP_ALLOW_LAUNCH=1 \
LLDB_MCP_ALLOW_ATTACH=1 \
  .venv/bin/python -m lldb_mcp_server.fastmcp_server \
  --transport http --host 127.0.0.1 --port 8765
```

Example tool calls:
- Create session (POST `/tools/call`):
  `{"name":"lldb_initialize","arguments":{}}`
- Create target:
  `{"name":"lldb_createTarget","arguments":{"sessionId":"<SID>","file":"/path/app"}}`
- Launch process:
  `{"name":"lldb_launch","arguments":{"sessionId":"<SID>","args":[]}}`
- Poll events:
  `{"name":"lldb_pollEvents","arguments":{"sessionId":"<SID>","limit":32}}`

## Events

Retrieve a list via `pollEvents`. Example types:
- `targetCreated`: target created
- `processLaunched`/`processAttached`: process started or attached
- `processStateChanged`: process state change (running/stopped/exited, etc.)
- `breakpointSet`/`breakpointHit`: breakpoint set/hit (with thread/frame info)
- `stdout`/`stderr`: captured process output

## Development and Verification (HTTP)

Example client:
- Prepare: `cd examples/client/c_test/hello && cc -g -O0 -Wall -Wextra -o hello hello.c`
- Start server (terminal 1) using the command above.
- Run client (terminal 2):
  `TARGET_BIN=$(pwd)/examples/client/c_test/hello/hello MCP_HOST=127.0.0.1 MCP_PORT=8765 .venv/bin/python examples/client/run_debug_flow.py`

If `import lldb` fails, the server attempts to augment the environment using `config.json` (`lldb -P` and `xcode-select -p`). If it still fails, verify your LLDB paths in `config.json`.

## FAQ

- `No module named lldb`: ensure your Python matches the LLDB bindings (Homebrew LLVM recommended) and that your `lldb.pth` or `lldb.python_paths` is configured.
