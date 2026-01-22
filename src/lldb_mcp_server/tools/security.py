from .decorators import handle_lldb_errors
from ..analysis.exploitability import ExploitabilityAnalyzer


def register_security_tools(mcp, manager):
    """Register security analysis tools."""

    @mcp.tool()
    @handle_lldb_errors
    def lldb_analyzeCrash(sessionId: str) -> dict:
        """Analyze the exploitability of the current crash."""
        analyzer = ExploitabilityAnalyzer(manager)
        return analyzer.analyze(sessionId)

    @mcp.tool()
    @handle_lldb_errors
    def lldb_getSuspiciousFunctions(sessionId: str) -> dict:
        """Get suspicious security-related functions in the stack."""
        analyzer = ExploitabilityAnalyzer(manager)
        return analyzer.get_suspicious_functions(sessionId)
