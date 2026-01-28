# LLDB MCP Server

**语言:** [English](../README.md) | [中文](README.zh.md)

[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://github.com/FYTJ/lldb-mcp-server)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/lldb-mcp-server)](https://pypi.org/project/lldb-mcp-server/)

## 概述

LLDB MCP Server 是一个基于 [Model Context Protocol (MCP)](https://modelcontextprotocol.io) 的调试服务器，通过 40 个专业工具将 LLDB 调试功能暴露给 Claude Code 和 Claude Desktop 等 AI 助手，支持 AI 驱动的 C/C++ 应用程序交互式调试。

**核心架构：** 多会话设计，每个调试会话拥有独立的 `SBDebugger`、`SBTarget` 和 `SBProcess` 实例，支持并发调试工作流。

**适用场景：**
- Claude Code / Claude Desktop 的 AI 辅助调试
- 自动化调试脚本和工作流
- 崩溃分析和安全漏洞检测
- 远程调试和核心转储分析

## 核心特性

### 🔧 40 个调试工具

| 类别 | 工具数 | 功能 |
|------|--------|------|
| **会话管理** | 3 | 创建、终止、列出调试会话 |
| **目标控制** | 6 | 加载二进制、启动/附加进程、重启、发送信号、加载核心转储 |
| **断点** | 4 | 设置、删除、列出、更新断点（支持符号、文件:行号、地址、条件） |
| **执行控制** | 5 | 继续、暂停、单步进入/跨越/跳出 |
| **检查** | 6 | 线程、栈帧、堆栈跟踪、表达式求值 |
| **内存操作** | 2 | 内存读/写（支持十六进制和 ASCII 视图） |
| **观察点** | 3 | 设置、删除、列出内存观察点 |
| **寄存器** | 2 | 读取、写入 CPU 寄存器 |
| **符号与模块** | 2 | 符号搜索、已加载模块列表 |
| **高级工具** | 4 | 事件轮询、原始 LLDB 命令、反汇编、会话记录 |
| **安全分析** | 2 | 崩溃可利用性分析、可疑函数检测 |
| **核心转储** | 2 | 加载/创建核心转储 |

### ✨ 关键能力

- **多会话调试**：并发运行多个独立调试会话，每个会话状态隔离
- **事件驱动架构**：后台事件收集，非阻塞轮询（状态变化、断点命中、stdout/stderr）
- **安全分析**：崩溃可利用性分类、危险函数检测（strcpy、sprintf 等）
- **会话记录**：自动记录所有命令和输出，带时间戳
- **灵活断点**：支持符号、文件:行号、地址断点，支持条件断点
- **内存调试**：内存读/写、观察点监控（读/写访问）

## 环境要求

### 系统要求

- **macOS**
- **Homebrew**（[安装指南](https://brew.sh/)）
- **Homebrew LLVM**
- **Python 3.10+**（通过 Homebrew 安装）


## 快速开始

### 1. 安装依赖

```bash
# 安装 Homebrew LLVM（包含 LLDB）
brew install llvm

# 安装 uv（提供 uvx 命令）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 将 Homebrew LLVM 添加到 PATH（添加到 ~/.zshrc）
export PATH="$(brew --prefix llvm)/bin:$PATH"

# 重新加载 shell 配置
source ~/.zshrc
hash -r

# 验证 LLDB 安装
which lldb
lldb --version
```

### 2. 配置 MCP

#### Claude Code

**方式 1：命令行配置（全局，推荐）**

Intel (x86_64):
```bash
claude mcp add-json --scope user lldb-debugger '{
  "type": "stdio",
  "command": "uvx",
  "args": ["--python", "/usr/local/opt/python@3.13/bin/python3.13", "lldb-mcp-server"],
  "env": {
    "LLDB_MCP_ALLOW_LAUNCH": "1",
    "LLDB_MCP_ALLOW_ATTACH": "1",
    "PYTHONPATH": "/usr/local/opt/llvm/lib/python3.13/site-packages"
  }
}'
```

Apple Silicon (arm64):
```bash
claude mcp add-json --scope user lldb-debugger '{
  "type": "stdio",
  "command": "uvx",
  "args": ["--python", "/opt/homebrew/opt/python@3.13/bin/python3.13", "lldb-mcp-server"],
  "env": {
    "LLDB_MCP_ALLOW_LAUNCH": "1",
    "LLDB_MCP_ALLOW_ATTACH": "1",
    "PYTHONPATH": "/opt/homebrew/opt/llvm/lib/python3.13/site-packages"
  }
}'
```

**方式 2：手动配置（项目特定）**

在项目根目录创建 `.mcp.json`（参见 [MCP 配置](#mcp-配置)）。

#### Claude Desktop

编辑 macOS 上的 `~/Library/Application Support/Claude/claude_desktop_config.json`（参见 [MCP 配置](#mcp-配置)）。

#### Cursor IDE

**方式 1：项目特定配置（推荐）**

在项目根目录创建 `.cursor/mcp.json`：

Intel (x86_64):
```bash
mkdir -p .cursor
cat > .cursor/mcp.json << 'EOF'
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "uvx",
      "args": ["--python", "/usr/local/opt/python@3.13/bin/python3.13", "lldb-mcp-server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1",
        "PYTHONPATH": "/usr/local/opt/llvm/lib/python3.13/site-packages"
      }
    }
  }
}
EOF
```

Apple Silicon (arm64):
```bash
mkdir -p .cursor
cat > .cursor/mcp.json << 'EOF'
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "uvx",
      "args": ["--python", "/opt/homebrew/opt/python@3.13/bin/python3.13", "lldb-mcp-server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1",
        "PYTHONPATH": "/opt/homebrew/opt/llvm/lib/python3.13/site-packages"
      }
    }
  }
}
EOF
```

**方式 2：全局配置（适用于所有项目）**

在主目录创建 `~/.cursor/mcp.json`，使用与上述相同的 JSON 结构。这使得 LLDB 调试器在所有 Cursor 项目中可用。

配置完成后，重启 Cursor 以加载 MCP 服务器。

#### Codex (OpenAI)

**通过 CLI 全局配置（推荐）**

Intel (x86_64):
```bash
codex mcp add lldb-debugger \
  --env LLDB_MCP_ALLOW_LAUNCH=1 \
  --env LLDB_MCP_ALLOW_ATTACH=1 \
  --env PYTHONPATH=/usr/local/opt/llvm/lib/python3.13/site-packages \
  -- uvx --python /usr/local/opt/python@3.13/bin/python3.13 lldb-mcp-server
```

Apple Silicon (arm64):
```bash
codex mcp add lldb-debugger \
  --env LLDB_MCP_ALLOW_LAUNCH=1 \
  --env LLDB_MCP_ALLOW_ATTACH=1 \
  --env PYTHONPATH=/opt/homebrew/opt/llvm/lib/python3.13/site-packages \
  -- uvx --python /opt/homebrew/opt/python@3.13/bin/python3.13 lldb-mcp-server
```

**手动配置**

或者直接编辑 `~/.codex/config.toml`：

Intel (x86_64):
```toml
[mcp_servers.lldb-debugger]
command = "uvx"
args = ["--python", "/usr/local/opt/python@3.13/bin/python3.13", "lldb-mcp-server"]

[mcp_servers.lldb-debugger.env]
LLDB_MCP_ALLOW_LAUNCH = "1"
LLDB_MCP_ALLOW_ATTACH = "1"
PYTHONPATH = "/usr/local/opt/llvm/lib/python3.13/site-packages"
```

Apple Silicon (arm64):
```toml
[mcp_servers.lldb-debugger]
command = "uvx"
args = ["--python", "/opt/homebrew/opt/python@3.13/bin/python3.13", "lldb-mcp-server"]

[mcp_servers.lldb-debugger.env]
LLDB_MCP_ALLOW_LAUNCH = "1"
LLDB_MCP_ALLOW_ATTACH = "1"
PYTHONPATH = "/opt/homebrew/opt/llvm/lib/python3.13/site-packages"
```

配置完成后，MCP 服务器将在 Codex CLI 和 IDE 扩展中可用。

### 3. 开始使用

无需手动安装！使用 `uvx` 配置 MCP 服务器后，它会自动：
- 从 PyPI 安装包
- 管理依赖
- 在隔离环境中运行服务器

只需配置 `.mcp.json` 并启动 Claude Code 或重启 Claude Desktop。

## MCP 配置

### Claude Code & Cursor

#### Intel (x86_64)

在项目根目录创建 `.mcp.json`（Claude Code）或 `.cursor/mcp.json`（Cursor）：

```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "uvx",
      "args": ["--python", "/usr/local/opt/python@3.13/bin/python3.13", "lldb-mcp-server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1"
      }
    }
  }
}
```

**注意：** 对于 Claude Desktop，请改为编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`。

#### Apple Silicon (arm64)

```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "uvx",
      "args": ["--python", "/opt/homebrew/opt/python@3.13/bin/python3.13", "lldb-mcp-server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1"
      }
    }
  }
}
```

**注意：** 对于 Claude Desktop，请改为编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`。

**重要：** `--python` 参数指定 Homebrew Python 3.13 的完整路径，确保 `uvx` 不使用系统 Python 3.9。

### Codex

#### Intel (x86_64)

**CLI 命令：**
```bash
codex mcp add lldb-debugger \
  --env LLDB_MCP_ALLOW_LAUNCH=1 \
  --env LLDB_MCP_ALLOW_ATTACH=1 \
  --env PYTHONPATH=/usr/local/opt/llvm/lib/python3.13/site-packages \
  -- uvx --python /usr/local/opt/python@3.13/bin/python3.13 lldb-mcp-server
```

**或编辑 `~/.codex/config.toml`：**
```toml
[mcp_servers.lldb-debugger]
command = "uvx"
args = ["--python", "/usr/local/opt/python@3.13/bin/python3.13", "lldb-mcp-server"]

[mcp_servers.lldb-debugger.env]
LLDB_MCP_ALLOW_LAUNCH = "1"
LLDB_MCP_ALLOW_ATTACH = "1"
PYTHONPATH = "/usr/local/opt/llvm/lib/python3.13/site-packages"
```

#### Apple Silicon (arm64)

**CLI 命令：**
```bash
codex mcp add lldb-debugger \
  --env LLDB_MCP_ALLOW_LAUNCH=1 \
  --env LLDB_MCP_ALLOW_ATTACH=1 \
  --env PYTHONPATH=/opt/homebrew/opt/llvm/lib/python3.13/site-packages \
  -- uvx --python /opt/homebrew/opt/python@3.13/bin/python3.13 lldb-mcp-server
```

**或编辑 `~/.codex/config.toml`：**
```toml
[mcp_servers.lldb-debugger]
command = "uvx"
args = ["--python", "/opt/homebrew/opt/python@3.13/bin/python3.13", "lldb-mcp-server"]

[mcp_servers.lldb-debugger.env]
LLDB_MCP_ALLOW_LAUNCH = "1"
LLDB_MCP_ALLOW_ATTACH = "1"
PYTHONPATH = "/opt/homebrew/opt/llvm/lib/python3.13/site-packages"
```

**注意：** 你也可以在项目根目录创建项目特定的 `.codex/config.toml`（仅限受信任的项目）。

### 如果 LLDB 自动检测失败

如果服务器无法自动找到 LLDB Python 绑定，添加 `LLDB_PYTHON_PATH`：

**Intel (x86_64):**
```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "uvx",
      "args": ["--python", "/usr/local/opt/python@3.13/bin/python3.13", "lldb-mcp-server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1",
        "LLDB_PYTHON_PATH": "/usr/local/opt/llvm/lib/python3.13/site-packages"
      }
    }
  }
}
```

**Apple Silicon (arm64):**
```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "uvx",
      "args": ["--python", "/opt/homebrew/opt/python@3.13/bin/python3.13", "lldb-mcp-server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1",
        "LLDB_PYTHON_PATH": "/opt/homebrew/opt/llvm/lib/python3.13/site-packages"
      }
    }
  }
}
```

### 环境变量

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `LLDB_MCP_ALLOW_LAUNCH=1` | 允许启动新进程 | 禁用 |
| `LLDB_MCP_ALLOW_ATTACH=1` | 允许附加到现有进程 | 禁用 |
| `LLDB_PYTHON_PATH` | 覆盖 LLDB Python 模块路径 | 自动检测 |

## 工具参考

完整的 40 个 MCP 工具列表：

### 会话管理（3 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_initialize` | 创建新调试会话 | - |
| `lldb_terminate` | 终止调试会话 | `sessionId` |
| `lldb_listSessions` | 列出所有活动会话 | - |

### 目标控制（6 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_createTarget` | 加载可执行文件 | `sessionId`, `file` |
| `lldb_launch` | 启动进程 | `sessionId`, `args`, `env` |
| `lldb_attach` | 附加到运行中的进程 | `sessionId`, `pid`/`name` |
| `lldb_restart` | 重启进程 | `sessionId` |
| `lldb_signal` | 向进程发送信号 | `sessionId`, `signal` |
| `lldb_loadCore` | 加载核心转储 | `sessionId`, `corePath`, `executablePath` |

### 断点（4 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_setBreakpoint` | 设置断点 | `sessionId`, `symbol`/`file:line`/`address` |
| `lldb_deleteBreakpoint` | 删除断点 | `sessionId`, `breakpointId` |
| `lldb_listBreakpoints` | 列出所有断点 | `sessionId` |
| `lldb_updateBreakpoint` | 修改断点属性 | `sessionId`, `breakpointId`, `enabled`, `condition` |

### 执行控制（5 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_continue` | 继续执行 | `sessionId` |
| `lldb_pause` | 暂停执行 | `sessionId` |
| `lldb_stepIn` | 单步进入函数 | `sessionId` |
| `lldb_stepOver` | 单步跨越函数 | `sessionId` |
| `lldb_stepOut` | 单步跳出函数 | `sessionId` |

### 检查（6 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_threads` | 列出线程 | `sessionId` |
| `lldb_frames` | 列出栈帧 | `sessionId`, `threadId`（可选） |
| `lldb_stackTrace` | 获取格式化的堆栈跟踪 | `sessionId`, `threadId`（可选） |
| `lldb_selectThread` | 选择线程 | `sessionId`, `threadId` |
| `lldb_selectFrame` | 选择栈帧 | `sessionId`, `frameIndex` |
| `lldb_evaluate` | 求值表达式 | `sessionId`, `expression`, `frameIndex`（可选） |

### 内存操作（2 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_readMemory` | 读取内存内容 | `sessionId`, `address`, `size` |
| `lldb_writeMemory` | 写入内存 | `sessionId`, `address`, `data` |

### 观察点（3 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_setWatchpoint` | 设置内存观察点 | `sessionId`, `address`, `size`, `read`, `write` |
| `lldb_deleteWatchpoint` | 删除观察点 | `sessionId`, `watchpointId` |
| `lldb_listWatchpoints` | 列出所有观察点 | `sessionId` |

### 寄存器（2 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_readRegisters` | 读取 CPU 寄存器 | `sessionId`, `threadId`（可选） |
| `lldb_writeRegister` | 写入寄存器 | `sessionId`, `name`, `value` |

### 符号与模块（2 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_searchSymbol` | 搜索符号 | `sessionId`, `pattern`, `module`（可选） |
| `lldb_listModules` | 列出已加载的模块 | `sessionId` |

### 高级工具（4 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_pollEvents` | 轮询调试事件 | `sessionId`, `limit` |
| `lldb_command` | 执行原始 LLDB 命令 | `sessionId`, `command` |
| `lldb_getTranscript` | 获取会话记录 | `sessionId` |
| `lldb_disassemble` | 反汇编代码 | `sessionId`, `address`, `count` |

### 安全分析（2 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_analyzeCrash` | 分析崩溃可利用性 | `sessionId` |
| `lldb_getSuspiciousFunctions` | 查找可疑函数 | `sessionId` |

### 核心转储（2 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_loadCore` | 加载核心转储 | `sessionId`, `corePath`, `executablePath` |
| `lldb_createCoredump` | 创建核心转储 | `sessionId`, `path` |

## Claude Code Skill 集成

本项目包含一个为 Claude Code 预构建的**调试技能（skill）**，提供 AI 指导的调试工作流。该技能教会 Claude 何时以及如何有效使用 LLDB 调试工具。

### 安装技能

技能位于 `skills/lldb-debug/` 目录。安装方式：

**方式 1：项目特定（推荐用于测试）**
```bash
# 技能已在项目的 .claude/skills/ 目录中
# 在此项目中工作时，Claude Code 会自动检测到它
```

**方式 2：全局安装（适用于所有项目）**
```bash
# 复制到个人技能目录
cp -r skills/lldb-debug ~/.claude/skills/
```

### 使用技能

配置 MCP 服务器后，可以调用技能：

**手动调用：**
```bash
/lldb-debug path/to/binary
```

**自动调用：**
当您描述调试任务时，Claude 会在适当时自动使用调试工具，例如：
- "调试这个崩溃的程序"
- "找出这个二进制文件中的缓冲区溢出"
- "分析这个核心转储"

### 技能激活条件

该技能设计为**仅在直接代码分析不足时**激活：

1. **项目复杂度**使静态分析不可靠
2. **错误日志缺失**或未指示根本原因
3. **多次代码修复均失败**
4. **需要运行时行为分析**（内存损坏、崩溃等）

对于可以通过代码审查单独解决的简单问题，技能**不会**激活。

### 技能能力

调试技能提供：

- **调试思维**：科学方法、二分定位、最小化复现
- **错误类型分类**：空指针、缓冲区溢出、释放后使用等
- **汇编级调试**：编译器优化问题、ABI 不匹配、仅二进制调试
- **多会话策略**：带会话限制和结构化日志的迭代调试
- **决策树**：常见调试模式的自动化工作流
- **快速参考**：基于场景的工具组合和故障排除指南

### 测试程序

项目包含带有故意错误的测试程序，用于技能验证：

```bash
# 构建所有测试程序
cd examples/client/c_test
./build_all.sh

# 可用的测试程序：
examples/client/c_test/
├── null_deref/          # 空指针解引用
├── buffer_overflow/     # 栈缓冲区溢出
├── use_after_free/      # 释放后使用
├── divide_by_zero/      # 除以零
├── stack_overflow/      # 通过递归导致的栈溢出
├── format_string/       # 格式字符串漏洞
├── double_free/         # 双重释放
└── infinite_loop/       # 无限循环
```

### 技能文档

完整的调试指南可在技能文件中找到：
- **位置**：`skills/lldb-debug/SKILL.md`
- **内容**：700+ 行综合调试方法论
- **涵盖**：思维方式、工作流、错误类型、策略、决策树、参考表

## 使用示例

### 示例 1：使用 Claude Code 进行基本调试

配置 MCP 后，可以在 Claude Code 中自然地进行调试：

```
用户："调试位于 /path/to/my/app 的程序"

Claude 自动执行：
1. 调用 lldb_initialize 创建会话
2. 调用 lldb_createTarget 加载二进制文件
3. 调用 lldb_setBreakpoint 在 main 设置断点
4. 调用 lldb_launch 启动进程
5. 调用 lldb_pollEvents 检查断点命中
6. 调用 lldb_stackTrace 显示堆栈
```

### 示例 2：崩溃分析

```
用户："这个程序崩溃了，帮我分析原因"

Claude 会：
1. 调用 lldb_pollEvents 获取崩溃事件
2. 调用 lldb_analyzeCrash 分类崩溃类型
3. 调用 lldb_stackTrace 显示崩溃堆栈
4. 调用 lldb_readRegisters 检查寄存器状态
5. 调用 lldb_getSuspiciousFunctions 检测危险函数
6. 提供修复建议
```

### 示例 3：内存调试

```
用户："检查地址 0x100000 是否存在缓冲区溢出"

Claude 会：
1. 调用 lldb_readMemory 检查内存内容
2. 调用 lldb_setWatchpoint 监控内存访问
3. 调用 lldb_continue 恢复执行
4. 调用 lldb_pollEvents 检测观察点命中
5. 分析内存访问模式
```

## 事件类型

通过 `lldb_pollEvents` 获取的事件：

| 事件类型 | 描述 |
|----------|------|
| `targetCreated` | 目标已创建 |
| `processLaunched` | 进程已启动 |
| `processAttached` | 已附加到进程 |
| `processStateChanged` | 进程状态变化（running/stopped/exited） |
| `breakpointSet` | 断点已设置 |
| `breakpointHit` | 断点命中（包含线程/栈帧信息） |
| `stdout` | 进程标准输出 |
| `stderr` | 进程标准错误输出 |

## 故障排除

### 问题：`No module named lldb`

**原因：** LLDB Python 绑定配置不正确。

**解决方案：**

```bash
# 1. 验证 LLDB 来自 Homebrew
which lldb

# 2. 如果不是，检查 PATH 配置
cat ~/.zshrc | grep llvm

# 3. 如果缺失，添加到 PATH
echo 'export PATH="$(brew --prefix llvm)/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
hash -r

# 4. 在 .mcp.json 中设置 LLDB_PYTHON_PATH（参见 MCP 配置部分）
```

### 问题：LLDB 仍使用系统版本

**原因：** PATH 配置不正确或终端未重启。

**解决方案：**

```bash
# 1. 重新加载 shell 配置
source ~/.zshrc
hash -r

# 2. 完全重启终端

# 3. 验证 LLDB 路径
which lldb
lldb --version
```

### 问题：`uvx` 命令未找到

**原因：** 未安装 `uv`。

**解决方案：**

```bash
# 安装 uv（提供 uvx）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 验证安装
which uvx
uvx --version
```

### 问题：启动/附加时权限被拒绝

**原因：** 安全环境变量未设置。

**解决方案：**

确保 `.mcp.json` 包含：
```json
"env": {
  "LLDB_MCP_ALLOW_LAUNCH": "1",
  "LLDB_MCP_ALLOW_ATTACH": "1"
}
```

## 项目结构

```
lldb-mcp-server/
├── src/lldb_mcp_server/
│   ├── fastmcp_server.py      # MCP 入口点
│   ├── session/
│   │   └── manager.py          # SessionManager（核心）
│   ├── tools/                  # 9 个工具模块
│   │   ├── session.py          # 会话管理
│   │   ├── target.py           # 目标控制
│   │   ├── breakpoints.py      # 断点
│   │   ├── execution.py        # 执行控制
│   │   ├── inspection.py       # 检查
│   │   ├── memory.py           # 内存操作
│   │   ├── watchpoints.py      # 观察点
│   │   ├── registers.py        # 寄存器
│   │   └── advanced.py         # 高级工具
│   └── analysis/
│       └── exploitability.py   # 崩溃分析
├── .mcp.json.uvx               # MCP 配置模板
├── pyproject.toml              # 包配置
├── LICENSE                     # MIT 许可证
└── README.md                   # 英文文档
```

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](../LICENSE) 文件。

## 链接

- **PyPI 包**: [https://pypi.org/project/lldb-mcp-server/](https://pypi.org/project/lldb-mcp-server/)
- **源代码**: [https://github.com/FYTJ/lldb-mcp-server](https://github.com/FYTJ/lldb-mcp-server)
- **Issues**: [https://github.com/FYTJ/lldb-mcp-server/issues](https://github.com/FYTJ/lldb-mcp-server/issues)
- **MCP 文档**: [https://modelcontextprotocol.io](https://modelcontextprotocol.io)
