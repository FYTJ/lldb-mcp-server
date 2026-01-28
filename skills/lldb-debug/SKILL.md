---
name: lldb-debug
description: Debug C/C++ programs using LLDB debugger when direct code analysis is insufficient. Use ONLY when (1) project complexity makes static analysis unreliable, (2) error logs are missing or uninformative, (3) multiple code fixes have failed, or (4) runtime behavior analysis is required. Supports crash analysis, memory bugs, breakpoints, and core dump analysis.
argument-hint: [binary-path or debug-task]
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Bash(*), mcp__lldb-debugger__*
---

# LLDB Interactive Debugging Guide

You have access to an LLDB debugging MCP server with 40 tools for debugging C/C++ programs on macOS.

## ⚠️ CRITICAL SAFETY REQUIREMENT ⚠️

**Programs can hang indefinitely (infinite loops, deadlocks, blocking I/O). ALWAYS use timeout protection:**

- **NEVER** call `lldb_continue` without a timeout plan
- **NEVER** call `lldb_stepOver`, `lldb_stepIn`, or `lldb_stepOut` without timeout protection
- **ALWAYS** call `lldb_pause` after a reasonable timeout (default: 5-10 seconds)
- **ALWAYS** force-pause before inspecting state (`lldb_evaluate`, `lldb_readRegisters`, `lldb_readMemory`)
- **ALWAYS** implement hang detection by comparing stack traces across time

**Mandatory Pattern for ALL execution operations:**
```
operation (continue/step) → [wait N seconds] → lldb_pause → pollEvents → threads
```

**Recommended Timeout Values:**
- Fast operations (hit known breakpoint): **3-5 seconds**
- Normal execution: **5-10 seconds**
- I/O-heavy operations: **10-15 seconds**
- Initialization/startup: **15-20 seconds**
- Suspected hang detection: **2-3 seconds** (for quick verification)

**Hang Detection Strategy:**
1. Force pause after timeout
2. Get stack trace with `lldb_stackTrace`
3. Resume briefly (2s) then pause again
4. Compare stack traces - same location = confirmed hang

Failure to use timeouts will cause the debugger to hang and become unresponsive.

## When to Use This Skill

**Use LLDB debugging ONLY when direct code analysis is insufficient:**

1. **Project complexity prevents reliable static analysis**
   - Large codebase with complex call chains
   - Multiple modules with unclear interactions
   - Assembly or optimized code behavior needs verification

2. **Error logs are missing or uninformative**
   - No error messages or stack traces available
   - Error messages don't indicate root cause
   - Crash occurs without meaningful output

3. **Multiple code modifications have failed**
   - You've attempted fixes based on code review, but issues persist
   - Hypotheses about the bug have been proven wrong
   - Need to verify actual runtime behavior vs. assumptions

4. **Runtime behavior analysis is required**
   - Memory corruption (buffer overflow, use-after-free, double free)
   - Intermittent bugs that only occur under specific conditions
   - Need to inspect variable values, registers, or memory at specific execution points
   - Assembly-level debugging required (ABI mismatches, compiler optimization issues)

**Do NOT use this skill when:**
- Error messages clearly indicate the problem location and cause
- The bug can be identified through code review alone
- Simple syntax or type errors that the compiler identifies
- First attempt at fixing an issue (try direct code analysis first)

---

## Part 1: Debugging Mindset

### 1.1 Scientific Method: Observe → Hypothesize → Verify → Conclude

Debugging is a structured reasoning process, not random trial and error.

- **Observe**: Collect all symptoms (error messages, crash signals, abnormal output, logs)
- **Hypothesize**: Propose 2-3 candidate causes based on symptoms
- **Verify**: Design experiments to confirm or eliminate hypotheses (set breakpoints, inspect variables, modify input)
- **Conclude**: After confirming root cause, understand "why" not just "what"

**Anti-patterns:**
- Do NOT change code randomly upon seeing an error
- Do NOT assume a bug has only one cause
- Do NOT ignore intermittent bugs (they are often the most severe)

### 1.2 Binary Search Localization

The most efficient general-purpose localization strategy:

1. Set a breakpoint at the midpoint of the execution path
2. Check if the state is already abnormal at that point
3. If abnormal → bug is in the first half; if normal → bug is in the second half
4. Repeat, eliminating half the code each time

**Tools:** `lldb_setBreakpoint` → `lldb_evaluate` → `lldb_continue`

### 1.3 Minimal Reproduction

Before debugging, simplify the problem:

- Find the simplest input that triggers the bug
- Remove unrelated code paths and dependencies
- Stable reproduction is a prerequisite for effective debugging
- For intermittent bugs: consider race conditions, uninitialized variables, environment differences

### 1.4 Pre-Debugging Preparation

Ensure the binary can be effectively debugged:

- Compile with `-g` (debug symbols) and `-O0` (no optimization): `gcc -g -O0 -Wall -o program program.c`
- Optimized code may eliminate variables or reorder instructions, making debugger behavior unexpected
- If only a release binary is available (no symbols), refer to the "Binary-Only Debugging" section

---

## Part 2: Core Workflow

**🚨 TIMEOUT PROTECTION IS MANDATORY FOR ALL WORKFLOWS 🚨**

Every workflow in this section MUST follow timeout protection rules. Programs can hang due to:
- **Infinite loops** (missing/wrong termination condition)
- **Deadlocks** (circular lock dependencies)
- **Blocking I/O** (waiting for network/user input)
- **Resource starvation** (waiting for unavailable resources)

**Universal Safety Pattern:**
```
1. Execute operation (launch/continue/step)
2. Set explicit timeout based on operation type
3. Call lldb_pause() to force stop after timeout
4. Call lldb_pollEvents() to check state
5. Call lldb_threads() to verify stop reason
6. Analyze stopReason to determine next action
```

**NEVER assume a process will stop naturally. ALWAYS force verification.**

### 2.1 Basic Debugging Flow (with Timeout Protection)

1. **Initialize session** → `lldb_initialize()` returns sessionId
2. **Load binary** → `lldb_createTarget(sessionId, file="/path/to/binary")`
3. **Set breakpoints** (optional) → `lldb_setBreakpoint(sessionId, symbol="main")`
4. **Launch process** → `lldb_launch(sessionId)`
5. **Wait with timeout** → [Wait 5 seconds max for breakpoint/crash]
6. **Force stop** → `lldb_pause(sessionId)` **(MANDATORY - prevents hang)**
7. **Check state** → `lldb_pollEvents(sessionId)` → `lldb_threads(sessionId)`
8. **Analyze stop reason**:
   - If `stopReason == "breakpoint"` → Normal, proceed
   - If `stopReason == "exception"` → Crash, analyze
   - If `stopReason == "signal"` → Force-paused, check location
   - If process still running → Call `lldb_pause()` again
9. **Debug loop** (with hang detection):
   - Inspect state → `lldb_evaluate`, `lldb_stackTrace`
   - Step → `lldb_stepOver` / `lldb_stepIn`
   - **[Wait 2s MAXIMUM]** → `lldb_pause` **(MANDATORY)**
   - `lldb_pollEvents` → `lldb_threads` → Check if step completed
   - If step didn't complete → **Hang detected**, analyze with `lldb_stackTrace`
   - Continue → `lldb_continue`
   - **[Wait N seconds MAXIMUM]** → `lldb_pause` **(MANDATORY)**
   - `lldb_pollEvents` → `lldb_threads` → Check state
10. **Hang Detection** (if process seems stuck):
    - First snapshot: `lldb_pause` → `lldb_stackTrace` → Record location
    - Resume: `lldb_continue` → [Wait 2s] → `lldb_pause`
    - Second snapshot: `lldb_stackTrace` → Compare with first
    - **If same location** → Confirmed hang (infinite loop/deadlock)
    - **If different locations** → Process is progressing (may be slow)
11. **Terminate** → `lldb_terminate(sessionId)`

**Key difference from traditional LLDB:** Always use explicit timeouts and force-pause. Never assume the process will stop naturally.

**Timeout Selection Guide:**
- Known fast code path: 3-5 seconds
- Unknown code behavior: 5-10 seconds
- Code with I/O operations: 10-15 seconds
- If timeout expires: ALWAYS call `lldb_pause()` before any inspection

### 2.2 Two Ways to Start Debugging

There are two distinct approaches to begin debugging, depending on whether you control process startup:

#### Approach 1: Launch a New Process

**When to use:**
- You want to debug a program from the very beginning
- You need to control command-line arguments or environment variables
- You're debugging startup/initialization code
- The program hasn't started yet

**Workflow (with timeout protection):**
```
1. lldb_initialize()                        # Create session
2. lldb_createTarget(sessionId, file="...")  # Load executable
3. lldb_setBreakpoint(sessionId, ...)       # Set breakpoints (optional)
4. lldb_launch(sessionId, args=[], env={})  # Launch with args/env
5. [Wait 5 seconds max]                     # Timeout for breakpoint hit
6. lldb_pause(sessionId)                    # Force stop (safety)
7. lldb_pollEvents(sessionId)               # Check process state
8. lldb_threads(sessionId)                  # Verify stop reason
```

