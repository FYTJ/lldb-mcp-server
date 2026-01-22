from typing import Any, Dict, Optional

from ..utils.errors import LLDBError


class CrashAnalyzer:
    """Collect crash context from a stopped process."""

    def __init__(self, manager) -> None:
        self._manager = manager

    def collect(self, session_id: str) -> Dict[str, Any]:
        sess = self._manager._require_session(session_id)
        self._manager._require_stopped(sess)
        thread = sess.process.GetSelectedThread()
        if not thread or not thread.IsValid():
            raise LLDBError(4002, "Thread not found")
        crash_type = None
        fault_addr = None
        sig_num = None
        sig_name = None
        try:
            import lldb

            if thread.GetStopReason() == lldb.eStopReasonSignal:
                if thread.GetStopReasonDataCount() > 0:
                    sig_num = int(thread.GetStopReasonDataAtIndex(0))
                if thread.GetStopReasonDataCount() > 1:
                    fault_addr = int(thread.GetStopReasonDataAtIndex(1))
                sig_name = self._manager._signal_name(sig_num)
                crash_type = sig_name
        except Exception:
            pass
        return {
            "threadId": thread.GetThreadID(),
            "signalNumber": sig_num,
            "signalName": sig_name,
            "crashType": crash_type or "Unknown",
            "faultAddress": self._manager._format_address(fault_addr),
        }
