# Stack Overflow - Quick Reference

## Bug Identification
- **Type**: Stack Overflow
- **Cause**: Infinite Recursion
- **Function**: `recursive_function`
- **Binary**: `stack_overflow/stack_overflow`

## The Problem
```assembly
0x100000492 <+34>: callq 0x100000470  ; Unconditional recursive call - NO BASE CASE!
```

## Evidence
- Stack frames: 262,036
- Each call increments depth and consumes ~32 bytes of stack
- Total stack consumption: ~8.4 MB before crash
- No conditional jump instructions in the function
- Code after recursive call is unreachable

## Root Cause
Missing termination condition. The function signature (inferred):
```c
void recursive_function(int depth) {
    printf("Recursion depth: %d\n", depth);
    recursive_function(depth + 1);  // ← BUG: No base case!
}
```

## The Fix
Add a base case:
```c
void recursive_function(int depth) {
    if (depth >= 100) return;  // ← FIX: Add termination condition
    printf("Recursion depth: %d\n", depth);
    recursive_function(depth + 1);
}
```

## Assembly Location
- **Bug Address**: `0x100000492` (recursive_function:+34)
- **First Call**: `0x100000470` (recursive_function:+0)
- **Crash Point**: `0x7ff8071bbed8` (libsystem_c.dylib::_swrite)

## LLDB MCP Debugging Flow
1. Initialize session → Create target → Launch process
2. Process stops with exception (262K frames)
3. Set breakpoint on `recursive_function`
4. Disassemble to find missing base case
5. Verify recursion via register inspection
6. Analyze crash state

## Key Registers
| Call | RDI (depth) | RSP (stack) | Notes |
|------|-------------|-------------|-------|
| 1st  | 0x0         | 0x...f6b8   | Initial call |
| 2nd  | 0x1         | 0x...f698   | -32 bytes |
| Crash| N/A         | 0x...0000   | Stack exhausted |

## Severity
- **Impact**: Process crash (DoS)
- **Exploitability**: Low (stack exhaustion, not corruption)
- **Fix Difficulty**: Trivial (add one `if` statement)
