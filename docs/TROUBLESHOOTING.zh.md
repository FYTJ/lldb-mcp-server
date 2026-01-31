# LLDB MCP Server - 故障排除指南

**语言:** [English](TROUBLESHOOTING.md) | [中文](TROUBLESHOOTING.zh.md)

本指南涵盖了 LLDB MCP Server 在不同平台上的常见问题和解决方案。

## 目录

- [macOS 问题](#macos-问题)
- [Linux 问题](#linux-问题)
- [通用问题](#通用问题)
- [诊断工具](#诊断工具)

## macOS 问题

### 问题：`No module named lldb`

**原因：** LLDB Python 绑定配置不正确。

**解决方案：**

```bash
# 1. 验证 LLDB 来自 Homebrew
which lldb
# 应输出：/usr/local/opt/llvm/bin/lldb 或 /opt/homebrew/opt/llvm/bin/lldb

# 2. 如果不是，检查 PATH 配置
cat ~/.zshrc | grep llvm

# 3. 如果缺失，添加到 PATH
echo 'export PATH="$(brew --prefix llvm)/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
hash -r

# 4. 在 .mcp.json 中设置 LLDB_PYTHON_PATH（参见配置指南）
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
# 应显示 LLVM 版本，而非 "lldb-1500"（Xcode 版本）
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

## Linux 问题

### 问题：Linux 上的 `cannot import name '_lldb'` 错误

**原因：** `uvx` 使用的 Python 版本与 LLDB Python 绑定不匹配。

- LLDB Python 绑定是为特定 Python 版本编译的（例如，LLDB-19 → Python 3.12）
- `uvx` 默认使用系统 Python，可能版本不同（例如，linuxbrew 的 3.14）

**解决方案：**

```bash
# 1. 检查 LLDB 的 Python 版本
lldb-19 -P
# 输出：/usr/lib/llvm-19/lib/python3.12/site-packages
#       ^^^^^^^^ 这显示 Python 3.12

# 2. 检查 uvx 的默认 Python
uvx --python-preference system python --version
# 如果显示 3.14，但 LLDB 需要 3.12，这就是问题所在

# 3. 检查 Python 3.12 是否可用
which python3.12
python3.12 --version

# 4. 更新 MCP 配置以强制使用 Python 3.12
# 获取 LLDB 路径
LLDB_PATH=$(/usr/bin/lldb-19 -P)

# 更新配置（Claude Code）
claude mcp add-json --scope user lldb-debugger '{
  "type": "stdio",
  "command": "uvx",
  "args": ["--python", "/usr/bin/python3.12", "-q", "lldb-mcp-server", "--transport", "stdio"],
  "env": {
    "LLDB_MCP_ALLOW_LAUNCH": "1",
    "LLDB_MCP_ALLOW_ATTACH": "1",
    "LLDB_PYTHON_PATH": "'"$LLDB_PATH"'"
  }
}'

# 5. 验证修复
LLDB_PYTHON_PATH=$(/usr/bin/lldb-19 -P) \
uvx --python /usr/bin/python3.12 -q lldb-mcp-server --help
# 预期：显示帮助输出，无导入错误
```

**关键要点：**
- `--python /usr/bin/python3.12` 参数强制 uvx 使用 Python 3.12
- 将 `lldb-19` 替换为你的 LLDB 版本（例如 `lldb-18`）
- 将 `/usr/bin/python3.12` 替换为与你的 LLDB Python 版本匹配的路径

### 问题：Linux 上的 `uvx: command not found` 错误

**原因：** `uv` 未安装或不在 PATH 中。

**解决方案：**

```bash
# 1. 安装 uv（提供 uvx 命令）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 重新加载 shell 以更新 PATH
source ~/.bashrc  # zsh 用户使用 source ~/.zshrc

# 3. 验证安装
which uvx
uvx --version
```

### 问题：Linux 上的 Python 版本不匹配

**原因：** LLDB Python 绑定编译的 Python 版本与 uvx 使用的版本不同。

**解决方案：**

```bash
# 1. 检查 Python 版本
lldb-19 -P | grep -o 'python3\.[0-9]*'  # LLDB Python 版本（例如 python3.12）
uvx --python-preference system python --version  # uvx 的默认 Python

# 2. 强制 uvx 使用匹配的 Python 版本
# 如果 LLDB 需要 Python 3.12，更新 MCP 配置以包含：
{
  "command": "uvx",
  "args": ["--python", "/usr/bin/python3.12", "-q", "lldb-mcp-server", "--transport", "stdio"]
}

# 3. 验证修复
LLDB_PYTHON_PATH=$(/usr/bin/lldb-19 -P) \
uvx --python /usr/bin/python3.12 -c "import lldb; print('OK')"
```

### 问题：Ubuntu/Debian 上未找到 LLDB Python 模块

**原因：** 未安装 LLDB Python 绑定。

**解决方案：**

```bash
# 安装 LLDB 和 Python 绑定
sudo apt update
sudo apt install lldb-19 python3-lldb-19

# 验证安装
lldb-19 -P
# 预期：/usr/lib/llvm-19/lib/python3.12/site-packages

# 验证 Python 3.12 可用
which python3.12
python3.12 --version

# 测试导入
python3.12 -c "import sys; sys.path.insert(0, '$(/usr/bin/lldb-19 -P)'); import lldb; print('OK')"
```

> **注意：** 如果你的 Ubuntu 版本不提供 LLDB-19，可以使用 LLDB-18 或其他可用版本。只需确保相应匹配 Python 版本。

### 问题：Fedora/RHEL 上未找到 LLDB Python 模块

**原因：** 未安装 LLDB Python 绑定。

**解决方案：**

```bash
# 安装 LLDB 和 Python 绑定
sudo dnf install lldb lldb-devel python3-lldb

# 验证安装
lldb -P
python3 -c "import lldb; print('OK')"
```

### 问题：Arch Linux 上未找到 LLDB Python 模块

**原因：** 未安装 LLDB Python 绑定。

**解决方案：**

```bash
# 安装 LLDB
sudo pacman -S lldb

# Python 绑定应在 /usr/lib/python3.X/site-packages 中
python3 -c "import lldb; print('OK')"
```

## 通用问题

### 问题：MCP 服务器无响应

**原因：** 服务器崩溃或配置错误。

**调试步骤：**

1. **检查服务器日志**（如果在 Claude Desktop 中运行）：
   ```bash
   # macOS
   tail -f ~/Library/Logs/Claude/mcp*.log

   # Linux
   tail -f ~/.config/Claude/logs/mcp*.log
   ```

2. **手动测试服务器：**
   ```bash
   # macOS
   uvx --python /opt/homebrew/opt/python@3.13/bin/python3.13 lldb-mcp-server

   # Linux
   LLDB_PYTHON_PATH=$(/usr/bin/lldb-19 -P) \
   uvx --python /usr/bin/python3.12 -q lldb-mcp-server --help

   # 应显示帮助信息，无错误
   # 如果开始等待输入，按 Ctrl+C 退出
   ```

3. **验证 LLDB 导入：**
   ```bash
   python3 -c "import lldb; print('LLDB 导入成功')"
   ```

### 问题：断点未命中

**可能原因：**

1. **二进制文件未使用调试符号编译：**
   ```bash
   # 使用 -g 标志重新编译
   gcc -g myprogram.c -o myprogram
   ```

2. **优化删除了代码：**
   ```bash
   # 不使用优化编译
   gcc -g -O0 myprogram.c -o myprogram
   ```

3. **断点中的文件路径错误：**
   - 对 file:line 断点使用绝对路径
   - 或使用函数名：`lldb_setBreakpoint(sessionId, symbol="main")`

### 问题：无法求值表达式

**可能原因：**

1. **进程未停止：**
   - 只能在进程停止时（在断点处或暂停后）求值表达式

2. **变量被优化掉：**
   - 使用 `-O0` 编译以防止优化

3. **选择了错误的栈帧：**
   - 使用 `lldb_selectFrame` 选择正确的栈帧

### 问题：核心转储无法加载

**可能原因：**

1. **二进制文件不匹配：**
   ```bash
   # 确保二进制文件与核心转储匹配
   lldb_loadCore(sessionId, corePath="/path/to/core", executablePath="/path/to/exact/binary")
   ```

2. **核心转储生成被禁用：**
   ```bash
   # 启用核心转储（Linux）
   ulimit -c unlimited

   # 生成核心转储
   ./myprogram
   # 崩溃后：创建 core 文件
   ```

3. **不支持的核心转储格式：**
   - LLDB 支持 ELF 核心转储（Linux）和 Mach-O 核心转储（macOS）

## 诊断工具

### Linux 诊断脚本

对于 Linux 用户，我们提供了自动诊断脚本：

```bash
# 下载并运行诊断脚本
curl -sSL https://raw.githubusercontent.com/FYTJ/lldb-mcp-server/main/scripts/diagnose_lldb_linux.sh | bash

# 或如果你已克隆仓库
./scripts/diagnose_lldb_linux.sh
```

此脚本检查：
- 操作系统和版本
- Python 版本
- LLDB 安装
- LLDB Python 路径
- Python LLDB 导入
- 环境变量
- lldb-mcp-server 安装

并根据检测到的问题提供推荐的修复方案。

### 手动诊断

**检查 LLDB 安装：**
```bash
# macOS
which lldb
lldb --version
lldb -P

# Linux
which lldb lldb-18 lldb-19
lldb-19 --version  # 或 lldb-18（如果使用 LLDB-18）
lldb-19 -P
# 检查路径中的 Python 版本
lldb-19 -P | grep -o 'python3\.[0-9]*'
```

**检查 Python LLDB 导入：**
```bash
python3 -c "import lldb; print('LLDB 文件:', lldb.__file__); print('LLDB 版本:', lldb.SBDebugger.GetVersionString())"
```

**检查 lldb-mcp-server 安装：**
```bash
which lldb-mcp-server
lldb-mcp-server --help
```

**检查环境变量：**
```bash
echo $LLDB_PYTHON_PATH
echo $LLDB_MCP_ALLOW_LAUNCH
echo $LLDB_MCP_ALLOW_ATTACH
echo $PATH | grep -o "[^:]*local/bin[^:]*"
```

## 仍然有问题？

如果你仍然遇到问题：

1. **检查现有问题：** [GitHub Issues](https://github.com/FYTJ/lldb-mcp-server/issues)

2. **提交新问题**，包含以下信息：
   - 操作系统和版本
   - Python 版本（`python3 --version`）
   - LLDB 版本（`lldb --version` 或 `lldb-18 --version`）
   - `lldb -P` 或 `lldb-18 -P` 的输出
   - 完整的错误消息
   - 配置文件内容（`.mcp.json`）

3. **查看平台特定的安装指南：**
   - [Linux 安装指南](LINUX_INSTALLATION.md)
   - [主 README](README.zh.md)

## 另请参阅

- [配置指南](CONFIGURATION.zh.md) - 详细的配置说明
- [功能特性](FEATURES.zh.md) - 完整的 40 个工具列表
- [使用指南](USAGE.zh.md) - 使用示例
- [主 README](README.zh.md) - 快速开始指南