**Example:**
```
lldb_initialize()
→ sessionId: "debug-001"

lldb_createTarget(sessionId="debug-001", file="/path/to/program")
lldb_setBreakpoint(sessionId="debug-001", symbol="main")
lldb_launch(sessionId="debug-001", args=["--verbose", "input.txt"], env={"DEBUG": "1"})

# Wait for breakpoint hit (max 5 seconds)
[Wait 5 seconds]

# Force pause to ensure stopped state
lldb_pause(sessionId="debug-001")
lldb_pollEvents(sessionId="debug-001")
lldb_threads(sessionId="debug-001")

IF stopReason == "breakpoint":
  → Successfully hit breakpoint at main
ELSE:
  → Process was force-stopped, check where it stopped
  lldb_stackTrace(sessionId="debug-001")
```

**Security requirement:** Requires `LLDB_MCP_ALLOW_LAUNCH=1` environment variable in MCP configuration.

#### Approach 2: Attach to Running Process

**When to use:**
- The program is already running (perhaps started by another system)
- You want to debug a long-running service or daemon
- You need to inspect a process that's currently misbehaving
- You don't want to restart the process

**Workflow (with timeout protection):**
```
1. lldb_initialize()                           # Create session
2. lldb_createTarget(sessionId, file="...")    # Load executable (same binary as running process)
3. lldb_attach(sessionId, pid=1234)           # Attach by PID
   OR
   lldb_attach(sessionId, name="program_name") # Attach by process name
4. lldb_pollEvents(sessionId)                  # Check process state (will be "stopped")
5. lldb_threads(sessionId)                     # Verify process was successfully paused
6. lldb_stackTrace(sessionId)                  # Check where process was when attached
7. lldb_setBreakpoint(sessionId, ...)          # Set breakpoints while attached
8. lldb_continue(sessionId)                    # Resume execution
9. [Wait N seconds - MAXIMUM 15s for attach]  # Timeout for breakpoint hit
10. lldb_pause(sessionId)                      # Force stop (MANDATORY - safety measure)
11. lldb_pollEvents(sessionId)                 # Check current state
12. lldb_threads(sessionId)                    # Verify stop reason

IMPORTANT: If attaching to a hung process:
- Skip step 8 (don't continue)
- Use steps 4-6 to diagnose where it's hung
- Compare with a second snapshot after brief resume
```

**Example:**
```
# First, find the process PID (using system tools)
# $ ps aux | grep myapp
# user  12345  0.0  0.1  ...  myapp

lldb_initialize()
→ sessionId: "debug-002"

lldb_createTarget(sessionId="debug-002", file="/path/to/myapp")
lldb_attach(sessionId="debug-002", pid=12345)
lldb_pollEvents(sessionId="debug-002")
→ processAttached, process is stopped

lldb_setBreakpoint(sessionId="debug-002", symbol="process_request")
lldb_continue(sessionId="debug-002")

# Wait for breakpoint hit (max 15 seconds for this example)
[Wait 15 seconds]

# Force pause to ensure stopped state
lldb_pause(sessionId="debug-002")
lldb_pollEvents(sessionId="debug-002")
lldb_threads(sessionId="debug-002")

IF stopReason == "breakpoint":
  → Hit breakpoint at process_request
ELSE:
  → Process was force-stopped elsewhere
  lldb_stackTrace(sessionId="debug-002")
  → Check where it's currently executing
```

**Security requirement:** Requires `LLDB_MCP_ALLOW_ATTACH=1` environment variable in MCP configuration.

**Key differences:**

| Aspect | Launch | Attach |
|--------|--------|--------|
| **Process control** | You start the process | Process is already running |
| **Arguments/Environment** | Full control via `lldb_launch()` | Cannot modify (already set) |
| **Debugging from start** | Yes, can debug initialization | No, misses early execution |
| **Initial state** | Stopped at entry or first breakpoint | Stopped immediately upon attach |
| **Use case** | New debugging session | Inspect live/hanging process |
| **Permission needed** | `LLDB_MCP_ALLOW_LAUNCH=1` | `LLDB_MCP_ALLOW_ATTACH=1` |

**Important notes:**
- When attaching, the process is **paused immediately**. You must call `lldb_continue()` to resume it.
- When launching, the process starts and runs until it hits a breakpoint or exits.
- Both approaches require the same `lldb_createTarget()` step to load the binary file.
- For attach, the target binary path should match the running process's executable.

### 2.3 Crash Analysis Flow (with timeout protection)

1. **Initialize and load target**
   ```
   lldb_initialize()
   lldb_createTarget(sessionId, file="/path/to/crashing_program")
   ```

2. **Launch process (let it crash, but with timeout)**
   ```
   lldb_launch(sessionId)

   # Wait for crash (max 10 seconds - adjust based on expected crash time)
   [Wait 10 seconds]

   # Force pause if still running (might not have crashed)
   lldb_pause(sessionId)
   ```

3. **Check if process crashed**
   ```
   lldb_pollEvents(sessionId)
   lldb_threads(sessionId)

   IF stopReason == "exception" or "signal":
     → Process crashed (proceed to analysis)
   ELSE IF stopReason == "none" or process still running:
     → Process didn't crash in expected time
     → May need longer timeout or different input
   ```

4. **Analyze crash**
   ```
   lldb_stackTrace(sessionId)           # Get crash location
   lldb_readRegisters(sessionId)        # Check register state
   lldb_disassemble(sessionId, count=10) # View crash instruction
   lldb_analyzeCrash(sessionId)         # Security assessment
   lldb_getSuspiciousFunctions(sessionId) # Find dangerous functions
   ```

5. **Inspect crash context**
   ```
   lldb_evaluate(sessionId, "variable_name")  # Check variable values
   lldb_readMemory(sessionId, address, size)  # Inspect memory
   ```

**Example: Buffer Overflow Crash Analysis**
```
lldb_initialize()
→ sessionId: "crash-001"

lldb_createTarget(sessionId="crash-001", file="/path/to/vulnerable_program")
lldb_launch(sessionId="crash-001", args=["A" * 200])  # Trigger overflow

# Wait for crash (should happen quickly for overflow)
[Wait 5 seconds]

lldb_pause(sessionId="crash-001")
lldb_pollEvents(sessionId="crash-001")
lldb_threads(sessionId="crash-001")
→ stopReason: "exception", signal: SIGSEGV

lldb_stackTrace(sessionId="crash-001")
→ Shows corrupted stack frames

lldb_readRegisters(sessionId="crash-001")
→ rip/pc pointing to invalid address (0x41414141 - the 'A' characters)

lldb_analyzeCrash(sessionId="crash-001")
→ exploitability: "EXPLOITABLE - control flow hijack"

lldb_getSuspiciousFunctions(sessionId="crash-001")
→ Found: strcpy, sprintf in call stack
```

### 2.4 Key Principle: Interactive & Iterative

Each tool call's result informs your next action. Do NOT pre-plan all steps — debug iteratively based on runtime state.

**Critical rule:** Always call `lldb_pollEvents` after state-changing operations (`lldb_launch`, `lldb_continue`, `lldb_stepOver`, `lldb_stepIn`, `lldb_stepOut`).

### 2.5 Timeout Protection: Preventing Debugger Hangs

**CRITICAL: Programs can hang indefinitely (infinite loops, deadlocks). Always use timeout protection to prevent the debugger from getting stuck.**

#### The Problem

When debugging programs with infinite loops or deadlocks:
- `lldb_continue` may never return
- `lldb_pollEvents` may wait forever for a state change that never comes
- The debugging session becomes unresponsive

#### Solution: Proactive Timeout Strategy

**Never wait indefinitely for a process to stop naturally.** Use this pattern:

```
1. lldb_continue(sessionId)          # Resume execution
2. Wait briefly (3-10 seconds)       # Give program time to hit breakpoint or exit
3. lldb_pause(sessionId)             # Force stop if still running
4. lldb_pollEvents(sessionId)        # Check current state
5. lldb_threads(sessionId)           # Analyze where execution stopped
```

#### Recommended Timeout Values

| Operation | Recommended Timeout | Reasoning |
|-----------|-------------------|-----------|
| Normal execution to breakpoint | 5 seconds | Sufficient for most code paths |
| Loop-heavy code | 10 seconds | Allow for iteration but prevent true infinite loops |
| I/O operations (network, disk) | 15 seconds | External dependencies may be slow |
| Startup/initialization | 20 seconds | Loading and setup can take time |
| Known fast operations | 2 seconds | Quick sanity check |

**Important:** These are maximums. If you expect the operation to complete faster, use a shorter timeout.

#### Implementation Pattern

**Pattern 1: Continue with timeout**
```
lldb_continue(sessionId)
→ Process running

# Wait briefly for natural stop
[Wait 5 seconds using system sleep or timeout]

# Force pause if still running
lldb_pause(sessionId)
→ Process paused

lldb_pollEvents(sessionId)
→ Check if stopped at breakpoint or forced pause

IF event shows breakpoint hit:
  → Program hit breakpoint naturally (good)
ELSE IF stopReason == "none" or "signal":
  → Program was force-paused, likely in loop or waiting
  → lldb_stackTrace to see where it's stuck
```

**Pattern 2: Step operations with timeout**
```
lldb_stepOver(sessionId)
→ Stepping

[Wait 2 seconds]  # Steps should be fast

lldb_pause(sessionId)  # Safety measure
lldb_pollEvents(sessionId)

IF step completed:
  → Normal step
ELSE:
  → Step is taking too long (possible infinite loop inside the stepped function)
  → Consider using stepOut or setting breakpoint at return address
```

