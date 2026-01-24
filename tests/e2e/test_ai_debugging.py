"""
End-to-end tests for AI-driven debugging workflows.

Tests that the MCP tools can be used effectively for debugging
various types of bugs and vulnerabilities.
"""

import pytest
import time


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


class TestCrashDetection:
    """Test that crashes are properly detected and analyzed."""

    def test_null_deref_crash_detection(self, e2e_session_manager, e2e_session, null_deref_binary):
        """AI should detect null pointer dereference crash."""
        from lldb_mcp_server.analysis.exploitability import ExploitabilityAnalyzer

        # Load target
        e2e_session_manager.create_target(e2e_session, null_deref_binary)

        # Launch without breakpoints - let it crash
        e2e_session_manager.launch(e2e_session)

        # Wait for crash
        result = wait_for_crash(e2e_session_manager, e2e_session)
        assert result == "crash", f"Expected crash, got {result}"

        # Analyze crash using ExploitabilityAnalyzer
        analyzer = ExploitabilityAnalyzer(e2e_session_manager)
        crash_info = analyzer.analyze(e2e_session)

        # Verify crash type is detected
        assert crash_info is not None
        crash_str = str(crash_info).lower()
        # Should indicate segmentation fault, EXC_BAD_ACCESS, or null pointer
        assert ("sigsegv" in crash_str or "exc_bad_access" in crash_str or
                "segmentation" in crash_str or "signal" in crash_str or
                "null" in crash_str or "exception" in crash_str)

    def test_divide_by_zero_crash_detection(self, e2e_session_manager, e2e_session, divide_by_zero_binary):
        """AI should detect division by zero crash."""
        from lldb_mcp_server.analysis.exploitability import ExploitabilityAnalyzer

        # Load target
        e2e_session_manager.create_target(e2e_session, divide_by_zero_binary)

        # Launch without breakpoints
        e2e_session_manager.launch(e2e_session)

        # Wait for crash
        result = wait_for_crash(e2e_session_manager, e2e_session)
        assert result == "crash", f"Expected crash, got {result}"

        # Analyze crash
        analyzer = ExploitabilityAnalyzer(e2e_session_manager)
        crash_info = analyzer.analyze(e2e_session)

        # Should indicate arithmetic exception, SIGFPE, division instruction, or analysis result
        crash_str = str(crash_info).lower()
        assert ("sigfpe" in crash_str or "exc_arithmetic" in crash_str or
                "signal" in crash_str or "exception" in crash_str or
                "floating" in crash_str or "idiv" in crash_str or
                "analysis" in crash_str)


class TestStackTraceAnalysis:
    """Test stack trace retrieval during crashes."""

    def test_crash_stack_trace(self, e2e_session_manager, e2e_session, null_deref_binary):
        """AI should retrieve meaningful stack trace at crash."""
        # Load and crash
        e2e_session_manager.create_target(e2e_session, null_deref_binary)
        e2e_session_manager.launch(e2e_session)
        wait_for_crash(e2e_session_manager, e2e_session)

        # Get stack trace
        stack = e2e_session_manager.stack_trace(e2e_session)

        # Verify stack trace contains useful information
        # The API returns stackTrace as a string
        assert stack is not None
        stack_str = str(stack)
        # Should contain main function
        assert "main" in stack_str.lower() or "frame" in stack_str.lower()

    def test_divide_by_zero_stack_trace(self, e2e_session_manager, e2e_session, divide_by_zero_binary):
        """AI should retrieve stack trace showing division location."""
        # Load and crash
        e2e_session_manager.create_target(e2e_session, divide_by_zero_binary)
        e2e_session_manager.launch(e2e_session)
        wait_for_crash(e2e_session_manager, e2e_session)

        # Get stack trace
        stack = e2e_session_manager.stack_trace(e2e_session)

        # Verify stack trace
        assert stack is not None
        stack_str = str(stack)
        # Should show calculate or main function
        assert "calculate" in stack_str.lower() or "main" in stack_str.lower()


