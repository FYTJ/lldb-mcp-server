"""Pytest fixtures for LLDB MCP Server tests."""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
TEST_BINARY_DIR = PROJECT_ROOT / "examples" / "client" / "c_test" / "hello"
TEST_BINARY = TEST_BINARY_DIR / "hello"
TEST_SOURCE = TEST_BINARY_DIR / "hello.c"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from lldb_mcp_server.utils.config import config


@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """Ensure launch/attach permissions during tests."""
    os.environ.setdefault("LLDB_MCP_ALLOW_LAUNCH", "1")
    os.environ.setdefault("LLDB_MCP_ALLOW_ATTACH", "1")
    config.allow_launch = True
    config.allow_attach = True
    yield


@pytest.fixture(scope="session")
def test_binary():
    """Build and return path to test binary."""
    dsym_dir = TEST_BINARY_DIR / "hello.dSYM"
    if dsym_dir.exists():
        shutil.rmtree(dsym_dir)
    subprocess.run(
        ["cc", "-g", "-O0", "-Wall", "-Wextra", "-o", "hello", "hello.c"],
        cwd=TEST_BINARY_DIR,
        check=True,
    )
    if not dsym_dir.exists():
        try:
            subprocess.run(["dsymutil", str(TEST_BINARY)], cwd=TEST_BINARY_DIR, check=True)
        except FileNotFoundError:
            pass
    return str(TEST_BINARY)


@pytest.fixture(scope="session")
def test_source():
    """Return path to the test source file."""
    return str(TEST_SOURCE)


@pytest.fixture(scope="session")
def session_manager():
    """Create a SessionManager instance."""
    from lldb_mcp_server.session.manager import SessionManager

    return SessionManager()


@pytest.fixture
def session_id(session_manager):
    """Create a new session and clean it up after the test."""
    sid = session_manager.create_session()
    try:
        yield sid
    finally:
        try:
            session_manager.terminate_session(sid)
        except Exception:
            pass


@pytest.fixture
def lldb_session_id(session_manager, session_id):
    """Return a session with LLDB available, otherwise skip."""
    sess = session_manager._sessions.get(session_id)
    if not sess or sess.debugger is None:
        pytest.skip("LLDB unavailable")
    return session_id


def _advance_to_line(session_manager, session_id, min_line):
    sess = session_manager._sessions.get(session_id)
    if not sess or not sess.process or not sess.process.IsValid():
        return
    try:
        thread = sess.process.GetSelectedThread()
        frame = thread.GetSelectedFrame() if thread and thread.IsValid() else None
        line = frame.GetLineEntry().GetLine() if frame and frame.IsValid() else 0
    except Exception:
        return
    attempts = 0
    while line and line < min_line and attempts < 5:
        session_manager.step_over(session_id)
        try:
            thread = sess.process.GetSelectedThread()
            frame = thread.GetSelectedFrame() if thread and thread.IsValid() else None
            line = frame.GetLineEntry().GetLine() if frame and frame.IsValid() else 0
        except Exception:
            break
        attempts += 1


def _wait_for_stop(session_manager, session_id, timeout=5.0):
    sess = session_manager._sessions.get(session_id)
    if not sess or not sess.process or not sess.process.IsValid():
        return False
    try:
        import lldb
    except Exception:
        return False
    deadline = time.time() + timeout
    while time.time() < deadline:
        state = sess.process.GetState()
        if state == lldb.eStateStopped:
            return True
        if state == lldb.eStateExited:
            return False
        time.sleep(0.1)
    return False


@pytest.fixture
def session_with_target(session_manager, lldb_session_id, test_binary):
    """Create a session with a loaded target."""
    session_manager.create_target(lldb_session_id, test_binary)
    return lldb_session_id


@pytest.fixture
def session_with_process(session_manager, session_with_target, test_source):
    """Create a session with a running process stopped at a known line."""
    session_id = session_with_target
    session_manager.set_breakpoint(session_id, file=test_source, line=4)
    session_manager.launch(session_id)
    if not _wait_for_stop(session_manager, session_id):
        pytest.skip("Process did not stop at breakpoint")
    _advance_to_line(session_manager, session_id, 4)
    return session_id
