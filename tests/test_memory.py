"""Tests for memory read/write tools."""

import struct

import pytest

from lldb_mcp_server.utils.errors import LLDBError


def _parse_int(value):
    if value is None:
        return None
    text = str(value)
    return int(text, 16) if text.startswith("0x") else int(text)


def test_read_write_memory(session_manager, session_with_process):
    addr_value = session_manager.evaluate(session_with_process, "&x")["result"]["value"]
    addr = _parse_int(addr_value)
    assert addr is not None

    mem = session_manager.read_memory(session_with_process, addr, 4)
    assert mem["size"] > 0
    assert len(mem["bytes"]) >= mem["size"] * 2

    new_value = 2
    payload = struct.pack("<I", new_value).hex()
    result = session_manager.write_memory(session_with_process, addr, payload)
    assert result["bytesWritten"] == 4

    updated = session_manager.evaluate(session_with_process, "x")["result"]["value"]
    assert _parse_int(updated) == new_value


def test_write_memory_invalid_hex(session_manager, session_with_process):
    addr_value = session_manager.evaluate(session_with_process, "&x")["result"]["value"]
    addr = _parse_int(addr_value)
    assert addr is not None

    with pytest.raises(LLDBError) as excinfo:
        session_manager.write_memory(session_with_process, addr, "ZZ")
    assert excinfo.value.code == 1001
