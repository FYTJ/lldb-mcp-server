# LLDB MCP Server - 使用指南

**语言:** [English](USAGE.md) | [中文](USAGE.zh.md)

本指南提供了使用 LLDB MCP Server 与 Claude Code 等 AI 助手的使用示例和说明。

## 目录

- [使用示例](#使用示例)
- [Claude Code Skill 集成](#claude-code-skill-集成)
- [测试程序](#测试程序)
- [项目结构](#项目结构)

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

### 示例 4：核心转储分析

```
用户："分析位于 /path/to/core 的核心转储"

Claude 会：
1. 调用 lldb_initialize 创建会话
2. 调用 lldb_loadCore 加载核心转储
3. 调用 lldb_stackTrace 显示崩溃堆栈
4. 调用 lldb_analyzeCrash 确定崩溃类型
5. 调用 lldb_readMemory 检查内存状态
6. 提供根本原因分析
```

### 示例 5：多线程调试

```
用户："调试这个有竞态条件的多线程程序"

Claude 会：
1. 调用 lldb_initialize 和 lldb_createTarget
2. 在关键区设置断点 lldb_setBreakpoint
3. 调用 lldb_launch 启动程序
4. 调用 lldb_threads 列出所有线程
5. 为每个线程调用 lldb_stackTrace
6. 分析线程交互并识别竞态条件
```

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

### 技能文档

完整的调试指南可在技能文件中找到：
- **位置**：`skills/lldb-debug/SKILL.md`
- **内容**：700+ 行综合调试方法论
- **涵盖**：思维方式、工作流、错误类型、策略、决策树、参考表

## 测试程序

项目包含带有故意错误的测试程序，用于技能验证和测试：

### 构建测试程序

```bash
# 构建所有测试程序
cd examples/client/c_test
./build_all.sh

# 或构建单个程序
cd examples/client/c_test/null_deref
gcc -g null_deref.c -o null_deref
```

### 可用的测试程序

位于 `examples/client/c_test/`：

| 程序 | 错误类型 | 描述 |
|------|----------|------|
| `null_deref/` | 空指针解引用 | 解引用 NULL 指针 |
| `buffer_overflow/` | 栈缓冲区溢出 | 使用 strcpy 写入超出缓冲区边界 |
| `use_after_free/` | 释放后使用 | 在内存释放后访问 |
| `divide_by_zero/` | 除以零 | 整数除以零 |
| `stack_overflow/` | 栈溢出 | 无限递归导致栈耗尽 |
| `format_string/` | 格式字符串漏洞 | 不安全使用 printf 和用户输入 |
| `double_free/` | 双重释放 | 释放同一内存两次 |
| `infinite_loop/` | 无限循环 | 永不终止的循环 |

### 运行测试程序

**方法 1：使用 Claude Code 直接调试**
```
# 在 Claude Code 中，配置 MCP 后：
用户："调试位于 examples/client/c_test/null_deref/null_deref 的空指针解引用程序"
```

**方法 2：使用 Python 调试流程**
```bash
cd examples/client
TARGET_BIN=./c_test/null_deref/null_deref python3 run_debug_flow.py
```

**方法 3：手动调用 MCP 工具**
```python
# 示例：调试 null_deref 程序
import json

# 1. 初始化会话
lldb_initialize()
# 返回：{"sessionId": "session-123"}

# 2. 创建目标
lldb_createTarget("session-123", "examples/client/c_test/null_deref/null_deref")

# 3. 设置断点
lldb_setBreakpoint("session-123", symbol="main")

# 4. 启动
lldb_launch("session-123")

# 5. 轮询事件
lldb_pollEvents("session-123")

# 6. 继续执行
lldb_continue("session-123")

# 7. 获取崩溃信息
lldb_analyzeCrash("session-123")
lldb_stackTrace("session-123")
```

## 项目结构

```
lldb-mcp-server/
├── src/lldb_mcp_server/
│   ├── fastmcp_server.py      # MCP 入口点
│   ├── platform/               # 平台抽象层
│   │   ├── __init__.py
│   │   ├── detector.py         # 操作系统/发行版检测
│   │   ├── provider.py         # 抽象平台提供者
│   │   ├── macos.py            # macOS 特定路径
│   │   └── linux.py            # Linux 特定路径
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
│   ├── analysis/
│   │   └── exploitability.py   # 崩溃分析
│   └── utils/
│       ├── config.py           # 配置加载
│       └── errors.py           # 错误处理
├── skills/
│   └── lldb-debug/             # Claude Code 调试技能
│       └── SKILL.md            # 700+ 行调试指南
├── examples/
│   └── client/
│       ├── c_test/             # 带错误的测试程序
│       │   ├── null_deref/
│       │   ├── buffer_overflow/
│       │   ├── use_after_free/
│       │   └── ...
│       └── run_debug_flow.py   # 示例调试脚本
├── docs/
│   ├── FEATURES.zh.md          # 功能文档
│   ├── CONFIGURATION.zh.md     # 配置指南
│   ├── TROUBLESHOOTING.zh.md   # 故障排除指南
│   ├── USAGE.zh.md             # 本文件
│   └── LINUX_INSTALLATION.md   # Linux 安装指南
├── scripts/
│   └── diagnose_lldb_linux.sh  # Linux 诊断脚本
├── .mcp.json.uvx               # MCP 配置模板
├── pyproject.toml              # 包配置
├── LICENSE                     # MIT 许可证
└── README.zh.md                # 主文档
```

### 关键组件

**SessionManager (`src/lldb_mcp_server/session/manager.py`)**
- 所有调试会话的中央状态管理
- 拥有所有会话生命周期（创建、终止、列出）
- 实现所有 MCP 工具操作
- 线程安全，带后台事件收集

**平台抽象 (`src/lldb_mcp_server/platform/`)**
- 自动检测操作系统和 Linux 发行版
- 提供平台特定的 LLDB 路径
- 处理 macOS Homebrew 和 Linux 包管理器安装

**工具注册 (`src/lldb_mcp_server/tools/`)**
- 每个模块注册一类 MCP 工具
- 清晰的关注点分离
- 易于扩展新工具

## 另请参阅

- [功能特性](FEATURES.zh.md) - 完整的 40 个工具列表和能力
- [配置指南](CONFIGURATION.zh.md) - 所有 IDE 的详细配置
- [故障排除](TROUBLESHOOTING.zh.md) - 常见问题和解决方案
- [主 README](README.zh.md) - 快速开始指南
