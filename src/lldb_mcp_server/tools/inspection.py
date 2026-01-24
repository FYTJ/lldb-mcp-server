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
    def lldb_frames(sessionId: str, threadId: Optional[int] = None) -> dict:
        """Get stack frames for a thread.

        Args:
            sessionId: The debugging session ID
            threadId: Thread ID (if None, uses currently selected thread)

        Returns:
            List of stack frames with file, function, line info

        Raises:
            LLDBError: If session not found or thread invalid
        """
        if threadId is None:
            # Get current thread from session
            threads_result = manager.threads(sessionId)
            if not threads_result.get("threads"):
                from ..utils.errors import LLDBError
                raise LLDBError(3002, "No threads available in the process")
            threadId = threads_result["threads"][0]["id"]

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
        """Evaluate expression in current context.

        Args:
            sessionId: The debugging session ID
            expr: C/C++ expression to evaluate
            frameIndex: Stack frame index (0=current, 1=caller, etc.)

        Returns:
            {"result": {"value": "...", "type": "...", "summary": "..."}}

        Note:
            - Requires process to be stopped
            - May fail on stripped binaries without debug symbols
            - Use lldb_readRegisters or lldb_disassemble for binary-only debugging
        """
        from ..utils.errors import LLDBError
        try:
            return manager.evaluate(sessionId, expr, frameIndex)
        except LLDBError as e:
            # Enhance error message for common cases
            error_msg_lower = str(e).lower()
            if "not stopped" in error_msg_lower or "running" in error_msg_lower:
                raise LLDBError(e.code,
                              "Cannot evaluate: process is not stopped. Use lldb_pause() first.",
                              e.data)
            elif "debug symbol" in error_msg_lower or "unavailable" in error_msg_lower or "no value" in error_msg_lower:
                raise LLDBError(e.code,
                              f"Cannot evaluate '{expr}': debug symbols may be incomplete. "
                              f"Try lldb_readRegisters() or lldb_disassemble() instead.",
                              e.data)
            raise

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
