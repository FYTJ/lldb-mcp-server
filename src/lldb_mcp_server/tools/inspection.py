from typing import Optional

from .decorators import handle_lldb_errors


def register_inspection_tools(mcp, manager):
    """Register inspection tools."""

    @mcp.tool()
    @handle_lldb_errors
    def lldb_threads(sessionId: str) -> dict:
        """List all threads in the process."""
        return manager.threads(sessionId)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_frames(sessionId: str, threadId: int) -> dict:
        """Get stack frames for a specific thread."""
        return manager.frames(sessionId, threadId)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_stackTrace(sessionId: str, threadId: Optional[int] = None) -> dict:
        """Get a formatted stack trace for a thread."""
        return manager.stack_trace(sessionId, threadId)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_selectThread(sessionId: str, threadId: int) -> dict:
        """Select a thread as the current thread."""
        return manager.select_thread(sessionId, threadId)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_selectFrame(sessionId: str, threadId: int, frameIndex: int) -> dict:
        """Select a stack frame as the current frame."""
        return manager.select_frame(sessionId, threadId, frameIndex)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_evaluate(sessionId: str, expr: str, frameIndex: Optional[int] = None) -> dict:
        """Evaluate an expression in the current frame."""
        return manager.evaluate(sessionId, expr, frameIndex)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_disassemble(sessionId: str, addr: Optional[int] = None, count: int = 10) -> dict:
        """Disassemble instructions at an address or current location."""
        return manager.disassemble(sessionId, addr=addr, count=count)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_readRegisters(sessionId: str, threadId: Optional[int] = None) -> dict:
        """Read register values for a thread."""
        return manager.read_registers(sessionId, threadId)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_writeRegister(sessionId: str, name: str, value) -> dict:
        """Write a value to a register."""
        return manager.write_register(sessionId, name, value)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_searchSymbol(sessionId: str, pattern: str, module: Optional[str] = None) -> dict:
        """Search for symbols matching a pattern across modules."""
        return manager.search_symbol(sessionId, pattern, module)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_listModules(sessionId: str) -> dict:
        """List all loaded modules."""
        return manager.list_modules(sessionId)
