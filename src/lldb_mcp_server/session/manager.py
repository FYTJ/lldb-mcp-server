import datetime
import fnmatch
import threading
import uuid
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.config import config
from ..utils.errors import LLDBError
from ..utils.logging import get_logger
from .types import Session

logger = get_logger("lldb.session")


class SessionManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._sessions: dict[str, Session] = {}

    def create_session(self) -> str:
        with self._lock:
            session_id = str(uuid.uuid4())
            debugger = None
            try:
                import lldb

                debugger = lldb.SBDebugger.Create()
                debugger.SetAsync(False)
            except Exception as exc:
                logger.warning("lldb.unavailable %s", str(exc))
            sess = Session(
                session_id=session_id,
                debugger=debugger,
                events=deque(),
                event_stop=threading.Event(),
            )
            self._sessions[session_id] = sess
            if debugger is not None:
                try:
                    self.start_events(session_id)
                except Exception as exc:
                    logger.warning("session.events.start_failed %s", str(exc))
            logger.info("session.created %s", session_id)
            return session_id

    def terminate_session(self, session_id: str) -> None:
        with self._lock:
            sess = self._sessions.get(session_id)
            if not sess:
                raise LLDBError(1002, "Session not found", {"sessionId": session_id})
            if sess.event_stop is not None:
                sess.event_stop.set()
            try:
                if sess.debugger is not None:
                    try:
                        import lldb

                        if isinstance(sess.debugger, lldb.SBDebugger):
                            lldb.SBDebugger.Destroy(sess.debugger)
                    except Exception:
                        pass
            finally:
                self._sessions.pop(session_id, None)
            logger.info("session.terminated %s", session_id)

    def list_sessions(self) -> List[str]:
        with self._lock:
            return list(self._sessions.keys())

    def start_events(self, session_id: str) -> None:
        sess = self._require_session(session_id)
        self._require_lldb(sess)
        import lldb

        listener = lldb.SBListener(f"lldb.events.{session_id}")
        sess.listener = listener

        def run() -> None:
            while sess.event_stop is not None and not sess.event_stop.is_set():
                ev = lldb.SBEvent()
                got = listener.WaitForEvent(1, ev)
                if not got:
                    continue
                try:
                    self._handle_lldb_event(sess, ev)
                except Exception:
                    continue

        t = threading.Thread(target=run, daemon=True)
        sess.event_thread = t
        t.start()

    def _handle_lldb_event(self, sess: Session, ev: Any) -> None:
        try:
            import lldb
        except Exception:
            return
        if not lldb.SBProcess.EventIsProcessEvent(ev):
            return
        state = lldb.SBProcess.GetStateFromEvent(ev)
        state_name = self._state_name(state)
        self._emit_event(
            sess,
            {
                "type": "processStateChanged",
                "state": state_name,
                "timestamp": self._timestamp(),
            },
        )
        if sess.process and sess.process.IsValid():
            self._collect_process_output(sess)
        if state == lldb.eStateStopped:
            self._emit_stop_events(sess)
        if state == lldb.eStateExited:
            exit_code = None
            if sess.process and sess.process.IsValid():
                try:
                    exit_code = sess.process.GetExitStatus()
                except Exception:
                    exit_code = None
            self._emit_event(
                sess,
                {
                    "type": "processExited",
                    "exitCode": exit_code,
                },
            )

    def _emit_stop_events(self, sess: Session) -> None:
        if not sess.process or not sess.process.IsValid():
            return
        try:
            import lldb
        except Exception:
            return
        for i in range(sess.process.GetNumThreads()):
            thread = sess.process.GetThreadAtIndex(i)
            stop_reason = thread.GetStopReason()
            if stop_reason == lldb.eStopReasonBreakpoint:
                bp_id = self._stop_reason_data(thread, 0)
                frame = thread.GetFrameAtIndex(0)
                self._emit_event(
                    sess,
                    {
                        "type": "breakpointHit",
                        "breakpointId": int(bp_id) if bp_id is not None else None,
                        "threadId": thread.GetThreadID(),
                        "location": {
                            "file": self._safe_file_name(frame),
                            "line": self._safe_line_number(frame),
                            "address": self._format_address(frame.GetPC()),
                        },
                    },
                )
            elif stop_reason == lldb.eStopReasonWatchpoint:
                wp_id = self._stop_reason_data(thread, 0)
                watch_addr = None
                access_type = "write"
                if sess.target and wp_id is not None:
                    wp = sess.target.FindWatchpointByID(int(wp_id))
                    if wp and wp.IsValid():
                        try:
                            watch_addr = wp.GetWatchAddress()
                        except Exception:
                            watch_addr = None
                        try:
                            read_watch = wp.IsWatchingReads()
                            write_watch = wp.IsWatchingWrites()
                            if read_watch and write_watch:
                                access_type = "access"
                            elif read_watch:
                                access_type = "read"
                            elif write_watch:
                                access_type = "write"
                        except Exception:
                            access_type = "write"
                self._emit_event(
                    sess,
                    {
                        "type": "watchpointHit",
                        "watchpointId": int(wp_id) if wp_id is not None else None,
                        "threadId": thread.GetThreadID(),
                        "address": self._format_address(watch_addr),
                        "accessType": access_type,
                    },
                )
            elif stop_reason == lldb.eStopReasonSignal:
                sig_num = self._stop_reason_data(thread, 0)
                sig_name = self._signal_name(sig_num)
                self._emit_event(
                    sess,
                    {
                        "type": "signal",
                        "signalNumber": sig_num,
                        "signalName": sig_name,
                        "threadId": thread.GetThreadID(),
                    },
                )

    def _collect_process_output(self, sess: Session) -> None:
        if not sess.process or not sess.process.IsValid():
            return
        out = sess.process.GetSTDOUT(4096)
        if out:
            self._emit_event(sess, {"type": "stdout", "data": out})
        err = sess.process.GetSTDERR(4096)
        if err:
            self._emit_event(sess, {"type": "stderr", "data": err})

    def _emit_event(self, sess: Session, event: Dict[str, Any]) -> None:
        if sess.events is None:
            return
        sess.events.append(event)

    def _require_session(self, session_id: str) -> Session:
        sess = self._sessions.get(session_id)
        if not sess:
            raise LLDBError(1002, "Session not found", {"sessionId": session_id})
        return sess

    def _require_lldb(self, sess: Session) -> None:
        if sess.debugger is None:
            raise LLDBError(2000, "LLDB unavailable")

    def _require_target(self, sess: Session) -> None:
        if not sess.target or not sess.target.IsValid():
            raise LLDBError(2001, "No target loaded")

    def _require_process(self, sess: Session) -> None:
        if sess.is_core_session:
            raise LLDBError(2002, "No live process (core session)")
        if not sess.process or not sess.process.IsValid():
            raise LLDBError(2002, "No process running")

    def _require_stopped(self, sess: Session) -> None:
        self._require_process(sess)
        try:
            import lldb

            if sess.process.GetState() != lldb.eStateStopped:
                raise LLDBError(4001, "Process not stopped")
        except LLDBError:
            raise
        except Exception:
            raise LLDBError(4001, "Process not stopped")

    def _require_thread(self, sess: Session, thread_id: int):
        self._require_process(sess)
        thread = sess.process.GetThreadByID(thread_id)
        if not thread or not thread.IsValid():
            raise LLDBError(4002, "Thread not found")
        return thread

    def _format_address(self, addr: Any) -> str:
        if addr is None:
            return "0x0"
        try:
            import lldb

            if addr == lldb.LLDB_INVALID_ADDRESS:
                return "0x0"
        except Exception:
            pass
        try:
            return f"0x{int(addr):x}"
        except Exception:
            return "0x0"

    def _timestamp(self) -> str:
        return datetime.datetime.utcnow().isoformat(timespec="milliseconds") + "Z"

    def _state_name(self, state: int) -> str:
        try:
            import lldb

            mapping = {
                lldb.eStateInvalid: "invalid",
                lldb.eStateUnloaded: "unloaded",
                lldb.eStateConnected: "connected",
                lldb.eStateAttaching: "attaching",
                lldb.eStateLaunching: "launching",
                lldb.eStateStopped: "stopped",
                lldb.eStateRunning: "running",
                lldb.eStateStepping: "stepping",
                lldb.eStateCrashed: "crashed",
                lldb.eStateDetached: "detached",
                lldb.eStateExited: "exited",
                lldb.eStateSuspended: "suspended",
            }
            return mapping.get(state, "unknown")
        except Exception:
            return "unknown"

    def _stop_reason_name(self, reason: int) -> str:
        try:
            import lldb

            mapping = {
                lldb.eStopReasonNone: "none",
                lldb.eStopReasonTrace: "step",
                lldb.eStopReasonBreakpoint: "breakpoint",
                lldb.eStopReasonWatchpoint: "watchpoint",
                lldb.eStopReasonSignal: "signal",
                lldb.eStopReasonException: "exception",
                lldb.eStopReasonPlanComplete: "step",
            }
            return mapping.get(reason, "unknown")
        except Exception:
            return "unknown"

    def _stop_reason_data(self, thread: Any, index: int) -> Optional[int]:
        try:
            if thread.GetStopReasonDataCount() > index:
                return int(thread.GetStopReasonDataAtIndex(index))
        except Exception:
            return None
        return None

    def _signal_name(self, sig_num: Optional[int]) -> Optional[str]:
        if sig_num is None:
            return None
        try:
            import signal

            return signal.Signals(int(sig_num)).name
        except Exception:
            return None

    def _safe_file_name(self, frame: Any) -> Optional[str]:
        try:
            line_entry = frame.GetLineEntry()
            if not line_entry or not line_entry.IsValid():
                return None
            return line_entry.GetFileSpec().GetFilename()
        except Exception:
            return None

    def _safe_line_number(self, frame: Any) -> Optional[int]:
        try:
            line_entry = frame.GetLineEntry()
            if not line_entry or not line_entry.IsValid():
                return None
            return line_entry.GetLine()
        except Exception:
            return None

    def _write_transcript(
        self,
        session_id: str,
        command: str,
        output: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        path = self._transcript_path(session_id)
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        text = f"[{timestamp}] > {command}\n"
        if output:
            text += str(output)
        if error:
            text += str(error)
        try:
            with open(path, "a", encoding="utf-8", errors="ignore") as f:
                f.write(text)
                if not text.endswith("\n"):
                    f.write("\n")
        except Exception:
            pass

    def _ensure_logs(self) -> None:
        Path(config.log_dir or "logs").mkdir(parents=True, exist_ok=True)

    def _transcript_path(self, session_id: str) -> str:
        self._ensure_logs()
        return str(Path(config.log_dir or "logs") / f"transcript_{session_id}.log")

    def _attach_process_listener(self, sess: Session) -> None:
        if not sess.listener or not sess.process or not sess.process.IsValid():
            return
        try:
            import lldb

            bits = (
                lldb.SBProcess.eBroadcastBitStateChanged
                | lldb.SBProcess.eBroadcastBitSTDOUT
                | lldb.SBProcess.eBroadcastBitSTDERR
            )
            sess.process.GetBroadcaster().AddListener(sess.listener, bits)
        except Exception:
            pass

    def create_target(
        self,
        session_id: str,
        file: str,
        arch: Optional[str] = None,
        triple: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_lldb(sess)
            import lldb

            target = None
            error = lldb.SBError()
            try:
                if arch and hasattr(sess.debugger, "CreateTargetWithFileAndArch"):
                    target = sess.debugger.CreateTargetWithFileAndArch(file, arch)
                elif triple or platform:
                    target = sess.debugger.CreateTarget(file, triple or "", platform or "", False, error)
                else:
                    target = sess.debugger.CreateTarget(file)
            except Exception:
                target = None
            if not target or not target.IsValid():
                raise LLDBError(2001, "Failed to create target", {"file": file})
            sess.target = target
            sess.process = None
            sess.is_core_session = False
            sess.core_path = None
            sess.core_executable = None
            sess.core_pid = None
            sess.core_signal = None
            triple_value = target.GetTriple() or ""
            arch_value = arch or (triple_value.split("-")[0] if triple_value else "")
            self._emit_event(sess, {"type": "targetCreated", "file": file})
            self._write_transcript(session_id, f"target create {file}")
            return {
                "file": file,
                "arch": arch_value,
                "triple": triple_value,
            }

    def launch(
        self,
        session_id: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        flags: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_lldb(sess)
            self._require_target(sess)
            sess.is_core_session = False
            import lldb

            process = None
            error = lldb.SBError()
            if hasattr(lldb, "SBLaunchInfo"):
                launch_info = lldb.SBLaunchInfo(args or [])
                if cwd and hasattr(launch_info, "SetWorkingDirectory"):
                    launch_info.SetWorkingDirectory(cwd)
                if env:
                    if hasattr(launch_info, "SetEnvironmentEntry"):
                        for key, value in env.items():
                            launch_info.SetEnvironmentEntry(str(key), str(value), True)
                    elif hasattr(launch_info, "SetEnvironmentEntries"):
                        entries = [f"{k}={v}" for k, v in env.items()]
                        launch_info.SetEnvironmentEntries(entries, True)
                process = sess.target.Launch(launch_info, error)
            if not process or not process.IsValid():
                process = sess.target.LaunchSimple(args or [], None, cwd)
            if not process or not process.IsValid():
                raise LLDBError(2002, "Launch failed", {"error": error.GetCString()})
            sess.process = process
            sess.last_launch_args = args or []
            sess.last_launch_env = env or {}
            sess.last_launch_cwd = cwd
            sess.last_launch_flags = flags or {}
            self._attach_process_listener(sess)
            state = self._state_name(process.GetState())
            self._write_transcript(session_id, "process launch")
            return {"pid": process.GetProcessID(), "state": state}

    def attach(self, session_id: str, pid: Optional[int] = None, name: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_lldb(sess)
            import lldb

            if pid is None and not name:
                raise LLDBError(1001, "Invalid parameters")
            target = sess.target or sess.debugger.CreateTarget(None)
            sess.target = target
            process = None
            error = lldb.SBError()
            if pid is not None:
                if hasattr(target, "AttachToProcessWithID") and sess.listener is not None:
                    process = target.AttachToProcessWithID(sess.listener, int(pid), error)
                if not process or not process.IsValid():
                    cmd = f"process attach --pid {int(pid)}"
                    process = self._command_attach(sess, cmd)
            else:
                cmd = f"process attach --name \"{name}\""
                process = self._command_attach(sess, cmd)
            if not process or not process.IsValid():
                raise LLDBError(2003, "Attach failed")
            sess.process = process
            sess.is_core_session = False
            self._attach_process_listener(sess)
            state = self._state_name(process.GetState())
            self._write_transcript(session_id, "process attach")
            return {"pid": process.GetProcessID(), "state": state, "name": name}

    def _command_attach(self, sess: Session, cmd: str):
        import lldb

        ro = lldb.SBCommandReturnObject()
        sess.debugger.GetCommandInterpreter().HandleCommand(cmd, ro)
        self._write_transcript(sess.session_id, cmd, ro.GetOutput(), ro.GetError())
        return sess.target.GetProcess()

    def restart(self, session_id: str) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_lldb(sess)
            self._require_target(sess)
            self._require_process(sess)
            try:
                sess.process.Kill()
            except Exception:
                pass
            return self.launch(
                session_id,
                args=sess.last_launch_args or [],
                env=sess.last_launch_env or {},
                cwd=sess.last_launch_cwd,
                flags=sess.last_launch_flags or {},
            )

    def signal(self, session_id: str, sig: int) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_process(sess)
            sess.process.Signal(int(sig))
            return {"ok": True, "signal": int(sig)}

    def load_core(self, session_id: str, core_path: str, executable: str) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_lldb(sess)
            import lldb

            error = lldb.SBError()
            target = sess.debugger.CreateTarget(executable, None, None, False, error)
            if not target or not target.IsValid():
                raise LLDBError(2001, "Failed to create target", {"file": executable})
            process = target.LoadCore(core_path)
            if not process or not process.IsValid():
                raise LLDBError(2004, "Failed to load core", {"corePath": core_path})
            sess.target = target
            sess.process = process
            sess.is_core_session = True
            sess.core_path = core_path
            sess.core_executable = executable
            sess.core_pid = process.GetProcessID()
            sess.core_signal = None
            thread = process.GetSelectedThread()
            if thread and thread.IsValid():
                sig_num = self._stop_reason_data(thread, 0)
                sess.core_signal = self._signal_name(sig_num)
            threads = [self._thread_info(process.GetThreadAtIndex(i)) for i in range(process.GetNumThreads())]
            return {
                "target": {
                    "file": executable,
                    "arch": (target.GetTriple() or "").split("-")[0],
                },
                "core": {
                    "path": core_path,
                    "pid": sess.core_pid,
                    "signal": sess.core_signal,
                },
                "threads": threads,
            }

    def set_breakpoint(
        self,
        session_id: str,
        file: Optional[str] = None,
        line: Optional[int] = None,
        symbol: Optional[str] = None,
        address: Optional[int] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_target(sess)
            if file and line is not None:
                bp = sess.target.BreakpointCreateByLocation(str(file), int(line))
                cmd = f"breakpoint set --file \"{file}\" --line {int(line)}"
            elif symbol:
                bp = sess.target.BreakpointCreateByName(str(symbol))
                cmd = f"breakpoint set --name \"{symbol}\""
            elif address is not None:
                bp = sess.target.BreakpointCreateByAddress(int(address))
                cmd = f"breakpoint set --address {int(address)}"
            else:
                raise LLDBError(1001, "Invalid parameters")
            if not bp or not bp.IsValid():
                raise LLDBError(3001, "Failed to set breakpoint")
            self._write_transcript(session_id, cmd)
            return {"breakpoint": self._breakpoint_info(bp, sess)}

    def delete_breakpoint(self, session_id: str, breakpoint_id: int) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_target(sess)
            ok = sess.target.BreakpointDelete(int(breakpoint_id))
            if not ok:
                raise LLDBError(3001, "Breakpoint not found")
            return {"ok": True}

    def list_breakpoints(self, session_id: str) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_target(sess)
            items = []
            for i in range(sess.target.GetNumBreakpoints()):
                bp = sess.target.GetBreakpointAtIndex(i)
                items.append(self._breakpoint_info(bp, sess))
            return {"breakpoints": items}

    def update_breakpoint(
        self,
        session_id: str,
        breakpoint_id: int,
        enabled: Optional[bool] = None,
        ignore_count: Optional[int] = None,
        condition: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_target(sess)
            bp = sess.target.FindBreakpointByID(int(breakpoint_id))
            if not bp or not bp.IsValid():
                raise LLDBError(3001, "Breakpoint not found")
            if enabled is not None:
                bp.SetEnabled(bool(enabled))
            if ignore_count is not None:
                bp.SetIgnoreCount(int(ignore_count))
            if condition is not None:
                bp.SetCondition(str(condition))
            return {"breakpoint": self._breakpoint_info(bp, sess)}

    def continue_process(self, session_id: str) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_process(sess)
            try:
                sess.process.Continue()
            except Exception:
                pass
            state = self._state_name(sess.process.GetState())
            return {"process": {"state": state}}

    def pause_process(self, session_id: str) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_process(sess)
            sess.process.Stop()
            state = self._state_name(sess.process.GetState())
            return {"process": {"state": state}}

    def step_in(self, session_id: str) -> Dict[str, Any]:
        return self._step(session_id, "into")

    def step_over(self, session_id: str) -> Dict[str, Any]:
        return self._step(session_id, "over")

    def step_out(self, session_id: str) -> Dict[str, Any]:
        return self._step(session_id, "out")

    def _step(self, session_id: str, mode: str) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_stopped(sess)
            thread = sess.process.GetSelectedThread()
            if not thread or not thread.IsValid():
                raise LLDBError(4002, "Thread not found")
            if mode == "into":
                thread.StepInto()
            elif mode == "over":
                thread.StepOver()
            elif mode == "out":
                thread.StepOut()
            frame = thread.GetFrameAtIndex(0)
            return {
                "thread": {
                    "id": thread.GetThreadID(),
                    "stopReason": self._stop_reason_name(thread.GetStopReason()),
                },
                "frame": self._frame_info(frame, sess, 0),
            }

    def threads(self, session_id: str) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            if not sess.process or not sess.process.IsValid():
                raise LLDBError(2002, "No process running")
            items = [self._thread_info(sess.process.GetThreadAtIndex(i)) for i in range(sess.process.GetNumThreads())]
            return {"threads": items}

    def frames(self, session_id: str, thread_id: int) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            thread = self._require_thread(sess, int(thread_id))
            frames = []
            for i in range(thread.GetNumFrames()):
                frame = thread.GetFrameAtIndex(i)
                frames.append(self._frame_info(frame, sess, i))
            return {"frames": frames}

    def stack_trace(self, session_id: str, thread_id: Optional[int] = None) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            if not sess.process or not sess.process.IsValid():
                raise LLDBError(2002, "No process running")
            if thread_id is None:
                thread = sess.process.GetSelectedThread()
            else:
                thread = self._require_thread(sess, int(thread_id))
            lines = []
            for i in range(thread.GetNumFrames()):
                frame = thread.GetFrameAtIndex(i)
                addr = self._format_address(frame.GetPC())
                module = None
                try:
                    module = frame.GetModule().GetFileSpec().GetFilename()
                except Exception:
                    module = None
                func = frame.GetFunctionName() or "<unknown>"
                file = self._safe_file_name(frame) or "<unknown>"
                line = self._safe_line_number(frame) or 0
                prefix = "*" if i == 0 else " "
                module_part = f"{module}`" if module else ""
                lines.append(f"{prefix} frame #{i}: {addr} {module_part}{func} at {file}:{line}")
            return {"stackTrace": "\n".join(lines)}

    def select_thread(self, session_id: str, thread_id: int) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            thread = self._require_thread(sess, int(thread_id))
            sess.process.SetSelectedThread(thread)
            return {
                "thread": {
                    "id": thread.GetThreadID(),
                    "name": thread.GetName() or "",
                    "selected": True,
                }
            }

    def select_frame(self, session_id: str, thread_id: int, frame_index: int) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            thread = self._require_thread(sess, int(thread_id))
            if frame_index < 0 or frame_index >= thread.GetNumFrames():
                raise LLDBError(4003, "Frame not found")
            thread.SetSelectedFrame(int(frame_index))
            frame = thread.GetFrameAtIndex(int(frame_index))
            return {"frame": {**self._frame_info(frame, sess, int(frame_index)), "selected": True}}

    def evaluate(self, session_id: str, expr: str, frame_index: Optional[int] = None) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_stopped(sess)
            thread = sess.process.GetSelectedThread()
            if not thread or not thread.IsValid():
                raise LLDBError(4002, "Thread not found")
            if frame_index is None:
                frame = thread.GetSelectedFrame()
            else:
                if frame_index < 0 or frame_index >= thread.GetNumFrames():
                    raise LLDBError(4003, "Frame not found")
                frame = thread.GetFrameAtIndex(int(frame_index))
            try:
                value = frame.EvaluateExpression(str(expr))
            except Exception:
                raise LLDBError(4004, "Expression evaluation failed")
            if not value or not value.IsValid():
                raise LLDBError(4004, "Expression evaluation failed")
            if value.GetError().Fail():
                raise LLDBError(4004, "Expression evaluation failed", {"error": value.GetError().GetCString()})
            return {
                "result": {
                    "value": value.GetValue(),
                    "type": value.GetTypeName(),
                    "summary": value.GetSummary(),
                }
            }

    def disassemble(self, session_id: str, addr: Optional[int] = None, count: int = 10) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_target(sess)
            import lldb

            if addr is None:
                if not sess.process or not sess.process.IsValid():
                    raise LLDBError(2002, "No process running")
                thread = sess.process.GetSelectedThread()
                frame = thread.GetSelectedFrame()
                addr = int(frame.GetPC())
            address = lldb.SBAddress(int(addr), sess.target)
            inst_list = sess.target.ReadInstructions(address, int(count))
            instructions = []
            for i in range(inst_list.GetSize()):
                insn = inst_list.GetInstructionAtIndex(i)
                instructions.append(
                    {
                        "address": self._format_address(insn.GetAddress().GetLoadAddress(sess.target)),
                        "opcode": self._instruction_opcode(insn, sess.target),
                        "mnemonic": insn.GetMnemonic(sess.target),
                        "operands": insn.GetOperands(sess.target),
                    }
                )
            return {"instructions": instructions}

    def _instruction_opcode(self, insn: Any, target: Any) -> str:
        try:
            import lldb

            data = insn.GetData(target)
            size = data.GetByteSize()
            if size <= 0:
                return ""
            bytes_out = []
            for i in range(size):
                byte = data.GetUnsignedInt8(lldb.SBError(), i)
                bytes_out.append(f"{byte:02x}")
            return "".join(bytes_out)
        except Exception:
            return ""

    def read_memory(self, session_id: str, addr: int, size: int) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            if not sess.process or not sess.process.IsValid():
                raise LLDBError(2002, "No process running")
            import lldb

            err = lldb.SBError()
            raw = b""
            read = 0
            try:
                data = sess.process.ReadMemory(int(addr), int(size), err)
                if isinstance(data, str):
                    raw = data.encode()
                else:
                    raw = bytes(data)
                read = len(raw)
            except TypeError:
                import ctypes

                buf = ctypes.create_string_buffer(int(size))
                read = sess.process.ReadMemory(int(addr), buf, int(size), err)
                raw = buf.raw[:read]
            if err.Fail():
                raise LLDBError(5001, "Memory read failed", {"error": err.GetCString()})
            return {
                "address": self._format_address(addr),
                "size": int(read),
                "bytes": raw.hex(),
                "ascii": "".join(chr(b) if 32 <= b < 127 else "." for b in raw),
            }

    def write_memory(self, session_id: str, addr: int, data_hex: str) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            if sess.is_core_session:
                raise LLDBError(2002, "No live process (core session)")
            if not sess.process or not sess.process.IsValid():
                raise LLDBError(2002, "No process running")
            if not self._is_valid_hex(data_hex):
                raise LLDBError(1001, "Invalid parameters - bytes must be valid hex")
            import lldb

            data = bytes.fromhex(data_hex)
            err = lldb.SBError()
            wrote = sess.process.WriteMemory(int(addr), data, err)
            if err.Fail():
                raise LLDBError(5001, "Memory write failed", {"error": err.GetCString()})
            return {"address": self._format_address(addr), "bytesWritten": int(wrote)}

    def _is_valid_hex(self, value: str) -> bool:
        if not isinstance(value, str) or len(value) % 2 != 0:
            return False
        try:
            int(value, 16)
            return True
        except Exception:
            return False

    def set_watchpoint(
        self,
        session_id: str,
        addr: int,
        size: int,
        read: Optional[bool] = None,
        write: Optional[bool] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_target(sess)
            if size not in (1, 2, 4, 8):
                raise LLDBError(1001, "Invalid parameters - size must be 1, 2, 4, or 8")
            import lldb

            read_flag = bool(read) if read is not None else False
            write_flag = bool(write) if write is not None else True
            err = lldb.SBError()
            wp = sess.target.WatchAddress(int(addr), int(size), read_flag, write_flag, err)
            if not wp or not wp.IsValid():
                raise LLDBError(3002, "Failed to set watchpoint")
            return {"watchpoint": self._watchpoint_info(wp)}

    def delete_watchpoint(self, session_id: str, watchpoint_id: int) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_target(sess)
            ok = sess.target.DeleteWatchpoint(int(watchpoint_id))
            if not ok:
                raise LLDBError(3002, "Watchpoint not found")
            return {"ok": True}

    def list_watchpoints(self, session_id: str) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_target(sess)
            items = []
            for i in range(sess.target.GetNumWatchpoints()):
                wp = sess.target.GetWatchpointAtIndex(i)
                items.append(self._watchpoint_info(wp))
            return {"watchpoints": items}

    def poll_events(self, session_id: str, limit: int = 32) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            items = []
            if sess.events is not None:
                while limit > 0 and sess.events:
                    items.append(sess.events.popleft())
                    limit -= 1
            return {"events": items}

    def command(self, session_id: str, command: str) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_lldb(sess)
            import lldb

            ro = lldb.SBCommandReturnObject()
            sess.debugger.GetCommandInterpreter().HandleCommand(str(command), ro)
            out = ro.GetOutput() or ""
            err = ro.GetError() or ""
            self._write_transcript(session_id, command, out, err)
            return {"output": out if out else err}

    def get_transcript(self, session_id: str) -> Dict[str, Any]:
        path = self._transcript_path(session_id)
        try:
            transcript = Path(path).read_text(encoding="utf-8")
        except Exception:
            transcript = ""
        return {"transcript": transcript}

    def read_registers(self, session_id: str, thread_id: Optional[int] = None) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_stopped(sess)
            if thread_id is None:
                thread = sess.process.GetSelectedThread()
            else:
                thread = self._require_thread(sess, int(thread_id))
            frame = thread.GetSelectedFrame()
            if not frame or not frame.IsValid():
                raise LLDBError(4003, "Frame not found")
            registers: Dict[str, Dict[str, str]] = {}
            reg_sets = frame.GetRegisters()
            for i in range(reg_sets.GetSize()):
                reg_set = reg_sets.GetValueAtIndex(i)
                set_name = (reg_set.GetName() or "registers").lower()
                key = self._register_set_key(set_name)
                values: Dict[str, str] = {}
                for j in range(reg_set.GetNumChildren()):
                    reg = reg_set.GetChildAtIndex(j)
                    reg_name = reg.GetName()
                    reg_value = reg.GetValue()
                    if reg_value is None:
                        reg_value = f"0x{reg.GetValueAsUnsigned():x}"
                    if reg_name:
                        values[reg_name] = str(reg_value)
                registers[key] = values
            return {"registers": registers, "threadId": thread.GetThreadID()}

    def _register_set_key(self, name: str) -> str:
        if "general" in name:
            return "general"
        if "float" in name:
            return "floating_point"
        if "segment" in name:
            return "segment"
        return name.replace(" ", "_")

    def write_register(self, session_id: str, name: str, value: Any) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_stopped(sess)
            thread = sess.process.GetSelectedThread()
            if not thread or not thread.IsValid():
                raise LLDBError(4002, "Thread not found")
            frame = thread.GetSelectedFrame()
            if not frame or not frame.IsValid():
                raise LLDBError(4003, "Frame not found")
            reg_sets = frame.GetRegisters()
            for i in range(reg_sets.GetSize()):
                reg_set = reg_sets.GetValueAtIndex(i)
                for j in range(reg_set.GetNumChildren()):
                    reg = reg_set.GetChildAtIndex(j)
                    if reg.GetName() == name:
                        old_value = reg.GetValue()
                        ok = reg.SetValueFromCString(str(value))
                        if not ok:
                            raise LLDBError(5003, "Register write failed")
                        return {
                            "register": {
                                "name": name,
                                "oldValue": old_value,
                                "newValue": reg.GetValue(),
                            }
                        }
            raise LLDBError(1001, "Invalid parameters - unknown register name")

    def search_symbol(self, session_id: str, pattern: str, module: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_target(sess)
            import lldb

            results = []
            for i in range(sess.target.GetNumModules()):
                mod = sess.target.GetModuleAtIndex(i)
                mod_name = mod.GetFileSpec().GetFilename()
                if module and module not in mod_name:
                    continue
                for idx in range(mod.GetNumSymbols()):
                    sym = mod.GetSymbolAtIndex(idx)
                    name = sym.GetName()
                    if not name:
                        continue
                    if not fnmatch.fnmatchcase(name, pattern):
                        continue
                    start_addr = sym.GetStartAddress().GetLoadAddress(sess.target)
                    end_addr = sym.GetEndAddress().GetLoadAddress(sess.target)
                    sym_type = self._symbol_type(sym.GetType())
                    size = None
                    if start_addr is not None and end_addr is not None:
                        try:
                            size = max(0, int(end_addr) - int(start_addr))
                        except Exception:
                            size = None
                    results.append(
                        {
                            "name": name,
                            "address": self._format_address(start_addr),
                            "module": mod_name,
                            "type": sym_type,
                            "size": size,
                        }
                    )
            return {"symbols": results, "totalMatches": len(results)}

    def _symbol_type(self, sym_type: int) -> str:
        try:
            import lldb

            if sym_type in (lldb.eSymbolTypeCode, lldb.eSymbolTypeFunction, lldb.eSymbolTypeResolver):
                return "function"
            if sym_type in (lldb.eSymbolTypeData, lldb.eSymbolTypeObjCClass, lldb.eSymbolTypeObjCMetaClass):
                return "data"
            if sym_type == lldb.eSymbolTypeTrampoline:
                return "trampoline"
            if sym_type == lldb.eSymbolTypeUndefined:
                return "undefined"
        except Exception:
            pass
        return "unknown"

    def list_modules(self, session_id: str) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_target(sess)
            modules = []
            for i in range(sess.target.GetNumModules()):
                mod = sess.target.GetModuleAtIndex(i)
                mod_name = mod.GetFileSpec().GetFilename()
                mod_path = self._get_filespec_path(mod.GetFileSpec())
                module_type = self._module_type(sess, mod)
                load_addr = self._module_load_address(sess, mod)
                sections = self._module_sections(sess, mod)
                size = sum(section.get("size", 0) for section in sections)
                modules.append(
                    {
                        "name": mod_name,
                        "path": mod_path,
                        "uuid": mod.GetUUIDString(),
                        "arch": (mod.GetTriple() or "").split("-")[0],
                        "type": module_type,
                        "loadAddress": load_addr,
                        "size": int(size),
                        "sections": sections,
                    }
                )
            return {"modules": modules, "totalModules": len(modules)}

    def _module_type(self, sess: Session, mod: Any) -> str:
        exe = None
        try:
            exe = sess.target.GetExecutable().GetFilename()
        except Exception:
            exe = None
        if exe and exe == mod.GetFileSpec().GetFilename():
            return "executable"
        name = mod.GetFileSpec().GetFilename() or ""
        if ".framework" in self._get_filespec_path(mod.GetFileSpec()):
            return "framework"
        if name == "dyld":
            return "dylinker"
        return "shared_library"

    def _module_load_address(self, sess: Session, mod: Any) -> str:
        try:
            header = mod.GetObjectFileHeaderAddress()
            if header and header.IsValid():
                return self._format_address(header.GetLoadAddress(sess.target))
        except Exception:
            pass
        return "0x0"

    def _module_sections(self, sess: Session, mod: Any) -> List[Dict[str, Any]]:
        sections = []
        for i in range(mod.GetNumSections()):
            section = mod.GetSectionAtIndex(i)
            sections.append(
                {
                    "name": section.GetName(),
                    "address": self._format_address(section.GetLoadAddress(sess.target)),
                    "size": int(section.GetByteSize()),
                    "permissions": self._section_permissions(section),
                }
            )
        return sections

    def _section_permissions(self, section: Any) -> str:
        try:
            import lldb

            perms = section.GetPermissions()
            return "".join(
                [
                    "r" if perms & lldb.ePermissionsReadable else "-",
                    "w" if perms & lldb.ePermissionsWritable else "-",
                    "x" if perms & lldb.ePermissionsExecutable else "-",
                ]
            )
        except Exception:
            return "---"

    def create_coredump(self, session_id: str, path: str) -> Dict[str, Any]:
        with self._lock:
            sess = self._require_session(session_id)
            self._require_stopped(sess)
            try:
                import lldb

                err = lldb.SBError()
                ok = sess.process.SaveCore(str(path), err) if hasattr(sess.process, "SaveCore") else False
                if not ok or err.Fail():
                    raise LLDBError(5002, "Failed to create core dump", {"error": err.GetCString()})
            except LLDBError:
                raise
            except Exception:
                raise LLDBError(5002, "Failed to create core dump")
            size = None
            try:
                size = Path(path).stat().st_size
            except Exception:
                size = None
            return {"path": str(path), "size": size, "pid": sess.process.GetProcessID()}

    def _thread_info(self, thread: Any) -> Dict[str, Any]:
        return {
            "id": thread.GetThreadID(),
            "name": thread.GetName() or "",
            "stopReason": self._stop_reason_name(thread.GetStopReason()),
            "frameCount": thread.GetNumFrames(),
        }

    def _get_filespec_path(self, filespec: Any) -> str:
        """Get full path from SBFileSpec (compatible with LLDB 20+)."""
        try:
            directory = filespec.GetDirectory()
            filename = filespec.GetFilename()
            if directory and filename:
                return directory + "/" + filename
            elif filename:
                return filename
            else:
                return ""
        except Exception:
            return ""

    def _frame_info(self, frame: Any, sess: Session, index: int) -> Dict[str, Any]:
        return {
            "index": index,
            "function": frame.GetFunctionName() or "<unknown>",
            "file": self._safe_file_name(frame) or "",
            "line": self._safe_line_number(frame) or 0,
            "address": self._format_address(frame.GetPC()),
        }

    def _breakpoint_info(self, bp: Any, sess: Session) -> Dict[str, Any]:
        locations = []
        for i in range(bp.GetNumLocations()):
            loc = bp.GetLocationAtIndex(i)
            addr = loc.GetAddress()
            line_entry = addr.GetLineEntry()
            locations.append(
                {
                    "address": self._format_address(addr.GetLoadAddress(sess.target)),
                    "file": line_entry.GetFileSpec().GetFilename() if line_entry and line_entry.IsValid() else None,
                    "line": line_entry.GetLine() if line_entry and line_entry.IsValid() else None,
                    "resolved": loc.IsResolved(),
                }
            )
        return {
            "id": bp.GetID(),
            "enabled": bp.IsEnabled(),
            "hitCount": bp.GetHitCount(),
            "ignoreCount": bp.GetIgnoreCount(),
            "condition": bp.GetCondition(),
            "locations": locations,
        }

    def _watchpoint_info(self, wp: Any) -> Dict[str, Any]:
        size = None
        if hasattr(wp, "GetWatchSize"):
            size = wp.GetWatchSize()
        elif hasattr(wp, "GetByteSize"):
            size = wp.GetByteSize()
        return {
            "id": wp.GetID(),
            "address": self._format_address(wp.GetWatchAddress()),
            "size": size,
            "read": wp.IsWatchingReads(),
            "write": wp.IsWatchingWrites(),
            "enabled": wp.IsEnabled(),
            "hitCount": wp.GetHitCount(),
        }