#### Detecting Infinite Loops

After force-pausing a suspected infinite loop:

```
lldb_pause(sessionId)
lldb_stackTrace(sessionId)
→ Note the current location (function + line number)

lldb_continue(sessionId)
[Wait 2 seconds]
lldb_pause(sessionId)
lldb_stackTrace(sessionId)
→ Check location again

IF both stack traces show same location:
  → Confirmed infinite loop at that location
  → lldb_evaluate to check loop condition variables
ELSE:
  → Program is making progress, may just be slow
```

#### Example: Safe Continue Pattern

```
# Set breakpoint first
lldb_setBreakpoint(sessionId, symbol="main")
lldb_continue(sessionId)

# Wait up to 5 seconds for breakpoint hit
import time
time.sleep(5)

# Ensure process is stopped
lldb_pause(sessionId)
lldb_pollEvents(sessionId)

# Check result
lldb_threads(sessionId)
IF stopReason == "breakpoint":
  → Success: hit breakpoint naturally
ELSE:
  → Process was running elsewhere, now force-stopped
  → lldb_stackTrace to see where it was
```

**Key principle: NEVER assume the process will stop on its own. Always set a timeout and force-pause.**

---

## Part 2.6: Complete Debugging Example with Timeout Protection

This example demonstrates a full debugging session with proper timeout handling:

**Scenario:** Debug a program that processes user input and may hang on invalid input.

```
# Step 1: Initialize
lldb_initialize()
→ sessionId: "debug-session-001"

# Step 2: Load target
lldb_createTarget(sessionId="debug-session-001", file="/path/to/process_data")

# Step 3: Set initial breakpoint
lldb_setBreakpoint(sessionId="debug-session-001", symbol="main")

# Step 4: Launch with timeout protection
lldb_launch(sessionId="debug-session-001", args=["input.txt"])
[Wait 5 seconds]  # Should hit main quickly
lldb_pause(sessionId="debug-session-001")
lldb_pollEvents(sessionId="debug-session-001")
lldb_threads(sessionId="debug-session-001")
→ stopReason: "breakpoint" at main - Good!

# Step 5: Set breakpoint at suspect function
lldb_setBreakpoint(sessionId="debug-session-001", symbol="parse_input")

# Step 6: Continue to parse_input
lldb_continue(sessionId="debug-session-001")
[Wait 5 seconds]
lldb_pause(sessionId="debug-session-001")
lldb_pollEvents(sessionId="debug-session-001")
lldb_threads(sessionId="debug-session-001")
→ stopReason: "breakpoint" at parse_input - Good!

# Step 7: Inspect input parameter
lldb_evaluate(sessionId="debug-session-001", "input_buffer")
→ value: "malformed_data_xyz@@@"

# Step 8: Step through parse logic with timeout
lldb_stepOver(sessionId="debug-session-001")
[Wait 2 seconds]
lldb_pause(sessionId="debug-session-001")
lldb_pollEvents(sessionId="debug-session-001")

lldb_stepOver(sessionId="debug-session-001")
[Wait 2 seconds]
lldb_pause(sessionId="debug-session-001")
lldb_pollEvents(sessionId="debug-session-001")

lldb_stepOver(sessionId="debug-session-001")
[Wait 2 seconds]
lldb_pause(sessionId="debug-session-001")
lldb_threads(sessionId="debug-session-001")
→ stopReason: "signal" (force-paused, step didn't complete)

# Step 9: Detected hang during step - investigate
lldb_stackTrace(sessionId="debug-session-001")
→ Stopped in "validate_token" at line 87 (inside a while loop)

# Step 10: Confirm infinite loop with double-snapshot
# First snapshot
lldb_disassemble(sessionId="debug-session-001", count=5)
→ Note current instruction address: 0x100001234

lldb_continue(sessionId="debug-session-001")
[Wait 2 seconds]
lldb_pause(sessionId="debug-session-001")

# Second snapshot
lldb_disassemble(sessionId="debug-session-001", count=5)
→ Same instruction address: 0x100001234
→ Confirmed: infinite loop

# Step 11: Diagnose loop condition
lldb_evaluate(sessionId="debug-session-001", "token_index")
→ value: 157

lldb_evaluate(sessionId="debug-session-001", "input_length")
→ value: 150

# Found the bug: token_index > input_length but loop continues
# This is caused by missing boundary check

# Step 12: Verify fix hypothesis by modifying variable
lldb_command(sessionId="debug-session-001", "expr token_index = 0")
lldb_continue(sessionId="debug-session-001")
[Wait 3 seconds]
lldb_pause(sessionId="debug-session-001")
lldb_pollEvents(sessionId="debug-session-001")
lldb_threads(sessionId="debug-session-001")
→ Process exited normally

# Conclusion: Bug confirmed - missing boundary check in validate_token
# Fix: Add condition "token_index < input_length" to while loop

# Step 13: Clean up
lldb_terminate(sessionId="debug-session-001")
```

**Key takeaways from this example:**

1. ✅ Used timeout after every `launch`, `continue`, and `step`
2. ✅ Always called `pause` before `pollEvents` and `threads`
3. ✅ Detected infinite loop by double-snapshot technique
4. ✅ Used short timeouts (2-5s) to catch hang quickly
5. ✅ Never waited indefinitely for process state change
6. ✅ Session remained responsive throughout debugging

**Without timeout protection, this session would have:**
- Hung indefinitely during the third `stepOver`
- Required terminal interruption or process kill
- Lost all debugging context and progress

---

## Part 3: Debugging by Error Type

### 3.1 Compile Errors (No LLDB needed)

Compile errors are static — the compiler tells you the location and cause.

- Fix from the first error (later errors may be cascading)
- Common types: syntax errors, type errors, linker errors (`undefined reference`), missing headers
- Ensure correct flags: `gcc -g -O0 -Wall -o program program.c`

### 3.2 Runtime Crashes

#### 3.2.1 Null Pointer Dereference

**Signal:** SIGSEGV, access address near 0x0

**Diagnosis:**
1. `lldb_launch` → `lldb_pollEvents` → process stops with exception
2. `lldb_stackTrace` → locate crash function and line
3. `lldb_readRegisters` → check if rax/rdi/x0 is 0x0
4. `lldb_disassemble` → confirm which instruction dereferenced NULL
5. `lldb_analyzeCrash` → get exploitability assessment

**Root causes:** Uninitialized pointer; function returned NULL without caller check; conditional branch missed pointer assignment

#### 3.2.2 Buffer Overflow

**Signal:** SIGSEGV or SIGABRT (with stack protection); crash location may be far from actual overflow

**Diagnosis:**
1. `lldb_stackTrace` → corrupted frames (`<unknown>` or abnormal addresses) suggest stack overflow
2. `lldb_readRegisters` → rsp abnormal or rip/pc pointing to non-code region
3. Set breakpoint at suspect function → `lldb_evaluate` to check buffer size vs input length
4. `lldb_setWatchpoint` → set watchpoint just past buffer boundary to catch out-of-bounds writes
5. `lldb_readMemory` → inspect memory around the buffer

**Root causes:** Unsafe functions (`strcpy`, `sprintf`); off-by-one loop errors; unchecked external input length

#### 3.2.3 Use-After-Free

**Signal:** SIGSEGV, accessing freed heap memory

**Diagnosis:**
1. `lldb_stackTrace` → locate code accessing freed memory
2. `lldb_evaluate` → check pointer value (may point to recycled address)
3. Set breakpoint at `free()` → confirm free timing
4. `lldb_setWatchpoint` → monitor address after free for re-writes
5. `lldb_readMemory` → check memory content (freed memory may contain sentinel values)

**Root causes:** Pointer not set to NULL after free; multiple pointers to same allocation; async/callback referencing freed resource

#### 3.2.4 Division by Zero

**Signal:** SIGFPE

**Diagnosis:**
1. `lldb_stackTrace` → locate the division line
2. `lldb_evaluate` → check divisor value (should be 0)
3. Trace back: how did divisor become 0? Set breakpoint at assignment

#### 3.2.5 Stack Overflow

**Signal:** SIGSEGV, rsp/sp extremely small or out of stack range

**Diagnosis:**
1. `lldb_stackTrace` → extremely deep call stack, possibly with repeated frames
2. `lldb_frames` → check recursion depth
3. `lldb_evaluate` → check termination condition variables in recursive function

**Root causes:** Missing recursion termination; termination logic error; overly large stack-allocated arrays

#### 3.2.6 Format String Vulnerability

**Signal:** Abnormal output, SIGSEGV

**Diagnosis:**
1. `lldb_setBreakpoint` at `printf`/`sprintf` calls
2. `lldb_evaluate` → check if format string parameter comes from user input
3. `lldb_readMemory` → inspect leaked stack data

**Root cause:** `printf(user_input)` instead of `printf("%s", user_input)`

#### 3.2.7 Double Free

**Signal:** SIGABRT (glibc detects double free)

**Diagnosis:**
1. `lldb_stackTrace` → locate the second `free()` call
2. `lldb_setBreakpoint(symbol="free")` → breakpoint on all free calls
3. `lldb_evaluate` → record pointer passed to each free, find duplicates

**Root causes:** Same pointer freed twice; multiple code paths both attempt to free same resource

### 3.3 Assembly-Level Errors

#### 3.3.1 Compiler Optimization Anomalies

