from typing import Optional

from .decorators import handle_lldb_errors


def register_breakpoint_tools(mcp, manager):
    """Register breakpoint tools."""

    @mcp.tool()
    @handle_lldb_errors
    def lldb_setBreakpoint(
        sessionId: str,
        file: Optional[str] = None,
        line: Optional[int] = None,
        symbol: Optional[str] = None,
        address: Optional[int] = None,
    ) -> dict:
        """Set a breakpoint at a specified location."""
        return manager.set_breakpoint(sessionId, file=file, line=line, symbol=symbol, address=address)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_deleteBreakpoint(sessionId: str, breakpointId: int) -> dict:
        """Delete a breakpoint by its ID."""
        return manager.delete_breakpoint(sessionId, breakpointId)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_listBreakpoints(sessionId: str) -> dict:
        """List all breakpoints in the session."""
        return manager.list_breakpoints(sessionId)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_updateBreakpoint(
        sessionId: str,
        breakpointId: int,
        enabled: Optional[bool] = None,
        ignoreCount: Optional[int] = None,
        condition: Optional[str] = None,
    ) -> dict:
        """Update breakpoint properties."""
        return manager.update_breakpoint(
            sessionId,
            breakpointId,
            enabled=enabled,
            ignore_count=ignoreCount,
            condition=condition,
        )
