# Advanced Tools

## Overview

Advanced tools provide additional debugging capabilities including event polling, raw LLDB command execution, transcript retrieval, and core dump creation.

## Tools

### lldb_pollEvents

**Description**: Poll for pending events from the debug session.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| limit | integer | No | Maximum events to retrieve (default: 32) |

**Returns**:
```json
{
  "events": [
    {
      "type": "processStateChanged",
      "state": "stopped",
      "timestamp": "2024-01-15T10:30:45.123Z"
    },
    {
      "type": "breakpointHit",
      "breakpointId": 1,
      "threadId": 1,
      "location": {
        "file": "main.c",
        "line": 42
      }
    },
    {
      "type": "stdout",
      "data": "Hello, World!\n"
    }
  ]
}
```

**Example**:
```python
# Poll for events after continuing
client.call_tool("lldb_continue", {"sessionId": session_id})

# Wait a moment, then check for events
import time
time.sleep(0.5)

result = client.call_tool("lldb_pollEvents", {
    "sessionId": session_id,
    "limit": 10
})

for event in result["events"]:
    if event["type"] == "breakpointHit":
        print(f"Hit breakpoint {event['breakpointId']}")
    elif event["type"] == "stdout":
        print(f"Output: {event['data']}")
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |

**Implementation Notes**:
- Events are removed from queue after retrieval
- Non-blocking operation
- Background thread continuously collects events

---

### Event Types

| Type | Description | Fields |
|------|-------------|--------|
| processStateChanged | Process state changed | state |
| breakpointHit | Breakpoint was hit | breakpointId, threadId, location |
| watchpointHit | Watchpoint was triggered | watchpointId, address, accessType |
| stdout | Process wrote to stdout | data |
| stderr | Process wrote to stderr | data |
| targetCreated | Target was loaded | file |
| processExited | Process terminated | exitCode |
| signal | Signal received | signalNumber, signalName |

---

### lldb_command

**Description**: Execute a raw LLDB command string.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| command | string | Yes | LLDB command to execute |

**Returns**:
```json
{
  "output": "Process 12345 stopped\n* thread #1, queue = 'com.apple.main-thread', stop reason = breakpoint 1.1\n    frame #0: 0x0000000100003f00 a.out`main at main.c:10"
}
```

**Example**:
```python
# Execute arbitrary LLDB commands
result = client.call_tool("lldb_command", {
    "sessionId": session_id,
    "command": "bt"  # backtrace
})
print(result["output"])

# Use LLDB expressions
result = client.call_tool("lldb_command", {
    "sessionId": session_id,
    "command": "p/x $rax"  # print register in hex
})

# Memory examination
result = client.call_tool("lldb_command", {
    "sessionId": session_id,
    "command": "x/16xb $rsp"  # examine 16 bytes at stack pointer
})
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2000 | LLDB unavailable |

**Implementation Notes**:
- Escape hatch for commands not exposed as tools
- Output is captured as a string
- Some commands may have side effects
- Commands are logged to transcript

---

### Common LLDB Commands

| Command | Description |
|---------|-------------|
| `bt` | Print backtrace |
| `bt all` | Print backtrace for all threads |
| `p <expr>` | Print expression value |
| `p/x <expr>` | Print in hexadecimal |
| `x/<n><fmt> <addr>` | Examine memory |
| `register read` | Show all registers |
| `register read rax rbx` | Show specific registers |
| `image list` | List loaded images/modules |
| `image lookup -a <addr>` | Look up address |
| `disassemble -n <func>` | Disassemble function |
| `memory read <addr>` | Read memory |
| `type lookup <type>` | Show type information |

---

### lldb_getTranscript

**Description**: Get the transcript log of all commands and outputs for the session.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |

**Returns**:
```json
{
  "transcript": "[2024-01-15 10:30:00] > target create /path/to/binary\n[2024-01-15 10:30:00] Current executable set to '/path/to/binary' (arm64).\n[2024-01-15 10:30:05] > breakpoint set -n main\n[2024-01-15 10:30:05] Breakpoint 1: where = a.out`main, address = 0x0000000100003f00\n..."
}
```

**Example**:
```python
result = client.call_tool("lldb_getTranscript", {
    "sessionId": session_id
})
print(result["transcript"])

# Save to file
with open("debug_session.log", "w") as f:
    f.write(result["transcript"])
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |

**Implementation Notes**:
- Includes all commands and their outputs
- Timestamped entries
- Useful for debugging session review
- Can be used for reproducibility

---

### lldb_createCoredump (NEW - Phase 2)

**Description**: Create a core dump of the current process state.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| path | string | Yes | Path to save the core dump file |

**Returns**:
```json
{
  "path": "/tmp/crash.core",
  "size": 104857600
}
```

**Example**:
```python
result = client.call_tool("lldb_createCoredump", {
    "sessionId": session_id,
    "path": "/tmp/debug_core"
})
print(f"Core dump saved: {result['path']} ({result['size']} bytes)")
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2002 | No process running |
| 5002 | Failed to create core dump |

**Implementation Notes**:
- Process must be stopped
- Requires sufficient disk space
- Core dump can be loaded later with `lldb_loadCore`

---

## Event Polling Pattern

The server uses a polling architecture rather than callbacks:

```
┌─────────────────────────────────────────────────────────────┐
│                     Background Thread                       │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │ LLDB Listener   │───▶│  Event Queue    │                 │
│  │ WaitForEvent(1) │    │  (deque)        │                 │
│  └─────────────────┘    └────────┬────────┘                 │
│                                  │                          │
└──────────────────────────────────┼──────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────┐
│                      Client                                 │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │ pollEvents()    │───▶│  Process Events │                 │
│  │ (non-blocking)  │    │                 │                 │
│  └─────────────────┘    └─────────────────┘                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Typical Event Loop

```python
import time

def debug_loop(session_id):
    while True:
        # Poll for events
        result = client.call_tool("lldb_pollEvents", {
            "sessionId": session_id,
            "limit": 32
        })

        for event in result["events"]:
            if event["type"] == "processExited":
                print(f"Process exited with code {event['exitCode']}")
                return
            elif event["type"] == "breakpointHit":
                handle_breakpoint(event)
            elif event["type"] == "stdout":
                print(event["data"], end="")
            elif event["type"] == "signal":
                handle_signal(event)

        # Small delay to avoid busy-waiting
        time.sleep(0.1)
```
