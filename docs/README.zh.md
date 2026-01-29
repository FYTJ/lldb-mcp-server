# LLDB MCP Server

**语言:** [English](../README.md) | [中文](README.zh.md)

[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](https://github.com/FYTJ/lldb-mcp-server)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](../LICENSE)
[![PyPI](https://img.shields.io/pypi/v/lldb-mcp-server)](https://pypi.org/project/lldb-mcp-server/)

## 概述

LLDB MCP Server 是一个基于 [Model Context Protocol (MCP)](https://modelcontextprotocol.io) 的调试服务器，通过 40 个专业工具将 LLDB 调试功能暴露给 Claude Code 和 Claude Desktop 等 AI 助手，支持 AI 驱动的 C/C++ 应用程序交互式调试。

**核心架构：** 多会话设计，每个调试会话拥有独立的 `SBDebugger`、`SBTarget` 和 `SBProcess` 实例，支持并发调试工作流。

**适用场景：**
- Claude Code / Claude Desktop 的 AI 辅助调试
- 自动化调试脚本和工作流
- 崩溃分析和安全漏洞检测
- 远程调试和核心转储分析

**关键能力：**
- 🔧 **40 个调试工具**：会话管理、断点、执行控制、内存操作、安全分析等
- 🔄 **多会话支持**：并发运行多个独立调试会话
- 📊 **事件驱动架构**：非阻塞事件收集，捕获状态变化、断点命中、stdout/stderr
- 🛡️ **安全分析**：崩溃可利用性分类和危险函数检测
- 📝 **会话记录**：自动记录所有命令和输出，带时间戳
- 💻 **跨平台**：支持 macOS（Intel 和 Apple Silicon）和 Linux（Ubuntu、Fedora、Arch）

## 文档

- **[功能特性](FEATURES.zh.md)** - 完整的 40 个工具列表和详细能力
- **[配置指南](CONFIGURATION.zh.md)** - Claude Code、Claude Desktop、Cursor 和 Codex 的详细配置
- **[使用指南](USAGE.zh.md)** - 使用示例、Claude Code Skill 集成和测试程序
- **[故障排除](TROUBLESHOOTING.zh.md)** - 所有平台的常见问题和解决方案
- **[Linux 安装](LINUX_INSTALLATION.md)** - 详细的 Linux 安装指南

## 环境要求

### 系统要求

- **操作系统**：macOS（Intel 或 Apple Silicon）**或** Linux（Ubuntu 22.04+、Fedora 38+、Arch Linux）
- **LLDB**：带 Python 绑定（版本 14+，推荐 18+）
- **Python 3.10+**

### 平台特定要求

**macOS：**
- **Homebrew**（[安装指南](https://brew.sh/)）
- **Homebrew LLVM** 或 Xcode Command Line Tools

**Linux：**
- **包管理器**：apt（Ubuntu/Debian）、dnf（Fedora/RHEL）或 pacman（Arch）
- **LLDB**：通过 `sudo apt install lldb-18 python3-lldb-18`（Ubuntu）或等效命令安装

## 快速开始

### 1. 安装依赖

#### macOS

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

#### Linux（Ubuntu/Debian）

```bash
# 安装 LLDB 和 Python 绑定
sudo apt update
sudo apt install lldb-18 python3-lldb-18

# 安装 lldb-mcp-server（使用 pip，不要在 Linux 上使用 uvx）
pip3 install --user lldb-mcp-server

# 查找 LLDB Python 路径
lldb-18 -P
# 示例输出：/usr/lib/llvm-18/lib/python3.12/site-packages

# 设置 LLDB_PYTHON_PATH（添加到 ~/.bashrc 以持久化）
export LLDB_PYTHON_PATH="/usr/lib/llvm-18/lib/python3.12/site-packages"

# 验证安装
python3 -c "import lldb; print('LLDB Python 绑定正常')"
lldb-mcp-server --help
```

> **⚠️ 重要提示 - Linux 用户：**
> - **不要在 Linux 上使用 `uvx`** - 它创建的隔离环境无法访问系统 LLDB
> - **请使用 `pip3 install --user lldb-mcp-server`**
> - **务必在配置中设置 `LLDB_PYTHON_PATH`**
> - 直接使用 `lldb-mcp-server` 命令（不要使用 `uvx lldb-mcp-server`）

**其他 Linux 发行版（Fedora、Arch 等）**，请参见 [Linux 安装指南](LINUX_INSTALLATION.md)。

### 2. 配置 MCP

选择你的 IDE 并遵循配置说明：

#### Claude Code

**macOS - 全局配置（推荐）：**

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

**Linux:**
```bash
claude mcp add-json --scope user lldb-debugger '{
  "type": "stdio",
  "command": "lldb-mcp-server",
  "args": [],
  "env": {
    "LLDB_MCP_ALLOW_LAUNCH": "1",
    "LLDB_MCP_ALLOW_ATTACH": "1",
    "LLDB_PYTHON_PATH": "/usr/lib/llvm-18/lib/python3.12/site-packages"
  }
}'
```
> **注意：** 将 `/usr/lib/llvm-18/lib/python3.12/site-packages` 替换为 `lldb-18 -P` 的输出

#### Claude Desktop

**macOS:**
编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`

**Linux:**
编辑 `~/.config/claude/claude_desktop_config.json`

请参见 [配置指南](CONFIGURATION.zh.md) 获取详细配置示例。

#### Cursor IDE

在项目根目录创建 `.cursor/mcp.json` 或创建 `~/.cursor/mcp.json` 进行全局配置。

请参见 [配置指南](CONFIGURATION.zh.md) 获取平台特定示例。

#### Codex (OpenAI)

使用 `codex mcp add` 命令或编辑 `~/.codex/config.toml`。

请参见 [配置指南](CONFIGURATION.zh.md) 获取详细说明。

### 3. 开始使用

**macOS：**
无需手动安装！使用 `uvx` 配置 MCP 服务器后，它会自动安装和管理包。

**Linux：**
使用 `pip` 安装并配置环境变量后，服务器即可使用。

只需配置你的 IDE 并启动 Claude Code 或重启 Claude Desktop。

## 使用示例

### 基本调试

```
用户："调试位于 /path/to/my/app 的程序"

Claude 自动：
1. 创建调试会话
2. 加载二进制文件
3. 设置断点
4. 启动进程
5. 分析执行
```

### 崩溃分析

```
用户："这个程序崩溃了，帮我分析原因"

Claude 会：
1. 分析崩溃事件
2. 显示崩溃堆栈跟踪
3. 检查寄存器状态
4. 检测危险函数
5. 提供修复建议
```

更多示例请参见 [使用指南](USAGE.zh.md)。

## 环境变量

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `LLDB_MCP_ALLOW_LAUNCH=1` | 允许启动新进程 | 禁用 |
| `LLDB_MCP_ALLOW_ATTACH=1` | 允许附加到现有进程 | 禁用 |
| `LLDB_PYTHON_PATH` | 覆盖 LLDB Python 模块路径 | 自动检测 |

## 故障排除

### macOS：`No module named lldb`

```bash
# 验证 LLDB 来自 Homebrew
which lldb

# 添加到 PATH
echo 'export PATH="$(brew --prefix llvm)/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
hash -r
```

### Linux：`cannot import name '_lldb'`

```bash
# 使用 pip 安装（不是 uvx）
pip3 install --user lldb-mcp-server

# 设置 LLDB_PYTHON_PATH
lldb-18 -P
export LLDB_PYTHON_PATH="/usr/lib/llvm-18/lib/python3.12/site-packages"
```

更多问题和解决方案请参见 [故障排除指南](TROUBLESHOOTING.zh.md)。

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](../LICENSE) 文件。

## 链接

- **文档**：[功能特性](FEATURES.zh.md) | [配置指南](CONFIGURATION.zh.md) | [使用指南](USAGE.zh.md) | [故障排除](TROUBLESHOOTING.zh.md)
- **PyPI 包**: [https://pypi.org/project/lldb-mcp-server/](https://pypi.org/project/lldb-mcp-server/)
- **源代码**: [https://github.com/FYTJ/lldb-mcp-server](https://github.com/FYTJ/lldb-mcp-server)
- **Issues**: [https://github.com/FYTJ/lldb-mcp-server/issues](https://github.com/FYTJ/lldb-mcp-server/issues)
- **MCP 文档**: [https://modelcontextprotocol.io](https://modelcontextprotocol.io)
