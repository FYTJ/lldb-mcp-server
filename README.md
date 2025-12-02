# LLDB MCP Server

## 概述

一个可通过 MCP 工具调用 LLDB 的服务器，提供会话管理、目标/进程控制、断点、执行控制、栈与变量、表达式、内存读写与事件轮询。

## 环境要求

- macOS，安装 Xcode 或 Command Line Tools，确保 Python 可 `import lldb`。
- Python 3.12。

## 配置 config.json

- 位置：项目根目录 `config.json`，运行时自动加载，亦可通过环境变量 `LLDB_MCP_CONFIG=/path/to/config.json` 指定。
- 关键字段：
  - `log_dir`：日志目录，默认 `logs`（不存在时会自动创建）。
  - `server_host`/`server_port`：TCP 监听地址与端口（用于 `--listen` 模式）。
  - `allowed_root`：可调试的根目录限制（可选，提升安全性）。
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
- `LLDB_MCP_ALLOWED_ROOT=/path/to/dir` 限定可调试路径（可选）

## 运行（内部协议 STDIO）

- 启动：`PYTHONPATH=src LLDB_MCP_ALLOW_LAUNCH=1 LLDB_MCP_ALLOWED_ROOT=$(pwd)/examples/client/c_test/hello PYTHONUNBUFFERED=1 python3 -u -m lldb_mcp_server.mcp.server --listen 127.0.0.1:8765`
- 示例：
  - 创建会话：
    `{"id":"1","method":"initialize","params":{}}`
  - 创建目标：
    `{"id":"2","method":"createTarget","params":{"sessionId":"<SID>","file":"/path/app"}}`
  - 启动进程：
    `{"id":"3","method":"launch","params":{"sessionId":"<SID>","args":[]}}`
  - 轮询事件：
    `{"id":"4","method":"pollEvents","params":{"sessionId":"<SID>","limit":32}}`
    - 通过 `pollEvents` 获取事件列表，示例类型：
      - `targetCreated`：目标创建
      - `processLaunched`/`processAttached`：进程启动或附加
      - `processStateChanged`：进程状态变化（running/stopped/exited 等）
      - `breakpointSet`/`breakpointHit`：断点设置与命中（含线程和帧信息）
      - `stdout`/`stderr`：进程输出抓取

## 客户端示例

- 示例客户端：
  - 入口：`MCP_HOST=127.0.0.1 MCP_PORT=8765 python3 examples/client/run_debug_flow.py`
  - 准备：`cd examples/client/c_test/hello && cc -g -O0 -o hello hello.c` 并设置 `TARGET_BIN=$(pwd)/hello`
  - 服务：可直接由客户端派生，或预先启动 `PYTHONPATH=src LLDB_MCP_ALLOW_LAUNCH=1 LLDB_MCP_ALLOWED_ROOT=$(pwd)/examples/client/c_test/hello PYTHONUNBUFFERED=1 python3 -u -m lldb_mcp_server.mcp.server --listen 127.0.0.1:8765`(建议)
  - 若 `import lldb` 失败，服务端会尝试根据 `config.json` 自动补全环境（`lldb -P` 与 `xcode-select -p` 路径）；仍失败时按上节“配置 config.json”修正。

## 一键启动

- 构建示例目标：`cd examples/client/c_test/hello && cc -g -O0 -Wall -Wextra -o hello hello.c`
- 启动服务端：`PYTHONPATH=src LLDB_MCP_ALLOW_LAUNCH=1 LLDB_MCP_ALLOWED_ROOT=$(pwd)/examples/client/c_test/hello PYTHONUNBUFFERED=1 python3 -u -m lldb_mcp_server.mcp.server --listen 127.0.0.1:8765`
- 启动客户端：`TARGET_BIN=$(pwd)/examples/client/c_test/hello/hello MCP_HOST=127.0.0.1 MCP_PORT=8765 python3 examples/client/run_debug_flow.py`


## 常见问题

- `No module named lldb`：安装 Xcode/CLT，并在 Python 使用系统 LLDB 绑定；如果仍不可用，可先使用协议与工具映射进行开发，实际调试能力在有 LLDB 绑定时自动启用。

## 目录结构

- 顶层：`src/`、`examples/`、`scripts/`、`README.md`、`pyproject.toml`、`config.json`
- 服务端代码：`src/lldb_mcp_server/...`
- 示例与客户端：`examples/client/c_test/hello/hello.c`、`examples/client/*`