**Symptom:** Code works at `-O0` but fails at `-O2`/`-O3`. Source looks correct.

**Diagnosis:**
1. `lldb_setBreakpoint(file, line)` at suspect code
2. `lldb_disassemble(count=20)` → view generated instructions
3. Compare `-O0` vs `-O2` disassembly: check if conditionals were removed, loops vectorized incorrectly
4. `lldb_readRegisters` → verify register values match source expectations
5. `lldb_evaluate` → if `<optimized out>`, use registers and memory instead

**Key indicators:**
- Conditional jumps deleted → compiler assumed condition via undefined behavior (UB)
- `<optimized out>` → variable eliminated, use `lldb_readRegisters` / `lldb_readMemory`

#### 3.3.2 Inline Assembly Errors

**Symptom:** Crash near `__asm__` / `asm volatile` code

**Diagnosis:**
1. `lldb_setBreakpoint` at function entry containing inline asm
2. `lldb_disassemble(count=40)` → view context around inline asm
3. `lldb_readRegisters` before entering asm block
4. `lldb_command(command="si")` + `lldb_readRegisters` → single-instruction step, compare registers
5. Check: clobbered-but-undeclared registers, rsp consistency, direction flag (DF) restoration

#### 3.3.3 ABI / Calling Convention Mismatch

**Symptom:** Parameters garbled across module calls, abnormal return values

**Diagnosis:**
1. `lldb_setBreakpoint(symbol="target_function")` → breakpoint at callee entry
2. `lldb_readRegisters` → check parameter registers
3. `lldb_selectFrame(frameIndex=1)` → switch to caller frame
4. `lldb_disassemble` → check how caller prepared parameters
5. Compare both sides for consistency

**Parameter Register Reference (x86_64 System V ABI):**

| Param # | Integer/Pointer | Float |
|---------|----------------|-------|
| 1st | rdi | xmm0 |
| 2nd | rsi | xmm1 |
| 3rd | rdx | xmm2 |
| 4th | rcx | xmm3 |
| 5th | r8 | xmm4 |
| 6th | r9 | xmm5 |
| 7th+ | stack | xmm6, xmm7, then stack |
| Return | rax (+rdx) | xmm0 (+xmm1) |

**ARM64 (Apple Silicon) ABI:**

| Param # | Integer/Pointer | Float |
|---------|----------------|-------|
| 1st-8th | x0 - x7 | d0 - d7 |
| 9th+ | stack | stack |
| Return | x0 (+x1) | d0 (+d1) |

#### 3.3.4 Stack Frame Corruption & Control Flow Hijack

**Symptom:** `lldb_stackTrace` shows `<unknown>` frames, return address pointing to non-code region

**Diagnosis:**
1. `lldb_readRegisters` → check rip/pc, rsp/sp, rbp/fp
2. `lldb_disassemble(addr=rip_value)` → is current instruction in legitimate code?
3. `lldb_readMemory(addr=rsp_value, size=128)` → inspect stack for overwritten return addresses or patterns like `0x41414141`
4. `lldb_listModules` → get legitimate code address ranges
5. `lldb_command(command="image lookup --address 0xADDRESS")` → query which module/function owns an address

**Key judgments:**
- `rip`/`pc` not in any module's code segment → control flow hijack (severe vulnerability)
- `rsp`/`sp` not 16-byte aligned → may cause SIGSEGV with SSE/NEON instructions
- `rbp`/`fp` chain broken → stack frame corruption

#### 3.3.5 Instruction-Level Exception Analysis

When a crash occurs on a specific machine instruction:

1. `lldb_disassemble(count=5)` → view crash instruction and context
2. Analyze by instruction type:

| Instruction | Example | Common Failure |
|------------|---------|----------------|
| Memory read | `mov rax, [rbx]` | rbx is NULL or unmapped |
| Memory write | `mov [rax], 0x42` | rax is NULL, read-only, or unmapped |
| Division | `div rcx` | rcx is 0 |
| Aligned access | `movaps [rsp+0x10], xmm0` | Address not 16-byte aligned |
| Indirect jump | `call [rax]` | rax points to non-code (corrupted function pointer) |
| Syscall | `syscall` | Illegal arguments |
| Privileged | `in al, dx` | User-mode executing kernel instruction |

3. `lldb_readRegisters` → read registers involved in the instruction
4. `lldb_readMemory(addr, size)` → check if target memory is accessible
5. `lldb_command(command="memory region 0xADDRESS")` → check memory region permissions (r/w/x)

#### 3.3.6 Binary-Only Reverse Debugging (No Source, No Symbols)

When you only have a stripped binary:

**Challenges:** `lldb_evaluate` unusable (no variable names); `lldb_stackTrace` shows only addresses; must rely entirely on assembly-level tools.

**Workflow:**

1. **Reconnaissance:**
   - `lldb_listModules` → understand binary structure
   - `lldb_searchSymbol(pattern="*")` → even stripped binaries may have dynamic symbols
   - `lldb_command(command="image dump sections")` → view segment info (.text, .data, .bss)

2. **Entry point:**
   - `lldb_searchSymbol(pattern="main")` → try to find main
   - `lldb_disassemble(addr=entry_address, count=30)` → disassemble entry code

3. **Runtime analysis:**
   - `lldb_setBreakpoint(symbol="malloc")` / `lldb_setBreakpoint(symbol="printf")` → break on library functions
   - `lldb_readRegisters` → infer arguments via parameter registers
   - `lldb_selectFrame(frameIndex=1)` → switch to caller, `lldb_disassemble` → analyze caller logic

4. **Data structure inference:**
   - `lldb_readMemory(addr, size=64)` → read pointer targets
   - `lldb_setWatchpoint(addr, size, write=True)` → watch critical data modifications

5. **Control flow tracing:**
   - `lldb_setBreakpoint(address=target_addr)` → break at key branch addresses
   - `lldb_command(command="si")` → single-instruction step
   - `lldb_readRegisters` → check flags register (RFLAGS/CPSR) for branch direction

### 3.4 Logic Errors

Program does not crash but produces incorrect results. This is the hardest error type to debug.

#### Strategy 1: Input-Output Comparison

1. Define a known-correct "input → expected output" test case
2. `lldb_setBreakpoint` at key function entry
3. `lldb_evaluate` → check function input parameters
4. `lldb_stepOver` → execute line by line, check intermediate results after each step
5. Find the first point where results diverge from expectations

#### Strategy 2: Conditional Breakpoints

When you know "it only fails when x > 100":

1. `lldb_setBreakpoint(symbol="process_data")`
2. `lldb_updateBreakpoint(breakpointId, condition="x > 100")`
3. Only stops when the abnormal condition is met

#### Strategy 3: Watchpoints to Track Variable Changes

When you know "a variable changed at some point, but not who changed it":

1. `lldb_evaluate("&my_var")` → get variable address
2. `lldb_setWatchpoint(address, size, write=True)` → watch writes
3. `lldb_continue` → stops automatically when variable is modified
4. `lldb_stackTrace` → see which function modified it

### 3.5 Hangs and Deadlocks

Program does not crash or exit — it appears stuck.

**CRITICAL: Use timeout protection when continuing execution. Never wait indefinitely.**

#### Automatic Hang Detection Protocol

**MANDATORY: Implement this protocol for ANY operation that may hang**

```
FUNCTION: detect_hang(sessionId, operation_name, max_wait_seconds)

  # Step 1: Get baseline before operation
  lldb_pause(sessionId)
  baseline_threads = lldb_threads(sessionId)
  baseline_trace = lldb_stackTrace(sessionId)
  baseline_location = extract_location(baseline_trace)  # file:line or address

  # Step 2: Execute the operation with timeout
  IF operation_name == "continue":
    lldb_continue(sessionId)
  ELSE IF operation_name == "stepOver":
    lldb_stepOver(sessionId)
  ELSE IF operation_name == "stepIn":
    lldb_stepIn(sessionId)

  # Step 3: Wait for completion with timeout
  [Wait max_wait_seconds]

  # Step 4: Force stop and check state
  lldb_pause(sessionId)                    # MANDATORY
  lldb_pollEvents(sessionId)
  current_threads = lldb_threads(sessionId)

  # Step 5: Analyze stop reason
  IF current_threads.stopReason == "breakpoint":
    RETURN "normal"  # Hit breakpoint as expected

  IF current_threads.stopReason == "exception":
    RETURN "crashed"  # Program crashed

  # Step 6: Suspected hang - verify with double snapshot
  current_trace = lldb_stackTrace(sessionId)
  current_location = extract_location(current_trace)

  # Brief resume to check if making progress
  lldb_continue(sessionId)
  [Wait 2 seconds]  # Short verification period
  lldb_pause(sessionId)

  verify_trace = lldb_stackTrace(sessionId)
  verify_location = extract_location(verify_trace)

  # Step 7: Compare locations to confirm hang
  IF current_location == verify_location:
    # Same location after brief execution = confirmed hang
    RETURN "hang_confirmed" + {
      "type": identify_hang_type(current_threads),
      "location": current_location,
      "threads": current_threads
    }
  ELSE:
    # Different locations = making progress (just slow)
    RETURN "slow_execution"
```

**Hang Type Identification:**
```
FUNCTION: identify_hang_type(threads_info)

  IF all_threads_in_same_function():
    RETURN "infinite_loop"

  IF multiple_threads_in_lock_wait():
    RETURN "deadlock"

  IF thread_in_io_function(read, recv, accept):
    RETURN "blocking_io"

  IF thread_in_sleep_function():
    RETURN "deliberate_wait"

  RETURN "unknown_hang"
```

