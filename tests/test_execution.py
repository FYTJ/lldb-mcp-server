"""Tests for execution control tools."""

import time


def test_step_over(session_manager, session_with_process):
    result = session_manager.step_over(session_with_process)
    assert result["thread"]["id"] > 0
    assert result["frame"]["function"]


def test_step_in_and_out(session_manager, session_with_process):
    stepped_in = session_manager.step_in(session_with_process)
    assert stepped_in["thread"]["id"] > 0

    stepped_out = session_manager.step_out(session_with_process)
    assert stepped_out["thread"]["id"] > 0


def test_pause_process(session_manager, session_with_process):
    result = session_manager.pause_process(session_with_process)
    assert result["process"]["state"] == "stopped"


def test_continue_process(session_manager, session_with_process):
    result = session_manager.continue_process(session_with_process)
    assert result["process"]["state"] in {"running", "stopped", "exited"}
    time.sleep(0.1)
