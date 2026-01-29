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

**原因：** `uvx` 创建的隔离环境无法访问系统 LLDB Python 绑定。

**解决方案：**

```bash
# 1. 如果使用 uvx 安装则卸载
#（无需操作，uvx 使用临时环境）

# 2. 改用 pip 安装
pip3 install --user lldb-mcp-server

# 3. 查找 LLDB Python 路径
lldb-18 -P
# 输出：/usr/lib/llvm-18/lib/python3.12/site-packages

# 4. 永久设置环境变量
echo 'export LLDB_PYTHON_PATH="/usr/lib/llvm-18/lib/python3.12/site-packages"' >> ~/.bashrc
source ~/.bashrc

# 5. 更新配置以使用 lldb-mcp-server 命令
# 在 .mcp.json 或 claude_desktop_config.json 中：
{
  "command": "lldb-mcp-server",  # 不是 "uvx"
  "args": [],
  "env": {
    "LLDB_PYTHON_PATH": "/usr/lib/llvm-18/lib/python3.12/site-packages"
  }
}
```

### 问题：Linux 上的 `lldb-mcp-server: command not found` 错误

**原因：** `~/.local/bin` 不在 PATH 中。

**解决方案：**

```bash
# 1. 永久添加到 PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 2. 或在配置中使用完整路径
{
  "command": "/home/YOUR_USERNAME/.local/bin/lldb-mcp-server",
  "env": {
    "PATH": "/home/YOUR_USERNAME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
  }
}
```

### 问题：Linux 上的 Python 版本不匹配

**原因：** LLDB Python 绑定编译的 Python 版本与系统默认 Python 版本不同。

**解决方案：**

```bash
# 1. 检查 Python 版本
python3 --version  # 系统 Python
lldb-18 -P | grep python  # LLDB Python 版本

# 2. 如果不匹配，确保正确设置 LLDB_PYTHON_PATH
# 示例：如果 LLDB 使用 Python 3.12 但系统是 3.14：
export LLDB_PYTHON_PATH="/usr/lib/llvm-18/lib/python3.12/site-packages"

# 3. 验证导入工作
python3 -c "import sys; sys.path.insert(0, '/usr/lib/llvm-18/lib/python3.12/site-packages'); import lldb; print('OK')"
```

### 问题：Ubuntu/Debian 上未找到 LLDB Python 模块

**原因：** 未安装 LLDB Python 绑定。

**解决方案：**

```bash
# 安装 LLDB 和 Python 绑定
sudo apt update
sudo apt install lldb-18 python3-lldb-18

# 验证安装
lldb-18 -P
python3 -c "import sys; sys.path.insert(0, '$(lldb-18 -P)'); import lldb; print('OK')"
```

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
   lldb-mcp-server

   # 应输出："LLDB MCP Server starting..." 并等待输入
   # 按 Ctrl+C 退出
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
lldb-18 --version
lldb-18 -P
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
