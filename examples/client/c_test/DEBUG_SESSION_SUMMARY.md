# LLDB MCP 调试任务完整流程总结

**任务日期**: 2026-01-24
**调试目标**: null_deref 二进制程序
**调试方式**: 使用 LLDB MCP Server 工具（无源代码访问）

---

## 任务背景

用户要求使用 LLDB MCP 工具调试 `null_deref` 二进制文件，并明确要求：
1. 必须使用 LLDB MCP 工具进行调试
2. 不能访问源代码文件
3. 只能使用编译后的二进制文件
4. 调试完成后使用 `lldb_getTranscript` 显示调试过程

---

## 第一阶段：探索与问题诊断

### 1.1 初始尝试 - MCP 工具调用失败

**问题现象**：
```bash
Error: No such tool available: mcp__lldb-debugger__lldb_initialize
```

**分析思路**：
- 尝试直接调用 MCP 工具，但工具名称格式不正确
- 检查了 `.mcp.json` 配置文件，发现 MCP 服务器运行在 HTTP 模式
- 确认服务器进程正在运行（PID: 81594）

**关键发现**：
- MCP 服务器配置为 HTTP transport，运行在 `http://127.0.0.1:8765`
- Claude Code 环境中无法直接通过工具调用访问 MCP 服务器
- 需要通过 HTTP API 与 MCP 服务器通信

### 1.2 第一次脚本尝试 - JSON-RPC 协议错误

**创建的脚本**: `debug_with_mcp.py`

**使用的方法**：
```python
payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": tool_name,
        "arguments": arguments
    }
}
response = requests.post(f"{MCP_URL}/mcp/v1", json=payload)
```

**错误信息**：
```
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**问题分析**：
- FastMCP 服务器的 HTTP API 端点不是标准的 JSON-RPC 格式
- `/mcp/v1` 路径返回空响应
- 需要找到正确的 API 调用方式

---

## 第二阶段：解决方案探索

### 2.1 寻找官方客户端实现

**关键发现**：找到了官方 MCP 客户端实现

**文件位置**: `/Users/zhuyanbo/PycharmProjects/lldb-mcp-server/examples/client/mcp_client.py`

**核心代码分析**：
```python
class MCPClient:
    def __init__(self):
        self.base_url = f"http://{host}:{port}"

    def _post(self, path, payload=None):
        # 直接调用 /tools/call 端点
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload or {}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def tools_call(self, name, arguments):
        resp = self._post("/tools/call", {"name": name, "arguments": arguments})
        return resp.get("result")
