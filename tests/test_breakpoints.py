"""Tests for breakpoint tools."""

import pytest

from lldb_mcp_server.utils.errors import LLDBError


def test_breakpoint_lifecycle(session_manager, session_with_target, test_source):
    result = session_manager.set_breakpoint(session_with_target, file=test_source, line=4)
    bp = result["breakpoint"]
    assert bp["id"] > 0
    assert bp["enabled"] is True

    listed = session_manager.list_breakpoints(session_with_target)
    assert any(item["id"] == bp["id"] for item in listed["breakpoints"])

    updated = session_manager.update_breakpoint(session_with_target, bp["id"], enabled=False, ignore_count=2)
    assert updated["breakpoint"]["enabled"] is False
    assert updated["breakpoint"]["ignoreCount"] == 2

    deleted = session_manager.delete_breakpoint(session_with_target, bp["id"])
    assert deleted == {"ok": True}


def test_breakpoint_invalid_parameters(session_manager, session_with_target):
    with pytest.raises(LLDBError) as excinfo:
        session_manager.set_breakpoint(session_with_target)
    assert excinfo.value.code == 1001
