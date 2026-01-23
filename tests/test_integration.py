"""Integration test for a basic debug workflow."""

import time


def test_debug_workflow(session_manager, session_with_process):
    events = session_manager.poll_events(session_with_process, limit=10)
    assert "events" in events

    evaluation = session_manager.evaluate(session_with_process, "x")
    assert evaluation["result"]["value"] is not None

    session_manager.continue_process(session_with_process)
    time.sleep(0.1)
    session_manager.poll_events(session_with_process, limit=10)
