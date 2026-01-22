from typing import Dict, List, Optional

from ..utils.config import config
from ..utils.errors import LLDBError
from .decorators import handle_lldb_errors


def register_target_tools(mcp, manager):
    """Register target/process control tools."""

    @mcp.tool()
    @handle_lldb_errors
    def lldb_createTarget(
        sessionId: str,
        file: str,
        arch: Optional[str] = None,
        triple: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> dict:
        """Load an executable file as a debug target."""
        target = manager.create_target(sessionId, file, arch, triple, platform)
        return {"target": target}

    @mcp.tool()
    @handle_lldb_errors
    def lldb_launch(
        sessionId: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        flags: Optional[Dict[str, str]] = None,
    ) -> dict:
        """Launch the target process."""
        if not config.allow_launch:
            raise LLDBError(7001, "Launch not allowed. Set LLDB_MCP_ALLOW_LAUNCH=1 to enable.")
        result = manager.launch(sessionId, args=args, env=env, cwd=cwd, flags=flags)
        return {"process": result}

    @mcp.tool()
    @handle_lldb_errors
    def lldb_attach(sessionId: str, pid: Optional[int] = None, name: Optional[str] = None) -> dict:
        """Attach to a running process."""
        if not config.allow_attach:
            raise LLDBError(7002, "Attach not allowed. Set LLDB_MCP_ALLOW_ATTACH=1 to enable.")
        result = manager.attach(sessionId, pid=pid, name=name)
        return {"process": result}

    @mcp.tool()
    @handle_lldb_errors
    def lldb_restart(sessionId: str) -> dict:
        """Restart the process with the last launch parameters."""
        result = manager.restart(sessionId)
        return {"process": result}

    @mcp.tool()
    @handle_lldb_errors
    def lldb_signal(sessionId: str, sig: int) -> dict:
        """Send a signal to the running process."""
        return manager.signal(sessionId, sig)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_loadCore(sessionId: str, corePath: str, executable: str) -> dict:
        """Load a core dump file for post-mortem debugging."""
        return manager.load_core(sessionId, corePath, executable)
