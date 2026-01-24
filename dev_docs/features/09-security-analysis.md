# Security Analysis Tools (NEW - Phase 2)

## Overview

Security analysis tools provide vulnerability exploitability analysis capabilities. These tools help security researchers assess crash severity, identify potential exploits, and analyze suspicious function calls.

## Tools

### lldb_analyzeCrash

**Description**: Analyze the exploitability of the current crash or stopped state.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |

**Returns**:
```json
{
  "analysis": {
    "rating": "High",
    "confidence": 0.85,
    "crashType": "SIGSEGV",
    "accessType": "write",
    "faultAddress": "0x41414141",
    "instruction": {
      "address": "0x100003f00",
      "mnemonic": "mov",
      "operands": "[rax], rbx"
    },
    "registers": {
      "rip": "0x100003f00",
      "rsp": "0x7fff5fbff8c0",
      "rax": "0x41414141",
      "rbx": "0x42424242"
    },
    "indicators": [
      {
        "type": "controlled_write",
        "description": "Write to user-controlled address",
        "severity": "high"
      },
      {
        "type": "heap_address",
        "description": "Fault address appears to be in heap region",
        "severity": "medium"
      }
    ],
    "recommendation": "Potential arbitrary write vulnerability. Investigate buffer overflow or use-after-free."
  }
}
```

**Example**:
```python
# After process crashes
events = client.call_tool("lldb_pollEvents", {"sessionId": session_id})
# Process stopped due to signal

# Analyze the crash
result = client.call_tool("lldb_analyzeCrash", {
    "sessionId": session_id
})

print(f"Exploitability: {result['analysis']['rating']}")
print(f"Crash type: {result['analysis']['crashType']}")

for indicator in result['analysis']['indicators']:
    print(f"  - {indicator['description']} ({indicator['severity']})")
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2002 | No process available |
| 4001 | Process not stopped |
| 6001 | Analysis failed |

**Implementation Notes**:
- Process must be in stopped state (crash or signal)
- Analysis examines registers, memory, and crash instruction
- Uses heuristics to determine exploitability

---

### lldb_getSuspiciousFunctions

**Description**: Identify suspicious security-related functions in the call stack.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |

**Returns**:
```json
{
  "suspiciousFunctions": [
    {
      "name": "malloc",
      "address": "0x7fff20403080",
      "frameIndex": 2,
      "category": "memory_allocation",
      "risk": "medium",
      "description": "Memory allocation function - check for heap corruption"
    },
    {
      "name": "strcpy",
      "address": "0x7fff20401234",
      "frameIndex": 1,
      "category": "unsafe_string",
      "risk": "high",
      "description": "Unsafe string copy - potential buffer overflow"
    },
    {
      "name": "objc_msgSend",
      "address": "0x7fff203f5678",
      "frameIndex": 3,
      "category": "objective_c",
      "risk": "medium",
      "description": "Objective-C message dispatch - check for use-after-free"
    }
  ],
  "summary": {
    "totalFunctions": 3,
    "highRisk": 1,
    "mediumRisk": 2,
    "lowRisk": 0
  }
}
```

**Example**:
```python
result = client.call_tool("lldb_getSuspiciousFunctions", {
    "sessionId": session_id
})

print(f"Found {result['summary']['totalFunctions']} suspicious functions")
print(f"High risk: {result['summary']['highRisk']}")

for func in result['suspiciousFunctions']:
    if func['risk'] == 'high':
        print(f"WARNING: {func['name']} - {func['description']}")
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2002 | No process available |
| 4001 | Process not stopped |

---

## Exploitability Rating System

| Rating | Score | Conditions |
|--------|-------|------------|
| Critical | 9-10 | Controllable PC/SP + Write access + Sensitive function in stack |
| High | 7-8 | Write access violation + Heap/stack address |
| Medium | 4-6 | Read access violation + Predictable address pattern |
| Low | 1-3 | Null pointer dereference + No control over crash |
| Unknown | 0 | Cannot determine exploitability |

