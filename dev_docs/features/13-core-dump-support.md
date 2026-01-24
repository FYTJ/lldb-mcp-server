# Core Dump Support Tools (NEW - Phase 1)

## Overview

Core dump support tools enable loading and analyzing core dump files for post-mortem debugging. This is essential for analyzing crashes that occurred in production environments or during fuzzing.

## Tools

### lldb_loadCore

**Description**: Load a core dump file for post-mortem analysis.

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
    "arch": "arm64"
  },
  "core": {
    "path": "/path/to/core",
    "pid": 12345,
    "signal": "SIGSEGV"
  },
  "threads": [
    {
      "id": 1,
      "name": "main",
      "state": "crashed"
    }
  ]
}
```

**Example**:
```python
result = client.call_tool("lldb_loadCore", {
    "sessionId": session_id,
    "corePath": "/cores/core.12345",
    "executable": "/usr/bin/crashed_app"
})

print(f"Loaded core from PID {result['core']['pid']}")
print(f"Crash signal: {result['core']['signal']}")
print(f"Threads: {len(result['threads'])}")
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2001 | Failed to create target - executable not found |
| 2004 | Failed to load core dump - file not found or invalid |

**Implementation Notes**:
- Core dump analysis is read-only (no continue/step)
- Requires matching executable with debug symbols for best results
- Large core files may take time to load

---

### lldb_createCoredump

**Description**: Create a core dump of the current process state.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| path | string | Yes | Path to save the core dump |

**Returns**:
```json
{
  "path": "/tmp/debug.core",
  "size": 104857600,
  "pid": 12345
}
```

**Example**:
```python
# Stop at an interesting point
client.call_tool("lldb_pause", {"sessionId": session_id})

# Create core dump for later analysis
result = client.call_tool("lldb_createCoredump", {
    "sessionId": session_id,
    "path": "/tmp/snapshot.core"
})

print(f"Core dump saved: {result['path']}")
print(f"Size: {result['size']} bytes")
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2002 | No process running |
| 4001 | Process not stopped |
| 5002 | Failed to create core dump - permission denied or disk full |

---

## Core Dump Analysis Workflow

### Loading and Inspecting

```python
# 1. Initialize session
result = client.call_tool("lldb_initialize", {})
session_id = result["sessionId"]

# 2. Load the core dump
result = client.call_tool("lldb_loadCore", {
    "sessionId": session_id,
    "corePath": "/cores/core.12345",
    "executable": "/usr/bin/crashed_app"
})

# 3. Examine threads
threads = client.call_tool("lldb_threads", {"sessionId": session_id})
for thread in threads["threads"]:
    print(f"Thread {thread['id']}: {thread['state']}")

# 4. Get stack trace
for thread in threads["threads"]:
    trace = client.call_tool("lldb_stackTrace", {
        "sessionId": session_id,
        "threadId": thread["id"]
    })
    print(f"\n=== Thread {thread['id']} ===")
    print(trace["stackTrace"])

# 5. Read registers
regs = client.call_tool("lldb_readRegisters", {"sessionId": session_id})
print(f"\nRIP: {regs['registers']['general']['rip']}")
print(f"RSP: {regs['registers']['general']['rsp']}")

# 6. Analyze crash
crash = client.call_tool("lldb_analyzeCrash", {"sessionId": session_id})
print(f"\nExploitability: {crash['analysis']['rating']}")
```

### Examining Memory at Crash

```python
# Read memory around the fault address
fault_addr = int(crash["analysis"]["faultAddress"], 16)

# Read before and after
before = client.call_tool("lldb_readMemory", {
    "sessionId": session_id,
    "addr": fault_addr - 64,
    "size": 64
})

after = client.call_tool("lldb_readMemory", {
    "sessionId": session_id,
    "addr": fault_addr,
    "size": 64
})

print(f"Memory before fault: {before['bytes']}")
print(f"Memory at/after fault: {after['bytes']}")
```

### Examining Variables

```python
# Evaluate expressions in crash context
variables = ["argc", "argv", "environ", "errno"]

