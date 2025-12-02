import threading
import uuid
from collections import deque

from ..utils.config import config
from ..utils.errors import LLDBError
from ..utils.logging import get_logger
from .types import Session

logger = get_logger("lldb.session")

class SessionManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._sessions: dict[str, Session] = {}
        self._selected_threads: dict[str, int] = {}

    def create_session(self) -> str:
        with self._lock:
            session_id = str(uuid.uuid4())
            dbg = None
            try:
                import lldb
                dbg = lldb.SBDebugger.Create()
                dbg.SetAsync(False)
            except Exception as e:
                logger.warning("lldb.unavailable %s", str(e))
            self._sessions[session_id] = Session(session_id=session_id, debugger=dbg)
            self._sessions[session_id].events = deque()
            try:
                if dbg is not None:
                    self.start_events(session_id)
            except Exception:
                pass
            logger.info("session.created %s", session_id)
            return session_id

    def terminate_session(self, session_id: str) -> None:
        with self._lock:
            sess = self._sessions.get(session_id)
            if not sess:
                raise LLDBError(1002, "Session not found", {"sessionId": session_id})
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

    def list_sessions(self) -> list[str]:
        with self._lock:
            return list(self._sessions.keys())

    def start_events(self, session_id: str) -> None:
        with self._lock:
            sess = self._sessions.get(session_id)
            if not sess:
                raise LLDBError(1002, "Session not found", {"sessionId": session_id})
            try:
                import lldb
            except Exception as e:
                raise LLDBError(2000, "LLDB import failed", {"error": str(e)})
            listener = lldb.SBListener("lldb.events." + session_id)
            sess.listener = listener
            def run():
                while True:
                    ev = lldb.SBEvent()
                    got = listener.WaitForEvent(1, ev)
                    if not got:
                        continue
                    try:
                        if lldb.SBProcess.EventIsProcessEvent(ev):
                            st = lldb.SBProcess.GetStateFromEvent(ev)
                            if sess.events is not None:
                                sess.events.append(
                                    {
                                        "type": "processStateChanged",
                                        "sessionId": session_id,
                                        "data": {"state": int(st)},
                                    }
                                )
                            if st == lldb.eStateStopped and sess.process and sess.process.IsValid():
                                for i in range(sess.process.GetNumThreads()):
                                    th = sess.process.GetThreadAtIndex(i)
                                    sr = th.GetStopReason()
                                    if sr == lldb.eStopReasonBreakpoint:
                                        bpid = th.GetStopReasonDataAtIndex(0) if th.GetStopReasonDataCount() > 0 else 0
                                        fr = th.GetFrameAtIndex(0)
                                        if sess.events is not None:
                                            sess.events.append(
                                                {
                                                    "type": "breakpointHit",
                                                    "sessionId": session_id,
                                                    "data": {
                                                        "breakpointId": int(bpid),
                                                        "threadId": th.GetThreadID(),
                                                        "function": fr.GetFunctionName(),
                                                        "file": fr.GetLineEntry().GetFileSpec().GetFilename(),
                                                        "line": fr.GetLineEntry().GetLine(),
                                                    },
                                                }
                                            )
                                    elif sr == lldb.eStopReasonWatchpoint:
                                        wpid = th.GetStopReasonDataAtIndex(0) if th.GetStopReasonDataCount() > 0 else 0
                                        fr = th.GetFrameAtIndex(0)
                                        if sess.events is not None:
                                            sess.events.append(
                                                {
                                                    "type": "watchpointHit",
                                                    "sessionId": session_id,
                                                    "data": {
                                                        "watchpointId": int(wpid),
                                                        "threadId": th.GetThreadID(),
                                                        "function": fr.GetFunctionName(),
                                                        "file": fr.GetLineEntry().GetFileSpec().GetFilename(),
                                                        "line": fr.GetLineEntry().GetLine(),
                                                    },
                                                }
                                            )
                            if sess.process and sess.process.IsValid():
                                out = sess.process.GetSTDOUT(4096)
                                if out:
                                    if sess.events is not None:
                                        sess.events.append(
                                            {
                                                "type": "stdout",
                                                "sessionId": session_id,
                                                "data": {"text": out},
                                            }
                                        )
                                err = sess.process.GetSTDERR(4096)
                                if err:
                                    if sess.events is not None:
                                        sess.events.append(
                                            {
                                                "type": "stderr",
                                                "sessionId": session_id,
                                                "data": {"text": err},
                                            }
                                        )
                    except Exception:
                        pass
            t = threading.Thread(target=run, daemon=True)
            sess.event_thread = t
            t.start()

    def _get(self, session_id: str) -> Session:
        sess = self._sessions.get(session_id)
        if not sess:
            raise LLDBError(1002, "Session not found", {"sessionId": session_id})
        return sess

    def _ensure_logs(self):
        import os
        from ..utils.config import config
        os.makedirs(config.log_dir or "logs", exist_ok=True)

    def _transcript_path(self, session_id: str) -> str:
        self._ensure_logs()
        from pathlib import Path
        from ..utils.config import config
        return str(Path(config.log_dir or "logs") / ("transcript_" + session_id + ".log"))

    def _write_transcript(self, session_id, command, output, error):
        path = self._transcript_path(session_id)
        text = "(lldb) " + str(command) + "\n"
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
        sess = self._sessions.get(session_id)
        if sess and sess.events is not None:
            sess.events.append({"type": "transcript", "sessionId": session_id, "data": {"text": text}})

    def _ci(self, sess: Session):
        return sess.debugger.GetCommandInterpreter()

    def create_target(self, session_id, file, arch=None, triple=None, platform=None):
        with self._lock:
            sess = self._get(session_id)
            if sess.debugger is None:
                raise LLDBError(2000, "LLDB unavailable")
            if config.allowed_root:
                import os
                real = os.path.realpath(file)
                root = os.path.realpath(config.allowed_root)
                if not real.startswith(root + os.sep) and real != root:
                    raise LLDBError(
                        7003,
                        "Target outside allowed root",
                        {"file": file, "allowed_root": config.allowed_root},
                    )
            import lldb
            ro = lldb.SBCommandReturnObject()
            cmd = "target create \"" + file + "\""
            self._ci(sess).HandleCommand(cmd, ro)
            out = ro.GetOutput()
            err = ro.GetError()
            self._write_transcript(session_id, cmd, out, err)
            target = sess.debugger.GetSelectedTarget()
            if not target or not target.IsValid():
                raise LLDBError(2001, "Target creation failed", {"file": file})
            sess.target = target
            payload = {"triple": target.GetTriple(), "platform": platform or ""}
            if sess.events is not None:
                sess.events.append(
                    {
                        "type": "targetCreated",
                        "sessionId": session_id,
                        "data": {"file": file},
                    }
                )
            return {"triple": payload["triple"], "platform": payload["platform"], "transcript": "(lldb) " + cmd + "\n" + (out or "") + (err or "")}

    def launch(self, session_id, args=None, env=None, cwd=None, flags=None):
        with self._lock:
            sess = self._get(session_id)
            if sess.debugger is None:
                raise LLDBError(2000, "LLDB unavailable")
            if not sess.target or not sess.target.IsValid():
                raise LLDBError(2001, "Target missing")
            import lldb
            ro = lldb.SBCommandReturnObject()
            cmd = "process launch"
            if args:
                cmd += " -- " + " ".join(str(a) for a in args)
            self._ci(sess).HandleCommand(cmd, ro)
            out = ro.GetOutput()
            err = ro.GetError()
            self._write_transcript(session_id, cmd, out, err)
            process = sess.target.GetProcess()
            if not process or not process.IsValid():
                raise LLDBError(2002, "Launch failed")
            sess.process = process
            sess.last_launch_args = args or []
            sess.last_launch_env = env or {}
            sess.last_launch_cwd = cwd
            sess.last_launch_flags = flags or {}
            try:
                if sess.listener:
                    bits = (
                        lldb.SBProcess.eBroadcastBitStateChanged
                        | lldb.SBProcess.eBroadcastBitSTDOUT
                        | lldb.SBProcess.eBroadcastBitSTDERR
                    )
                    process.GetBroadcaster().AddListener(sess.listener, bits)
                import os
                from ..utils.config import config
                os.makedirs(config.log_dir or "logs", exist_ok=True)
                ci = sess.debugger.GetCommandInterpreter()
                ro = lldb.SBCommandReturnObject()
                log_file = (config.log_dir or "logs") + f"/lldb_{session_id}.log"
                ci.HandleCommand(
                    f"log enable --threadsafe --file {log_file} lldb api process breakpoint thread expr",
                    ro,
                )
            except Exception:
                pass
            state = process.GetState()
            if sess.events is not None:
                sess.events.append(
                    {
                        "type": "processLaunched",
                        "sessionId": session_id,
                        "data": {"pid": process.GetProcessID(), "state": int(state)},
                    }
                )
            return {"pid": process.GetProcessID(), "state": int(state), "transcript": "(lldb) " + cmd + "\n" + (out or "") + (err or "")}

    def attach(self, session_id, pid=None, name=None):
        with self._lock:
            sess = self._get(session_id)
            if sess.debugger is None:
                raise LLDBError(2000, "LLDB unavailable")
            import lldb
            target = sess.target or sess.debugger.CreateTarget(None)
            sess.target = target
            ro = lldb.SBCommandReturnObject()
            if pid:
                cmd = "process attach --pid " + str(int(pid))
            elif name:
                cmd = "process attach --name \"" + str(name) + "\""
            else:
                raise LLDBError(1001, "Invalid params")
            self._ci(sess).HandleCommand(cmd, ro)
            out = ro.GetOutput()
            err = ro.GetError()
            self._write_transcript(session_id, cmd, out, err)
            process = sess.target.GetProcess()
            if not process or not process.IsValid():
                raise LLDBError(2003, "Attach failed")
            sess.process = process
            try:
                if sess.listener:
                    bits = (
                        lldb.SBProcess.eBroadcastBitStateChanged
                        | lldb.SBProcess.eBroadcastBitSTDOUT
                        | lldb.SBProcess.eBroadcastBitSTDERR
                    )
                    process.GetBroadcaster().AddListener(sess.listener, bits)
                import os
                from ..utils.config import config
                os.makedirs(config.log_dir or "logs", exist_ok=True)
                ci = sess.debugger.GetCommandInterpreter()
                ro = lldb.SBCommandReturnObject()
                log_file = (config.log_dir or "logs") + f"/lldb_{session_id}.log"
                ci.HandleCommand(
                    f"log enable --threadsafe --file {log_file} lldb api process breakpoint thread expr",
                    ro,
                )
            except Exception:
                pass
            state = process.GetState()
            if sess.events is not None:
                sess.events.append(
                    {
                        "type": "processAttached",
                        "sessionId": session_id,
                        "data": {"pid": process.GetProcessID(), "state": int(state)},
                    }
                )
            return {"pid": process.GetProcessID(), "state": int(state), "transcript": "(lldb) " + cmd + "\n" + (out or "") + (err or "")}

    def update_breakpoint(self, session_id, breakpoint_id, enabled=None, ignore_count=None, condition=None):
        with self._lock:
            sess = self._get(session_id)
            if not sess.target or not sess.target.IsValid():
                raise LLDBError(2001, "Target missing")
            bp = sess.target.FindBreakpointByID(breakpoint_id)
            if not bp or not bp.IsValid():
                raise LLDBError(3001, "Breakpoint not found")
            if enabled is not None:
                bp.SetEnabled(bool(enabled))
            if ignore_count is not None:
                bp.SetIgnoreCount(int(ignore_count))
            if condition is not None:
                bp.SetCondition(str(condition))
            if sess.events is not None:
                sess.events.append(
                    {
                        "type": "breakpointUpdated",
                        "sessionId": session_id,
                        "data": {
                            "breakpointId": bp.GetID(),
                            "enabled": bp.IsEnabled(),
                            "ignoreCount": bp.GetIgnoreCount(),
                            "condition": condition or "",
                        },
                    }
                )
            return {"ok": True}

    def set_watchpoint(self, session_id, addr, size, read=True, write=True):
        with self._lock:
            sess = self._get(session_id)
            if not sess.target or not sess.target.IsValid():
                raise LLDBError(2001, "Target missing")
            import lldb
            wp = sess.target.WatchAddress(addr, size, read, write, lldb.SBError())
            if not wp or not wp.IsValid():
                raise LLDBError(3002, "Watchpoint create failed")
            if sess.events is not None:
                sess.events.append(
                    {
                        "type": "watchpointSet",
                        "sessionId": session_id,
                        "data": {"watchpointId": wp.GetID(), "read": read, "write": write, "size": size},
                    }
                )
            return {"watchpointId": wp.GetID()}

    def delete_watchpoint(self, session_id, watchpoint_id):
        with self._lock:
            sess = self._get(session_id)
            if not sess.target or not sess.target.IsValid():
                raise LLDBError(2001, "Target missing")
        
            ok = sess.target.DeleteWatchpoint(watchpoint_id)
            if not ok:
                raise LLDBError(3002, "Watchpoint delete failed")
            if sess.events is not None:
                sess.events.append(
                    {
                        "type": "watchpointDeleted",
                        "sessionId": session_id,
                        "data": {"watchpointId": watchpoint_id},
                    }
                )
            return {"ok": True}

    def list_watchpoints(self, session_id):
        with self._lock:
            sess = self._get(session_id)
            if not sess.target or not sess.target.IsValid():
                raise LLDBError(2001, "Target missing")
            n = sess.target.GetNumWatchpoints()
            items = []
            for i in range(n):
                wp = sess.target.GetWatchpointAtIndex(i)
                items.append({"id": wp.GetID(), "enabled": wp.IsEnabled(), "hitCount": wp.GetHitCount()})
            return {"watchpoints": items}

    def disassemble(self, session_id, addr=None, count=64):
        with self._lock:
            sess = self._get(session_id)
            if not sess.target or not sess.target.IsValid():
                raise LLDBError(2001, "Target missing")
            import lldb
            if addr is None:
                if not sess.process or not sess.process.IsValid():
                    raise LLDBError(2002, "Process missing")
                th = sess.process.GetSelectedThread()
                fr = th.GetSelectedFrame()
                addr = int(fr.GetPC())
            address = lldb.SBAddress(addr, sess.target)
            insn_list = sess.target.ReadInstructions(address, count)
            out = []
            for i in range(insn_list.GetSize()):
                insn = insn_list.GetInstructionAtIndex(i)
                out.append(
                    {
                        "addr": insn.GetAddress().GetLoadAddress(sess.target),
                        "mnemonic": insn.GetMnemonic(sess.target),
                        "operands": insn.GetOperands(sess.target),
                    }
                )
            return {"instructions": out}

    def signal(self, session_id, sig):
        with self._lock:
            sess = self._get(session_id)
            if not sess.process or not sess.process.IsValid():
                raise LLDBError(2002, "Process missing")
            sess.process.Signal(sig)
            return {"ok": True}

    def restart(self, session_id):
        with self._lock:
            sess = self._get(session_id)
            if not sess.target or not sess.target.IsValid():
                raise LLDBError(2001, "Target missing")
            import lldb
            if sess.process and sess.process.IsValid():
                try:
                    sess.process.Kill()
                except Exception:
                    pass
            args = sess.last_launch_args or []
            env = sess.last_launch_env or {}
            cwd = sess.last_launch_cwd
            launch_info = lldb.SBLaunchInfo(args)
            if cwd:
                launch_info.SetWorkingDirectory(cwd)
            for k, v in env.items():
                launch_info.SetEnvironmentEntry(k, v)
            process = sess.target.Launch(launch_info, lldb.SBError())
            if not process or not process.IsValid():
                raise LLDBError(2002, "Launch failed")
            sess.process = process
            state = process.GetState()
            return {"pid": process.GetProcessID(), "state": int(state)}

    def set_breakpoint(self, session_id, file=None, line=None, symbol=None, address=None):
        with self._lock:
            sess = self._get(session_id)
            if sess.debugger is None or not sess.target or not sess.target.IsValid():
                raise LLDBError(2001, "Target missing")
            import lldb
            ro = lldb.SBCommandReturnObject()
            if file and line:
                cmd = "breakpoint set --file \"" + str(file) + "\" --line " + str(int(line))
            elif symbol:
                cmd = "breakpoint set --name \"" + str(symbol) + "\""
            elif address is not None:
                cmd = "breakpoint set --address " + str(int(address))
            else:
                raise LLDBError(1001, "Invalid params")
            self._ci(sess).HandleCommand(cmd, ro)
            out = ro.GetOutput()
            err = ro.GetError()
            self._write_transcript(session_id, cmd, out, err)
            bp = sess.target.GetBreakpointAtIndex(sess.target.GetNumBreakpoints() - 1)
            if not bp or not bp.IsValid():
                raise LLDBError(3001, "Breakpoint create failed")
            if sess.events is not None:
                sess.events.append(
                    {
                        "type": "breakpointSet",
                        "sessionId": session_id,
                        "data": {"breakpointId": bp.GetID()},
                    }
                )
            return {"breakpointId": bp.GetID(), "transcript": "(lldb) " + cmd + "\n" + (out or "") + (err or "")}

    def delete_breakpoint(self, session_id, breakpoint_id):
        with self._lock:
            sess = self._get(session_id)
            if not sess.target or not sess.target.IsValid():
                raise LLDBError(2001, "Target missing")
            ok = sess.target.BreakpointDelete(breakpoint_id)
            if not ok:
                raise LLDBError(3001, "Breakpoint delete failed")
            return {"ok": True}

    def list_breakpoints(self, session_id):
        with self._lock:
            sess = self._get(session_id)
            if not sess.target or not sess.target.IsValid():
                raise LLDBError(2001, "Target missing")
            n = sess.target.GetNumBreakpoints()
            items = []
            for i in range(n):
                bp = sess.target.GetBreakpointAtIndex(i)
                items.append({"id": bp.GetID(), "enabled": bp.IsEnabled(), "hitCount": bp.GetHitCount()})
            return {"breakpoints": items}

    def continue_process(self, session_id):
        with self._lock:
            sess = self._get(session_id)
            if not sess.process or not sess.process.IsValid():
                raise LLDBError(2002, "Process missing")
            import lldb
            state = sess.process.GetState()
            if state != lldb.eStateStopped:
                cmd = "process continue"
                note = "process is already running\n"
                self._write_transcript(session_id, cmd, None, note)
                return {"ok": True, "transcript": "(lldb) " + cmd + "\n" + note}
            ro = lldb.SBCommandReturnObject()
            cmd = "process continue"
            self._ci(sess).HandleCommand(cmd, ro)
            out = ro.GetOutput()
            err = ro.GetError()
            self._write_transcript(session_id, cmd, out, err)
            return {"ok": True, "transcript": "(lldb) " + cmd + "\n" + (out or "") + (err or "")}

    def pause_process(self, session_id):
        with self._lock:
            sess = self._get(session_id)
            if not sess.process or not sess.process.IsValid():
                raise LLDBError(2002, "Process missing")
            sess.process.Stop()
            return {"ok": True}

    def _get_selected_thread(self, sess):
        return sess.process.GetSelectedThread() if sess.process else None

    def step_in(self, session_id):
        with self._lock:
            sess = self._get(session_id)
            th = self._get_selected_thread(sess)
            if not th or not th.IsValid():
                raise LLDBError(2002, "Thread missing")
            import lldb
            ro = lldb.SBCommandReturnObject()
            cmd = "thread step-in"
            self._ci(sess).HandleCommand(cmd, ro)
            out = ro.GetOutput()
            err = ro.GetError()
            self._write_transcript(session_id, cmd, out, err)
            return {"ok": True, "transcript": "(lldb) " + cmd + "\n" + (out or "") + (err or "")}

    def step_over(self, session_id):
        with self._lock:
            sess = self._get(session_id)
            th = self._get_selected_thread(sess)
            if not th or not th.IsValid():
                raise LLDBError(2002, "Thread missing")
            import lldb
            ro = lldb.SBCommandReturnObject()
            cmd = "thread step-over"
            self._ci(sess).HandleCommand(cmd, ro)
            out = ro.GetOutput()
            err = ro.GetError()
            self._write_transcript(session_id, cmd, out, err)
            return {"ok": True, "transcript": "(lldb) " + cmd + "\n" + (out or "") + (err or "")}

    def step_out(self, session_id):
        with self._lock:
            sess = self._get(session_id)
            th = self._get_selected_thread(sess)
            if not th or not th.IsValid():
                raise LLDBError(2002, "Thread missing")
            import lldb
            ro = lldb.SBCommandReturnObject()
            cmd = "thread step-out"
            self._ci(sess).HandleCommand(cmd, ro)
            out = ro.GetOutput()
            err = ro.GetError()
            self._write_transcript(session_id, cmd, out, err)
            return {"ok": True, "transcript": "(lldb) " + cmd + "\n" + (out or "") + (err or "")}

    def threads(self, session_id):
        with self._lock:
            sess = self._get(session_id)
            if not sess.process or not sess.process.IsValid():
                raise LLDBError(2002, "Process missing")
            items = []
            for i in range(sess.process.GetNumThreads()):
                th = sess.process.GetThreadAtIndex(i)
                items.append({"id": th.GetThreadID(), "state": int(th.GetState())})
            return {"threads": items}

    def frames(self, session_id, thread_id):
        with self._lock:
            sess = self._get(session_id)
            if not sess.process or not sess.process.IsValid():
                raise LLDBError(2002, "Process missing")
            th = sess.process.GetThreadByID(thread_id)
            if not th or not th.IsValid():
                raise LLDBError(2002, "Thread missing")
            frames = []
            for i in range(th.GetNumFrames()):
                fr = th.GetFrameAtIndex(i)
                frames.append(
                    {
                        "index": i,
                        "function": fr.GetFunctionName(),
                        "file": fr.GetLineEntry().GetFileSpec().GetFilename(),
                        "line": fr.GetLineEntry().GetLine(),
                        "pc": fr.GetPC(),
                    }
                )
            return {"frames": frames}

    def stack_trace(self, session_id, thread_id=None):
        with self._lock:
            sess = self._get(session_id)
            if not sess.process or not sess.process.IsValid():
                raise LLDBError(2002, "Process missing")
            th = sess.process.GetThreadByID(thread_id) if thread_id else sess.process.GetSelectedThread()
            if not th or not th.IsValid():
                raise LLDBError(2002, "Thread missing")
            frames = []
            for i in range(th.GetNumFrames()):
                fr = th.GetFrameAtIndex(i)
                frames.append(
                    {
                        "index": i,
                        "function": fr.GetFunctionName(),
                        "file": fr.GetLineEntry().GetFileSpec().GetFilename(),
                        "line": fr.GetLineEntry().GetLine(),
                        "pc": fr.GetPC(),
                    }
                )
            return {"frames": frames}

    def select_thread(self, session_id, thread_id):
        with self._lock:
            sess = self._get(session_id)
            if not sess.process or not sess.process.IsValid():
                raise LLDBError(2002, "Process missing")
            th = sess.process.GetThreadByID(thread_id)
            if not th or not th.IsValid():
                raise LLDBError(2002, "Thread missing")
            sess.process.SetSelectedThread(th)
            return {"ok": True}

    def select_frame(self, session_id, thread_id, frame_index):
        with self._lock:
            sess = self._get(session_id)
            if not sess.process or not sess.process.IsValid():
                raise LLDBError(2002, "Process missing")
            th = sess.process.GetThreadByID(thread_id)
            if not th or not th.IsValid():
                raise LLDBError(2002, "Thread missing")
            th.SetSelectedFrame(frame_index)
            return {"ok": True}

    def evaluate(self, session_id, expr, frame_index=None):
        with self._lock:
            sess = self._get(session_id)
            if not sess.process or not sess.process.IsValid():
                raise LLDBError(2002, "Process missing")
            import lldb
            ro = lldb.SBCommandReturnObject()
            cmd = "expr " + str(expr)
            self._ci(sess).HandleCommand(cmd, ro)
            out = ro.GetOutput()
            err = ro.GetError()
            self._write_transcript(session_id, cmd, out, err)
            val = None
            if out:
                val = out.strip().splitlines()[-1]
            return {"value": val, "transcript": "(lldb) " + cmd + "\n" + (out or "") + (err or "")}

    def command(self, session_id: str, command: str):
        with self._lock:
            sess = self._get(session_id)
            if sess.debugger is None:
                raise LLDBError(2000, "LLDB unavailable")
            import lldb
            ro = lldb.SBCommandReturnObject()
            self._ci(sess).HandleCommand(str(command), ro)
            out = ro.GetOutput()
            err = ro.GetError()
            self._write_transcript(session_id, command, out, err)
            return {"ok": ro.Succeeded(), "output": out or "", "error": err or "", "transcript": "(lldb) " + str(command) + "\n" + (out or "") + (err or "")}

    def read_memory(self, session_id, addr, size):
        with self._lock:
            sess = self._get(session_id)
            if not sess.process or not sess.process.IsValid():
                raise LLDBError(2002, "Process missing")
            import ctypes
            buf = ctypes.create_string_buffer(size)
            err = __import__("lldb").SBError()
            read = sess.process.ReadMemory(addr, buf, size, err)
            if err.Fail():
                raise LLDBError(5001, "Read memory failed", {"error": err.GetCString()})
            return {"bytes": buf.raw[:read].hex()}

    def write_memory(self, session_id, addr, data_hex):
        with self._lock:
            sess = self._get(session_id)
            if not sess.process or not sess.process.IsValid():
                raise LLDBError(2002, "Process missing")
            data = bytes.fromhex(data_hex)
            err = __import__("lldb").SBError()
            wrote = sess.process.WriteMemory(addr, data, err)
            if err.Fail():
                raise LLDBError(5001, "Write memory failed", {"error": err.GetCString()})
            return {"written": wrote}

    def poll_events(self, session_id, limit=32):
        with self._lock:
            sess = self._get(session_id)
            items = []
            if sess.events is not None:
                while limit > 0 and sess.events:
                    items.append(sess.events.popleft())
                    limit -= 1
            return {"events": items}
