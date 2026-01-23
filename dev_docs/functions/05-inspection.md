# Inspection Tools

## Overview

Inspection tools allow you to examine the state of a stopped process, including threads, stack frames, variables, and disassembly.

## Tools

### lldb_threads

**Description**: List all threads in the process.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |

**Returns**:
```json
{
  "threads": [
    {
      "id": 1,
      "name": "main",
      "state": "stopped",
      "stopReason": "breakpoint",
      "frameCount": 5
    },
    {
      "id": 2,
      "name": "worker",
      "state": "stopped",
      "stopReason": "none",
      "frameCount": 3
    }
  ]
}
```

**Example**:
```python
result = client.call_tool("lldb_threads", {
    "sessionId": session_id
})
for thread in result["threads"]:
    print(f"Thread {thread['id']}: {thread['name']} - {thread['state']}")
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2002 | No process running |

---

### lldb_frames

**Description**: Get stack frames for a specific thread.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| threadId | integer | Yes | The thread ID |

**Returns**:
```json
{
  "frames": [
    {
      "index": 0,
      "function": "process_data",
      "file": "processor.c",
      "line": 42,
      "address": "0x100003f00"
    },
    {
      "index": 1,
      "function": "main",
      "file": "main.c",
      "line": 25,
      "address": "0x100003e80"
    }
  ]
}
```

**Example**:
```python
result = client.call_tool("lldb_frames", {
    "sessionId": session_id,
    "threadId": 1
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2002 | No process running |
| 4002 | Thread not found |

---

### lldb_stackTrace

**Description**: Get a formatted stack trace for a thread.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| threadId | integer | No | Thread ID (defaults to current thread) |

**Returns**:
```json
{
  "stackTrace": "* frame #0: 0x100003f00 a.out`process_data at processor.c:42\n  frame #1: 0x100003e80 a.out`main at main.c:25"
}
```

**Example**:
```python
result = client.call_tool("lldb_stackTrace", {
    "sessionId": session_id
})
print(result["stackTrace"])
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2002 | No process running |

---

### lldb_selectThread

**Description**: Select a thread as the current thread for operations.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| threadId | integer | Yes | The thread ID to select |

**Returns**:
```json
{
  "thread": {
    "id": 2,
    "name": "worker",
    "selected": true
  }
}
```

**Example**:
```python
result = client.call_tool("lldb_selectThread", {
    "sessionId": session_id,
    "threadId": 2
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 4002 | Thread not found |

---

### lldb_selectFrame

**Description**: Select a stack frame as the current frame for evaluation.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| threadId | integer | Yes | The thread ID |
| frameIndex | integer | Yes | The frame index (0 = top of stack) |

**Returns**:
```json
{
  "frame": {
    "index": 1,
    "function": "main",
    "file": "main.c",
    "line": 25,
    "selected": true
  }
}
```

**Example**:
```python
result = client.call_tool("lldb_selectFrame", {
    "sessionId": session_id,
    "threadId": 1,
    "frameIndex": 1
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 4002 | Thread not found |
| 4003 | Frame not found |

---

### lldb_evaluate

**Description**: Evaluate an expression in the context of the current frame.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| expr | string | Yes | Expression to evaluate |
| frameIndex | integer | No | Frame index for context (defaults to current) |

**Returns**:
```json
{
  "result": {
    "value": "42",
    "type": "int",
    "summary": "42"
  }
}
```

**Example**:
```python
# Evaluate a variable
result = client.call_tool("lldb_evaluate", {
    "sessionId": session_id,
    "expr": "argc"
})

# Evaluate an expression
result = client.call_tool("lldb_evaluate", {
    "sessionId": session_id,
    "expr": "array[0] + array[1]"
})

# Call a function
result = client.call_tool("lldb_evaluate", {
    "sessionId": session_id,
    "expr": "strlen(str)"
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2002 | No process running |
| 4001 | Process not stopped |
| 4004 | Expression evaluation failed |

**Implementation Notes**:
- Expressions are evaluated in the target process
- Function calls in expressions actually execute
- Be careful with expressions that modify state

---

### lldb_disassemble

**Description**: Disassemble instructions at a specified address or current location.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| addr | integer | No | Start address (defaults to current PC) |
| count | integer | No | Number of instructions (default: 10) |

**Returns**:
```json
{
  "instructions": [
    {
      "address": "0x100003f00",
      "opcode": "55",
      "mnemonic": "push",
      "operands": "rbp"
    },
    {
      "address": "0x100003f01",
      "opcode": "4889e5",
      "mnemonic": "mov",
      "operands": "rbp, rsp"
    }
  ]
}
```

**Example**:
```python
# Disassemble at current location
result = client.call_tool("lldb_disassemble", {
    "sessionId": session_id,
    "count": 20
})

# Disassemble at specific address
result = client.call_tool("lldb_disassemble", {
    "sessionId": session_id,
    "addr": 0x100003f00,
    "count": 10
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2002 | No process running |

---

## Stack Frame Navigation

```
Thread 1:
┌─────────────────────────────────┐
│ Frame 0: process_data()         │ ◄── Current frame (top of stack)
│   processor.c:42                │
├─────────────────────────────────┤
│ Frame 1: main()                 │
│   main.c:25                     │
├─────────────────────────────────┤
│ Frame 2: _start()               │
│   (no source)                   │
└─────────────────────────────────┘
```

## Expression Evaluation Context

Expressions are evaluated in the context of the selected frame:
- Local variables from that frame are accessible
- `this`/`self` pointer is available in methods
- Global variables are always accessible

```python
# Select frame 1 (main)
client.call_tool("lldb_selectFrame", {
    "sessionId": session_id,
    "threadId": 1,
    "frameIndex": 1
})

# Now evaluate in main's context
result = client.call_tool("lldb_evaluate", {
    "sessionId": session_id,
    "expr": "argc"  # main's argc parameter
})
```

## Expression Types

| Expression | Description | Example |
|------------|-------------|---------|
| Variable | Read variable value | `count` |
| Member access | Access struct/class member | `obj.field` or `obj->field` |
| Array access | Access array element | `array[5]` |
| Arithmetic | Compute value | `a + b * 2` |
| Function call | Call function in target | `strlen(str)` |
| Cast | Type conversion | `(char*)ptr` |
| Address-of | Get address | `&variable` |
| Dereference | Follow pointer | `*ptr` |
