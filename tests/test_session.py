"""Unit tests for session management tools."""

import uuid

import pytest

from lldb_mcp_server.utils.errors import LLDBError


def test_create_session(session_manager):
    session_id = session_manager.create_session()
    try:
        uuid.UUID(session_id)
    finally:
        session_manager.terminate_session(session_id)


def test_list_sessions(session_manager, session_id):
    sessions = session_manager.list_sessions()
    assert session_id in sessions


def test_terminate_session(session_manager):
    session_id = session_manager.create_session()
    session_manager.terminate_session(session_id)
    assert session_id not in session_manager.list_sessions()


def test_terminate_missing_session_raises(session_manager):
    with pytest.raises(LLDBError) as excinfo:
        session_manager.terminate_session("missing")
    assert excinfo.value.code == 1002