```

**关键认识**：
- FastMCP HTTP API 使用简化的端点：`/tools/call`
- 不需要 JSON-RPC 包装
- 直接传递 `{"name": "tool_name", "arguments": {...}}`

### 2.2 创建正确的调试脚本

**新脚本**: `debug_null_deref.py`

**改进点**：
1. 导入官方 `mcp_client.py` 模块
2. 使用 `MCPClient` 类进行 API 调用
3. 添加异常处理机制
4. 结构化输出调试信息

---

## 第三阶段：调试执行过程

### 3.1 第一次完整运行 - 部分工具失败

**运行结果**：
- ✅ Session 初始化成功
- ✅ Target 创建成功
- ✅ 程序启动成功（立即崩溃）
- ✅ 事件轮询成功
- ✅ 线程信息获取成功
- ✅ 堆栈跟踪成功
- ❌ `lldb_frames` 调用失败 (HTTP 500 错误)

**错误分析**：
```
Step 7: Get Frame Details
HTTP Error 500: Internal Server Error
```

**修改策略**：
- 为所有可能失败的 MCP 工具调用添加 try-except 异常处理
- 即使某个工具失败，继续执行后续调试步骤
- 确保能够收集到足够的诊断信息

### 3.2 最终成功的调试流程

**完整的 10 步调试流程**：

#### Step 1: 初始化会话
```python
session_id = client.init_session()
# 结果: session_id = "9c141524-fa97-47ea-831d-196eda7c0f43"
```

#### Step 2: 创建目标
```python
client.create_target(session_id, binary_path)
# 结果: {
#   "target": {
#     "file": ".../null_deref",
#     "arch": "x86_64",
#     "triple": "x86_64-apple-macosx15.0.0"
#   }
# }
```

#### Step 3: 启动程序
```python
client.launch(session_id)
# 结果: {
#   "process": {
#     "pid": 88046,
#     "state": "stopped"  # 程序立即崩溃停止
#   }
# }
```

#### Step 4: 轮询事件
```python
client.tools_call("lldb_pollEvents", {"sessionId": session_id})
# 结果: {
#   "events": [{
#     "type": "targetCreated",
#     "file": ".../null_deref"
#   }]
# }
```

#### Step 5: 获取线程信息
```python
client.tools_call("lldb_threads", {"sessionId": session_id})
# 结果: {
#   "threads": [{
#     "id": 4176316,
#     "stopReason": "exception",  # 关键：异常停止
#     "frameCount": 2
#   }]
# }
```

#### Step 6: 获取堆栈跟踪
```python
client.tools_call("lldb_stackTrace", {"sessionId": session_id})
# 结果:
# frame #0: 0x1000004a0 null_deref`main at <unknown>:0
# frame #1: 0x7ff806f65530 dyld`start at <unknown>:0
```

**关键发现**：
- 崩溃发生在 `main` 函数
- 地址：`0x1000004a0`

#### Step 7: 获取帧详情（失败）
```python
client.tools_call("lldb_frames", {"sessionId": session_id})
# 错误: HTTP Error 500
```

**跳过此步骤，继续后续分析**

#### Step 8: 读取寄存器（关键步骤）
```python
client.tools_call("lldb_readRegisters", {"sessionId": session_id})
```

**关键寄存器状态**：
```json
{
  "rax": "0x0000000000000000",  // ← NULL 指针！
  "rip": "0x00000001000004a0",  // 指令指针
  "rsp": "0x00007ff7bfeff6d0",  // 栈指针
  "rbp": "0x00007ff7bfeff6f0"   // 帧指针
}
```

**异常状态寄存器**：
```json
{
  "trapno": "0x0000000e",        // 页面错误
  "err": "0x00000004",           // 错误代码（读访问）
  "faultvaddr": "0x0000000000000000"  // 错误地址：NULL
}
```

#### Step 9: 反汇编崩溃位置（关键步骤）
```python
client.tools_call("lldb_disassemble", {
    "sessionId": session_id,
    "count": 20
})
```

**崩溃指令**：
```asm
0x1000004a0: movl (%rax), %eax  ← 崩溃位置
```

**指令分析**：
- `movl (%rax), %eax`: 从 RAX 指向的地址读取 4 字节数据到 EAX
- RAX = 0x0（NULL）
- 试图从地址 0x0 读取数据导致段错误

**后续指令上下文**：
```asm
0x1000004a2: movl %eax, -0x1c(%rbp)    // 将值存储到栈上
0x1000004a5: movl -0x1c(%rbp), %esi   // 准备参数
0x1000004a8: leaq 0x3b(%rip), %rdi    // 加载字符串地址
0x1000004af: movb $0x0, %al           // 清零 AL
0x1000004b1: callq 0x1000004be        // 调用 printf
```

**推断源代码逻辑**：
```c
int *ptr = NULL;
int value = *ptr;        // ← 0x1000004a0: 崩溃位置
printf("...", value);    // ← 0x1000004b1: 后续调用
```

#### Step 10: 崩溃分析（验证步骤）
```python
client.tools_call("lldb_analyzeCrash", {"sessionId": session_id})
```

**分析结果**：
```json
{
  "analysis": {
    "rating": "Low",
    "confidence": 0.6,
    "crashType": "Unknown",
    "accessType": "write",
    "faultAddress": "0x0",
    "instruction": {
      "address": "0x1000004a0",
      "mnemonic": "movl",
      "operands": "(%rax), %eax"
    },
    "indicators": [{
      "type": "null_dereference",
      "description": "Fault address near null",
      "severity": "low"
    }],
    "recommendation": "Likely null dereference or low impact crash."
  }
}
```

**工具确认**：空指针解引用

#### Step 11: 表达式求值（失败）
```python
client.tools_call("lldb_evaluate", {
    "sessionId": session_id,
    "expression": "ptr"
})
# 错误: HTTP Error 500
```

**原因分析**：
- 调试符号信息可能不完整
- 某些工具在崩溃状态下不可用

#### Step 12: 获取调试记录
```python
client.tools_call("lldb_getTranscript", {"sessionId": session_id})
```

**记录内容**：
```
[2026-01-24 07:43:49] > target create /Users/.../null_deref
[2026-01-24 07:43:49] > process launch
```

---

## 第四阶段：问题诊断结果

### 4.1 Bug 类型
**空指针解引用 (Null Pointer Dereference)**

### 4.2 精确位置
- **函数**: `main`
- **地址**: `0x1000004a0`
- **指令**: `movl (%rax), %eax`

### 4.3 根本原因

**证据链**：
1. ✅ RAX 寄存器 = `0x0` (NULL)
2. ✅ 错误地址 = `0x0` (faultvaddr)
3. ✅ 陷阱号 = `0x0e` (页面错误)
4. ✅ 停止原因 = "exception"
5. ✅ 崩溃分析确认：null_dereference

**程序行为**：
程序试图解引用一个空指针（从地址 0x0 读取数据），触发段错误立即崩溃。

### 4.4 源代码推断

**可能的源代码**：
```c
#include <stdio.h>

