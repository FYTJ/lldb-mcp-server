# Target Control Tools

## Overview

Target control tools manage the executable target and process lifecycle. These tools handle loading executables, launching processes, attaching to running processes, and sending signals.

## Security Requirements

Some tools require explicit environment variable permissions:
- `LLDB_MCP_ALLOW_LAUNCH=1` - Required for `lldb_launch`
- `LLDB_MCP_ALLOW_ATTACH=1` - Required for `lldb_attach`

## Tools

### lldb_createTarget

**Description**: Load an executable file as a debug target.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| file | string | Yes | Path to the executable file |
| arch | string | No | Target architecture (e.g., "x86_64", "arm64") |
| triple | string | No | Target triple (e.g., "x86_64-apple-macosx") |
| platform | string | No | Platform name (e.g., "host") |

**Returns**:
```json
{
  "target": {
    "file": "/path/to/binary",
    "arch": "arm64",
    "triple": "arm64-apple-macosx14.0.0"
  }
}
```

**Example**:
```python
result = client.call_tool("lldb_createTarget", {
    "sessionId": session_id,
    "file": "/usr/bin/ls"
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2000 | LLDB unavailable |
| 2001 | Failed to create target - invalid file or path |

---

### lldb_launch

**Description**: Launch the target process with specified arguments and environment.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| args | string[] | No | Command-line arguments |
| env | object | No | Environment variables as key-value pairs |
| cwd | string | No | Working directory for the process |
| flags | object | No | Additional launch flags |

**Returns**:
```json
{
  "process": {
    "pid": 12345,
    "state": "stopped"
  }
}
```

**Example**:
```python
result = client.call_tool("lldb_launch", {
    "sessionId": session_id,
    "args": ["-la", "/tmp"],
    "env": {"DEBUG": "1"},
    "cwd": "/home/user"
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2001 | No target loaded |
| 2002 | Launch failed |
| 7001 | Launch not allowed - set LLDB_MCP_ALLOW_LAUNCH=1 |

**Implementation Notes**:
- Requires `LLDB_MCP_ALLOW_LAUNCH=1` environment variable
- Process starts in stopped state at entry point
- Use `lldb_continue` to start execution

---

### lldb_attach

**Description**: Attach to a running process by PID or name.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| pid | integer | No | Process ID to attach to |
| name | string | No | Process name to attach to |

Note: Either `pid` or `name` must be provided.

**Returns**:
```json
{
  "process": {
    "pid": 12345,
    "name": "target_process",
    "state": "stopped"
  }
}
```

**Example**:
```python
# Attach by PID
result = client.call_tool("lldb_attach", {
    "sessionId": session_id,
    "pid": 12345
})

# Attach by name
result = client.call_tool("lldb_attach", {
    "sessionId": session_id,
    "name": "Safari"
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1001 | Invalid parameters - must provide pid or name |
| 1002 | Session not found |
| 2003 | Attach failed - process not found or permission denied |
| 7002 | Attach not allowed - set LLDB_MCP_ALLOW_ATTACH=1 |

**Implementation Notes**:
- Requires `LLDB_MCP_ALLOW_ATTACH=1` environment variable
- May require elevated privileges for system processes
- Process is stopped upon successful attach

---

### lldb_restart

**Description**: Restart the process with the same launch parameters.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |

**Returns**:
```json
{
  "process": {
    "pid": 12346,
    "state": "stopped"
  }
}
```

**Example**:
```python
result = client.call_tool("lldb_restart", {
    "sessionId": session_id
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2001 | No target loaded |
| 2002 | Restart failed |

---

### lldb_signal

**Description**: Send a signal to the running process.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| sig | integer | Yes | Signal number (e.g., 9 for SIGKILL, 15 for SIGTERM) |

**Returns**:
```json
{
  "ok": true,
  "signal": 15
}
```

**Example**:
```python
# Send SIGTERM
result = client.call_tool("lldb_signal", {
    "sessionId": session_id,
    "sig": 15
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2002 | No running process |

**Common Signals**:
| Signal | Number | Description |
|--------|--------|-------------|
| SIGINT | 2 | Interrupt |
| SIGKILL | 9 | Kill (cannot be caught) |
| SIGTERM | 15 | Terminate |
| SIGSTOP | 17 | Stop process |
| SIGCONT | 19 | Continue process |

---

### lldb_loadCore (NEW - Phase 1)

**Description**: Load a core dump file for post-mortem debugging.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| corePath | string | Yes | Path to the core dump file |
| executable | string | Yes | Path to the executable that generated the core |

**Returns**:
```json
{
  "target": {
    "file": "/path/to/binary",
    "core": "/path/to/core"
  },
  "process": {
    "state": "stopped"
  }
}
```

**Example**:
```python
result = client.call_tool("lldb_loadCore", {
    "sessionId": session_id,
    "corePath": "/cores/core.12345",
    "executable": "/usr/bin/crashed_app"
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2001 | Failed to create target |
| 2004 | Failed to load core dump |

**Implementation Notes**:
- Core dump analysis is read-only
- Cannot continue or step - only inspect state
- Useful for crash analysis and security research

---

## Process States

| State | Description |
|-------|-------------|
| stopped | Process is stopped (breakpoint, signal, etc.) |
| running | Process is executing |
| exited | Process has terminated |
| crashed | Process crashed with signal |

## Typical Workflow

```python
# 1. Create target
client.call_tool("lldb_createTarget", {
    "sessionId": session_id,
    "file": "/path/to/binary"
})

# 2. Set breakpoints (see breakpoints.md)

# 3. Launch process
client.call_tool("lldb_launch", {
    "sessionId": session_id,
    "args": ["arg1", "arg2"]
})

# 4. Debug... (continue, step, evaluate, etc.)

# 5. Restart if needed
client.call_tool("lldb_restart", {
    "sessionId": session_id
})
```
