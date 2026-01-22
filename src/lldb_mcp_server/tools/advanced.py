from typing import Optional

from .decorators import handle_lldb_errors


def register_advanced_tools(mcp, manager):
    """Register advanced tools."""

    @mcp.tool()
    @handle_lldb_errors
    def lldb_pollEvents(sessionId: str, limit: Optional[int] = 32) -> dict:
        """Poll for pending events from the debug session."""
        return manager.poll_events(sessionId, limit or 32)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_command(sessionId: str, command: str) -> dict:
        """Execute a raw LLDB command string."""
        return manager.command(sessionId, command)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_getTranscript(sessionId: str) -> dict:
        """Get the transcript log for the session."""
        return manager.get_transcript(sessionId)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_createCoredump(sessionId: str, path: str) -> dict:
        """Create a core dump of the current process."""
        return manager.create_coredump(sessionId, path)
