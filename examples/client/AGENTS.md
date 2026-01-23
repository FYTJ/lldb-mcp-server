# Codex LLDB 调试指令

目标：通过 LLDB MCP 精确定位问题并给出最小修复；全程中文；仅用 `tools.call` 与服务交互。

## 连接与前置
- 传输：仅支持 TCP。设置 `MCP_HOST=127.0.0.1`、`MCP_PORT=8765`。
- 目标：设置 `TARGET_BIN=/absolute/path/to/your/executable`。
- 构建：在源文件同目录执行 `cc -g -O0 -Wall -Wextra -o <basename> <basename>.c`。
- 日志目录：在目标同级目录创建 `logs/sessions/` 与 `logs/lldb_summary.log`。


## 命令流约束
- 统一请求：顶层方法固定为 `tools.call`。
- 启动流程：
  1) `lldb.initialize` → `lldb.createTarget`
  2) 设置断点（如 `break main` 通过 `lldb.command`）
  3) `lldb.launch` 后必须校验运行状态：连续调用 `lldb.threads`，存在线程才视为“运行中”。
- 运行态门禁：只有在“运行中”时才允许发送 `next/step/continue/print/info registers/readMemory/setWatchpoint` 等命令。
- 非运行态处理：若任何输出包含“程序未在运行/启动失败/exit code 127”，立即停止上述运行态命令；改为记录错误、收集环境信息（允许 `show environment`、`list`、`info line` 等静态命令），必要时结束会话或重新启动。
- 决策依赖：每个“下一步命令”必须基于上一条输出的状态判断；禁止忽略错误继续下发运行态命令。

## 日志规范
- 会话日志：`logs/sessions/<YYYYMMDD_HHMMSS>.log`，每执行一条命令即刻追加一条“决策条目”，不可延迟。
- 决策条目包含四段：
  1) `决策<n>`
  2) 分析（当前状态与选择该命令的理由）
  3) 命令（以 `(lldb) <原生命令>` 原样记录）
  4) 输出（完整原始 transcript，不做改写）
- 测试记录：代码改动后在当前会话日志追加构建与运行的命令、`stdout`/`stderr`、退出码与结论。
- 变更记录：不使用 `git diff`；手动生成统一 diff 文本（含文件路径与 hunks）并追加到 `logs/lldb_summary.log`，同时写入测试结论。
- 写入位置：客户端以 `target_bin` 的同级目录为根写入以上日志；服务端 transcript 位于工作目录 `logs/transcript_<sessionId>.log` 可用于复制内容。

## 收尾与压缩
- 会话结束：写入本次结论到 `logs/lldb_summary.log`。

## 参考启动命令
`MCP_HOST=127.0.0.1 MCP_PORT=8765 TARGET_BIN=/absolute/path/to/your/exe python3 lldb_mcp/run_debug_flow.py`

## 引用规范
- 指向代码位置时使用 `file_path:line_number`（例：`c_test/array-index1/array_index.c:12`）。
- 不得改变原始语义；仅做最小必要修改并验证通过。
