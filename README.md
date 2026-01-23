# LLDB MCP Server

语言: [中文](README.md) | [English](docs/README.en.md)

## 概述

一个可通过 MCP 工具调用 LLDB 的服务器，提供会话管理、目标/进程控制、断点、执行控制、栈与变量、表达式、寄存器读写、符号搜索、模块列表、内存读写、核心转储与崩溃分析、事件轮询。

## 环境要求

### ✅ 推荐配置（Homebrew LLVM + Python 3.13）

**关键问题：** LLDB 与 FastMCP 的 Python 版本冲突
- **Xcode LLDB**: 仅支持 Python 3.9.6
- **FastMCP**: 需要 Python ≥3.10

**解决方案：** 使用 Homebrew LLVM，其 LLDB 支持现代 Python 版本（3.10+）

**系统要求：**
- macOS
- Homebrew (`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`)
- `uv` 包管理器: `brew install uv`


## 安装与环境配置

### 方案一：Homebrew LLVM（推荐）

**步骤 1：安装 LLVM 和 Python 3.13**

```bash
# 安装 LLVM（包含支持现代 Python 的 LLDB）
brew install llvm

# 安装 Python 3.13
brew install python@3.13

# 验证安装
/usr/local/opt/python@3.13/bin/python3.13 -V
$(brew --prefix llvm)/bin/lldb --version
```

**步骤 2：配置 Shell 环境**

在 `~/.zshrc` (或 `~/.bashrc`) 中添加：

```bash
# 将 Homebrew LLVM 添加到 PATH（优先于系统 LLDB）
export PATH="$(brew --prefix llvm)/bin:$PATH"
```

重新加载配置：
```bash
source ~/.zshrc  # 或 source ~/.bashrc
hash -r          # 清除命令缓存
```

验证 LLDB 来自 Homebrew：
```bash
which lldb
# 期望输出: /usr/local/opt/llvm/bin/lldb（不是 /usr/bin/lldb）

lldb --version
lldb -P  # 查看 LLDB Python 路径
```

**步骤 3：创建 Python 3.13 虚拟环境**

```bash
# 删除旧的 venv（如果存在）
deactivate 2>/dev/null || true
rm -rf .venv

# 使用 Python 3.13 创建 venv
/usr/local/opt/python@3.13/bin/python3.13 -m venv .venv
source .venv/bin/activate

# 验证 Python 版本
python -c "import sys; print(sys.version)"
# 期望: Python 3.13.x
```

**步骤 4：将 LLDB Python 路径添加到虚拟环境**

此步骤使 LLDB 模块永久可用，无需 PYTHONPATH：

```bash
# 获取 LLDB Python 模块路径
LLDB_PY_PATH="$(lldb -P)"
echo "LLDB Python 路径: $LLDB_PY_PATH"

# 获取 venv 的 site-packages 目录
SITE_PKGS="$(python -c 'import site; print(site.getsitepackages()[0])')"
echo "Site packages: $SITE_PKGS"

# 将 LLDB 路径写入 .pth 文件（永久 Python 路径配置）
echo "$LLDB_PY_PATH" > "$SITE_PKGS/lldb.pth"
```

**步骤 5：验证 LLDB 导入（无需 PYTHONPATH）**

```bash
python - <<'PY'
import lldb
print("lldb 模块:", lldb.__file__)
print("lldb 版本:", lldb.SBDebugger.GetVersionString())

# 验证内部模块
import lldb._lldb as m
print("lldb._lldb:", m.__file__)
PY
```

期望输出：
```
lldb 模块: /usr/local/opt/llvm/lib/python3.13/site-packages/lldb/__init__.py
lldb 版本: lldb-<版本>
lldb._lldb: /usr/local/opt/llvm/lib/python3.13/site-packages/lldb/_lldb.cpython-313-darwin.so
```

**步骤 6：安装项目依赖**

```bash
# 使用 uv 安装（推荐）
uv pip install -e ".[dev]"

# 或使用 pip
pip install -e ".[dev]"

# 验证 FastMCP 已安装
python -c "import fastmcp; print('FastMCP:', fastmcp.__version__)"
```

**步骤 7：最终验证**

```bash
# 测试所有导入
python -c "
import lldb
import fastmcp
print('✅ LLDB 版本:', lldb.SBDebugger.GetVersionString())
print('✅ FastMCP 版本:', fastmcp.__version__)
print('✅ 两个模块都正常工作！')
"
```

