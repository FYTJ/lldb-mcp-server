from typing import Optional

from .decorators import handle_lldb_errors


def register_watchpoint_tools(mcp, manager):
    """Register watchpoint tools."""

    @mcp.tool()
    @handle_lldb_errors
    def lldb_setWatchpoint(
        sessionId: str,
        addr: int,
        size: int,
        read: Optional[bool] = None,
        write: Optional[bool] = None,
    ) -> dict:
        """Set a watchpoint on a memory location."""
        return manager.set_watchpoint(sessionId, addr, size, read=read, write=write)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_deleteWatchpoint(sessionId: str, watchpointId: int) -> dict:
        """Delete a watchpoint by ID."""
        return manager.delete_watchpoint(sessionId, watchpointId)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_listWatchpoints(sessionId: str) -> dict:
        """List all watchpoints in the session."""
        return manager.list_watchpoints(sessionId)
