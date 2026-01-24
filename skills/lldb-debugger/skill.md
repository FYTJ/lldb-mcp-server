# LLDB Debugger Skill

You have access to an LLDB debugging server with 40 tools for debugging C/C++ programs on macOS.

## MCP Server Configuration

Add to your Claude Desktop or Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "python3",
      "args": ["-m", "lldb_mcp_server.fastmcp_server", "--transport", "stdio"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1"
      }
    }
  }
}
```

## Available Tool Categories

### Session Management
- `lldb_initialize` - Create a new debug session
- `lldb_terminate` - End a debug session
- `lldb_listSessions` - List active sessions

### Target Control
- `lldb_createTarget` - Load an executable
- `lldb_launch` - Start the process
- `lldb_attach` - Attach to running process
- `lldb_restart` - Restart the process
- `lldb_signal` - Send signal to process
- `lldb_loadCore` - Load core dump file

### Breakpoints
- `lldb_setBreakpoint` - Set breakpoint (by symbol, file:line, or address)
- `lldb_deleteBreakpoint` - Remove breakpoint
- `lldb_listBreakpoints` - List all breakpoints
- `lldb_updateBreakpoint` - Modify breakpoint (enable/disable, condition)

### Execution Control
- `lldb_continue` - Continue execution
- `lldb_pause` - Pause execution
- `lldb_stepIn` - Step into function
- `lldb_stepOver` - Step over function
- `lldb_stepOut` - Step out of function

### Inspection
- `lldb_threads` - List threads
- `lldb_frames` - List stack frames
- `lldb_stackTrace` - Get detailed stack trace
- `lldb_selectThread` - Select active thread
- `lldb_selectFrame` - Select active frame
- `lldb_evaluate` - Evaluate expression
- `lldb_disassemble` - Disassemble code

### Memory & Registers
- `lldb_readMemory` - Read memory at address
- `lldb_writeMemory` - Write memory at address
- `lldb_readRegisters` - Read CPU registers
- `lldb_writeRegister` - Write CPU register

### Watchpoints
- `lldb_setWatchpoint` - Set memory watchpoint
- `lldb_deleteWatchpoint` - Remove watchpoint
- `lldb_listWatchpoints` - List watchpoints

### Symbol & Module
- `lldb_searchSymbol` - Search for symbols
- `lldb_listModules` - List loaded modules

### Security Analysis
- `lldb_analyzeCrash` - Analyze crash details
- `lldb_getSuspiciousFunctions` - Find suspicious function calls

### Advanced
- `lldb_command` - Execute raw LLDB command
- `lldb_pollEvents` - Poll for debug events
- `lldb_getTranscript` - Get session transcript
- `lldb_createCoredump` - Create core dump

## Debugging Workflow

### Basic Workflow

1. **Initialize session**
   ```
   lldb_initialize → returns sessionId
   ```

2. **Load binary**
   ```
   lldb_createTarget(sessionId, file="/path/to/binary")
   ```

3. **Set breakpoints** (optional)
   ```
   lldb_setBreakpoint(sessionId, symbol="main")
   lldb_setBreakpoint(sessionId, file="main.c", line=42)
   ```

4. **Launch process**
   ```
   lldb_launch(sessionId, args=[], env={})
   ```

5. **Debug loop**
   - Check state: `lldb_threads(sessionId)`
   - Inspect: `lldb_stackTrace(sessionId)`, `lldb_evaluate(sessionId, expr="variable")`
   - Navigate: `lldb_stepOver(sessionId)`, `lldb_stepIn(sessionId)`
   - Continue: `lldb_continue(sessionId)`

6. **Terminate**
   ```
   lldb_terminate(sessionId)
   ```

### Crash Analysis Workflow

1. Initialize and load target
2. Launch without breakpoints (let it crash)
3. Analyze crash:
   ```
   lldb_analyzeCrash(sessionId)
   lldb_stackTrace(sessionId)
   lldb_readRegisters(sessionId)
   ```
4. Identify vulnerability type (null deref, overflow, etc.)

## Important Rules

1. **Always save session ID** - Every operation requires the sessionId from `lldb_initialize`

2. **Check process state before stepping** - Verify process is stopped before using step commands
   - Check `lldb_threads` response for `stopReason`

3. **Poll events for state changes** - Use `lldb_pollEvents` to detect breakpoint hits, crashes, and process exit

4. **Use raw commands when needed** - `lldb_command` allows any LLDB command not covered by tools

5. **Session isolation** - Each session is independent; multiple sessions can run concurrently

## Common Patterns

### Finding a Bug
```
1. Set breakpoint at suspicious function
2. Launch and wait for breakpoint
3. Examine variables with lldb_evaluate
4. Step through code watching for anomalies
5. Identify root cause
```

### Analyzing a Crash
```
1. Launch without breakpoints
2. Wait for crash (lldb_pollEvents)
3. Get crash info (lldb_analyzeCrash)
4. Get stack trace (lldb_stackTrace)
5. Read registers (lldb_readRegisters)
6. Identify crash type and location
```

### Memory Debugging
```
1. Set breakpoint at memory operation
2. Examine pointer values (lldb_evaluate)
3. Read memory at address (lldb_readMemory)
4. Set watchpoint on suspicious address
5. Continue and watch for corruption
```

## Interactive Debugging

For complex debugging scenarios where you need to make decisions based on runtime state,
see [INTERACTIVE_DEBUGGING.md](./INTERACTIVE_DEBUGGING.md) for patterns and examples.

**Key principle**: Each MCP tool call returns results that inform your next decision.
You don't need to plan all steps in advance - debug iteratively!

### When to Use Interactive Debugging

Use interactive debugging when:
- You don't know the exact bug location yet
- The bug behavior depends on runtime values
- You need to explore the program state dynamically
- Previous step results determine your next action

### Example: Decision-Based Debugging

```
1. Launch process → lldb_pollEvents → Process crashed
   ↓
   DECISION: Crash occurred, analyze it

2. lldb_threads → stopReason: "exception"
   ↓
   DECISION: Exception crash, check registers

3. lldb_readRegisters → rax: "0x0"
   ↓
   DECISION: NULL pointer, get crash location

4. lldb_stackTrace → Frame 0: main at line 42
   ↓
   CONCLUSION: NULL pointer dereference at main:42
```

Each step's result determines what to do next. See INTERACTIVE_DEBUGGING.md for:
- Decision tree patterns (crash analysis, variable inspection, conditional stepping)
- Common decision points after each tool
- Multi-threaded debugging strategies
- Binary-only debugging (no source code)
- Troubleshooting common issues