---

## 环境验证

**验证安装是否成功：**

```bash
# 步骤 1：验证 LLDB 来自 Homebrew
which lldb
# 期望输出: /usr/local/opt/llvm/bin/lldb

lldb --version
# 期望输出: LLDB 版本信息

# 步骤 2：验证 Python 版本
python --version
# 期望输出: Python 3.13.x

# 步骤 3：验证 LLDB 导入（无需 PYTHONPATH）
python -c "import lldb; print(lldb.SBDebugger.GetVersionString())"
# 期望输出: lldb-<版本>

# 步骤 4：验证 FastMCP 安装
python -c "import fastmcp; print('FastMCP:', fastmcp.__version__)"
# 期望输出: FastMCP: <版本号>

# 步骤 5：完整验证
python - <<'PY'
import lldb
import fastmcp
print('✅ LLDB 版本:', lldb.SBDebugger.GetVersionString())
print('✅ FastMCP 版本:', fastmcp.__version__)
print('✅ 环境配置完成！')
PY
```

**如果验证失败：**

1. **LLDB 仍来自 Xcode** (`/usr/bin/lldb`)
   - 检查 `~/.zshrc` 或 `~/.bashrc` 是否添加了 PATH 配置
   - 运行 `source ~/.zshrc && hash -r`
   - 重新打开终端

2. **LLDB 导入失败**
   - 检查 `.pth` 文件是否存在：
     ```bash
     SITE_PKGS="$(python -c 'import site; print(site.getsitepackages()[0])')"
     cat "$SITE_PKGS/lldb.pth"
     ```
   - 如果不存在，重新运行步骤 4：
     ```bash
     LLDB_PY_PATH="$(lldb -P)"
     SITE_PKGS="$(python -c 'import site; print(site.getsitepackages()[0])')"
     echo "$LLDB_PY_PATH" > "$SITE_PKGS/lldb.pth"
     ```

3. **FastMCP 导入失败**
   - 运行 `uv pip install -e ".[dev]"` 重新安装
   - 检查 Python 版本是否 ≥3.10

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

## 运行服务器

**FastMCP 服务器 - HTTP 模式（测试用）：**
```bash
LLDB_MCP_ALLOW_LAUNCH=1 \
LLDB_MCP_ALLOW_ATTACH=1 \
  .venv/bin/python -m lldb_mcp_server.fastmcp_server \
  --transport http --host 127.0.0.1 --port 8765
```

**FastMCP 服务器 - Stdio 模式（Claude Desktop）：**
```bash
LLDB_MCP_ALLOW_LAUNCH=1 \
LLDB_MCP_ALLOW_ATTACH=1 \
  .venv/bin/python -m lldb_mcp_server.fastmcp_server
```

**FastMCP 开发模式（自动重载）：**
```bash
LLDB_MCP_ALLOW_LAUNCH=1 \
  fastmcp dev src/lldb_mcp_server/fastmcp_server.py
```

---

## 使用示例

### FastMCP 服务器（HTTP 模式）

**启动服务器：**
```bash
LLDB_MCP_ALLOW_LAUNCH=1 LLDB_MCP_ALLOW_ATTACH=1 \
  .venv/bin/python -m lldb_mcp_server.fastmcp_server \
  --transport http --host 127.0.0.1 --port 8765
```

**测试工具调用：**
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

### 准备测试程序

```bash
# 编译测试程序
cd examples/client/c_test/hello
cc -g -O0 -Wall -Wextra -o hello hello.c
cd ../../../..
```

### 运行示例客户端

**使用 Homebrew LLDB：**
```bash
# 启动服务器（终端 1）
LLDB_MCP_ALLOW_LAUNCH=1 LLDB_MCP_ALLOW_ATTACH=1 \
  .venv/bin/python -m lldb_mcp_server.fastmcp_server \
  --transport http --host 127.0.0.1 --port 8765

# 运行客户端（终端 2）
TARGET_BIN=$(pwd)/examples/client/c_test/hello/hello \
MCP_HOST=127.0.0.1 \
MCP_PORT=8765 \
  .venv/bin/python examples/client/run_debug_flow.py
```



## 常见问题

- `No module named lldb`：安装 Xcode/CLT，并在 Python 使用系统 LLDB 绑定；如果仍不可用，可先使用协议与工具映射进行开发，实际调试能力在有 LLDB 绑定时自动启用。
