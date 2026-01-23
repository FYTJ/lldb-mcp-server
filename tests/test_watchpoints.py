"""Tests for watchpoint tools."""

import pytest

from lldb_mcp_server.utils.errors import LLDBError


def _parse_int(value):
    if value is None:
        return None
    text = str(value)
    return int(text, 16) if text.startswith("0x") else int(text)


def test_watchpoint_lifecycle(session_manager, session_with_process):
    addr_value = session_manager.evaluate(session_with_process, "&x")["result"]["value"]
    addr = _parse_int(addr_value)
    assert addr is not None

    try:
        result = session_manager.set_watchpoint(session_with_process, addr, 4, write=True)
    except LLDBError as exc:
        if exc.code == 3002:
            pytest.skip("Watchpoint unavailable on this target")
        raise

    wp_id = result["watchpoint"]["id"]
    listed = session_manager.list_watchpoints(session_with_process)
    assert any(wp["id"] == wp_id for wp in listed["watchpoints"])

    deleted = session_manager.delete_watchpoint(session_with_process, wp_id)
    assert deleted == {"ok": True}
