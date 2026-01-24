# Test C Programs for LLDB MCP Server

This directory contains test C programs with intentional bugs for testing AI-driven debugging capabilities.

## Programs

| Program | Bug Type | Description |
|---------|----------|-------------|
| `null_deref` | Crash | Null pointer dereference |
| `buffer_overflow` | Memory Corruption | Stack buffer overflow via strcpy |
| `use_after_free` | Memory Corruption | Accessing memory after free |
| `infinite_loop` | Logic Bug | Loop that never terminates |
| `divide_by_zero` | Crash | Integer division by zero |
| `stack_overflow` | Crash | Infinite recursion |
| `format_string` | Security | Format string vulnerability |
| `double_free` | Memory Corruption | Freeing same memory twice |

## Building

Build all test programs with debug symbols:

```bash
chmod +x build_all.sh
./build_all.sh
```

Or build individually:

```bash
cd null_deref
cc -g -O0 -Wall -Wextra -o null_deref null_deref.c
```

## Usage with LLDB MCP Server

### 1. Start the MCP server

```bash
LLDB_MCP_ALLOW_LAUNCH=1 \
  .venv/bin/python -m lldb_mcp_server.fastmcp_server \
  --transport http --host 127.0.0.1 --port 8765
```

### 2. Debug a test program

Example debugging workflow for `null_deref`:

```python
# Initialize session
session = client.call_tool("lldb_initialize", {})
session_id = session["sessionId"]

# Load the target binary
client.call_tool("lldb_createTarget", {
    "sessionId": session_id,
    "file": "/path/to/examples/client/c_test/null_deref/null_deref"
})

# Launch and let it crash
client.call_tool("lldb_launch", {
    "sessionId": session_id,
    "args": []
})

# Analyze the crash
crash_info = client.call_tool("lldb_analyzeCrash", {
    "sessionId": session_id
})
print(crash_info)  # Should show null pointer dereference

# Get stack trace
stack = client.call_tool("lldb_stackTrace", {
    "sessionId": session_id
})
print(stack)  # Should show crash location
```

## Expected AI Debugging Results

### null_deref
- **Expected Finding**: Null pointer dereference at line 17
- **Root Cause**: `ptr` initialized to NULL and dereferenced without check

### buffer_overflow
- **Expected Finding**: Buffer overflow at line 17 (strcpy)
- **Root Cause**: 44-byte string copied into 16-byte buffer

### use_after_free
- **Expected Finding**: Use-after-free at line 23
- **Root Cause**: `buffer` accessed after `free(buffer)` was called

### infinite_loop
- **Expected Finding**: Infinite loop at line 16
- **Root Cause**: `counter--` instead of `counter++` causes loop to never terminate

### divide_by_zero
- **Expected Finding**: Division by zero at line 7 (in calculate function)
- **Root Cause**: `denominator` is 0, causing arithmetic exception

### stack_overflow
- **Expected Finding**: Stack overflow due to infinite recursion at line 11
- **Root Cause**: No base case in recursive function

### format_string
- **Expected Finding**: Format string vulnerability at line 9
- **Root Cause**: User-controlled input passed directly to printf

### double_free
- **Expected Finding**: Double free at line 27
- **Root Cause**: `buffer` freed in `process_data()` and again in `main()`

## Security Notes

These programs contain intentional vulnerabilities for testing purposes.
Do not use them in production environments.

- `buffer_overflow` and `format_string` are compiled with security warnings suppressed (`-Wno-format-security`)
- These vulnerabilities can be exploited in real-world scenarios
