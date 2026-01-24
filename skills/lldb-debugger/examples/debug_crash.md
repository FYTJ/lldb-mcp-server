# Example: Debug a Crash

This example demonstrates how to debug a crashing program using the LLDB MCP Server.

## Scenario

We have a program that crashes with a segmentation fault. We need to find the root cause.

## Step-by-Step Debugging

### 1. Initialize Debug Session

```
Tool: lldb_initialize
Arguments: {}

Response:
{
  "sessionId": "abc123-def456",
  "message": "Session created"
}
```

### 2. Load the Target Binary

```
Tool: lldb_createTarget
Arguments: {
  "sessionId": "abc123-def456",
  "file": "/path/to/examples/client/c_test/null_deref/null_deref"
}

Response:
{
  "target": {
    "file": "null_deref",
    "arch": "x86_64"
  }
}
```

### 3. Launch the Process

```
Tool: lldb_launch
Arguments: {
  "sessionId": "abc123-def456",
  "args": [],
  "env": {}
}

Response:
{
  "process": {
    "pid": 12345,
    "state": "stopped"
  }
}
```

### 4. Continue Until Crash

```
Tool: lldb_continue
Arguments: {
  "sessionId": "abc123-def456"
}
```

### 5. Poll for Events

```
Tool: lldb_pollEvents
Arguments: {
  "sessionId": "abc123-def456",
  "limit": 10
}

Response:
{
  "events": [
    {
      "type": "processStateChanged",
      "state": "stopped",
      "reason": "signal",
      "signal": "SIGSEGV"
    }
  ]
}
```

### 6. Analyze the Crash

```
Tool: lldb_analyzeCrash
Arguments: {
  "sessionId": "abc123-def456"
}

Response:
{
  "crash": {
    "type": "SIGSEGV",
    "address": "0x0000000000000000",
    "description": "Null pointer dereference",
    "thread": 1,
    "frame": {
      "function": "main",
      "file": "null_deref.c",
      "line": 17
    }
  },
  "exploitability": "low"
}
```

### 7. Get Stack Trace

```
Tool: lldb_stackTrace
Arguments: {
  "sessionId": "abc123-def456"
}

Response:
{
  "frames": [
    {
      "index": 0,
      "function": "main",
      "file": "null_deref.c",
      "line": 17,
      "address": "0x100003f50"
    }
  ]
}
```

### 8. Examine Variables

```
Tool: lldb_evaluate
Arguments: {
  "sessionId": "abc123-def456",
  "expression": "ptr"
}

Response:
{
  "result": {
    "value": "0x0000000000000000",
    "type": "int *",
    "summary": "NULL"
  }
}
```

### 9. Read Registers

```
Tool: lldb_readRegisters
Arguments: {
  "sessionId": "abc123-def456"
}

Response:
{
  "registers": {
    "rax": "0x0000000000000000",
    "rbx": "0x0000000000000000",
    "rcx": "0x0000000000000001",
    ...
  }
}
```

### 10. Terminate Session

```
Tool: lldb_terminate
Arguments: {
  "sessionId": "abc123-def456"
}
```

## Conclusion

The debugging session revealed:

1. **Crash Type**: Segmentation Fault (SIGSEGV)
2. **Crash Location**: `null_deref.c:17` in `main()` function
3. **Root Cause**: Null pointer dereference - `ptr` is NULL (0x0) and is being dereferenced
4. **Fix**: Add null check before dereferencing `ptr`

```c
// Before (buggy)
int value = *ptr;

// After (fixed)
if (ptr != NULL) {
    int value = *ptr;
} else {
    // Handle null case
}
```
