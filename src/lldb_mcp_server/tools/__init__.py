"""FastMCP tool registrations."""

from .advanced import register_advanced_tools
from .breakpoints import register_breakpoint_tools
from .execution import register_execution_tools
from .inspection import register_inspection_tools
from .memory import register_memory_tools
from .security import register_security_tools
from .session import register_session_tools
from .target import register_target_tools
from .watchpoints import register_watchpoint_tools

__all__ = [
    "register_advanced_tools",
    "register_breakpoint_tools",
    "register_execution_tools",
    "register_inspection_tools",
    "register_memory_tools",
    "register_security_tools",
    "register_session_tools",
    "register_target_tools",
    "register_watchpoint_tools",
]
