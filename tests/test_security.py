"""Tests for security analysis tools."""

from lldb_mcp_server.analysis.exploitability import ExploitabilityAnalyzer


def test_analyze_crash(session_manager, session_with_process):
    analyzer = ExploitabilityAnalyzer(session_manager)
    result = analyzer.analyze(session_with_process)
    analysis = result["analysis"]
    assert analysis["rating"]
    assert analysis["crashType"] is not None
    assert "registers" in analysis


def test_suspicious_functions(session_manager, session_with_process):
    analyzer = ExploitabilityAnalyzer(session_manager)
    result = analyzer.get_suspicious_functions(session_with_process)
    summary = result["summary"]
    assert summary["totalFunctions"] >= 0
