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

### 2.1 Basic Debugging Flow

1. **Initialize session** → `lldb_initialize()` returns sessionId
2. **Load binary** → `lldb_createTarget(sessionId, file="/path/to/binary")`
3. **Set breakpoints** (optional) → `lldb_setBreakpoint(sessionId, symbol="main")`
4. **Launch process** → `lldb_launch(sessionId)`
5. **Debug loop**: poll events → inspect state → step → continue
6. **Terminate** → `lldb_terminate(sessionId)`

### 2.2 Two Ways to Start Debugging

There are two distinct approaches to begin debugging, depending on whether you control process startup:

#### Approach 1: Launch a New Process

**When to use:**
- You want to debug a program from the very beginning
- You need to control command-line arguments or environment variables
- You're debugging startup/initialization code
- The program hasn't started yet

**Workflow:**
```
1. lldb_initialize()                        # Create session
2. lldb_createTarget(sessionId, file="...")  # Load executable
3. lldb_setBreakpoint(sessionId, ...)       # Set breakpoints (optional)
4. lldb_launch(sessionId, args=[], env={})  # Launch with args/env
5. lldb_pollEvents(sessionId)               # Check process state
```

**Example:**
```
lldb_initialize()
→ sessionId: "debug-001"

lldb_createTarget(sessionId="debug-001", file="/path/to/program")
lldb_setBreakpoint(sessionId="debug-001", symbol="main")
lldb_launch(sessionId="debug-001", args=["--verbose", "input.txt"], env={"DEBUG": "1"})
lldb_pollEvents(sessionId="debug-001")
→ breakpointHit at main
```

**Security requirement:** Requires `LLDB_MCP_ALLOW_LAUNCH=1` environment variable in MCP configuration.

#### Approach 2: Attach to Running Process

**When to use:**
- The program is already running (perhaps started by another system)
- You want to debug a long-running service or daemon
- You need to inspect a process that's currently misbehaving
- You don't want to restart the process

**Workflow:**
```
1. lldb_initialize()                           # Create session
2. lldb_createTarget(sessionId, file="...")    # Load executable (same binary as running process)
3. lldb_attach(sessionId, pid=1234)           # Attach by PID
   OR
   lldb_attach(sessionId, name="program_name") # Attach by process name
4. lldb_pollEvents(sessionId)                  # Check process state (will be "stopped")
5. lldb_setBreakpoint(sessionId, ...)          # Set breakpoints while attached
6. lldb_continue(sessionId)                    # Resume execution
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
lldb_pollEvents(sessionId="debug-002")
→ process running, waiting for breakpoint hit
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

### 2.3 Crash Analysis Flow

1. Initialize and load target
2. Launch process (let it crash)
3. `lldb_pollEvents` → detect crash
4. `lldb_threads` → check stopReason
5. `lldb_stackTrace` + `lldb_readRegisters` + `lldb_disassemble` → analyze crash
6. `lldb_analyzeCrash` → get exploitability assessment

### 2.4 Key Principle: Interactive & Iterative

Each tool call's result informs your next action. Do NOT pre-plan all steps — debug iteratively based on runtime state.

**Critical rule:** Always call `lldb_pollEvents` after state-changing operations (`lldb_launch`, `lldb_continue`, `lldb_stepOver`, `lldb_stepIn`, `lldb_stepOut`).

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

**Diagnosis:**
1. `lldb_pause` → pause the running process
2. `lldb_threads` → list all threads and their stop reasons
3. For each thread: `lldb_stackTrace(threadId=N)` → check what each thread is waiting on
4. Look for patterns:
   - **Deadlock**: Thread A waits on lock X while holding lock Y, Thread B waits on lock Y while holding lock X
   - **Infinite loop**: A thread repeatedly executes the same code
   - **Blocking I/O**: Thread waiting on `read()`, `recv()`, etc.

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

### Pattern 1: After `lldb_pollEvents`

```
IF event.state == "stopped":
  → lldb_threads(sessionId)
    IF stopReason == "exception" → Go to CRASH_ANALYSIS
    IF stopReason == "breakpoint" → Go to BREAKPOINT_INSPECTION
    IF stopReason == "signal" → Go to SIGNAL_ANALYSIS
    IF stopReason == "trace" → Step completed, continue stepping or inspect
