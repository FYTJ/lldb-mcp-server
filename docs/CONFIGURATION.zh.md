# LLDB MCP Server - 配置指南

**语言:** [English](CONFIGURATION.md) | [中文](CONFIGURATION.zh.md)

本指南提供了 LLDB MCP Server 在不同 IDE 和平台上的详细配置说明。

## 目录

- [环境变量](#环境变量)
- [Claude Code 配置](#claude-code-配置)
- [Claude Desktop 配置](#claude-desktop-配置)
- [Cursor IDE 配置](#cursor-ide-配置)
- [Codex 配置](#codex-配置)
- [手动 LLDB 路径配置](#手动-lldb-路径配置)

## 环境变量

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `LLDB_MCP_ALLOW_LAUNCH=1` | 允许启动新进程 | 禁用 |
| `LLDB_MCP_ALLOW_ATTACH=1` | 允许附加到现有进程 | 禁用 |
| `LLDB_PYTHON_PATH` | 覆盖 LLDB Python 模块路径 | 自动检测 |

**安全说明：** 启动和附加操作需要 `LLDB_MCP_ALLOW_LAUNCH` 和 `LLDB_MCP_ALLOW_ATTACH`。没有这些变量，服务器将拒绝此类操作。

## Claude Code 配置

### 全局配置（推荐）

**macOS - Intel (x86_64):**
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

**macOS - Apple Silicon (arm64):**
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

### 项目特定配置

在项目根目录创建 `.mcp.json`：

**macOS - Intel (x86_64):**
```json
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
```

**macOS - Apple Silicon (arm64):**
```json
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
```

**Linux:**
```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "lldb-mcp-server",
      "args": [],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1",
        "LLDB_PYTHON_PATH": "/usr/lib/llvm-18/lib/python3.12/site-packages",
        "PATH": "/home/YOUR_USERNAME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
      }
    }
  }
}
```

> **Linux 注意事项：**
> - 使用 `lldb-mcp-server` 命令（不是 `uvx`）
> - 设置 `LLDB_PYTHON_PATH` 为 `lldb-18 -P` 的输出
> - 包含完整的 `PATH`，其中包含 `~/.local/bin`
> - 将 `YOUR_USERNAME` 替换为你的用户名

## Claude Desktop 配置

### macOS

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`：

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
        "PYTHONPATH": "/usr/local/opt/llvm/lib/python3.13/site-packages"
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
        "PYTHONPATH": "/opt/homebrew/opt/llvm/lib/python3.13/site-packages"
      }
    }
  }
}
```

### Linux

编辑 `~/.config/claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "lldb-mcp-server",
      "args": [],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1",
        "LLDB_PYTHON_PATH": "/usr/lib/llvm-18/lib/python3.12/site-packages",
        "PATH": "/home/YOUR_USERNAME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
      }
    }
  }
}
```

> **注意：** 将 `/usr/lib/llvm-18/lib/python3.12/site-packages` 替换为 `lldb-18 -P` 的输出，将 `YOUR_USERNAME` 替换为你的实际用户名。

编辑后，重启 Claude Desktop。

## Cursor IDE 配置

### 方式 1：项目特定配置（推荐）

在项目根目录创建 `.cursor/mcp.json`：

**macOS - Intel (x86_64):**
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

**macOS - Apple Silicon (arm64):**
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

**Linux:**
```bash
mkdir -p .cursor
cat > .cursor/mcp.json << 'EOF'
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "lldb-mcp-server",
      "args": [],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1",
        "LLDB_PYTHON_PATH": "/usr/lib/llvm-18/lib/python3.12/site-packages",
        "PATH": "/home/YOUR_USERNAME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
      }
    }
  }
}
EOF
```
> **注意：** 将 `/usr/lib/llvm-18/lib/python3.12/site-packages` 替换为 `lldb-18 -P` 的输出，将 `YOUR_USERNAME` 替换为你的实际用户名。

### 方式 2：全局配置

在主目录创建 `~/.cursor/mcp.json`，使用与上述相同的 JSON 结构。这使得 LLDB 调试器在所有 Cursor 项目中可用。

配置完成后，重启 Cursor 以加载 MCP 服务器。

## Codex 配置

### macOS

**Intel (x86_64) - CLI:**
```bash
codex mcp add lldb-debugger \
  --env LLDB_MCP_ALLOW_LAUNCH=1 \
  --env LLDB_MCP_ALLOW_ATTACH=1 \
  --env PYTHONPATH=/usr/local/opt/llvm/lib/python3.13/site-packages \
  -- uvx --python /usr/local/opt/python@3.13/bin/python3.13 lldb-mcp-server
```

**Apple Silicon (arm64) - CLI:**
```bash
codex mcp add lldb-debugger \
  --env LLDB_MCP_ALLOW_LAUNCH=1 \
  --env LLDB_MCP_ALLOW_ATTACH=1 \
  --env PYTHONPATH=/opt/homebrew/opt/llvm/lib/python3.13/site-packages \
  -- uvx --python /opt/homebrew/opt/python@3.13/bin/python3.13 lldb-mcp-server
```

**手动 - 编辑 `~/.codex/config.toml` (Intel):**
```toml
[mcp_servers.lldb-debugger]
command = "uvx"
args = ["--python", "/usr/local/opt/python@3.13/bin/python3.13", "lldb-mcp-server"]

[mcp_servers.lldb-debugger.env]
LLDB_MCP_ALLOW_LAUNCH = "1"
LLDB_MCP_ALLOW_ATTACH = "1"
PYTHONPATH = "/usr/local/opt/llvm/lib/python3.13/site-packages"
```

**手动 - 编辑 `~/.codex/config.toml` (Apple Silicon):**
```toml
[mcp_servers.lldb-debugger]
command = "uvx"
args = ["--python", "/opt/homebrew/opt/python@3.13/bin/python3.13", "lldb-mcp-server"]

[mcp_servers.lldb-debugger.env]
LLDB_MCP_ALLOW_LAUNCH = "1"
LLDB_MCP_ALLOW_ATTACH = "1"
PYTHONPATH = "/opt/homebrew/opt/llvm/lib/python3.13/site-packages"
```

### Linux

**CLI:**
```bash
codex mcp add lldb-debugger \
  --env LLDB_MCP_ALLOW_LAUNCH=1 \
  --env LLDB_MCP_ALLOW_ATTACH=1 \
  --env LLDB_PYTHON_PATH=/usr/lib/llvm-18/lib/python3.12/site-packages \
  -- lldb-mcp-server
```

**手动 - 编辑 `~/.codex/config.toml`:**
```toml
[mcp_servers.lldb-debugger]
command = "lldb-mcp-server"
args = []

[mcp_servers.lldb-debugger.env]
LLDB_MCP_ALLOW_LAUNCH = "1"
LLDB_MCP_ALLOW_ATTACH = "1"
LLDB_PYTHON_PATH = "/usr/lib/llvm-18/lib/python3.12/site-packages"
```
> **注意：** 将 `/usr/lib/llvm-18/lib/python3.12/site-packages` 替换为 `lldb-18 -P` 的输出

**注意：** 你也可以在项目根目录创建项目特定的 `.codex/config.toml`（仅限受信任的项目）。

## 手动 LLDB 路径配置

如果服务器无法自动找到 LLDB Python 绑定，你需要显式设置 `LLDB_PYTHON_PATH`：

### 查找 LLDB 路径

**macOS:**
```bash
# 方法 1：检查 Homebrew LLVM 路径
brew --prefix llvm
# 输出：/usr/local/opt/llvm (Intel) 或 /opt/homebrew/opt/llvm (ARM)

# 添加 Python 版本：/usr/local/opt/llvm/lib/python3.13/site-packages

# 方法 2：使用 lldb -P 命令
lldb -P
```

**Linux:**
```bash
# 使用带版本的 lldb -P 命令
lldb-18 -P
# 示例输出：/usr/lib/llvm-18/lib/python3.12/site-packages

# 或手动检查
ls /usr/lib/llvm-*/lib/python*/site-packages/lldb
```

### 添加到配置

获得 LLDB Python 路径后，将其添加到配置的 `env` 部分：

**macOS 示例:**
```json
{
  "env": {
    "LLDB_MCP_ALLOW_LAUNCH": "1",
    "LLDB_MCP_ALLOW_ATTACH": "1",
    "LLDB_PYTHON_PATH": "/opt/homebrew/opt/llvm/lib/python3.13/site-packages"
  }
}
```

**Linux 示例:**
```json
{
  "env": {
    "LLDB_MCP_ALLOW_LAUNCH": "1",
    "LLDB_MCP_ALLOW_ATTACH": "1",
    "LLDB_PYTHON_PATH": "/usr/lib/llvm-18/lib/python3.12/site-packages"
  }
}
```

## 验证配置

配置后，验证设置：

**测试 LLDB 导入:**
```bash
python3 -c "import lldb; print('LLDB version:', lldb.SBDebugger.GetVersionString())"
```

**测试 MCP 服务器（如果全局安装）:**
```bash
lldb-mcp-server --help
```

## 另请参阅

- [功能特性](FEATURES.zh.md) - 完整的 40 个工具列表
- [使用指南](USAGE.zh.md) - 使用示例和技能集成
- [故障排除](TROUBLESHOOTING.zh.md) - 常见配置问题
- [主 README](README.zh.md) - 快速开始指南
