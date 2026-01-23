# Breakpoint Tools

## Overview

Breakpoint tools manage code breakpoints that pause execution at specific locations. Breakpoints can be set by file/line, function symbol, or memory address.

## Tools

### lldb_setBreakpoint

**Description**: Set a breakpoint at a specified location.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| file | string | No | Source file path (requires line) |
| line | integer | No | Line number in the file (requires file) |
| symbol | string | No | Function or symbol name |
| address | integer | No | Memory address (hex as integer) |

Note: Provide one of: `file`+`line`, `symbol`, or `address`.

**Returns**:
```json
{
  "breakpoint": {
    "id": 1,
    "locations": [
      {
        "address": "0x100003f00",
        "file": "main.c",
        "line": 10
      }
    ],
    "enabled": true
  }
}
```

**Example**:
```python
# By file and line
result = client.call_tool("lldb_setBreakpoint", {
    "sessionId": session_id,
    "file": "main.c",
    "line": 25
})

# By symbol
result = client.call_tool("lldb_setBreakpoint", {
    "sessionId": session_id,
    "symbol": "main"
})

# By address
result = client.call_tool("lldb_setBreakpoint", {
    "sessionId": session_id,
    "address": 0x100003f00
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1001 | Invalid parameters - must provide location |
| 1002 | Session not found |
| 2001 | No target loaded |
| 3001 | Failed to set breakpoint |

**Implementation Notes**:
- Symbolic breakpoints may resolve to multiple locations
- Address breakpoints require knowing the load address
- File/line breakpoints require debug symbols

---

### lldb_deleteBreakpoint

**Description**: Delete a breakpoint by its ID.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| breakpointId | integer | Yes | The breakpoint ID to delete |

**Returns**:
```json
{
  "ok": true
}
```

**Example**:
```python
result = client.call_tool("lldb_deleteBreakpoint", {
    "sessionId": session_id,
    "breakpointId": 1
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 3001 | Breakpoint not found |

---

### lldb_listBreakpoints

**Description**: List all breakpoints in the session.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |

**Returns**:
```json
{
  "breakpoints": [
    {
      "id": 1,
      "enabled": true,
      "hitCount": 3,
      "ignoreCount": 0,
      "condition": null,
      "locations": [
        {
          "address": "0x100003f00",
          "file": "main.c",
          "line": 10,
          "resolved": true
        }
      ]
    },
    {
      "id": 2,
      "enabled": false,
      "hitCount": 0,
      "ignoreCount": 5,
      "condition": "i > 10",
      "locations": [
        {
          "address": "0x100003f50",
          "symbol": "process_data",
          "resolved": true
        }
      ]
    }
  ]
}
```

**Example**:
```python
result = client.call_tool("lldb_listBreakpoints", {
    "sessionId": session_id
})
for bp in result["breakpoints"]:
    print(f"Breakpoint {bp['id']}: enabled={bp['enabled']}, hits={bp['hitCount']}")
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |

---

### lldb_updateBreakpoint

**Description**: Update breakpoint properties.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| breakpointId | integer | Yes | The breakpoint ID to update |
| enabled | boolean | No | Enable or disable the breakpoint |
| ignoreCount | integer | No | Number of hits to ignore before stopping |
| condition | string | No | Conditional expression to evaluate |

**Returns**:
```json
{
  "breakpoint": {
    "id": 1,
    "enabled": false,
    "ignoreCount": 10,
    "condition": "x > 100"
  }
}
```

**Example**:
```python
# Disable a breakpoint
result = client.call_tool("lldb_updateBreakpoint", {
    "sessionId": session_id,
    "breakpointId": 1,
    "enabled": False
})

# Add a condition
result = client.call_tool("lldb_updateBreakpoint", {
    "sessionId": session_id,
    "breakpointId": 1,
    "condition": "count > 100"
})

# Set ignore count
result = client.call_tool("lldb_updateBreakpoint", {
    "sessionId": session_id,
    "breakpointId": 1,
    "ignoreCount": 5
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 3001 | Breakpoint not found |

---

## Breakpoint Types

### Source Line Breakpoint
Set at a specific line in a source file. Requires debug symbols (`-g` flag during compilation).

```python
client.call_tool("lldb_setBreakpoint", {
    "sessionId": session_id,
    "file": "main.c",
    "line": 42
})
```

### Symbolic Breakpoint
Set at a function or symbol name. May resolve to multiple addresses (overloaded functions, inlined code).

```python
client.call_tool("lldb_setBreakpoint", {
    "sessionId": session_id,
    "symbol": "malloc"
})
```

### Address Breakpoint
Set at an exact memory address. Useful when symbols are not available.

```python
client.call_tool("lldb_setBreakpoint", {
    "sessionId": session_id,
    "address": 0x7fff12345678
})
```

## Conditional Breakpoints

Conditions are expressions evaluated when the breakpoint is hit. The breakpoint only stops if the condition is true.

```python
# Stop only when i equals 100
client.call_tool("lldb_setBreakpoint", {
    "sessionId": session_id,
    "symbol": "process_item"
})
client.call_tool("lldb_updateBreakpoint", {
    "sessionId": session_id,
    "breakpointId": 1,
    "condition": "i == 100"
})
```

## Ignore Count

Skip the first N hits before stopping.

```python
# Skip first 10 hits
client.call_tool("lldb_updateBreakpoint", {
    "sessionId": session_id,
    "breakpointId": 1,
    "ignoreCount": 10
})
```

## Events

When a breakpoint is hit, a `breakpointHit` event is generated and can be retrieved via `lldb_pollEvents`:

```json
{
  "type": "breakpointHit",
  "breakpointId": 1,
  "threadId": 1,
  "location": {
    "file": "main.c",
    "line": 42
  }
}
```
