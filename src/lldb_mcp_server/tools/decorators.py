from functools import wraps

from fastmcp.exceptions import ToolError

from ..utils.errors import LLDBError


def handle_lldb_errors(func):
    """Convert LLDBError to ToolError for FastMCP."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except LLDBError as exc:
            raise exc.to_tool_error()
        except ToolError:
            raise
        except Exception as exc:
            raise ToolError(f"Unexpected error: {str(exc)}")

    return wrapper
