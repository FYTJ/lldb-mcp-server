# LLDB MCP Server

语言: [中文](README.md) | [English](docs/README.en.md)

## 概述

一个可通过 MCP 工具调用 LLDB 的服务器，提供会话管理、目标/进程控制、断点、执行控制、栈与变量、表达式、内存读写与事件轮询。

## 环境要求

- macOS，安装 Xcode 或 Command Line Tools，确保 Python 可 `import lldb`。
- Python 3.12。

## 配置 config.json

- 位置：项目根目录 `config.json`，运行时自动加载，亦可通过环境变量 `LLDB_MCP_CONFIG=/path/to/config.json` 指定。
- 关键字段：
  - `log_dir`：日志目录，默认 `logs`（不存在时会自动创建）。
  - `server_host`/`server_port`：HTTP/SSE 地址与端口（用于 `--transport http|sse`）。
  - `lldb.python_executable`：首选 Python 可执行文件（如 Xcode 的 `.../usr/bin/python3`）。
  - `lldb.python_paths`：`import lldb` 所需的 Python 路径：
    - 使用 `lldb -P` 输出的路径（推荐）
    - 或 Xcode/CLT 提供的 `LLDB.framework/Resources/Python`
  - `lldb.framework_paths`：`LLDB.framework` 所在目录，用于预加载与 `DYLD_*` 环境：
    - 通过 `xcode-select -p` 获取开发者根，再检查：
      - `${DEVROOT}/../SharedFrameworks`
      - `${DEVROOT}/Library/PrivateFrameworks`
  - `project_root`：项目根目录绝对路径（如 `$(pwd)`）。
  - `src_path`：源码路径（通常为 `<project_root>/src`）。
  - `client.target_bin`：示例客户端默认的被调试可执行路径；也可用环境变量 `TARGET_BIN` 覆盖。

- 如何找到路径：
  - `lldb -P` 获取 Python 路径（优先使用）。
  - `which python3` 或 Xcode `.../usr/bin/python3` 设为 `python_executable`。
  - `xcode-select -p` 得到 `${DEVROOT}`；将以上两类 Framework 路径加入 `framework_paths`。
  - 其余字段按本机实际路径填写即可。

## 安全配置

- `LLDB_MCP_ALLOW_LAUNCH=1` 允许 `launch`
- `LLDB_MCP_ALLOW_ATTACH=1` 允许 `attach`

## 运行（FastMCP）

- 启动（HTTP）：`PYTHONPATH=src LLDB_MCP_ALLOW_LAUNCH=1 PYTHONUNBUFFERED=1 python3 -u -m lldb_mcp_server.fastmcp_server --transport http --host 127.0.0.1 --port 8765`
- 示例：
  - 创建会话（POST `/tools/call`）：
    `{"name":"lldb_initialize","arguments":{}}`
  - 创建目标：
    `{"name":"lldb_createTarget","arguments":{"sessionId":"<SID>","file":"/path/app"}}`
  - 启动进程：
    `{"name":"lldb_launch","arguments":{"sessionId":"<SID>","args":[]}}`
  - 轮询事件：
    `{"name":"lldb_pollEvents","arguments":{"sessionId":"<SID>","limit":32}}`
    - 事件类型示例：
      - `targetCreated`：目标创建
      - `processStateChanged`：进程状态变化（running/stopped/exited 等）
      - `breakpointHit`：断点命中
      - `stdout`/`stderr`：进程输出抓取

## 客户端示例（HTTP）

- 示例客户端：
  - 入口：`MCP_HOST=127.0.0.1 MCP_PORT=8765 python3 examples/client/run_debug_flow.py`
  - 准备：`cd examples/client/c_test/hello && cc -g -O0 -o hello hello.c` 并设置 `TARGET_BIN=$(pwd)/hello`
  - 连接：客户端通过 HTTP 调用 `/tools/call`
  - 若 `import lldb` 失败，服务端会尝试根据 `config.json` 自动补全环境（`lldb -P` 与 `xcode-select -p` 路径）；仍失败时按“配置 config.json”修正。

## 一键启动

- 构建示例目标：`cd examples/client/c_test/hello && cc -g -O0 -Wall -Wextra -o hello hello.c`
- 启动服务端：`PYTHONPATH=src LLDB_MCP_ALLOW_LAUNCH=1 PYTHONUNBUFFERED=1 python3 -u -m lldb_mcp_server.fastmcp_server --transport http --host 127.0.0.1 --port 8765`
- 启动客户端：`TARGET_BIN=$(pwd)/examples/client/c_test/hello/hello MCP_HOST=127.0.0.1 MCP_PORT=8765 python3 examples/client/run_debug_flow.py`


## 常见问题

- `No module named lldb`：安装 Xcode/CLT，并在 Python 使用系统 LLDB 绑定；如果仍不可用，可先使用协议与工具映射进行开发，实际调试能力在有 LLDB 绑定时自动启用。
