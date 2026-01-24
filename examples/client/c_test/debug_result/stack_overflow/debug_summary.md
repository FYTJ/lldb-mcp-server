# Stack Overflow Bug Analysis

## Binary Information
- **Binary Path**: `/Users/zhuyanbo/PycharmProjects/lldb-mcp-server/examples/client/c_test/stack_overflow/stack_overflow`
- **Architecture**: x86_64
- **Platform**: macOS 15.0.0

## Bug Type
**Stack Overflow due to Infinite Recursion**

## Executive Summary
The binary crashes due to an infinite recursive function call without a termination condition. The function `recursive_function` calls itself indefinitely, exhausting the stack space after approximately 262,036 recursive calls.

## Debugging Process

### 1. Initial Launch and Crash Detection
- Launched the binary using LLDB MCP tools
- Process immediately stopped with exception
- Thread showed 262,036 stack frames - clear indication of stack overflow

### 2. Stack Trace Analysis
The stack trace revealed a repeating pattern:
```
frame #6: 0x10000048c stack_overflow`recursive_function at <unknown>:0
frame #7: 0x100000497 stack_overflow`recursive_function at <unknown>:0
frame #8: 0x100000497 stack_overflow`recursive_function at <unknown>:0
frame #9: 0x100000497 stack_overflow`recursive_function at <unknown>:0
[... repeats 262,036 times ...]
```

The function calls itself at address `0x100000497` repeatedly.

### 3. Function Disassembly
Disassembled `recursive_function` to understand the logic:

```assembly
stack_overflow`recursive_function:
    0x100000470 <+0>:  pushq  %rbp                     ; Function prologue
    0x100000471 <+1>:  movq   %rsp, %rbp
    0x100000474 <+4>:  subq   $0x10, %rsp
    0x100000478 <+8>:  movl   %edi, -0x4(%rbp)         ; Store depth parameter
    0x10000047b <+11>: movl   -0x4(%rbp), %esi
    0x10000047e <+14>: leaq   0x69(%rip), %rdi         ; Load "Recursion depth: %d\n"
    0x100000485 <+21>: movb   $0x0, %al
    0x100000487 <+23>: callq  0x1000004e8              ; Call printf
    0x10000048c <+28>: movl   -0x4(%rbp), %edi         ; Load depth
    0x10000048f <+31>: addl   $0x1, %edi               ; Increment depth by 1
    0x100000492 <+34>: callq  0x100000470              ; RECURSIVE CALL (no condition!)
    0x100000497 <+39>: addq   $0x10, %rsp              ; UNREACHABLE CODE
    0x10000049b <+43>: popq   %rbp                     ; UNREACHABLE CODE
    0x10000049c <+44>: retq                            ; UNREACHABLE CODE
```

### 4. Key Findings from Disassembly

**Critical Issue**: The function has NO termination condition!
- No comparison instruction (cmp, test)
- No conditional jump (je, jne, jl, jg, etc.)
- The recursive call at `0x100000492` is UNCONDITIONAL
- Code after the recursive call (cleanup and return) is UNREACHABLE

### 5. Register Analysis
Verified the recursion by checking registers at multiple breakpoints:

**First call**:
- `rdi = 0x0000000000000000` (depth = 0)
- `rsp = 0x00007ff7bfeff6b8` (stack pointer)

**Second call**:
- `rdi = 0x0000000000000001` (depth = 1)
- `rsp = 0x00007ff7bfeff698` (stack decreased by 0x20 bytes)

This confirms:
1. Depth increments on each call
2. Stack grows downward with each recursion
3. Each call consumes stack space

### 6. Crash Point Analysis
When the stack is exhausted:
- **Crash Address**: `0x7ff8071bbed8` (inside `libsystem_c.dylib::_swrite`)
- **Stack Pointer**: `rsp = 0x00007ff7bf700000` (at stack limit)
- **Frame Count**: 262,036 frames
- The crash occurs within `printf` when the stack has no more space

## Root Cause

The function `recursive_function(int depth)` is implemented as:

```c
// Pseudocode based on assembly analysis
void recursive_function(int depth) {
    printf("Recursion depth: %d\n", depth);
    recursive_function(depth + 1);  // NO BASE CASE!
    // Unreachable code below
}
```

**Missing**: A base case to terminate recursion, such as:
```c
if (depth >= MAX_DEPTH) {
    return;
}
```

## Exact Location of Bug

- **Function**: `recursive_function`
- **Address**: `0x100000492` (the unconditional recursive call instruction)
- **Instruction**: `callq 0x100000470`
- **Line**: N/A (binary-only analysis)

## How to Fix

Add a termination condition before the recursive call:

```c
void recursive_function(int depth) {
    // ADD BASE CASE HERE
    if (depth >= 100) {  // or any reasonable limit
        return;
    }

    printf("Recursion depth: %d\n", depth);
    recursive_function(depth + 1);
}
```

In assembly, this would add:
```assembly
    movl   -0x4(%rbp), %eax        ; Load depth
    cmpl   $0x64, %eax             ; Compare with 100
    jge    return_label            ; Jump if >= 100
    ; ... rest of function ...
return_label:
    addq   $0x10, %rsp
    popq   %rbp
    retq
```

## LLDB MCP Tools Used

1. **lldb_initialize**: Create debugging session
2. **lldb_createTarget**: Load the binary
3. **lldb_launch**: Start the process
4. **lldb_threads**: Inspect thread state
5. **lldb_stackTrace**: Analyze call stack (262,036 frames!)
6. **lldb_setBreakpoint**: Set breakpoint on `recursive_function`
7. **lldb_disassemble** (via lldb_command): Examine assembly code
8. **lldb_readRegisters**: Verify depth increments
9. **lldb_stepOver**: Step through execution
10. **lldb_continue**: Run until crash
11. **lldb_analyzeCrash**: Analyze crash state
12. **lldb_getTranscript**: Retrieve debugging session history

## Summary

This is a classic textbook example of stack overflow caused by infinite recursion. The function lacks any termination logic and will continue calling itself until the stack is completely exhausted. The fix is simple: add a base case that checks the depth and returns before making the recursive call when a maximum depth is reached.
