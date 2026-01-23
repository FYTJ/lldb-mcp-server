# Watchpoint Tools

## Overview

Watchpoint tools monitor memory locations for access. When the watched memory is read or written, execution stops automatically. Watchpoints are essential for tracking down memory corruption bugs and understanding data flow.

## Tools

### lldb_setWatchpoint

**Description**: Set a watchpoint on a memory location.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| addr | integer | Yes | Memory address to watch |
| size | integer | Yes | Number of bytes to watch (1, 2, 4, or 8) |
| read | boolean | No | Trigger on read access (default: false) |
| write | boolean | No | Trigger on write access (default: true) |

**Returns**:
```json
{
  "watchpoint": {
    "id": 1,
    "address": "0x7fff5fbff8c0",
    "size": 4,
    "read": false,
    "write": true,
    "enabled": true
  }
}
```

**Example**:
```python
# Watch for writes to a variable
result = client.call_tool("lldb_evaluate", {
    "sessionId": session_id,
    "expr": "&counter"
})
addr = int(result["result"]["value"], 16)

result = client.call_tool("lldb_setWatchpoint", {
    "sessionId": session_id,
    "addr": addr,
    "size": 4,
    "write": True
})

# Watch for both reads and writes
result = client.call_tool("lldb_setWatchpoint", {
    "sessionId": session_id,
    "addr": 0x7fff5fbff8c0,
    "size": 8,
    "read": True,
    "write": True
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1001 | Invalid parameters - size must be 1, 2, 4, or 8 |
| 1002 | Session not found |
| 2002 | No process running |
| 3002 | Failed to set watchpoint - hardware limit reached |

**Implementation Notes**:
- Uses hardware debug registers (limited quantity, typically 4)
- Size must be a power of 2 (1, 2, 4, or 8 bytes)
- Address should be naturally aligned for best performance

---

### lldb_deleteWatchpoint

**Description**: Delete a watchpoint by its ID.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| watchpointId | integer | Yes | The watchpoint ID to delete |

**Returns**:
```json
{
  "ok": true
}
```

**Example**:
```python
result = client.call_tool("lldb_deleteWatchpoint", {
    "sessionId": session_id,
    "watchpointId": 1
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 3002 | Watchpoint not found |

---

### lldb_listWatchpoints

**Description**: List all watchpoints in the session.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |

**Returns**:
```json
{
  "watchpoints": [
    {
      "id": 1,
      "address": "0x7fff5fbff8c0",
      "size": 4,
      "read": false,
      "write": true,
      "enabled": true,
      "hitCount": 3
    },
    {
      "id": 2,
      "address": "0x7fff5fbff8d0",
      "size": 8,
      "read": true,
      "write": true,
      "enabled": true,
      "hitCount": 0
    }
  ]
}
```

**Example**:
```python
result = client.call_tool("lldb_listWatchpoints", {
    "sessionId": session_id
})
for wp in result["watchpoints"]:
    print(f"Watchpoint {wp['id']} at {wp['address']}: hits={wp['hitCount']}")
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |

---

## Watchpoint Types

### Write Watchpoint (Default)
Triggers when the memory location is written to.

```python
client.call_tool("lldb_setWatchpoint", {
    "sessionId": session_id,
    "addr": addr,
    "size": 4,
    "write": True
})
```

### Read Watchpoint
Triggers when the memory location is read.

```python
client.call_tool("lldb_setWatchpoint", {
    "sessionId": session_id,
    "addr": addr,
    "size": 4,
    "read": True
})
```

### Access Watchpoint
Triggers on both read and write access.

```python
client.call_tool("lldb_setWatchpoint", {
    "sessionId": session_id,
    "addr": addr,
    "size": 4,
    "read": True,
    "write": True
})
```

## Hardware Limitations

Watchpoints use CPU hardware debug registers:

| Architecture | Max Watchpoints | Max Size |
|--------------|-----------------|----------|
| x86/x64 | 4 | 8 bytes |
| ARM64 | 4-16 | 8 bytes |
| ARM32 | 2 | 4 bytes |

When the limit is reached, `lldb_setWatchpoint` will fail with error 3002.

## Events

When a watchpoint triggers, a `watchpointHit` event is generated:

```json
{
  "type": "watchpointHit",
  "watchpointId": 1,
  "address": "0x7fff5fbff8c0",
  "accessType": "write",
  "oldValue": "0x0000002a",
  "newValue": "0x0000002b",
  "threadId": 1
}
```

## Use Cases

### Finding Memory Corruption

```python
# Watch a variable that's being corrupted
addr = get_variable_address("important_data")
client.call_tool("lldb_setWatchpoint", {
    "sessionId": session_id,
    "addr": addr,
    "size": 8,
    "write": True
})

# Continue and wait for corruption
client.call_tool("lldb_continue", {"sessionId": session_id})
events = client.call_tool("lldb_pollEvents", {"sessionId": session_id})
# Watchpoint hit shows exactly where memory was modified
```

### Tracking Object Access

```python
# Watch when an object field is read
client.call_tool("lldb_setWatchpoint", {
    "sessionId": session_id,
    "addr": obj_addr + field_offset,
    "size": 4,
    "read": True
})
```

### Monitoring Global State

```python
# Watch a global configuration variable
result = client.call_tool("lldb_evaluate", {
    "sessionId": session_id,
    "expr": "&g_config.debug_level"
})
addr = int(result["result"]["value"], 16)

client.call_tool("lldb_setWatchpoint", {
    "sessionId": session_id,
    "addr": addr,
    "size": 4,
    "read": True,
    "write": True
})
```

## Alignment Requirements

For best performance and reliability, align watchpoint addresses:

| Size | Alignment |
|------|-----------|
| 1 byte | Any |
| 2 bytes | 2-byte aligned |
| 4 bytes | 4-byte aligned |
| 8 bytes | 8-byte aligned |

```python
# Good: aligned address
addr = 0x7fff5fbff8c0  # 8-byte aligned
client.call_tool("lldb_setWatchpoint", {
    "sessionId": session_id,
    "addr": addr,
    "size": 8,
    "write": True
})

# May cause issues: unaligned address
addr = 0x7fff5fbff8c3  # Not aligned
# Hardware may not support this, or may watch a larger region
```

## Comparison: Breakpoints vs Watchpoints

| Feature | Breakpoint | Watchpoint |
|---------|------------|------------|
| Triggers on | Code execution | Memory access |
| Uses | Software interrupt | Hardware debug registers |
| Quantity limit | Essentially unlimited | 4 (typical) |
| Use case | Stop at code locations | Monitor data changes |