## Crash Types

| Signal | Description | Common Causes |
|--------|-------------|---------------|
| SIGSEGV | Segmentation fault | Invalid memory access |
| SIGBUS | Bus error | Misaligned access, hardware fault |
| SIGABRT | Abort | assert() failure, heap corruption detected |
| SIGFPE | Floating-point exception | Division by zero |
| SIGILL | Illegal instruction | Corrupted code, jump to data |
| SIGTRAP | Trap | Debugger breakpoint, single-step |

## Access Type Analysis

| Access Type | Indicator | Exploitability |
|-------------|-----------|----------------|
| Write | Memory write at fault | Higher - potential arbitrary write |
| Read | Memory read at fault | Lower - information leak |
| Execute | Code execution at fault | Highest - code execution possible |

## Suspicious Function Categories

### Memory Allocation
- `malloc`, `realloc`, `calloc`, `free`
- `new`, `delete` (C++)
- Risk: Heap corruption, use-after-free, double-free

### Unsafe String Operations
- `strcpy`, `strcat`, `sprintf`, `gets`
- Risk: Buffer overflow

### Safe Alternatives (Lower Risk)
- `strncpy`, `strncat`, `snprintf`
- Risk: Still possible but bounded

### Objective-C Runtime
- `objc_msgSend`, `objc_release`, `objc_retain`
- Risk: Use-after-free, type confusion

### Memory Operations
- `memcpy`, `memmove`, `memset`
- Risk: Buffer overflow if size is controlled

## Analysis Workflow

```python
# 1. Run target until crash
client.call_tool("lldb_continue", {"sessionId": session_id})

# 2. Poll for crash event
events = client.call_tool("lldb_pollEvents", {"sessionId": session_id})
for event in events["events"]:
    if event["type"] == "signal":
        print(f"Crashed with {event['signalName']}")

# 3. Analyze exploitability
crash_analysis = client.call_tool("lldb_analyzeCrash", {
    "sessionId": session_id
})

# 4. Get suspicious functions
suspicious = client.call_tool("lldb_getSuspiciousFunctions", {
    "sessionId": session_id
})

# 5. Generate report
print(f"=== Crash Analysis Report ===")
print(f"Rating: {crash_analysis['analysis']['rating']}")
print(f"Type: {crash_analysis['analysis']['crashType']}")
print(f"Fault Address: {crash_analysis['analysis']['faultAddress']}")
print(f"\nSuspicious Functions:")
for func in suspicious['suspiciousFunctions']:
    print(f"  - {func['name']}: {func['description']}")
```

## Integration with Security Research

### Fuzzing Triage

```python
def triage_crash(crash_input):
    """Triage a fuzzer-generated crash."""
    # Initialize session
    result = client.call_tool("lldb_initialize", {})
    session_id = result["sessionId"]

    try:
        # Load target
        client.call_tool("lldb_createTarget", {
            "sessionId": session_id,
            "file": "/path/to/target"
        })

        # Launch with crash input
        client.call_tool("lldb_launch", {
            "sessionId": session_id,
            "args": [crash_input]
        })

        # Wait for crash
        time.sleep(1)
        events = client.call_tool("lldb_pollEvents", {
            "sessionId": session_id
        })

        # Analyze
        analysis = client.call_tool("lldb_analyzeCrash", {
            "sessionId": session_id
        })

        return {
            "input": crash_input,
            "rating": analysis["analysis"]["rating"],
            "type": analysis["analysis"]["crashType"]
        }

    finally:
        client.call_tool("lldb_terminate", {"sessionId": session_id})
```

### Vulnerability Assessment

The security analysis tools help answer key questions:

1. **Is this crash exploitable?** → `lldb_analyzeCrash` rating
2. **What functions are involved?** → `lldb_getSuspiciousFunctions`
3. **What type of vulnerability?** → Access type + crash type analysis
4. **What registers are controlled?** → Register values in crash analysis
