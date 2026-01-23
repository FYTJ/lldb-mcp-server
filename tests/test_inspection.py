"""Tests for inspection, register, symbol, and module tools."""

import pytest

from lldb_mcp_server.utils.errors import LLDBError


def _parse_int(value):
    if value is None:
        return None
    text = str(value)
    try:
        return int(text, 16) if text.startswith("0x") else int(text)
    except ValueError:
        return None


def test_threads_and_frames(session_manager, session_with_process):
    threads = session_manager.threads(session_with_process)["threads"]
    assert threads
    thread_id = threads[0]["id"]
    frames = session_manager.frames(session_with_process, thread_id)["frames"]
    assert frames


def test_stack_trace(session_manager, session_with_process):
    trace = session_manager.stack_trace(session_with_process)["stackTrace"]
    assert "frame #0" in trace


def test_select_thread_and_frame(session_manager, session_with_process):
    threads = session_manager.threads(session_with_process)["threads"]
    thread_id = threads[0]["id"]
    selected = session_manager.select_thread(session_with_process, thread_id)["thread"]
    assert selected["selected"] is True

    frames = session_manager.frames(session_with_process, thread_id)["frames"]
    frame_index = frames[0]["index"]
    frame = session_manager.select_frame(session_with_process, thread_id, frame_index)["frame"]
    assert frame["selected"] is True


def test_evaluate_and_disassemble(session_manager, session_with_process):
    result = session_manager.evaluate(session_with_process, "x")
    value = _parse_int(result["result"]["value"])
    assert value is not None

    disasm = session_manager.disassemble(session_with_process, count=5)["instructions"]
    assert disasm


def test_register_read_write(session_manager, session_with_process):
    regs = session_manager.read_registers(session_with_process)
    general = regs["registers"].get("general", {})
    assert general

    skip = {"rip", "pc", "rsp", "sp", "rbp", "fp", "lr"}
    candidate = next((name for name in general if name.lower() not in skip), None)
    if not candidate:
        pytest.skip("No writable general registers found")

    current = general[candidate]
    result = session_manager.write_register(session_with_process, candidate, current)
    assert result["register"]["name"] == candidate


def test_search_symbol_and_modules(session_manager, session_with_process):
    symbols = session_manager.search_symbol(session_with_process, "*main*")
    assert symbols["totalMatches"] >= 1
    assert any("main" in (sym["name"] or "") for sym in symbols["symbols"])

    modules = session_manager.list_modules(session_with_process)
    assert modules["totalModules"] >= 1
    assert any(mod["type"] == "executable" for mod in modules["modules"])
