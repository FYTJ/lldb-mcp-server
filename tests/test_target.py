"""Tests for target/process control tools."""

import signal as signal_mod

import pytest

from lldb_mcp_server.utils.errors import LLDBError


def test_create_target(session_manager, lldb_session_id, test_binary):
    target = session_manager.create_target(lldb_session_id, test_binary)
    assert target["file"] == test_binary
    assert target["triple"] is not None


def test_launch_process(session_manager, lldb_session_id, test_binary):
    session_manager.create_target(lldb_session_id, test_binary)
    session_manager.set_breakpoint(lldb_session_id, symbol="main")
    process = session_manager.launch(lldb_session_id)
    assert process["pid"] > 0
    assert process["state"] in {"stopped", "running", "exited"}


def test_restart_process(session_manager, session_with_process):
    result = session_manager.restart(session_with_process)
    assert result["pid"] > 0
    assert result["state"] in {"stopped", "running", "exited"}


def test_signal_process(session_manager, lldb_session_id, test_binary):
    session_manager.create_target(lldb_session_id, test_binary)
    session_manager.set_breakpoint(lldb_session_id, symbol="main")
    session_manager.launch(lldb_session_id)
    result = session_manager.signal(lldb_session_id, signal_mod.SIGTERM)
    assert result == {"ok": True, "signal": int(signal_mod.SIGTERM)}


def test_attach_invalid_parameters(session_manager, lldb_session_id):
    with pytest.raises(LLDBError) as excinfo:
        session_manager.attach(lldb_session_id)
    assert excinfo.value.code == 1001


def test_load_core_missing(session_manager, lldb_session_id, test_binary):
    with pytest.raises(LLDBError) as excinfo:
        session_manager.load_core(lldb_session_id, "/tmp/missing.core", test_binary)
    assert excinfo.value.code == 2004