```

### Pattern 2: After `lldb_stackTrace`

- Top frame in `main` → check argc/argv or main logic
- Top frame in library (libc, libsystem) → look at caller frame
- Top frame shows `<unknown>` → use `lldb_disassemble` for assembly analysis
- Multiple frames in same function → likely recursion issue

### Pattern 3: After `lldb_readRegisters`

- `rax/x0 == 0x0` → NULL pointer involved
- `rip/pc` in invalid range → control flow corrupted
- `rsp/sp` very small → stack overflow
- Segment registers point to invalid areas → memory corruption

### Pattern 4: After `lldb_evaluate`

- Value is NULL → add null check or investigate why
- Value is a huge number → integer overflow or uninitialized
- String contains unexpected data → input validation issue
- Pointer points to freed memory → use-after-free bug

### Pattern 5: Conditional Stepping (Find where variable becomes invalid)

```
LOOP:
  1. lldb_stepOver(sessionId)
  2. lldb_pollEvents(sessionId)
  3. lldb_evaluate(sessionId, "ptr")
     IF new_value == "0x0" AND old_value != "0x0":
        → Found it! ptr was set to NULL at this line
        → lldb_stackTrace to get exact location
        → BREAK
     IF step_count > 100:
        → Too many steps, try different approach
        → BREAK
     REPEAT
```

---

## Part 8: Quick Reference

### By Scenario

| Scenario | Recommended Tool Combination |
|----------|------------------------------|
| Program crashed, find cause | `launch` → `pollEvents` → `threads` → `stackTrace` → `readRegisters` → `disassemble` → `analyzeCrash` |
| Inspect specific function behavior | `setBreakpoint(symbol=...)` → `launch` → `pollEvents` → `evaluate` |
| Track when a variable is modified | `evaluate("&var")` → `setWatchpoint` → `continue` → `pollEvents` → `stackTrace` |
| Program appears stuck | `pause` → `threads` → `stackTrace` per thread |
| Line-by-line debugging | `setBreakpoint` → `stepOver` / `stepIn` → `pollEvents` → `evaluate` |
| Binary-only (no source) | `disassemble` → `readRegisters` → `readMemory` → `searchSymbol` |
| Compiler optimization anomaly | Compare `-O0`/`-O2` `disassemble` output → `readRegisters` → check if conditionals removed |
| ABI mismatch | `setBreakpoint` → `readRegisters` (check param registers) → `selectFrame` → `disassemble` (compare caller/callee) |
| Stack corruption / control flow hijack | `readRegisters` → `readMemory(rsp)` → `listModules` (compare address ranges) → `command("memory region")` |
| Single-instruction fault | `disassemble(count=5)` → `readRegisters` → `command("memory region 0xADDR")` |
| Core dump analysis | `loadCore` → `threads` → `stackTrace` → `readRegisters` → `readMemory` |
| Security vulnerability assessment | `analyzeCrash` → `getSuspiciousFunctions` → `readMemory` |

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
| `lldb_launch` / `lldb_continue` / `lldb_stepOver` / `lldb_stepIn` / `lldb_stepOut` | `lldb_pollEvents` — wait for state change |
| `lldb_pollEvents` returns stopped | `lldb_threads` — check stop reason |
| `lldb_threads` shows exception | `lldb_stackTrace` + `lldb_readRegisters` — analyze crash |
| Any variable inspection | Ensure process is in stopped state |

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

| Issue | Solution |
|-------|---------|
| "Cannot evaluate: process is not stopped" | Call `lldb_pause()` before `lldb_evaluate()` |
| "No threads available" | Process hasn't started — call `lldb_launch()` first |
| "Session not found" | Session was terminated — call `lldb_initialize()` for a new one |
| "Permission denied" for launch/attach | Set `LLDB_MCP_ALLOW_LAUNCH=1` and/or `LLDB_MCP_ALLOW_ATTACH=1` |
| Expression evaluation fails | Binary may lack debug symbols — use `lldb_readRegisters` or `lldb_disassemble` instead |
| `<optimized out>` for variables | Binary compiled with optimization — use registers and memory reads instead |
