# Interactive Debugging with LLDB MCP Tools

## Key Principle: Each Step Informs the Next

Unlike pre-scripted debugging, real debugging requires analyzing results at each step to determine the next action.

## Decision Tree Patterns

### Pattern 1: Crash Analysis Workflow

```
1. lldb_initialize() → sessionId
2. lldb_createTarget(sessionId, binary)
3. lldb_launch(sessionId)
4. lldb_pollEvents(sessionId)
   ↓
   Check event type:

   IF event.type == "processStateChanged" AND event.state == "stopped":
      ↓
      5a. lldb_threads(sessionId)
          ↓
          Check stopReason:

          IF stopReason == "exception":
             → Go to CRASH_ANALYSIS

          IF stopReason == "breakpoint":
             → Go to BREAKPOINT_INSPECTION

          IF stopReason == "signal":
             → Go to SIGNAL_ANALYSIS

CRASH_ANALYSIS:
  1. lldb_stackTrace(sessionId) → identify crash location
  2. lldb_readRegisters(sessionId) → check register values
     ↓
     IF register shows NULL (0x0):
        → Likely null pointer dereference
     IF instruction pointer in invalid range:
        → Likely stack corruption

  3. lldb_disassemble(sessionId, count=10) → see crash instruction
  4. lldb_analyzeCrash(sessionId) → get exploitability rating
```

### Pattern 2: Iterative Variable Inspection

```
1. Set breakpoint at suspicious function:
   lldb_setBreakpoint(sessionId, symbol="parse_input")

2. Launch and wait for breakpoint:
   lldb_launch(sessionId)
   lldb_pollEvents(sessionId) → wait for breakpointHit

3. Inspect initial state:
   lldb_evaluate(sessionId, "buffer") → returns address
   lldb_evaluate(sessionId, "buffer_size") → returns 16
   lldb_evaluate(sessionId, "input_length") → returns 50

   ↓
   DECISION: input_length > buffer_size
   → Buffer overflow risk detected!

4. Set watchpoint to catch overflow:
   lldb_setWatchpoint(sessionId, address="buffer+16", size=1, write=True)

5. Continue and monitor:
   lldb_continue(sessionId)
   lldb_pollEvents(sessionId)

   ↓
   IF event == watchpointHit:
      → Overflow confirmed! Get stack trace to find source.
```

### Pattern 3: Conditional Stepping

```
# Goal: Find where variable becomes invalid

current_value = None
step_count = 0

LOOP:
  1. lldb_stepOver(sessionId)
  2. lldb_pollEvents(sessionId) → wait for stopped state
  3. lldb_evaluate(sessionId, "ptr")
     ↓
     new_value = result["value"]

     IF new_value == "0x0" AND current_value != "0x0":
        → Found it! ptr was set to NULL at this line
        lldb_stackTrace(sessionId) → get exact location
        BREAK

     current_value = new_value
     step_count += 1

     IF step_count > 100:
        → Too many steps, try different approach
        BREAK

     REPEAT LOOP
```

## Common Decision Points

### After lldb_threads()

**Check stopReason to decide next action:**
- `"exception"` → Analyze crash (stackTrace, registers, analyzeCrash)
- `"breakpoint"` → Inspect variables (evaluate, frames)
- `"signal"` → Check signal type (SIGSEGV vs SIGABRT vs SIGINT)
- `"trace"` → Step completed, continue stepping or inspect

### After lldb_stackTrace()

**Examine top frame to decide investigation:**
- Frame in `main` → Check argc/argv or main logic
- Frame in library (libc, libsystem) → Look at caller frame
- Frame shows `<unknown>` → Use disassemble for assembly-level analysis
- Multiple frames in same function → Likely recursion issue

### After lldb_readRegisters()

**Analyze register values:**
- `rax/eax == 0x0` → NULL pointer involved
- `rip/eip` in invalid range → Control flow corrupted
- `rsp/esp` very small → Stack overflow
- Segment registers point to invalid areas → Memory corruption

### After lldb_evaluate()

**Variable inspection results:**
- Value is NULL → Add null check or investigate why
- Value is huge number → Integer overflow or uninitialized
- String contains unexpected data → Input validation issue
- Pointer points to freed memory → Use-after-free bug

## Integration with Claude Code

When debugging interactively in Claude Code, maintain session state across tool calls:

```python
# Claude Code automatically maintains context across tool calls
# Each tool call can reference results from previous calls

# Example conversation flow:
User: "Debug the crash in null_deref binary"

Claude (internal thought):
  1. Call lldb_initialize
  2. Store sessionId from result
  3. Call lldb_createTarget with that sessionId
  4. Analyze result, decide next step based on success/failure
  5. Continue iteratively until bug found

# Claude doesn't need to pre-plan all steps - each step informs the next!
```

## Best Practices

1. **Always poll events after state-changing operations**
   - After lldb_launch, lldb_continue, lldb_stepIn, etc.
   - Events tell you what happened (crash, breakpoint hit, exit)

