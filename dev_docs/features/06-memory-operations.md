# Memory Operations Tools

## Overview

Memory operation tools allow direct reading and writing of process memory. These are essential for low-level debugging, security research, and binary analysis.

## Tools

### lldb_readMemory

**Description**: Read raw bytes from process memory.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| addr | integer | Yes | Starting memory address |
| size | integer | Yes | Number of bytes to read |

**Returns**:
```json
{
  "address": "0x7fff5fbff8c0",
  "size": 16,
  "bytes": "48656c6c6f20576f726c6421000000",
  "ascii": "Hello World!..."
}
```

**Example**:
```python
# Read 64 bytes from stack
result = client.call_tool("lldb_readMemory", {
    "sessionId": session_id,
    "addr": 0x7fff5fbff8c0,
    "size": 64
})

# Parse the hex bytes
hex_data = result["bytes"]
raw_bytes = bytes.fromhex(hex_data)
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2002 | No process running |
| 5001 | Memory read failed - invalid address or permission denied |

**Implementation Notes**:
- Returns bytes as hexadecimal string
- ASCII representation shows printable characters, `.` for non-printable
- Large reads may be slow; consider chunking

---

### lldb_writeMemory

**Description**: Write raw bytes to process memory.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| addr | integer | Yes | Starting memory address |
| bytes | string | Yes | Hex-encoded bytes to write |

**Returns**:
```json
{
  "address": "0x7fff5fbff8c0",
  "bytesWritten": 4
}
```

**Example**:
```python
# Write 4 bytes (0xDEADBEEF)
result = client.call_tool("lldb_writeMemory", {
    "sessionId": session_id,
    "addr": 0x7fff5fbff8c0,
    "bytes": "DEADBEEF"
})

# Write a string
text = "Hello".encode().hex()
result = client.call_tool("lldb_writeMemory", {
    "sessionId": session_id,
    "addr": 0x7fff5fbff8c0,
    "bytes": text
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1001 | Invalid parameters - bytes must be valid hex |
| 1002 | Session not found |
| 2002 | No process running |
| 5001 | Memory write failed - invalid address or permission denied |

**Implementation Notes**:
- Bytes must be hex-encoded (e.g., "DEADBEEF" for 4 bytes)
- Writing to read-only memory will fail
- Be careful when modifying code sections

---

## Memory Regions

Process memory is divided into regions with different permissions:

| Region | Permissions | Contents |
|--------|-------------|----------|
| .text | r-x | Executable code |
| .data | rw- | Initialized global data |
| .bss | rw- | Uninitialized global data |
| heap | rw- | Dynamically allocated memory |
| stack | rw- | Local variables, return addresses |
| shared libs | r-x/rw- | Library code and data |

## Common Use Cases

### Inspecting String Data

```python
# Get address of a string variable
result = client.call_tool("lldb_evaluate", {
    "sessionId": session_id,
    "expr": "(void*)str"
})
str_addr = int(result["result"]["value"], 16)

# Read string bytes
result = client.call_tool("lldb_readMemory", {
    "sessionId": session_id,
    "addr": str_addr,
    "size": 256
})
print(result["ascii"])
```

### Examining Stack Contents

```python
# Get stack pointer
result = client.call_tool("lldb_evaluate", {
    "sessionId": session_id,
    "expr": "$rsp"
})
rsp = int(result["result"]["value"], 16)

# Read 128 bytes from stack
result = client.call_tool("lldb_readMemory", {
    "sessionId": session_id,
    "addr": rsp,
    "size": 128
})
```

### Patching Instructions

```python
# Replace instruction with NOP (0x90 on x86)
result = client.call_tool("lldb_writeMemory", {
    "sessionId": session_id,
    "addr": 0x100003f00,
    "bytes": "9090909090"  # 5 NOPs
})
```

### Modifying Variables

```python
# Get address of a variable
result = client.call_tool("lldb_evaluate", {
    "sessionId": session_id,
    "expr": "&counter"
})
addr = int(result["result"]["value"], 16)

# Write new value (42 as 4-byte little-endian integer)
import struct
value = struct.pack("<I", 42).hex()
result = client.call_tool("lldb_writeMemory", {
    "sessionId": session_id,
    "addr": addr,
    "bytes": value
})
```

## Memory Layout Visualization

```
High Address
┌─────────────────────────┐
│       Stack             │ ← Grows downward
│         ↓               │
├─────────────────────────┤
│                         │
│    (unmapped space)     │
│                         │
├─────────────────────────┤
│         ↑               │
│       Heap              │ ← Grows upward
├─────────────────────────┤
│       .bss              │ ← Uninitialized data
├─────────────────────────┤
│       .data             │ ← Initialized data
├─────────────────────────┤
│       .text             │ ← Code (read-only)
└─────────────────────────┘
Low Address
```

## Security Considerations

1. **ASLR**: Address Space Layout Randomization means addresses change each run
2. **Write-protect**: Code sections are typically read-only
3. **Stack canaries**: Writing to stack may trigger protection mechanisms
4. **DEP/NX**: Non-executable memory prevents code execution in data regions

## Endianness

When reading/writing multi-byte values, consider endianness:

```python
import struct

# Little-endian (x86/x64/ARM)
value = struct.pack("<I", 0x12345678).hex()  # "78563412"

# Big-endian
value = struct.pack(">I", 0x12345678).hex()  # "12345678"
```
