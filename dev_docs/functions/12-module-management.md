# Module Management Tools (NEW - Phase 1)

## Overview

Module management tools provide information about loaded modules (executables, shared libraries, frameworks). Understanding module layout is essential for debugging, understanding memory layout, and security analysis.

## Tools

### lldb_listModules

**Description**: List all modules loaded in the target process.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sessionId | string | Yes | The session ID |

**Returns**:
```json
{
  "modules": [
    {
      "name": "a.out",
      "path": "/Users/user/project/a.out",
      "uuid": "ABC123-DEF456-789012",
      "arch": "arm64",
      "type": "executable",
      "loadAddress": "0x0000000100000000",
      "size": 32768,
      "sections": [
        {
          "name": "__TEXT",
          "address": "0x0000000100000000",
          "size": 16384,
          "permissions": "r-x"
        },
        {
          "name": "__DATA",
          "address": "0x0000000100004000",
          "size": 8192,
          "permissions": "rw-"
        }
      ]
    },
    {
      "name": "libSystem.B.dylib",
      "path": "/usr/lib/libSystem.B.dylib",
      "uuid": "XYZ789-ABC123-456DEF",
      "arch": "arm64",
      "type": "shared_library",
      "loadAddress": "0x00007fff20000000",
      "size": 1048576,
      "sections": [
        {
          "name": "__TEXT",
          "address": "0x00007fff20000000",
          "size": 524288,
          "permissions": "r-x"
        }
      ]
    }
  ],
  "totalModules": 2
}
```

**Example**:
```python
result = client.call_tool("lldb_listModules", {
    "sessionId": session_id
})

print(f"Loaded {result['totalModules']} modules:\n")

for module in result["modules"]:
    print(f"Module: {module['name']}")
    print(f"  Path: {module['path']}")
    print(f"  Load Address: {module['loadAddress']}")
    print(f"  Size: {module['size']} bytes")
    print(f"  Type: {module['type']}")
    print()
```

**Error Codes**:
| Code | Description |
|------|-------------|
| 1002 | Session not found |
| 2001 | No target loaded |

**Implementation Notes**:
- Includes main executable and all shared libraries
- Section information may be incomplete for stripped binaries
- Load addresses change with ASLR

---

## Module Types

| Type | Description | Examples |
|------|-------------|----------|
| executable | Main program | `a.out`, `MyApp` |
| shared_library | Dynamic library | `libSystem.B.dylib`, `libc.so` |
| framework | macOS framework | `CoreFoundation.framework` |
| dylinker | Dynamic linker | `dyld` |

## Section Types

### Common Sections (Mach-O / macOS)

| Section | Permissions | Contents |
|---------|-------------|----------|
| `__TEXT.__text` | r-x | Executable code |
| `__TEXT.__stubs` | r-x | Import stubs |
| `__TEXT.__cstring` | r-- | C string literals |
| `__DATA.__data` | rw- | Initialized data |
| `__DATA.__bss` | rw- | Uninitialized data |
| `__DATA.__got` | rw- | Global Offset Table |
| `__DATA.__la_symbol_ptr` | rw- | Lazy symbol pointers |

**Note**: This project only supports macOS, which uses the Mach-O binary format.

## Use Cases

### Understanding Memory Layout

```python
result = client.call_tool("lldb_listModules", {
    "sessionId": session_id
})

print("Memory Map:")
print("-" * 60)

for module in result["modules"]:
    load_addr = int(module["loadAddress"], 16)
    end_addr = load_addr + module["size"]
    print(f"{module['loadAddress']}-{hex(end_addr)}: {module['name']}")

    for section in module.get("sections", []):
        sec_addr = section["address"]
        sec_end = hex(int(sec_addr, 16) + section["size"])
        print(f"  {sec_addr}-{sec_end}: {section['name']} [{section['permissions']}]")
```

### Finding Code/Data Regions

```python
result = client.call_tool("lldb_listModules", {
    "sessionId": session_id
})

executable_regions = []
writable_regions = []

for module in result["modules"]:
    for section in module.get("sections", []):
        addr = int(section["address"], 16)
        size = section["size"]

        if "x" in section["permissions"]:
            executable_regions.append({
                "module": module["name"],
                "section": section["name"],
                "start": addr,
                "end": addr + size
            })

        if "w" in section["permissions"]:
            writable_regions.append({
                "module": module["name"],
                "section": section["name"],
                "start": addr,
                "end": addr + size
            })

print(f"Found {len(executable_regions)} executable regions")
print(f"Found {len(writable_regions)} writable regions")
```

### Detecting ASLR Slide

```python
# Compare load address to preferred base address
result = client.call_tool("lldb_listModules", {
    "sessionId": session_id
})

main_module = next(m for m in result["modules"] if m["type"] == "executable")
load_addr = int(main_module["loadAddress"], 16)

# Typical preferred base on macOS (arm64)
preferred_base = 0x100000000

slide = load_addr - preferred_base
print(f"ASLR slide: {hex(slide)}")
```

### Finding Library Functions

```python
# Find a specific library
result = client.call_tool("lldb_listModules", {
    "sessionId": session_id
})

libc = next((m for m in result["modules"] if "libSystem" in m["name"]), None)

if libc:
    # Search for functions in this library
    symbols = client.call_tool("lldb_searchSymbol", {
        "sessionId": session_id,
        "pattern": "printf",
        "module": libc["name"]
    })
    print(f"printf at: {symbols['symbols'][0]['address']}")
```

### Checking Security Features

```python
result = client.call_tool("lldb_listModules", {
    "sessionId": session_id
})

for module in result["modules"]:
    has_pie = module.get("loadAddress", "0x0") != "0x0"

    # Check for writable+executable sections (security risk)
    wx_sections = [
        s for s in module.get("sections", [])
        if "w" in s.get("permissions", "") and "x" in s.get("permissions", "")
    ]

    print(f"{module['name']}:")
    print(f"  PIE/ASLR: {'Yes' if has_pie else 'No'}")
    print(f"  W+X sections: {len(wx_sections)}")
```

## Integration with Other Tools

### Module → Symbol Search

```python
# List modules, then search symbols in specific one
modules = client.call_tool("lldb_listModules", {"sessionId": session_id})

for module in modules["modules"]:
    if "crypto" in module["name"].lower():
        symbols = client.call_tool("lldb_searchSymbol", {
            "sessionId": session_id,
            "pattern": "*",
            "module": module["name"]
        })
        print(f"{module['name']} exports {len(symbols['symbols'])} symbols")
```

### Module → Disassembly

```python
# Find main executable and disassemble entry
modules = client.call_tool("lldb_listModules", {"sessionId": session_id})
main = next(m for m in modules["modules"] if m["type"] == "executable")

# Find __TEXT section
text = next(s for s in main["sections"] if "__TEXT" in s["name"] and "__text" in s["name"])

# Disassemble first instructions
client.call_tool("lldb_disassemble", {
    "sessionId": session_id,
    "addr": int(text["address"], 16),
    "count": 20
})
```