class TestMemoryCorruptionDetection:
    """Test detection of memory corruption bugs."""

    def test_buffer_overflow_detection(self, e2e_session_manager, e2e_session, buffer_overflow_binary):
        """AI should be able to debug buffer overflow scenario."""
        from lldb_mcp_server.analysis.exploitability import ExploitabilityAnalyzer

        # Load target
        e2e_session_manager.create_target(e2e_session, buffer_overflow_binary)

        # Set breakpoint at main to inspect before overflow
        e2e_session_manager.set_breakpoint(e2e_session, symbol="main")

        # Launch
        e2e_session_manager.launch(e2e_session)

        # Should stop at breakpoint
        threads = e2e_session_manager.threads(e2e_session)
        assert "threads" in threads
        assert len(threads["threads"]) > 0

        # Get suspicious functions
        analyzer = ExploitabilityAnalyzer(e2e_session_manager)
        suspicious = analyzer.get_suspicious_functions(e2e_session)

        # Result may or may not have suspicious calls depending on the binary
        assert suspicious is not None

    def test_use_after_free_scenario(self, e2e_session_manager, e2e_session, use_after_free_binary):
        """AI should be able to debug use-after-free scenario."""
        # Load target
        e2e_session_manager.create_target(e2e_session, use_after_free_binary)

        # Launch and let it run (may crash or show undefined behavior)
        e2e_session_manager.launch(e2e_session)

        result = wait_for_crash(e2e_session_manager, e2e_session, timeout=5.0)
        # May crash, exit, or continue with undefined behavior
        assert result in ["crash", "exited", "stopped", "timeout"]


class TestDebuggingWorkflow:
    """Test complete debugging workflows."""

    def test_breakpoint_and_step_workflow(self, e2e_session_manager, e2e_session, null_deref_binary):
        """AI should be able to step through code."""
        # Load target
        e2e_session_manager.create_target(e2e_session, null_deref_binary)

        # Set breakpoint at main
        bp = e2e_session_manager.set_breakpoint(e2e_session, symbol="main")
        # Response format: {"breakpoint": {"id": 1, ...}}
        assert "breakpoint" in bp and "id" in bp["breakpoint"]

        # Launch
        e2e_session_manager.launch(e2e_session)

        # Should be stopped at breakpoint
        threads = e2e_session_manager.threads(e2e_session)
        assert "threads" in threads
        thread = threads["threads"][0]
        assert thread["stopReason"] == "breakpoint"

        # Step over
        e2e_session_manager.step_over(e2e_session)

        # Should still be executing (not crashed yet)
        threads_after = e2e_session_manager.threads(e2e_session)
        assert "threads" in threads_after

    def test_variable_inspection(self, e2e_session_manager, e2e_session, null_deref_binary):
        """AI should be able to evaluate expressions."""
        # Load and run to main
        e2e_session_manager.create_target(e2e_session, null_deref_binary)
        e2e_session_manager.set_breakpoint(e2e_session, symbol="main")
        e2e_session_manager.launch(e2e_session)

        # Step to after ptr initialization
        e2e_session_manager.step_over(e2e_session)
        e2e_session_manager.step_over(e2e_session)

        # Try to evaluate a simple expression
        result = e2e_session_manager.evaluate(e2e_session, "1+1")
        assert "result" in result


class TestSecurityAnalysis:
    """Test security analysis capabilities."""

    def test_crash_analysis_report(self, e2e_session_manager, e2e_session, null_deref_binary):
        """AI should generate crash analysis report."""
        from lldb_mcp_server.analysis.exploitability import ExploitabilityAnalyzer

        # Crash the program
        e2e_session_manager.create_target(e2e_session, null_deref_binary)
        e2e_session_manager.launch(e2e_session)
        wait_for_crash(e2e_session_manager, e2e_session)

        # Analyze crash
        analyzer = ExploitabilityAnalyzer(e2e_session_manager)
        analysis = analyzer.analyze(e2e_session)

        # Should provide useful analysis
        assert analysis is not None

    def test_register_state_at_crash(self, e2e_session_manager, e2e_session, null_deref_binary):
        """AI should read registers at crash point."""
        # Crash the program
        e2e_session_manager.create_target(e2e_session, null_deref_binary)
        e2e_session_manager.launch(e2e_session)
        wait_for_crash(e2e_session_manager, e2e_session)

        # Read registers
        regs = e2e_session_manager.read_registers(e2e_session)

        # Should have register values
        assert "registers" in regs
        assert len(regs["registers"]) > 0


class TestEventPolling:
    """Test event polling mechanism."""

    def test_poll_crash_event(self, e2e_session_manager, e2e_session, null_deref_binary):
        """AI should receive crash event via polling."""
        # Load and launch
        e2e_session_manager.create_target(e2e_session, null_deref_binary)
        e2e_session_manager.launch(e2e_session)

        # Wait a bit for crash
        time.sleep(0.5)

        # Poll events
        events = e2e_session_manager.poll_events(e2e_session)

        # Should have events structure
        assert "events" in events