int main() {
    int *ptr = NULL;        // 定义空指针
    int value = *ptr;       // ← 崩溃：解引用空指针
    printf("Value: %d\n", value);
    return 0;
}
```

### 4.5 修复方案

**方法 1：添加空指针检查**
```c
int *ptr = NULL;
if (ptr != NULL) {
    int value = *ptr;
    printf("Value: %d\n", value);
} else {
    fprintf(stderr, "Error: ptr is NULL\n");
    return 1;
}
```

**方法 2：正确初始化指针**
```c
int data = 42;
int *ptr = &data;       // 指向有效内存
int value = *ptr;       // 安全
printf("Value: %d\n", value);
```

**方法 3：使用断言进行防御性编程**
```c
#include <assert.h>

int *ptr = NULL;
assert(ptr != NULL);    // 调试版本会在此停止
int value = *ptr;
```

---

## 技术难点与解决方案

### 难点 1: MCP 工具访问方式
**问题**: Claude Code 环境无法直接调用 MCP 工具
**解决**: 通过 HTTP API 间接调用，使用官方 MCPClient

### 难点 2: API 协议理解
**问题**: 初始使用错误的 JSON-RPC 格式
**解决**: 研究官方客户端代码，理解 FastMCP 简化协议

### 难点 3: 部分工具失败
**问题**: `lldb_frames` 和 `lldb_evaluate` 返回 500 错误
**解决**: 添加异常处理，使用其他工具收集足够信息

### 难点 4: 无源代码调试
**问题**: 只有二进制文件，需要纯粹从汇编推断
**解决**: 结合寄存器、反汇编、堆栈跟踪多维度分析

---

## 使用的 MCP 工具清单

| # | 工具名称 | 用途 | 状态 |
|---|---------|------|------|
| 1 | `lldb_initialize` | 创建调试会话 | ✅ 成功 |
| 2 | `lldb_createTarget` | 加载二进制文件 | ✅ 成功 |
| 3 | `lldb_launch` | 启动程序 | ✅ 成功 |
| 4 | `lldb_pollEvents` | 监控进程事件 | ✅ 成功 |
| 5 | `lldb_threads` | 检查线程状态 | ✅ 成功 |
| 6 | `lldb_stackTrace` | 获取调用栈 | ✅ 成功 |
| 7 | `lldb_frames` | 获取帧详情 | ❌ 失败 |
| 8 | `lldb_readRegisters` | 读取寄存器 | ✅ 成功 |
| 9 | `lldb_disassemble` | 反汇编代码 | ✅ 成功 |
| 10 | `lldb_analyzeCrash` | 崩溃分析 | ✅ 成功 |
| 11 | `lldb_evaluate` | 表达式求值 | ❌ 失败 |
| 12 | `lldb_getTranscript` | 获取调试历史 | ✅ 成功 |

**成功率**: 10/12 (83.3%)

---

## 关键经验总结

### 1. MCP 集成策略
- 在 Claude Code 环境中，需要通过脚本间接调用 MCP 服务器
- FastMCP HTTP API 使用简化协议，不是标准 JSON-RPC
- 官方客户端库是最可靠的集成方式

### 2. 调试方法论
- 即使部分工具失败，也能通过其他工具收集足够信息
- 寄存器状态 + 反汇编 + 堆栈跟踪 = 完整的崩溃画面
- 异常处理确保调试流程的鲁棒性

### 3. 无源码调试技巧
- 通过汇编指令序列推断高级语言逻辑
- 利用调用约定理解函数参数和返回值
- 寄存器状态是最直接的真相来源

### 4. 空指针检测特征
- RAX/EAX = 0x0
- faultvaddr = 0x0
- trapno = 0x0e (页面错误)
- 指令模式：`mov (%reg), ...` 其中 reg = 0

---

## 验证与文档

### 生成的文件
1. `debug_with_mcp.py` - 第一次尝试（失败）
2. `debug_null_deref.py` - 最终成功的调试脚本
3. `DEBUG_SESSION_SUMMARY.md` - 本文档

### 下一步建议

#### 验证脚本测试
```bash
cd /Users/zhuyanbo/PycharmProjects/lldb-mcp-server/examples/client/c_test
python3 debug_null_deref.py > debug_output.log 2>&1
```

#### 使用官方验证工具
```bash
python ../../../scripts/verify_mcp_usage.py debug_output.log crash
```

#### 测试其他二进制
- `divide_by_zero` - 除零错误
- `buffer_overflow` - 缓冲区溢出
- `use_after_free` - 释放后使用
- `double_free` - 双重释放

---

## 结论

本次任务成功演示了：
1. ✅ 在无源代码情况下使用 LLDB MCP 工具调试二进制程序
2. ✅ 通过 HTTP API 集成 MCP 服务器
3. ✅ 准确识别空指针解引用 bug
4. ✅ 定位精确的崩溃指令和根本原因
5. ✅ 提供可行的修复方案

**调试效率**: 10 个 MCP 工具调用即可完成完整诊断

**适用场景**:
- 生产环境崩溃分析（无源码）
- 逆向工程
- 安全漏洞分析
- CI/CD 自动化测试
- AI 辅助调试

---

**文档创建时间**: 2026-01-24
**会话 ID**: 9c141524-fa97-47ea-831d-196eda7c0f43
**调试脚本**: `debug_null_deref.py`