2. **Check process state before commands**
   - lldb_evaluate requires stopped state
   - lldb_continue requires stopped state
   - lldb_pause requires running state

3. **Use thread/frame selection strategically**
   - After crash, inspect thread with exception
   - In multi-threaded apps, check all threads for deadlocks

4. **Combine tools for complete picture**
   - stackTrace + registers + disassemble = full crash context
   - evaluate + readMemory = variable content validation
   - watchpoints + breakpoints = precise bug localization

5. **Handle tool failures gracefully**
   - If lldb_evaluate fails → try lldb_disassemble
   - If lldb_frames fails → use lldb_stackTrace instead
   - Tool failures are clues (e.g., stripped binary)

## Example: Full Interactive Debugging Session

```
User: "Find the bug in examples/client/c_test/null_deref/null_deref"

Step 1: Initialize session
→ lldb_initialize()
← {"sessionId": "abc123"}

Step 2: Load binary
→ lldb_createTarget("abc123", "/path/to/null_deref")
← {"success": true}

Step 3: Launch process
→ lldb_launch("abc123")
← {"success": true, "pid": 12345}

Step 4: Wait for events
→ lldb_pollEvents("abc123")
← {"events": [{"type": "processStateChanged", "state": "stopped"}]}

DECISION: Process stopped, check why

Step 5: Check threads
→ lldb_threads("abc123")
← {"threads": [{"id": 1, "stopReason": "exception"}]}

DECISION: Exception occurred, likely crash

Step 6: Get stack trace
→ lldb_stackTrace("abc123")
← {"frames": [
     {"function": "main", "line": 5, "file": "null_deref.c"},
     ...
   ]}

DECISION: Crash in main at line 5, check registers

Step 7: Read registers
→ lldb_readRegisters("abc123")
← {"registers": {"rax": "0x0", "rip": "0x100000f50", ...}}

DECISION: rax is NULL, likely null pointer dereference

Step 8: Confirm with disassembly
→ lldb_disassemble("abc123")
← {"instructions": [
     {"address": "0x100000f50", "mnemonic": "mov", "operands": "dword ptr [rax], 0x42"}
   ]}

CONCLUSION: Dereferencing NULL pointer (rax=0x0) at main:5
Bug: Missing null check before dereferencing pointer

Step 9: Get exploitability analysis
→ lldb_analyzeCrash("abc123")
← {"exploitability": "LOW", "reason": "NULL pointer dereference"}

FINAL REPORT:
- Bug Type: Null pointer dereference
- Location: null_deref.c:5 in main()
- Instruction: mov dword ptr [rax], 0x42
- Root Cause: rax register is 0x0 (NULL)
- Fix: Add null check before line 5
- Exploitability: Low
```

## Advanced Patterns

### Multi-threaded Deadlock Detection

```
1. Process appears hung
   → lldb_pause(sessionId)

2. Check all threads
   → lldb_threads(sessionId)
   ← Shows 4 threads, all stopped

3. For each thread:
   → lldb_stackTrace(sessionId, threadId=N)
   ← Check what each thread is waiting on

4. Identify circular wait:
   - Thread 1 waiting on mutex A, holds mutex B
   - Thread 2 waiting on mutex B, holds mutex A
   → Deadlock detected!
```

### Memory Corruption Investigation

```
1. Set watchpoint on critical memory
   → lldb_setWatchpoint(sessionId, address=0x12345000, size=8, write=True)

2. Continue execution
   → lldb_continue(sessionId)
   → lldb_pollEvents(sessionId)
   ← Watchpoint hit

3. Check what wrote to memory
   → lldb_stackTrace(sessionId)
   → lldb_readRegisters(sessionId)
   ← Identify culprit function

4. Analyze write instruction
   → lldb_disassemble(sessionId)
   ← See exact instruction that modified memory
```

### Binary-Only Debugging (No Source)

```
When debug symbols are missing:

1. Cannot use lldb_evaluate (requires symbols)
   → Use lldb_readRegisters instead

2. Cannot see source lines in stack trace
   → Use lldb_disassemble to see assembly

3. Cannot inspect variables by name
   → Use lldb_readMemory with calculated addresses

Example workflow:
  lldb_stackTrace → get function addresses
  lldb_disassemble → understand code flow
  lldb_readRegisters → check argument values (rdi, rsi, rdx on x86_64)
  lldb_readMemory → inspect data structures
```

## Troubleshooting Common Issues

### "Cannot evaluate: process is not stopped"
→ Call lldb_pause() before lldb_evaluate()

### "No threads available"
→ Process hasn't started yet, call lldb_launch() first

### "Session not found"
→ Session was terminated, call lldb_initialize() to create new one

### "Permission denied" for launch/attach
→ Set environment variables:
   export LLDB_MCP_ALLOW_LAUNCH=1
   export LLDB_MCP_ALLOW_ATTACH=1

### Expression evaluation fails
→ Binary may lack debug symbols
→ Use lldb_readRegisters or lldb_disassemble instead
