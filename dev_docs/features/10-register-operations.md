# Register Operations Tools (NEW - Phase 1)

## Overview

Register operation tools provide direct access to CPU registers. These tools are essential for low-level debugging, exploit development, and understanding program state at the machine level.

## Tools

### lldb_readRegisters

**Description**: Read all register values for a thread.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| threadId | integer | No | Thread ID (defaults to current thread) |

**Returns**:
```json
{
  "registers": {
    "general": {
      "rax": "0x000000000000002a",
      "rbx": "0x0000000000000000",
      "rcx": "0x00007fff5fbff8c0",
      "rdx": "0x0000000000000001",
      "rsi": "0x00007fff5fbff8d0",
      "rdi": "0x0000000000000001",
      "rbp": "0x00007fff5fbff8b0",
      "rsp": "0x00007fff5fbff880",
      "r8": "0x0000000000000000",
      "r9": "0x0000000000000000",
      "r10": "0x0000000000000000",
      "r11": "0x0000000000000000",
      "r12": "0x0000000000000000",
      "r13": "0x0000000000000000",
      "r14": "0x0000000000000000",
      "r15": "0x0000000000000000",
      "rip": "0x0000000100003f00",
      "rflags": "0x0000000000000206"
    },
    "floating_point": {
      "xmm0": "0x00000000000000000000000000000000",
      "xmm1": "0x00000000000000000000000000000000"
    },
    "segment": {
      "cs": "0x002b",
      "ds": "0x0000",
      "es": "0x0000",
      "fs": "0x0000",
      "gs": "0x0000",
      "ss": "0x0023"
    }
  },
  "threadId": 1
}
```

**Example**:
```python
# Read registers for current thread
result = client.call_tool("lldb_readRegisters", {
    "sessionId": session_id
})

# Print instruction pointer
print(f"RIP: {result['registers']['general']['rip']}")

# Print stack pointer
print(f"RSP: {result['registers']['general']['rsp']}")

# Read registers for specific thread
result = client.call_tool("lldb_readRegisters", {
    "sessionId": session_id,
    "threadId": 2
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2002 | No process running |
| 4001 | Process not stopped |
| 4002 | Thread not found |

**Implementation Notes**:
- Process must be stopped to read registers
- Register availability depends on target architecture
- Some registers may require elevated privileges

---

### lldb_writeRegister

**Description**: Write a value to a specific register.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| name | string | Yes | Register name (e.g., "rax", "rip") |
| value | integer/string | Yes | Value to write (integer or hex string) |

**Returns**:
```json
{
  "register": {
    "name": "rax",
    "oldValue": "0x000000000000002a",
    "newValue": "0x0000000000000064"
  }
}
```

**Example**:
```python
# Write to RAX register
result = client.call_tool("lldb_writeRegister", {
    "sessionId": session_id,
    "name": "rax",
    "value": 100
})

# Write using hex string
result = client.call_tool("lldb_writeRegister", {
    "sessionId": session_id,
    "name": "rbx",
    "value": "0xDEADBEEF"
})

# Modify instruction pointer (be careful!)
result = client.call_tool("lldb_writeRegister", {
    "sessionId": session_id,
    "name": "rip",
    "value": 0x100003f50
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1001 | Invalid parameters - unknown register name |
| 1002 | Session not found |
| 2002 | No process running |
| 4001 | Process not stopped |
| 5003 | Register write failed |

**Implementation Notes**:
- Writing to certain registers (RIP, RSP) can crash the process
- Use with caution in production debugging
- Changes take effect immediately

---

## Register Categories

### General Purpose Registers (x86-64)

| Register | Size | Purpose |
|----------|------|---------|
| RAX | 64-bit | Accumulator, return value |
| RBX | 64-bit | Base register (callee-saved) |
| RCX | 64-bit | Counter, 4th argument |
| RDX | 64-bit | Data, 3rd argument |
| RSI | 64-bit | Source index, 2nd argument |
| RDI | 64-bit | Destination index, 1st argument |
| RBP | 64-bit | Base pointer (callee-saved) |
| RSP | 64-bit | Stack pointer |
| R8-R15 | 64-bit | Additional registers |
| RIP | 64-bit | Instruction pointer |
| RFLAGS | 64-bit | Status flags |

### General Purpose Registers (ARM64)

| Register | Size | Purpose |
|----------|------|---------|
| X0-X7 | 64-bit | Arguments and return value |
| X8 | 64-bit | Indirect result location |
| X9-X15 | 64-bit | Temporary registers |
| X16-X17 | 64-bit | Intra-procedure-call scratch |
| X18 | 64-bit | Platform register |
| X19-X28 | 64-bit | Callee-saved registers |
| X29 (FP) | 64-bit | Frame pointer |
| X30 (LR) | 64-bit | Link register (return address) |
| SP | 64-bit | Stack pointer |
| PC | 64-bit | Program counter |

### Flags Register (x86-64)

| Flag | Bit | Description |
|------|-----|-------------|
| CF | 0 | Carry flag |
| PF | 2 | Parity flag |
| AF | 4 | Auxiliary carry flag |
| ZF | 6 | Zero flag |
| SF | 7 | Sign flag |
| TF | 8 | Trap flag |
| IF | 9 | Interrupt enable flag |
| DF | 10 | Direction flag |
| OF | 11 | Overflow flag |

## Calling Conventions

### System V AMD64 ABI (Linux/macOS x86-64)

```
Arguments: RDI, RSI, RDX, RCX, R8, R9 (then stack)
Return:    RAX (and RDX for 128-bit)
Preserved: RBX, RBP, R12-R15
Scratch:   RAX, RCX, RDX, RSI, RDI, R8-R11
```

### ARM64 (Apple Silicon)

```
Arguments: X0-X7 (then stack)
Return:    X0 (and X1 for 128-bit)
Preserved: X19-X28, SP
Scratch:   X0-X18, X30
```

## Common Use Cases

### Inspecting Function Arguments

```python
# At function entry, read argument registers
result = client.call_tool("lldb_readRegisters", {
    "sessionId": session_id
})

# x86-64: First argument in RDI
arg1 = int(result['registers']['general']['rdi'], 16)
arg2 = int(result['registers']['general']['rsi'], 16)
print(f"Function called with: arg1={arg1}, arg2={arg2}")
```

### Modifying Return Value

```python
# At function return, modify RAX
client.call_tool("lldb_writeRegister", {
    "sessionId": session_id,
    "name": "rax",
    "value": 0  # Force function to return 0
})
```

### Redirecting Execution

```python
# Skip over an instruction by modifying RIP
result = client.call_tool("lldb_readRegisters", {
    "sessionId": session_id
})
current_rip = int(result['registers']['general']['rip'], 16)

# Move RIP past a 5-byte instruction
client.call_tool("lldb_writeRegister", {
    "sessionId": session_id,
    "name": "rip",
    "value": current_rip + 5
})
```

### Checking Flags

```python
result = client.call_tool("lldb_readRegisters", {
    "sessionId": session_id
})
rflags = int(result['registers']['general']['rflags'], 16)

# Check zero flag (bit 6)
zero_flag = (rflags >> 6) & 1
print(f"Zero flag: {zero_flag}")

# Check carry flag (bit 0)
carry_flag = rflags & 1
print(f"Carry flag: {carry_flag}")
```

## Security Considerations

1. **RIP modification**: Can redirect execution to arbitrary code
2. **RSP modification**: Can corrupt stack, cause crashes
3. **Segment registers**: Usually protected by OS
4. **Debug registers**: May be used by other tools

Always verify register modifications in a controlled environment before using in production debugging.