**Recommended Timeouts by Operation:**

| Operation Type | Timeout | Rationale |
|---------------|---------|-----------|
| `lldb_continue` to known breakpoint | 5s | Should hit quickly |
| `lldb_continue` general execution | 10s | Allow reasonable progress |
| `lldb_stepOver` normal statement | 2s | Single statements are fast |
| `lldb_stepOver` function call | 5s | Function may be complex |
| `lldb_stepIn` | 3s | Entering function is fast |
| `lldb_stepOut` | 5s | May need to complete function |
| Program initialization | 15-20s | Loading and setup overhead |
| I/O-heavy operations | 15s | External dependencies |
| Suspected infinite loop | 3s | Want quick detection |
| Verification snapshot | 2s | Quick double-check |

#### Detection Workflow

1. **Launch with timeout protection:**
   ```
   lldb_launch(sessionId)
   [Wait 10 seconds max]
   lldb_pause(sessionId)
   lldb_pollEvents(sessionId)
   ```

2. **Check if program is hung:**
   ```
   lldb_threads(sessionId)
   → List all threads and their states
   ```

3. **Analyze each thread:**
   ```
   FOR each thread:
     lldb_stackTrace(sessionId, threadId=N)
     → Check what each thread is doing
   ```

4. **Identify hang type:**

   | Pattern | Diagnosis | Next Steps |
   |---------|-----------|------------|
   | All threads in same location | **Infinite loop** | Check loop variables with `lldb_evaluate` |
   | Multiple threads waiting | **Deadlock** | Check lock ownership and wait chains |
   | One thread in `read()`/`recv()` | **Blocking I/O** | Check file descriptors or network state |
   | Thread in `pthread_mutex_lock()` | **Lock contention** | Find lock holder |
   | Thread in `sleep()`/`nanosleep()` | **Deliberate wait** | May be normal behavior |

#### Infinite Loop Diagnosis

**Step 1: Confirm it's a loop (take two snapshots)**
```
# First snapshot
lldb_pause(sessionId)
lldb_stackTrace(sessionId)
→ Record location: function "process_data" at line 45

# Resume briefly
lldb_continue(sessionId)
[Wait 2 seconds]

# Second snapshot
lldb_pause(sessionId)
lldb_stackTrace(sessionId)
→ Check location again

IF both snapshots show same line:
  → Confirmed infinite loop
ELSE IF nearby lines (within 5 lines):
  → Tight loop (loop body is small)
ELSE:
  → Program is making progress
```

**Step 2: Inspect loop condition**
```
lldb_evaluate(sessionId, "loop_counter")
→ Check current value

lldb_evaluate(sessionId, "max_iterations")
→ Check termination condition

lldb_disassemble(sessionId, count=10)
→ View loop's assembly to understand branch logic
```

**Step 3: Check for infinite recursion**
```
lldb_frames(sessionId)
→ If frame count > 1000, likely stack overflow via recursion

IF many repeated frames:
  → Infinite recursion
  → lldb_evaluate termination condition variables
```

#### Deadlock Diagnosis

**Step 1: Find all waiting threads**
```
lldb_threads(sessionId)
→ Look for threads with stopReason indicating wait state

FOR each waiting thread:
  lldb_stackTrace(sessionId, threadId=N)
  → Note which lock/mutex each is waiting for
```

**Step 2: Map lock dependencies**
```
Thread 1: Holds lock A, waiting for lock B
Thread 2: Holds lock B, waiting for lock A
→ Classic deadlock (circular wait)
```

**Step 3: Identify culprit**
```
lldb_selectThread(sessionId, threadId=1)
lldb_evaluate(sessionId, "mutex_owner_id")
→ Check which thread owns the blocking lock

lldb_readRegisters(sessionId, threadId=1)
→ May reveal lock addresses in registers
```

**Step 4: Break the deadlock (for debugging purposes)**
```
# Option 1: Kill one thread's wait (dangerous, for analysis only)
lldb_command(sessionId, "thread return")
→ Force current thread to return from function

# Option 2: Modify lock state (requires deep understanding)
lldb_writeMemory(sessionId, address=lock_addr, bytes="00000000")
→ Release lock (may cause undefined behavior)
```

#### Blocking I/O Diagnosis

**Common blocking calls:**
- `read()`, `recv()`, `accept()` — waiting for data/connection
- `write()`, `send()` — waiting for buffer space
- `sleep()`, `nanosleep()` — deliberate delay
- `pthread_cond_wait()` — waiting for condition variable

**Diagnosis steps:**
```
lldb_stackTrace(sessionId)
→ Top frame shows blocking function

lldb_selectFrame(sessionId, frameIndex=1)
→ Switch to caller

lldb_evaluate(sessionId, "fd")
→ Check file descriptor number

lldb_evaluate(sessionId, "timeout")
→ Check if there's a timeout set (0 = infinite)
```

**Check file descriptor state (requires external tools):**
```
# Via lldb_command using shell
lldb_command(sessionId, "platform shell lsof -p <pid>")
→ List open file descriptors

# Check if fd is still valid
lldb_command(sessionId, "platform shell ls -l /proc/<pid>/fd/<fd>")
→ See what fd points to
```

#### Timeout Protection Pattern for Hang Diagnosis

**Always use this pattern when debugging potential hangs:**

```
# Initial launch with timeout
lldb_setBreakpoint(sessionId, symbol="main")
lldb_launch(sessionId)
[Wait 5 seconds]
lldb_pause(sessionId)

# Check if we hit main breakpoint
lldb_pollEvents(sessionId)
lldb_threads(sessionId)

IF stopReason == "breakpoint":
  → Normal execution, hit main

  # Continue to next point
  lldb_continue(sessionId)
  [Wait 10 seconds]
  lldb_pause(sessionId)

  # Analyze hang location
  lldb_stackTrace(sessionId)
  → See where program got stuck

ELSE:
  → Process never reached main (stuck in initialization)
  lldb_stackTrace(sessionId)
  → Check initialization code
```

**Key principle: Set progressively longer timeouts based on expected execution time, but ALWAYS set a timeout.**

### 3.6 Performance Issues

Program runs but is slow. LLDB is not the primary tool for profiling, but can help in specific scenarios.

