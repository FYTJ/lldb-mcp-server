"""Pytest fixtures for end-to-end LLDB MCP Server tests."""

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
C_TEST_DIR = PROJECT_ROOT / "examples" / "client" / "c_test"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture(scope="session", autouse=True)
def setup_e2e_environment():
    """Ensure launch/attach permissions during e2e tests."""
    os.environ.setdefault("LLDB_MCP_ALLOW_LAUNCH", "1")
    os.environ.setdefault("LLDB_MCP_ALLOW_ATTACH", "1")
    from lldb_mcp_server.utils.config import config
    config.allow_launch = True
    config.allow_attach = True
    yield


@pytest.fixture(scope="session")
def build_test_programs():
    """Build all test programs and return the directory."""
    build_script = C_TEST_DIR / "build_all.sh"
    if build_script.exists():
        subprocess.run(["bash", str(build_script)], cwd=C_TEST_DIR, check=True)
    return C_TEST_DIR


def _get_test_binary(name: str) -> Path:
    """Get path to a test binary by name."""
    return C_TEST_DIR / name / name


@pytest.fixture(scope="session")
def null_deref_binary(build_test_programs):
    """Path to null_deref test binary."""
    binary = _get_test_binary("null_deref")
    if not binary.exists():
        pytest.skip(f"Test binary not found: {binary}")
    return str(binary)


@pytest.fixture(scope="session")
def buffer_overflow_binary(build_test_programs):
    """Path to buffer_overflow test binary."""
    binary = _get_test_binary("buffer_overflow")
    if not binary.exists():
        pytest.skip(f"Test binary not found: {binary}")
    return str(binary)


@pytest.fixture(scope="session")
def use_after_free_binary(build_test_programs):
    """Path to use_after_free test binary."""
    binary = _get_test_binary("use_after_free")
    if not binary.exists():
        pytest.skip(f"Test binary not found: {binary}")
    return str(binary)


@pytest.fixture(scope="session")
def divide_by_zero_binary(build_test_programs):
    """Path to divide_by_zero test binary."""
    binary = _get_test_binary("divide_by_zero")
    if not binary.exists():
        pytest.skip(f"Test binary not found: {binary}")
    return str(binary)


@pytest.fixture(scope="session")
def double_free_binary(build_test_programs):
    """Path to double_free test binary."""
    binary = _get_test_binary("double_free")
    if not binary.exists():
        pytest.skip(f"Test binary not found: {binary}")
    return str(binary)


@pytest.fixture(scope="session")
def e2e_session_manager():
    """Create a SessionManager instance for e2e tests."""
    from lldb_mcp_server.session.manager import SessionManager
    return SessionManager()


@pytest.fixture
def e2e_session(e2e_session_manager):
    """Create a new session and clean it up after the test."""
    sid = e2e_session_manager.create_session()
    try:
        yield sid
    finally:
        try:
            e2e_session_manager.terminate_session(sid)
        except Exception:
            pass


def wait_for_crash(session_manager, session_id, timeout=10.0):
    """Wait for process to crash or exit."""
    sess = session_manager._sessions.get(session_id)
    if not sess or not sess.process or not sess.process.IsValid():
        return None

    try:
        import lldb
    except Exception:
        return None

    deadline = time.time() + timeout
    while time.time() < deadline:
        state = sess.process.GetState()
        if state == lldb.eStateStopped:
            # Check if it's a crash (signal)
            thread = sess.process.GetSelectedThread()
            if thread and thread.IsValid():
                stop_reason = thread.GetStopReason()
                if stop_reason == lldb.eStopReasonSignal:
                    return "crash"
                elif stop_reason == lldb.eStopReasonException:
                    return "crash"
            return "stopped"
        if state == lldb.eStateExited:
            return "exited"
        if state == lldb.eStateCrashed:
            return "crash"
        time.sleep(0.1)
    return "timeout"
