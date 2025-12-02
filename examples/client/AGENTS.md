# Codex 调试代理（LLDB）

本文档旨在让 Codex 仅使用 LLDB 对 C 测试程序进行调试，输出完整、可复现的定位过程与结论，并将全部调试决策与原始输出按会话划分记录到 `logs/sessions/*.log`，并在 `logs/lldb_summary.log` 归纳会话总结。

## 目标与原则
- 目标：用 LLDB 定位错误位置与根因，给出最小修改方案。
- 语言：所有输出与报告使用中文。
- 约束：只使用 LLDB；不使用 gdb 或其他调试器；不凭空给结论。
 - 引用：指向代码位置时使用 `file_path:line_number`（如 `c_test/array-index1/array_index.c:12`）。
 - 强制要求：必须通过 LLDB MCP 进行调试，所有交互仅用 `tools.call`。
 - 改动原则：持续调用 LLDB 进行调试与验证，迭代最小修复直至代码正确运行；不得改变代码的原始语义与功能。

## 输入与前置
- 默认调试对象为 `.c` 文件；本地已完整安装 LLDB。
- 构建命令（开启符号，关闭优化）：
  - 在与测试程序（`.c`）文件相同目录下进行构建与调试：`cc -g -O0 -Wall -Wextra -o <basename> <basename>.c`（可执行文件名与 `.c` 文件同名，去除扩展名）。
- 如有运行参数，自行判断并在调试中使用。
- 测试开始时，在调试目标代码文件的同级目录创建 `logs/` 文件夹：包含 `sessions/` 子目录与 `lldb_summary.log`。日志写入规则见“日志记录要求（logs/）”。
 - 自动化约定：代码修改后自动执行构建与测试（同目录编译并运行）；在任何代码改动后，将此次改动以统一 diff 格式（包含文件路径与变更 hunks）追加到 `logs/lldb_summary.log`，并附测试结果。

## 启动与连接 MCP
客户端与 MCP 服务以 JSON 行协议通信；默认通过网络连接到一个常驻服务，不依赖任何服务端文件路径或目录结构。

- 必备环境变量：
  - `export TARGET_BIN=/absolute/path/to/your/executable`
  - 使用网络连接：
    - `export MCP_HOST=127.0.0.1`
    - `export MCP_PORT=8765`

- 统一请求 Envelope：顶层方法固定为 `tools.call`。

- 提示词要点：
  - 仅通过 MCP 的 `tools.call` 与 LLDB 交互。
  - 每条 LLDB 命令后按“决策条目”实时写入 `logs/sessions/<timestamp>.log`。
  - 支持多次会话；每次结束追加总结到 `logs/lldb_summary.log` 并在codex终端执行 `/compact`命令压缩上下文。
  - 发现错误可直接修改代码，修改后自动构建与测试；将统一 diff 与测试结果写入 `logs/lldb_summary.log`。
  - 不改变代码的原始语义与功能。


## 执行流程（一次完整调试）
1) 构建目标：在测试程序所在目录执行 `cc -g -O0 -Wall -Wextra -o <basename> <basename>.c`（可执行文件名与 `.c` 同名去扩展）。
2) 初始化日志：在目标代码同级目录创建 `logs/`（含 `sessions/` 与 `lldb_summary.log`）；后续每条 LLDB 命令按“决策条目”实时追加到 `logs/sessions/<timestamp>.log`。
3) 启动会话：运行命令`MCP_HOST=127.0.0.1 MCP_PORT=8765 TARGET_BIN=/absolute/path/to/your/exe python3 client/run_debug_flow.py`启动 LLDB mcp。若启动失败，则重试该命令。
4) 调试交互：通过 MCP 发送 LLDB 命令进行断点、栈、单步、变量/内存与寄存器检查；每次命令严格按“分析/命令/输出”记录到会话日志。
5) 多会话：为定位错误允许多次启动/终止/重启 LLDB 会话；每次会话写入独立的 `logs/sessions/<timestamp>.log`。会话结束时追加本次总结到 `logs/lldb_summary.log` 并执行 `/compact`。
6) 修改与测试：必要时直接修改代码；修改后自动构建与测试，记录构建与运行命令、`stdout`/`stderr`、退出码与结论；将统一 diff（包含文件路径与 hunks）与测试结果写入 `logs/lldb_summary.log`。任何修改不得改变原始语义与功能。
7) 历史查询：需要回看某次会话时，先根据 `logs/lldb_summary.log` 查找并定位对应 `logs/sessions/<timestamp>.log`。

## 日志记录要求（logs/）
- 目录结构：在调试目标代码文件的同级目录创建 `logs/`，其中包含：`logs/lldb_summary.log` 与 `logs/sessions/`。
- 会话日志命名：使用当前时间命名日志文件（例如 `YYYYMMDD_HHMMSS.log`）。
- 会话日志：从 MCP 会话创建并开始与 LLDB 交互时立即开始记录，统一采用“决策条目”格式依次追加到 `logs/sessions/<timestamp>.log`（使用当前时间命名，如 `YYYYMMDD_HHMMSS.log`）。每执行一条 LLDB 命令后立即将对应条目落盘，不在会话结束后一次性写入。
 - 测试记录：每次代码修改触发的自动测试需记录到当前会话日志，包括构建命令、运行命令、`stdout`/`stderr`、退出码与测试结论（通过/失败）。
 - 变更记录：在任何代码改动后，将统一 diff 格式的改动记录（建议使用 unified diff，包含文件路径与具体 hunks）追加到 `logs/lldb_summary.log`，并附本次测试结果与结论。
 - 收尾命令：每次会话结束并完成日志写入与总结后，执行 `/compact` 命令。
- 每一次决策严格包含三部分，顺序固定：
  1. 决策序号：`<决策n>`
  2. 分析：当前状态判断、为何选择下一条 LLDB 命令、预期得到的信息。
  3. 命令：以 `(lldb) <命令>` 的形式原样写入。
  4. 输出：原样拷贝 LLDB 对该命令的完整响应内容。
- 日志只包含上述三项，不记录构建、环境或与调试无关的输出。
- 若为多线程程序，日志中需包含对线程状态与各线程栈的记录与分析（不限定具体命令名）。
- 单条命令对应一条“决策条目”，不得在内存中缓存超过一条命令的日志。

 - 历史查询：需要查询历史 LLDB 会话时，以 `logs/lldb_summary.log` 为索引按需查找对应的 `logs/sessions/<timestamp>.log`。
