# Execution Control Tools

## Overview

Execution control tools manage the flow of program execution. They allow you to continue, pause, and step through code at various granularities.

## Tools

### lldb_continue

**Description**: Continue process execution until the next breakpoint or program exit.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |

**Returns**:
```json
{
  "process": {
    "state": "running"
  }
}
```

**Example**:
```python
result = client.call_tool("lldb_continue", {
    "sessionId": session_id
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2002 | No process running |

**Implementation Notes**:
- Returns immediately while process runs in background
- Use `lldb_pollEvents` to detect when process stops
- Process will stop at breakpoints, watchpoints, or signals

---

### lldb_pause

**Description**: Pause (interrupt) the running process.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |

**Returns**:
```json
{
  "process": {
    "state": "stopped"
  }
}
```

**Example**:
```python
result = client.call_tool("lldb_pause", {
    "sessionId": session_id
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2002 | No process running |

**Implementation Notes**:
- Sends SIGSTOP to the process
- All threads are stopped
- Useful for debugging infinite loops

---

### lldb_stepIn

**Description**: Step into the next source line, entering function calls.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |

**Returns**:
```json
{
  "thread": {
    "id": 1,
    "stopReason": "step"
  },
  "frame": {
    "index": 0,
    "function": "helper_function",
    "file": "helper.c",
    "line": 15
  }
}
```

**Example**:
```python
result = client.call_tool("lldb_stepIn", {
    "sessionId": session_id
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2002 | No process running |
| 4001 | Process not stopped |

**Implementation Notes**:
- Steps into function calls
- Requires source-level debug info for best results
- May step into library code

---

### lldb_stepOver

**Description**: Step over the next source line, executing function calls without entering them.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |

**Returns**:
```json
{
  "thread": {
    "id": 1,
    "stopReason": "step"
  },
  "frame": {
    "index": 0,
    "function": "main",
    "file": "main.c",
    "line": 26
  }
}
```

**Example**:
```python
result = client.call_tool("lldb_stepOver", {
    "sessionId": session_id
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2002 | No process running |
| 4001 | Process not stopped |

**Implementation Notes**:
- Executes entire function calls without stopping inside
- Stops at next line in current function
- Preferred for navigating through code quickly

---

### lldb_stepOut

**Description**: Step out of the current function, returning to the caller.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |

**Returns**:
```json
{
  "thread": {
    "id": 1,
    "stopReason": "step"
  },
  "frame": {
    "index": 0,
    "function": "main",
    "file": "main.c",
    "line": 42
  }
}
```

**Example**:
```python
result = client.call_tool("lldb_stepOut", {
    "sessionId": session_id
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2002 | No process running |
| 4001 | Process not stopped |

**Implementation Notes**:
- Continues until current function returns
- Stops at the return site in the caller
- Useful for exiting deeply nested calls

---

## Execution Flow Diagram

```
                    ┌─────────────┐
                    │   Stopped   │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │  stepIn    │  │  stepOver  │  │  stepOut   │
    └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
          │               │               │
          └───────────────┼───────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │   Stopped   │
                   │ (next line) │
                   └──────┬──────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  continue   │
                   └──────┬──────┘
                          │
                          ▼
                   ┌─────────────┐
                   │   Running   │◄──────┐
                   └──────┬──────┘       │
                          │              │
                   ┌──────┴──────┐       │
                   ▼             ▼       │
            ┌───────────┐ ┌───────────┐  │
            │ Breakpoint│ │   pause   │──┘
            │    hit    │ └───────────┘
            └───────────┘
```

## Step Comparison

| Operation | Enters Functions | Stops At |
|-----------|-----------------|----------|
| stepIn | Yes | First line of called function |
| stepOver | No | Next line in current function |
| stepOut | N/A | Return site in caller |

## Threading Considerations

- Step operations affect only the current thread
- Other threads may continue running (depending on LLDB settings)
- Use `lldb_selectThread` to change the current thread before stepping

## Stop Reasons

After stepping, the `stopReason` field indicates why execution stopped:

| Reason | Description |
|--------|-------------|
| step | Step completed normally |
| breakpoint | Hit a breakpoint during step |
| watchpoint | Watchpoint triggered |
| signal | Signal received |
| exception | Exception occurred |

## Example Workflow

```python
# Hit a breakpoint
events = client.call_tool("lldb_pollEvents", {"sessionId": session_id})
# events contains breakpointHit

# Step into the function call
result = client.call_tool("lldb_stepIn", {"sessionId": session_id})
# Now inside the called function

# Step over a few lines
client.call_tool("lldb_stepOver", {"sessionId": session_id})
client.call_tool("lldb_stepOver", {"sessionId": session_id})

# Step out back to caller
client.call_tool("lldb_stepOut", {"sessionId": session_id})

# Continue until next breakpoint
client.call_tool("lldb_continue", {"sessionId": session_id})
```
