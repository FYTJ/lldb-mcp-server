"""Basic import tests to verify module structure."""

import pytest


def test_import_fastmcp_server():
    try:
        import fastmcp  # noqa: F401
    except Exception:
        pytest.skip("fastmcp unavailable for this Python version")
    from lldb_mcp_server import fastmcp_server

    assert fastmcp_server is not None


def test_import_session_manager():
    from lldb_mcp_server.session.manager import SessionManager

    assert SessionManager is not None


def test_import_errors():
    from lldb_mcp_server.utils.errors import LLDBError

    assert LLDBError is not None
