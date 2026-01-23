"""Tests for advanced tools (events, command, transcript, core dump)."""

import tempfile
from pathlib import Path

import pytest

from lldb_mcp_server.utils.errors import LLDBError


def test_poll_events(session_manager, session_with_process):
    events = session_manager.poll_events(session_with_process, limit=5)
    assert "events" in events


def test_command_and_transcript(session_manager, session_with_process):
    output = session_manager.command(session_with_process, "target list")["output"]
    assert isinstance(output, str)

    transcript = session_manager.get_transcript(session_with_process)["transcript"]
    assert isinstance(transcript, str)
    assert transcript


def test_create_coredump(session_manager, session_with_process):
    core_path = Path(tempfile.gettempdir()) / f"lldb_mcp_{session_with_process}.core"
    try:
        result = session_manager.create_coredump(session_with_process, str(core_path))
        assert result["path"] == str(core_path)
        assert core_path.exists()
    except LLDBError as exc:
        assert exc.code == 5002
    finally:
        try:
            core_path.unlink()
        except Exception:
            pass
