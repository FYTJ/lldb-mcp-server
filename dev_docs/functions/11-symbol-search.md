# Symbol Search Tools (NEW - Phase 1)

## Overview

Symbol search tools enable searching for symbols (functions, variables, types) across all loaded modules. This is essential for understanding program structure, finding function addresses, and reverse engineering.

## Tools

### lldb_searchSymbol

**Description**: Search for symbols matching a pattern across all loaded modules.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |
| pattern | string | Yes | Search pattern (supports wildcards) |
| module | string | No | Limit search to specific module |

**Returns**:
```json
{
  "symbols": [
    {
      "name": "malloc",
      "address": "0x7fff20403080",
      "module": "libsystem_malloc.dylib",
      "type": "function",
      "size": 256
    },
    {
      "name": "malloc_zone_malloc",
      "address": "0x7fff20403180",
      "module": "libsystem_malloc.dylib",
      "type": "function",
      "size": 128
    },
    {
      "name": "__malloc_lock",
      "address": "0x7fff20410000",
      "module": "libsystem_malloc.dylib",
      "type": "data",
      "size": 8
    }
  ],
  "totalMatches": 3
}
```

**Example**:
```python
# Search for all malloc-related functions
result = client.call_tool("lldb_searchSymbol", {
    "sessionId": session_id,
    "pattern": "*malloc*"
})

for sym in result["symbols"]:
    print(f"{sym['name']} at {sym['address']} in {sym['module']}")

# Search in specific module
result = client.call_tool("lldb_searchSymbol", {
    "sessionId": session_id,
    "pattern": "process*",
    "module": "a.out"
})

# Find a specific function
result = client.call_tool("lldb_searchSymbol", {
    "sessionId": session_id,
    "pattern": "main"
})
main_addr = result["symbols"][0]["address"]
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2001 | No target loaded |

**Implementation Notes**:
- Uses LLDB's symbol table searching
- Wildcards: `*` matches any characters, `?` matches single character
- Search is case-sensitive by default
- Large symbol tables may take time to search

---

## Search Patterns

### Exact Match
```python
client.call_tool("lldb_searchSymbol", {
    "sessionId": session_id,
    "pattern": "main"
})
```

### Prefix Match
```python
# Find all functions starting with "process_"
client.call_tool("lldb_searchSymbol", {
    "sessionId": session_id,
    "pattern": "process_*"
})
```

### Suffix Match
```python
# Find all functions ending with "_init"
client.call_tool("lldb_searchSymbol", {
    "sessionId": session_id,
    "pattern": "*_init"
})
```

### Contains Match
```python
# Find all symbols containing "alloc"
client.call_tool("lldb_searchSymbol", {
    "sessionId": session_id,
    "pattern": "*alloc*"
})
```

### C++ Mangled Names
```python
# Search for C++ method
client.call_tool("lldb_searchSymbol", {
    "sessionId": session_id,
    "pattern": "*MyClass*"
})
```

## Symbol Types

| Type | Description | Examples |
|------|-------------|----------|
| function | Executable code | `main`, `printf` |
| data | Global/static variables | `errno`, `environ` |
| trampoline | Jump stubs | `printf$LAZY` |
| undefined | External references | Imported symbols |

## Module-Specific Search

```python
# Search only in main executable
result = client.call_tool("lldb_searchSymbol", {
    "sessionId": session_id,
    "pattern": "*",
    "module": "a.out"
})

# Search in specific library
result = client.call_tool("lldb_searchSymbol", {
    "sessionId": session_id,
    "pattern": "NS*",
    "module": "Foundation"
})
```

## Use Cases

### Finding Function Addresses for Breakpoints

```python
# Find all handler functions
result = client.call_tool("lldb_searchSymbol", {
    "sessionId": session_id,
    "pattern": "*_handler"
})

# Set breakpoints on all of them
for sym in result["symbols"]:
    if sym["type"] == "function":
        client.call_tool("lldb_setBreakpoint", {
            "sessionId": session_id,
            "address": int(sym["address"], 16)
        })
```

### Analyzing Library Usage

```python
# Find all functions used from libcrypto
result = client.call_tool("lldb_searchSymbol", {
    "sessionId": session_id,
    "pattern": "*",
    "module": "libcrypto*"
})

crypto_functions = [s for s in result["symbols"] if s["type"] == "function"]
print(f"Using {len(crypto_functions)} cryptographic functions")
```

### Reverse Engineering

```python
# Find potential entry points
interesting_patterns = ["main", "*_init", "*_start", "*_entry"]

for pattern in interesting_patterns:
    result = client.call_tool("lldb_searchSymbol", {
        "sessionId": session_id,
        "pattern": pattern
    })
    for sym in result["symbols"]:
        print(f"Entry point: {sym['name']} at {sym['address']}")
```

### Finding Global Variables

```python
# Find configuration variables
result = client.call_tool("lldb_searchSymbol", {
    "sessionId": session_id,
    "pattern": "*config*"
})

data_symbols = [s for s in result["symbols"] if s["type"] == "data"]
for sym in data_symbols:
    # Read the value
    addr = int(sym["address"], 16)
    mem = client.call_tool("lldb_readMemory", {
        "sessionId": session_id,
        "addr": addr,
        "size": sym.get("size", 8)
    })
    print(f"{sym['name']}: {mem['bytes']}")
```

## Integration with Other Tools

### Symbol → Breakpoint Workflow

```python
# 1. Search for function
result = client.call_tool("lldb_searchSymbol", {
    "sessionId": session_id,
    "pattern": "vulnerable_function"
})

if result["symbols"]:
    addr = int(result["symbols"][0]["address"], 16)

    # 2. Set breakpoint at address
    client.call_tool("lldb_setBreakpoint", {
        "sessionId": session_id,
        "address": addr
    })

    # 3. Or disassemble the function
    client.call_tool("lldb_disassemble", {
        "sessionId": session_id,
        "addr": addr,
        "count": 50
    })
```

### Symbol → Memory Read Workflow

```python
# Find a global variable
result = client.call_tool("lldb_searchSymbol", {
    "sessionId": session_id,
    "pattern": "g_important_data"
})

if result["symbols"]:
    sym = result["symbols"][0]
    addr = int(sym["address"], 16)
    size = sym.get("size", 64)

    # Read the variable's contents
    mem = client.call_tool("lldb_readMemory", {
        "sessionId": session_id,
        "addr": addr,
        "size": size
    })
    print(f"Value: {mem['bytes']}")
```
