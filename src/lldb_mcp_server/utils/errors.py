try:
    from fastmcp.exceptions import ToolError
except Exception:  # pragma: no cover - fallback for Python environments without fastmcp
    class ToolError(Exception):
        """Fallback ToolError when fastmcp is unavailable."""

        pass


class LLDBError(Exception):
    """LLDB-specific error with structured metadata."""

    SESSION_ERROR = 1000
    TARGET_ERROR = 2000
    BREAKPOINT_ERROR = 3000
    EXECUTION_ERROR = 4000
    MEMORY_ERROR = 5000
    SECURITY_ERROR = 6000
    PERMISSION_ERROR = 7000

    def __init__(self, code, message, data=None):
        super().__init__(message)
        self.code = int(code)
        self.message = str(message)
        self.data = data or {}

    def to_error(self) -> dict:
        payload = {"code": self.code, "message": self.message}
        if self.data:
            payload["data"] = self.data
        return payload

    def to_tool_error(self) -> ToolError:
        error_msg = f"[{self.code}] {self.message}"
        if self.data:
            error_msg += f" (data: {self.data})"
        return ToolError(error_msg)
