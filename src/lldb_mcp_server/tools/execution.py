from .decorators import handle_lldb_errors


def register_execution_tools(mcp, manager):
    """Register execution control tools."""

    @mcp.tool()
    @handle_lldb_errors
    def lldb_continue(sessionId: str) -> dict:
        """Continue process execution."""
        return manager.continue_process(sessionId)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_pause(sessionId: str) -> dict:
        """Pause the running process."""
        return manager.pause_process(sessionId)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_stepIn(sessionId: str) -> dict:
        """Step into the next source line."""
        return manager.step_in(sessionId)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_stepOver(sessionId: str) -> dict:
        """Step over the next source line."""
        return manager.step_over(sessionId)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_stepOut(sessionId: str) -> dict:
        """Step out of the current function."""
        return manager.step_out(sessionId)