1. `lldb_pause` → pause during the slow period
2. `lldb_stackTrace` → see current execution point (if multiple pauses land in the same place, it's a hotspot)
3. `lldb_setBreakpoint` + `lldb_evaluate` → check loop iteration counts
4. Conditional breakpoint: `lldb_updateBreakpoint(condition="i > 1000000")` → stop when loop count is excessive

---

## Part 4: Large Project Localization Strategies

### 4.1 Top-Down: Trace from Crash Stack

1. `lldb_stackTrace` → get full call stack
2. Start from top frame (crash point), inspect downward (toward callers)
3. `lldb_selectFrame(frameIndex=N)` → switch to caller context
4. `lldb_evaluate` → check parameters at each level
5. Find the first frame where parameters are already wrong — that's the root cause layer

### 4.2 Bottom-Up: Trace from Input Entry

1. `lldb_setBreakpoint` at the input-handling entry function
2. `lldb_launch(args=["problematic_input"])` → launch with the problematic input
3. `lldb_stepOver` / `lldb_stepIn` → trace the input processing flow step by step
4. Check data validity at each step

### 4.3 Binary Search: Cut into the Middle of Call Chain

1. `lldb_stackTrace` → get call chain
2. Set breakpoint at a function in the middle of the chain
3. Check data state: abnormal → bug is in upper half; normal → bug is in lower half
4. Repeat, typically 3-4 rounds to locate the specific function

### 4.4 Symbol Search: Find Relevant Code Quickly

1. `lldb_searchSymbol(pattern="parse*")` → search matching function names
2. `lldb_searchSymbol(pattern="*buffer*")` → search symbols related to key concepts
3. `lldb_listModules` → determine if issue is in main program or a library
4. Set targeted breakpoints based on search results

### 4.5 Module Isolation

1. `lldb_listModules` → list all loaded .dylib / .so files
2. `lldb_stackTrace` → the module containing the crash frame is the directly affected module
3. `lldb_searchSymbol(pattern="suspect_func", module="libfoo.dylib")` → search within a specific module

---

## Part 5: Multiple Bug Handling Strategy

### 5.1 Identify Dependencies Between Bugs

- **Causal chain**: Memory corruption (bug A) → subsequent access of corrupted data causes crash (bug B). Fixing A eliminates B.
- **Common root cause**: Bugs A and B both stem from the same wrong assumption. Fixing the root cause resolves both.
- **Independent**: Two unrelated bugs coexist. Fix separately.

**Diagnostic tips:**
- Debug with input that triggers only bug A — does bug B also appear?
- Temporarily patch bug A — does bug B still reproduce?
- Compare call stacks — shared frames suggest dependency

### 5.2 Priority Order

| Priority | Error Type | Reason |
|----------|-----------|--------|
| 1 (Highest) | Memory corruption (overflow, UAF, double free) | Causes unpredictable cascading failures |
| 2 | Crashes (null pointer, div-by-zero, stack overflow) | Prevents normal execution |
| 3 | Logic errors | Program runs but produces wrong results |
| 4 | Performance issues | Correct but slow |
| 5 (Lowest) | Resource leaks | No short-term impact, long-term problems |

**Principle:** Fix memory corruption bugs first — they "contaminate" other code behavior, making other bugs unreliable to debug.

### 5.3 Isolation Testing

1. List all known bugs
2. Prepare independent reproduction cases for each
3. Fix in priority order (highest first)
4. After each fix: verify the fix, re-run all other bug reproduction cases, record which bugs were affected
5. Update bug list, repeat

### 5.4 Core Dump Comparison

1. Before fix: `lldb_createCoredump(path="before_fix.core")` → save crash scene
2. Apply fix
3. After fix: re-run, save another core dump if issues remain
4. Load both with `lldb_loadCore` and compare call stacks, register values, memory contents

---

## Part 6: Multi-Session Iterative Debugging

### 6.1 Core Concept

Complex bugs often cannot be fully located in a single debugging session. Treat debugging as an **iterative experiment process**: each session has a clear goal, record conclusions afterward, then decide the next session's direction.

**Reasons to allow multiple sessions:**
- A single session may only verify one hypothesis
- Different breakpoint/watchpoint strategies require restarting from program start
- Some bugs need multiple triggers with different inputs to see the full picture
- Previous session findings lead to new investigation directions

### 6.2 Session Count Threshold

**Upper limit: 10 debugging sessions per bug.**

| Session Count | Expected State |
|--------------|---------------|
| 1-3 | Normal exploration: collect info, verify initial hypotheses |
| 4-6 | Should have narrowed scope: focused on specific module/function |
| 7-9 | Deep phase: tracking at instruction/variable level |
| 10 | Reflection point: pause debugging, reassess overall approach |

If 10 sessions haven't found the root cause, reconsider:
- Are hypotheses correct? Missing possibilities?
- Need a completely different debugging method? (e.g., switch to static analysis/code review)
- Is the problem deeper than expected? (compiler bug, hardware issue, race condition)

### 6.3 Debugging Conclusion Document

Maintain a structured document as cross-session "memory":

```markdown
# Debug Record: [Bug Summary]

## Goal
[Problem description, reproduction steps, expected vs actual behavior]

## Current Conclusion
[Continuously updated summary conclusion]

## Session Log

### Session 1
- **Goal:** [What this session aims to verify]
- **Actions:** [Key debugging commands executed]
- **Findings:**
  - [Finding 1]
  - [Finding 2]
- **Conclusion:** [This session's conclusion]
- **Next step:** [What the next session should do based on this conclusion]

### Session 2
- **Goal:** [Continues from Session 1's "Next step"]
- ...

## Eliminated Hypotheses
- [Hypothesis A] — eliminated in session N via [method]

## Pending Hypotheses
- [Hypothesis C] — plan to verify in next session via [method]
```

**Usage rules:**
1. Update document immediately after each session
2. Review document before starting each new session
3. Reference document when making debugging command decisions
4. Keep "Current Conclusion" always up to date

### 6.4 Decision Flow

```
Start Debugging
  │
  ├─ First session?
  │    ├─ Yes → Create debug document → Set initial hypotheses → Start session
  │    └─ No → Review document → Check:
  │              ├─ Session count < 10?
  │              │    ├─ Yes → Set goal from last "Next step" → Start session
  │              │    └─ No → Pause, reassess overall approach
  │              └─ Did last conclusion point to a clear direction?
  │                   ├─ Yes → Go deeper in that direction
  │                   └─ No → Review all eliminated hypotheses, try new angle
  │
  ├─ During session
  │    ├─ Before each command: reference existing conclusions in document
  │    ├─ New finding → compare with existing conclusions (consistent? contradictory? supplementary?)
  │    └─ Session goal achieved or cannot continue → End session
  │
  └─ Session ended
       ├─ Update document (findings, conclusion, next step, eliminated hypotheses)
       ├─ Update "Current Conclusion"
       └─ Judge:
            ├─ Root cause located → End debugging, output final report
            └─ Need to continue → Return to "Not first session" branch
```

---

## Part 7: Decision Tree Patterns

### Pattern 1: Safe Continue with Timeout

```
BEFORE calling lldb_continue:
  1. Decide maximum wait time (based on expected operation)
  2. Set timeout value (default: 5-10 seconds)

EXECUTE:
  lldb_continue(sessionId)
  [Wait <timeout> seconds]
  lldb_pause(sessionId)
  lldb_pollEvents(sessionId)
  lldb_threads(sessionId)

ANALYZE stopReason:
  IF stopReason == "breakpoint":
    → Successfully hit breakpoint naturally
    → Proceed with inspection

  IF stopReason == "exception":
    → Program crashed during execution
    → Go to CRASH_ANALYSIS

  IF stopReason == "signal" (SIGSTOP, SIGINT):
    → Force-paused by lldb_pause (normal timeout behavior)
    → Check where it stopped: lldb_stackTrace
    → Decide: infinite loop? slow operation? need longer timeout?

  IF stopReason == "none" or state == "running":
    → Process still running (lldb_pause failed?)
    → Call lldb_pause again
    → If still running: lldb_terminate and restart session

  IF stopReason == "exited":
    → Program completed normally
    → lldb_pollEvents to get exit code
```

### Pattern 2: After `lldb_pollEvents`

```
IF event.state == "stopped":
  → lldb_threads(sessionId)
    IF stopReason == "exception" → Go to CRASH_ANALYSIS
    IF stopReason == "breakpoint" → Go to BREAKPOINT_INSPECTION
    IF stopReason == "signal" → Check if force-paused or actual signal
    IF stopReason == "trace" → Step completed, continue stepping or inspect

IF event.state == "running":
  → Process is still executing
  → [Wait additional time] OR lldb_pause immediately
  → Re-check with lldb_pollEvents

IF event.state == "exited":
  → Process terminated
  → Check exit code for success/failure
```

### Pattern 3: After `lldb_stackTrace`

- Top frame in `main` → check argc/argv or main logic
- Top frame in library (libc, libsystem) → look at caller frame
- Top frame shows `<unknown>` → use `lldb_disassemble` for assembly analysis
- Multiple frames in same function → likely recursion issue
- **Same frame appears in consecutive snapshots** → infinite loop at that location

### Pattern 4: After `lldb_readRegisters`

- `rax/x0 == 0x0` → NULL pointer involved
- `rip/pc` in invalid range → control flow corrupted
- `rsp/sp` very small → stack overflow
- Segment registers point to invalid areas → memory corruption

### Pattern 5: After `lldb_evaluate`

- Value is NULL → add null check or investigate why
- Value is a huge number → integer overflow or uninitialized
- String contains unexpected data → input validation issue
- Pointer points to freed memory → use-after-free bug

### Pattern 6: Conditional Stepping (Find where variable becomes invalid) - WITH TIMEOUT

```
step_count = 0
LOOP:
  1. lldb_stepOver(sessionId)
  2. [Wait 2 seconds]  # Step timeout
  3. lldb_pause(sessionId)  # Ensure stopped
  4. lldb_pollEvents(sessionId)
  5. lldb_threads(sessionId)

     IF stopReason != "trace" AND stopReason != "breakpoint":
        → Step took too long (infinite loop in stepped function?)
        → lldb_stackTrace to see where it got stuck
        → BREAK

  6. lldb_evaluate(sessionId, "ptr")
     IF new_value == "0x0" AND old_value != "0x0":
        → Found it! ptr was set to NULL at this line
        → lldb_stackTrace to get exact location
        → BREAK

     step_count++
     IF step_count > 100:
        → Too many steps, try different approach (breakpoint + watchpoint)
        → BREAK

     REPEAT
```

### Pattern 7: Timeout Decision Making

```
WHEN deciding timeout value:

  IF operation is "hitting known breakpoint in fast code":
    → Use 2-5 seconds

  IF operation is "general continue without specific expectation":
    → Use 5-10 seconds

  IF operation involves "I/O, network, or external resources":
    → Use 10-20 seconds

  IF operation is "initialization or first launch":
    → Use 15-20 seconds

  IF operation is "debugging suspect infinite loop":
    → Use 2-3 seconds (want to catch it quickly)

  IF you've force-paused and want to "verify it's truly stuck":
    → Continue, wait 2 seconds, pause again
    → Compare stack traces
    → If same location: confirmed stuck

ALWAYS:
  - Document timeout choice in debug notes
  - Adjust timeout based on previous observations
  - If unsure: start with shorter timeout (5s), increase if needed
```

---

## Part 8: Quick Reference

### By Scenario

| Scenario | Recommended Tool Combination (⏱️ = timeout required) |
|----------|------------------------------|
| Program crashed, find cause | `launch` → **⏱️[5s]** → `pause` → `pollEvents` → `threads` → `stackTrace` → `readRegisters` → `disassemble` → `analyzeCrash` |
| Inspect specific function behavior | `setBreakpoint(symbol=...)` → `launch` → **⏱️[5s]** → `pause` → `pollEvents` → `evaluate` |
| Track when a variable is modified | `evaluate("&var")` → `setWatchpoint` → `continue` → **⏱️[10s]** → `pause` → `pollEvents` → `stackTrace` |
| **Program appears stuck / infinite loop** | **`pause` → `threads` → `stackTrace` (snapshot 1) → `continue` → ⏱️[2s] → `pause` → `stackTrace` (snapshot 2) → compare locations** |
| **Suspected deadlock** | **`pause` → `threads` (check all states) → FOR each thread: `stackTrace(threadId)` → identify circular lock wait** |
| **Program hangs at startup** | **`launch` → ⏱️[15-20s] → `pause` → `stackTrace` → check if in `dyld`/constructors → increase timeout or investigate** |
| **Step operation never returns** | **After `stepOver/In/Out` → ⏱️[2-3s] → `pause` → `stackTrace` → if in loop: use `stepOut` or `setBreakpoint` past it** |
| **Can't tell if hung or slow** | **`pause` → `stackTrace` → note PC → `continue` → ⏱️[2s] → `pause` → `stackTrace` → compare PC values** |
| **Multiple threads, one hung** | **`pause` → `threads` → FOR each: `stackTrace(threadId)` → find thread not in syscall wait** |
| **Blocking I/O causing hang** | **`pause` → `stackTrace` → check for `read/recv/accept/sleep` → `evaluate` file descriptor variables** |
| Line-by-line debugging | `setBreakpoint` → `stepOver` / `stepIn` → **⏱️[2s]** → `pause` → `pollEvents` → `evaluate` |
| Binary-only (no source) | `disassemble` → `readRegisters` → `readMemory` → `searchSymbol` |
| Compiler optimization anomaly | Compare `-O0`/`-O2` `disassemble` output → `readRegisters` → check if conditionals removed |
| ABI mismatch | `setBreakpoint` → `readRegisters` (check param registers) → `selectFrame` → `disassemble` (compare caller/callee) |
| Stack corruption / control flow hijack | `readRegisters` → `readMemory(rsp)` → `listModules` (compare address ranges) → `command("memory region")` |
| Single-instruction fault | `disassemble(count=5)` → `readRegisters` → `command("memory region 0xADDR")` |
| Core dump analysis | `loadCore` → `threads` → `stackTrace` → `readRegisters` → `readMemory` |
| Security vulnerability assessment | `analyzeCrash` → `getSuspiciousFunctions` → `readMemory` |
| **Safe continue with timeout** | **`continue` → ⏱️[N seconds] → `pause` (MANDATORY) → `pollEvents` → `threads` (check stopReason)** |

### Tool One-Liner Reference

| Tool | Purpose |
|------|---------|
| `lldb_initialize` | Create new debug session |
| `lldb_terminate` | Destroy debug session |
| `lldb_listSessions` | List all active sessions |
| `lldb_createTarget` | Load executable to debug |
| `lldb_launch` | Start target process |
| `lldb_attach` | Attach to running process |
| `lldb_restart` | Restart process |
| `lldb_signal` | Send signal to process |
| `lldb_loadCore` | Load core dump for post-mortem analysis |
| `lldb_setBreakpoint` | Set breakpoint (by symbol, file:line, or address) |
| `lldb_deleteBreakpoint` | Delete breakpoint |
| `lldb_listBreakpoints` | List all breakpoints |
| `lldb_updateBreakpoint` | Update breakpoint (condition, enable/disable) |
| `lldb_continue` | Continue execution |
| `lldb_pause` | Pause running process |
| `lldb_stepIn` | Step into (enter function) |
| `lldb_stepOver` | Step over (skip function) |
| `lldb_stepOut` | Step out of current function |
| `lldb_threads` | List all threads |
| `lldb_frames` | Get thread's frame list |
| `lldb_stackTrace` | Get formatted call stack |
| `lldb_selectThread` | Select current thread |
| `lldb_selectFrame` | Select current stack frame |
| `lldb_evaluate` | Evaluate expression in current context |
| `lldb_disassemble` | Disassemble instructions |
| `lldb_readRegisters` | Read register values |
| `lldb_writeRegister` | Write register value |
| `lldb_searchSymbol` | Search symbols by pattern |
| `lldb_listModules` | List loaded modules |
| `lldb_readMemory` | Read process memory |
| `lldb_writeMemory` | Write process memory |
| `lldb_setWatchpoint` | Set memory watchpoint |
| `lldb_deleteWatchpoint` | Delete watchpoint |
| `lldb_listWatchpoints` | List watchpoints |
| `lldb_pollEvents` | Poll pending events |
| `lldb_command` | Execute raw LLDB command |
| `lldb_getTranscript` | Get session transcript log |
| `lldb_createCoredump` | Create core dump of process |
| `lldb_analyzeCrash` | Analyze crash exploitability |
| `lldb_getSuspiciousFunctions` | Find suspicious security-related functions in stack |

### Mandatory Follow-Up Actions

| Operation | Must Follow With |
|-----------|-----------------|
| `lldb_launch` / `lldb_continue` / `lldb_stepOver` / `lldb_stepIn` / `lldb_stepOut` | **[Wait N seconds with timeout]** → `lldb_pause` → `lldb_pollEvents` — ensure stopped state |
| `lldb_pollEvents` returns stopped | `lldb_threads` — check stop reason |
| `lldb_threads` shows exception | `lldb_stackTrace` + `lldb_readRegisters` — analyze crash |
| Any variable inspection | **`lldb_pause` first** — ensure process is in stopped state |
| `lldb_continue` without breakpoint | **ALWAYS set timeout** (5-10s) → `lldb_pause` → verify process didn't hang |
| Suspected infinite loop | `lldb_pause` → `lldb_stackTrace` → `lldb_continue` → [wait 2s] → `lldb_pause` → `lldb_stackTrace` — compare locations |

### Critical Safety Rules

**🚨 NEVER WAIT INDEFINITELY FOR PROCESS STATE CHANGES 🚨**

**THE GOLDEN RULE: Every operation that resumes execution MUST be followed by:**
```
[Wait N seconds] → lldb_pause() → lldb_pollEvents() → lldb_threads()
```

**Detailed Safety Rules:**

1. **Every `lldb_continue` MUST have a timeout plan**
   - Decide maximum wait time BEFORE calling (default: 5-10s)
   - NEVER assume breakpoint will be hit naturally
   - Use `lldb_pause()` as mandatory safety valve
   - Check result with `lldb_pollEvents()` and `lldb_threads()`
   - Document timeout choice: why this duration?

2. **Every step operation MUST have a timeout**
   - `lldb_stepOver` / `lldb_stepIn` / `lldb_stepOut` can hang if function has infinite loop
   - Force-pause after 2-5 seconds MAXIMUM
   - Shorter timeout for steps (2-3s) vs continue (5-10s)
   - If step times out: assume infinite loop, use alternative approach

3. **Always call `lldb_pause` before inspection**
   - Never assume process is stopped, even after timeout
   - Explicit pause ensures safe state for:
     - `lldb_evaluate()` - expression evaluation
     - `lldb_readRegisters()` - register reads
     - `lldb_readMemory()` - memory reads
     - `lldb_stackTrace()` - stack inspection
   - Process can transition states asynchronously

4. **Implement hang detection for uncertain operations**
   - Use double-snapshot technique:
     1. Pause → get stack trace → note location
     2. Continue → wait 2s → pause
     3. Get stack trace again → compare locations
   - Same location = confirmed hang
   - Different locations = slow but progressing

5. **If any operation appears to hang:**
   - Immediately call `lldb_pause(sessionId)` once
   - Wait 3 seconds for response
   - If still unresponsive: call `lldb_terminate(sessionId)`
   - Create new session with shorter timeouts
   - Review timeout strategy before continuing

6. **Handle unexpected stop reasons**
   - After pause, ALWAYS check `stopReason` from `lldb_threads()`:
     - `"breakpoint"` → Normal, expected stop
     - `"exception"` → Crash, analyze immediately
     - `"signal"` → Force-paused (timeout), investigate location
     - `"trace"` → Step completed normally
     - Process still running → Call `lldb_pause()` again
   - Never assume stopReason, always verify

7. **Session timeout budget**
   - Maximum cumulative wait time per debugging session: 2 minutes
   - If consistently hitting timeouts: reassess debugging strategy
   - May indicate need for different approach (static analysis, code review)

8. **Emergency recovery procedures**
   - If debugger becomes fully unresponsive:
     1. `lldb_terminate(sessionId)` (if possible)
     2. `lldb_listSessions()` to identify hung sessions
     3. Create new session with stricter controls
     4. Apply learned timeout values from previous attempt
   - Document what caused the hang for future prevention

### Useful Raw LLDB Commands (via `lldb_command`)

| Command | Purpose |
|---------|---------|
| `si` | Single-instruction step (enters calls) |
| `ni` | Single-instruction step over (skips calls) |
| `memory region 0xADDR` | View memory region permissions |
| `image dump sections` | View all segment info |
| `image lookup --address 0xADDR` | Look up which function/module owns an address |
| `register read --all` | Read all registers including flags |
| `x/16gx $rsp` | View 16 8-byte values at stack pointer |
| `disassemble --start-address 0xADDR --count 30` | Disassemble from specific address |

### Test Programs

| Program | Bug Type | Section |
|---------|---------|---------|
| `examples/client/c_test/null_deref/` | Null pointer dereference | 3.2.1 |
| `examples/client/c_test/buffer_overflow/` | Buffer overflow | 3.2.2 |
| `examples/client/c_test/use_after_free/` | Use-after-free | 3.2.3 |
| `examples/client/c_test/divide_by_zero/` | Division by zero | 3.2.4 |
| `examples/client/c_test/stack_overflow/` | Stack overflow | 3.2.5 |
| `examples/client/c_test/format_string/` | Format string | 3.2.6 |
| `examples/client/c_test/double_free/` | Double free | 3.2.7 |
| `examples/client/c_test/infinite_loop/` | Hang / infinite loop | 3.5 |

---

## Troubleshooting

### General Issues

| Issue | Solution |
|-------|---------|
| "Cannot evaluate: process is not stopped" | Call `lldb_pause()` before `lldb_evaluate()` |
| "No threads available" | Process hasn't started — call `lldb_launch()` first |
| "Session not found" | Session was terminated — call `lldb_initialize()` for a new one |
| "Permission denied" for launch/attach | Set `LLDB_MCP_ALLOW_LAUNCH=1` and/or `LLDB_MCP_ALLOW_ATTACH=1` |
| Expression evaluation fails | Binary may lack debug symbols — use `lldb_readRegisters` or `lldb_disassemble` instead |
| `<optimized out>` for variables | Binary compiled with optimization — use registers and memory reads instead |

### Hang Detection and Timeout Issues

| Symptom | Root Cause | Diagnostic Steps | Solution |
|---------|-----------|------------------|----------|
| **Debugger appears hung after `lldb_continue`** | Process in infinite loop/deadlock | 1. Call `lldb_pause()` immediately<br>2. Call `lldb_threads()` to verify stopped<br>3. Call `lldb_stackTrace()` to see location<br>4. Resume 2s then pause again<br>5. Compare stack traces | If same location: **Confirmed hang**<br>- Use `lldb_evaluate()` to check loop variables<br>- Use `lldb_setBreakpoint()` to break loop<br>- Use `lldb_writeRegister()` to modify condition |
| **`lldb_pollEvents` never returns** | Process still running, waiting for state change | 1. Call `lldb_pause()` first<br>2. Then call `lldb_pollEvents()`<br>3. Never poll on running process | Always pause before polling events |
| **Step operations take forever** | Stepped into function with infinite loop | 1. Call `lldb_pause()` immediately<br>2. Call `lldb_stackTrace()` to see location<br>3. Verify with double snapshot | Use `lldb_stepOut()` to exit function<br>OR set breakpoint after function and `lldb_continue()` |
| **Process won't stop at breakpoint** | Breakpoint never reached (wrong path or infinite loop before breakpoint) | 1. Use timeout pattern: `continue` → wait 5s → `pause`<br>2. Check `lldb_stackTrace()` where it stopped<br>3. Verify breakpoint location with `lldb_listBreakpoints()` | If stuck before breakpoint: fix that hang first<br>If wrong path: adjust breakpoint location |
| **Debugging session becomes unresponsive** | MCP server or LLDB deadlocked | 1. Try `lldb_pause()` once<br>2. If no response after 3s: `lldb_terminate()`<br>3. Create new session | Apply shorter timeouts in new session (reduce from 10s to 3s) |
| **Operation times out but program is progressing** | Timeout too short for operation | 1. Increase timeout incrementally<br>2. Monitor with repeated pause/trace snapshots<br>3. Check if hitting multiple breakpoints | Adjust timeout based on observed behavior<br>Document why longer timeout is needed |
| **Cannot determine if hung or just slow** | Ambiguous execution state | 1. Pause and get first stack trace<br>2. Resume for 2 seconds<br>3. Pause and get second stack trace<br>4. Check instruction pointer changes | Same PC/location = hung<br>PC changed but nearby = tight loop<br>PC very different = slow but progressing |
| **Hang detection says "slow" but feels stuck** | Very tight loop (thousands of iterations per second) | 1. Use shorter verification window (0.5s)<br>2. Check if PC changes but within small range<br>3. Use `lldb_evaluate()` on loop counter | Set conditional breakpoint on loop counter<br>Check iteration rate matches expectations |
| **Multiple threads, hard to identify hung thread** | Complex multi-threaded hang | 1. `lldb_threads()` to list all threads<br>2. For each: `lldb_stackTrace(threadId=N)`<br>3. Look for threads in syscall waits<br>4. Check for circular wait patterns | Identify thread in active code vs waiting<br>Focus on thread with highest stack depth<br>Check for lock functions in traces |
| **Timeout after `lldb_launch` but no crash** | Process initializing slowly or hung at startup | 1. Increase launch timeout to 20s<br>2. Use `lldb_pause()` and check location<br>3. Check if in dynamic linker/constructor code | If in `dyld` or `__libc_start_main`: increase timeout<br>If in user code: investigate that function |

### Timeout Protection Checklist

**Before each debugging session, ensure you follow these safety practices:**

✅ **NEVER call `lldb_continue` without a timeout plan**
- Always decide maximum wait time before calling continue
- Use `lldb_pause()` as a safety valve

✅ **Set appropriate timeouts based on operation:**
- Breakpoint hit: 5 seconds
- Loop-heavy code: 10 seconds
- I/O operations: 15 seconds
- Initialization: 20 seconds

✅ **Always force-pause before inspection:**
```
lldb_pause(sessionId)      # Ensure stopped state
lldb_pollEvents(sessionId) # Get current state
lldb_threads(sessionId)    # Check stop reason
```

✅ **Use double-snapshot technique for infinite loop detection:**
```
Pause → StackTrace → Continue → Wait 2s → Pause → StackTrace
→ Compare locations to confirm loop
```

✅ **If debugger appears hung:**
```
1. Call lldb_pause(sessionId) immediately
2. Call lldb_pollEvents(sessionId) to sync state
3. If still unresponsive: lldb_terminate(sessionId)
4. Start new session with shorter timeouts
```

✅ **Document timeout decisions in debug log:**
```
"Calling lldb_continue with 10s timeout (expecting network I/O)"
"Setting 5s timeout for breakpoint at process_data (normal execution)"
```

### Dynamic Timeout Adjustment Strategy

**IMPORTANT: Adjust timeouts based on observed behavior, not just initial estimates.**

#### Timeout Escalation Protocol

```
INITIAL_TIMEOUT = 5s  # Conservative default

FUNCTION: execute_with_adaptive_timeout(operation, sessionId)

  timeout = INITIAL_TIMEOUT
  max_attempts = 3
  attempt = 1

  WHILE attempt <= max_attempts:

    # Execute with current timeout
    execute_operation(operation, sessionId)
    [Wait timeout seconds]
    lldb_pause(sessionId)
    lldb_pollEvents(sessionId)
    threads_info = lldb_threads(sessionId)

    # Check result
    IF threads_info.stopReason == "breakpoint":
      RETURN "success"

    IF threads_info.stopReason == "exception":
      RETURN "crashed"

    # Timeout expired - determine if hung or slow
    trace1 = lldb_stackTrace(sessionId)
    location1 = extract_location(trace1)

    # Verification snapshot
    lldb_continue(sessionId)
    [Wait 2 seconds]
    lldb_pause(sessionId)

    trace2 = lldb_stackTrace(sessionId)
    location2 = extract_location(trace2)

    IF location1 == location2:
      # Confirmed hang
      RETURN "hang_detected" + {"location": location1}

    ELSE:
      # Making progress but slow
      LOG("Operation progressing slowly, increasing timeout")
      timeout = timeout * 2  # Double the timeout
      attempt++

      IF attempt <= max_attempts:
        LOG("Retrying with timeout: " + timeout + "s")
        CONTINUE

  RETURN "timeout_exhausted"
```

#### Timeout Tuning Guidelines

| Observed Behavior | Action |
|------------------|--------|
| Operation completes in < 50% of timeout | **Reduce timeout** to 60% of current value for next similar operation |
| Operation completes in 50-90% of timeout | **Keep current timeout** (optimal range) |
| Operation times out but progressing | **Double timeout** for next attempt |
| Operation times out with same location | **Hang confirmed** - don't increase timeout, diagnose hang instead |
| Multiple operations of same type | **Learn pattern** - use median completion time + 50% buffer |

#### Context-Specific Timeout Examples

```
# Example 1: Unknown code - start conservative
lldb_setBreakpoint(sessionId, symbol="unknown_function")
lldb_continue(sessionId)
[Wait 5 seconds]  # Initial conservative timeout
lldb_pause(sessionId)
# ... analyze and adjust for next iteration

# Example 2: Known I/O operation - start generous
lldb_setBreakpoint(sessionId, symbol="network_fetch")
lldb_continue(sessionId)
[Wait 15 seconds]  # I/O operations need longer timeout
lldb_pause(sessionId)

# Example 3: Tight loop - use short verification timeout
lldb_setBreakpoint(sessionId, symbol="process_loop")
lldb_continue(sessionId)
[Wait 3 seconds]  # Short timeout to quickly detect infinite loops
lldb_pause(sessionId)

# Example 4: Already confirmed slow operation - use learned timeout
lldb_continue(sessionId)
[Wait 25 seconds]  # Learned from previous attempts that this needs 25s
lldb_pause(sessionId)
```

#### Warning Signs of Incorrect Timeout

**Too Short:**
- Frequent false positive hangs
- Operations succeed when timeout increased
- Progress visible in double snapshot but flagged as timeout

**Too Long:**
- Actual hangs take too long to detect
- Debugging session feels unresponsive
- Wasted time waiting for confirmed infinite loops

**Optimal Timeout:**
- 90%+ of normal operations complete within timeout
- Actual hangs detected within 5-10 seconds
- Minimal false positives
- Responsive debugging experience