for var in variables:
    try:
        result = client.call_tool("lldb_evaluate", {
            "sessionId": session_id,
            "expr": var
        })
        print(f"{var} = {result['result']['value']}")
    except Exception:
        print(f"{var} = <unavailable>")
```

## Core Dump Locations (macOS)

```bash
# Default location
/cores/core.<pid>

# Enable core dumps
ulimit -c unlimited

# Check core dump settings
sysctl kern.corefile
```

**Note**: This project only supports macOS. LLDB Python bindings require Xcode or Command Line Tools.

## Limitations

Core dump analysis is **read-only**. The following operations are NOT available:

| Operation | Available |
|-----------|-----------|
| lldb_threads | Yes |
| lldb_frames | Yes |
| lldb_stackTrace | Yes |
| lldb_readRegisters | Yes |
| lldb_readMemory | Yes |
| lldb_evaluate | Yes (expressions only) |
| lldb_disassemble | Yes |
| lldb_continue | **No** |
| lldb_stepIn/Over/Out | **No** |
| lldb_writeMemory | **No** |
| lldb_writeRegister | **No** |
| lldb_setBreakpoint | **No** |

## Use Cases

### Production Crash Analysis

```python
def analyze_production_crash(core_path, executable_path):
    """Analyze a crash from production."""
    session = client.call_tool("lldb_initialize", {})["sessionId"]

    try:
        # Load core
        client.call_tool("lldb_loadCore", {
            "sessionId": session,
            "corePath": core_path,
            "executable": executable_path
        })

        # Get crash analysis
        crash = client.call_tool("lldb_analyzeCrash", {"sessionId": session})

        # Get stack trace
        trace = client.call_tool("lldb_stackTrace", {"sessionId": session})

        return {
            "rating": crash["analysis"]["rating"],
            "type": crash["analysis"]["crashType"],
            "address": crash["analysis"]["faultAddress"],
            "stack": trace["stackTrace"]
        }

    finally:
        client.call_tool("lldb_terminate", {"sessionId": session})
```

### Fuzzing Crash Triage

```python
import os
import glob

def triage_fuzzing_crashes(crash_dir, executable):
    """Triage all crashes from a fuzzing campaign."""
    crashes = []

    for core_file in glob.glob(f"{crash_dir}/core.*"):
        session = client.call_tool("lldb_initialize", {})["sessionId"]

        try:
            client.call_tool("lldb_loadCore", {
                "sessionId": session,
                "corePath": core_file,
                "executable": executable
            })

            crash = client.call_tool("lldb_analyzeCrash", {"sessionId": session})

            crashes.append({
                "file": core_file,
                "rating": crash["analysis"]["rating"],
                "type": crash["analysis"]["crashType"]
            })

        except Exception as e:
            crashes.append({
                "file": core_file,
                "error": str(e)
            })

        finally:
            client.call_tool("lldb_terminate", {"sessionId": session})

    # Sort by severity
    crashes.sort(key=lambda x: {
        "Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Unknown": 4
    }.get(x.get("rating", "Unknown"), 5))

    return crashes
```

### Comparing Crashes

```python
def compare_crashes(core1, core2, executable):
    """Compare two crashes to see if they're duplicates."""
    def get_crash_signature(core_path):
        session = client.call_tool("lldb_initialize", {})["sessionId"]
        try:
            client.call_tool("lldb_loadCore", {
                "sessionId": session,
                "corePath": core_path,
                "executable": executable
            })

            # Get top 3 frames as signature
            trace = client.call_tool("lldb_stackTrace", {"sessionId": session})
            crash = client.call_tool("lldb_analyzeCrash", {"sessionId": session})

            return {
                "type": crash["analysis"]["crashType"],
                "stack": trace["stackTrace"][:500]  # First 500 chars
            }
        finally:
            client.call_tool("lldb_terminate", {"sessionId": session})

    sig1 = get_crash_signature(core1)
    sig2 = get_crash_signature(core2)

    return sig1["type"] == sig2["type"] and sig1["stack"] == sig2["stack"]
```
