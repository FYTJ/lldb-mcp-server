# Session Management Tools

## Overview

Session management tools handle the lifecycle of LLDB debug sessions. Each session represents an isolated debugging environment with its own debugger instance, event queue, and state.

## Tools

### lldb_initialize

**Description**: Create a new LLDB debug session with an isolated debugger instance.

**Parameters**: None

**Returns**:
```json
{
  "sessionId": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Example**:
```python
result = client.call_tool("lldb_initialize", {})
session_id = result["sessionId"]
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 2000 | LLDB unavailable - LLDB module could not be imported |

**Implementation Notes**:
- Creates a new `lldb.SBDebugger` instance
- Spawns a background thread for event collection
- Initializes an empty event deque for `pollEvents`
- Sets debugger to synchronous mode by default

---

### lldb_terminate

**Description**: Terminate an active debug session and release all resources.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID to terminate |

**Returns**:
```json
{
  "ok": true
}
```

**Example**:
```python
result = client.call_tool("lldb_terminate", {
    "sessionId": "550e8400-e29b-41d4-a716-446655440000"
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |

**Implementation Notes**:
- Destroys the `SBDebugger` instance
- Stops the background event thread
- Clears the event queue
- Removes session from the session registry

---

### lldb_listSessions

**Description**: List all active debug sessions on the server.

**Parameters**: None

**Returns**:
```json
{
  "sessions": [
    "550e8400-e29b-41d4-a716-446655440000",
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
  ]
}
```

**Example**:
```python
result = client.call_tool("lldb_listSessions", {})
for session_id in result["sessions"]:
    print(f"Active session: {session_id}")
```

**Error Codes**: None - always succeeds

**Implementation Notes**:
- Thread-safe operation using RLock
- Returns empty array if no sessions exist
- Does not include any session state information (use other tools for that)

---

## Session Lifecycle

```
┌─────────────────┐
│ lldb_initialize │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Active Session  │ ◄── lldb_listSessions
└────────┬────────┘
         │
         │  (debugging operations)
         │
         ▼
┌─────────────────┐
│ lldb_terminate  │
└─────────────────┘
```

## Thread Safety

All session operations are protected by a reentrant lock (`threading.RLock`). This allows:
- Safe concurrent access from multiple clients
- Nested lock acquisition within the same thread
- Atomic session state modifications

## Best Practices

1. **Always terminate sessions**: Call `lldb_terminate` when done to free resources
2. **Store session IDs**: Keep track of session IDs for all subsequent operations
3. **Handle session not found**: Be prepared for `1002` errors if sessions expire
4. **One session per target**: Use separate sessions for different debug targets
