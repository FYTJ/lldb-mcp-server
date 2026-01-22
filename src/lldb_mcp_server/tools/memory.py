from .decorators import handle_lldb_errors


def register_memory_tools(mcp, manager):
    """Register memory operation tools."""

    @mcp.tool()
    @handle_lldb_errors
    def lldb_readMemory(sessionId: str, addr: int, size: int) -> dict:
        """Read raw bytes from process memory."""
        return manager.read_memory(sessionId, addr, size)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_writeMemory(sessionId: str, addr: int, bytes: str) -> dict:
        """Write raw bytes to process memory."""
        return manager.write_memory(sessionId, addr, bytes)
