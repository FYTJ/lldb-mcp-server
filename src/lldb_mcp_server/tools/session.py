from .decorators import handle_lldb_errors


def register_session_tools(mcp, manager):
    """Register session management tools."""

    @mcp.tool()
    @handle_lldb_errors
    def lldb_initialize() -> dict:
        """Create a new LLDB debug session.

        Returns a session ID for subsequent operations.
        """
        session_id = manager.create_session()
        return {"sessionId": session_id}

    @mcp.tool()
    @handle_lldb_errors
    def lldb_terminate(sessionId: str) -> dict:
        """Terminate an active debug session."""
        manager.terminate_session(sessionId)
        return {"ok": True}

    @mcp.tool()
    @handle_lldb_errors
    def lldb_listSessions() -> dict:
        """List all active debug sessions."""
        return {"sessions": manager.list_sessions()}
