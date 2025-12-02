# LLDB MCP Server

Language: [English](README.en.md) | [中文](../README.md)

## Overview

A server that invokes LLDB via MCP tools, providing session management, target/process control, breakpoints, execution control, stacks and variables, expression evaluation, memory read/write, and event polling.

## Requirements

- macOS with Xcode or Command Line Tools installed; ensure Python can `import lldb`.
- Python 3.12.

## Configure `config.json`

- Location: project root `config.json`; auto-loaded at runtime. You can also specify `LLDB_MCP_CONFIG=/path/to/config.json`.
- Key fields:
  - `log_dir`: logs directory, default `logs` (auto-created if missing).
  - `server_host`/`server_port`: TCP listen address/port (for `--listen` mode).
  - `allowed_root`: limit debuggable root directory (optional, improves security).
  - `lldb.python_executable`: preferred Python executable (e.g., Xcode `.../usr/bin/python3`).
  - `lldb.python_paths`: Python paths required for `import lldb`:
    - Use `lldb -P` output (recommended)
    - Or Xcode/CLT `LLDB.framework/Resources/Python`
  - `lldb.framework_paths`: directories containing `LLDB.framework`, used for preloading and `DYLD_*` env:
    - Get developer root via `xcode-select -p`, then check:
      - `${DEVROOT}/../SharedFrameworks`
      - `${DEVROOT}/Library/PrivateFrameworks`
  - `project_root`: absolute project root path (e.g., `$(pwd)`).
  - `src_path`: source path (usually `<project_root>/src`).
  - `client.target_bin`: default target executable for the example client; overridable via `TARGET_BIN` env.

- How to find paths:
  - `lldb -P` to get Python path (prefer this).
  - `which python3` or Xcode `.../usr/bin/python3` for `python_executable`.
  - `xcode-select -p` to get `${DEVROOT}`; add the two framework paths above to `framework_paths`.
  - Fill other fields with local paths accordingly.

## Security

- `LLDB_MCP_ALLOW_LAUNCH=1` allow `launch`
- `LLDB_MCP_ALLOW_ATTACH=1` allow `attach`
- `LLDB_MCP_ALLOWED_ROOT=/path/to/dir` restrict debuggable root (optional)

## Run (Internal Protocol: STDIO)

- Start: `PYTHONPATH=src LLDB_MCP_ALLOW_LAUNCH=1 LLDB_MCP_ALLOWED_ROOT=$(pwd)/examples/client/c_test/hello PYTHONUNBUFFERED=1 python3 -u -m lldb_mcp_server.mcp.server --listen 127.0.0.1:8765`
- Examples:
  - Create session:
    `{"id":"1","method":"initialize","params":{}}`
  - Create target:
    `{"id":"2","method":"createTarget","params":{"sessionId":"<SID>","file":"/path/app"}}`
  - Launch process:
    `{"id":"3","method":"launch","params":{"sessionId":"<SID>","args":[]}}`
  - Poll events:
    `{"id":"4","method":"pollEvents","params":{"sessionId":"<SID>","limit":32}}`

## Events

- Retrieve a list via `pollEvents`. Example types:
  - `targetCreated`: target created
  - `processLaunched`/`processAttached`: process started or attached
  - `processStateChanged`: process state change (running/stopped/exited, etc.)
  - `breakpointSet`/`breakpointHit`: breakpoint set/hit (with thread/frame info)
  - `stdout`/`stderr`: captured process output

## Development & Verification

- Example client:
  - Entry: `MCP_HOST=127.0.0.1 MCP_PORT=8765 python3 examples/client/run_debug_flow.py`
  - Prepare: `cd examples/client/c_test/hello && cc -g -O0 -o hello hello.c` and set `TARGET_BIN=$(pwd)/hello`
  - Server: can be spawned by the client, or start beforehand with `PYTHONPATH=src LLDB_MCP_ALLOW_LAUNCH=1 LLDB_MCP_ALLOWED_ROOT=$(pwd)/examples/client/c_test/hello PYTHONUNBUFFERED=1 python3 -u -m lldb_mcp_server.mcp.server --listen 127.0.0.1:8765` (recommended)
  - If `import lldb` fails, the server tries to augment the environment according to `config.json` (`lldb -P` and `xcode-select -p`); if it still fails, fix your `config.json` per the section above.

## One-Click Start

- Build example target: `cd examples/client/c_test/hello && cc -g -O0 -Wall -Wextra -o hello hello.c`
- Start server: `PYTHONPATH=src LLDB_MCP_ALLOW_LAUNCH=1 LLDB_MCP_ALLOWED_ROOT=$(pwd)/examples/client/c_test/hello PYTHONUNBUFFERED=1 python3 -u -m lldb_mcp_server.mcp.server --listen 127.0.0.1:8765`
- Start client: `TARGET_BIN=$(pwd)/examples/client/c_test/hello/hello MCP_HOST=127.0.0.1 MCP_PORT=8765 python3 examples/client/run_debug_flow.py`

## FAQ

- `No module named lldb`: install Xcode/CLT and use the system LLDB Python binding. If unavailable, you can still develop using the protocol and tool mapping; the actual debugging capabilities will enable automatically when LLDB bindings become available.

## Project Layout

- Top-level: `src/`, `examples/`, `scripts/`, `README.md`, `pyproject.toml`, `config.json`
- Server code: `src/lldb_mcp_server/...`
- Examples & client: `examples/client/c_test/hello/hello.c`, `examples/client/*`
- Build artifacts & logs: ignored by VCS, created at runtime (see `.gitignore`).

