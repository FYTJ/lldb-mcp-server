import json
import logging
import os
import sys

from ..protocol.schema import make_error, make_response
from ..session.manager import SessionManager
from ..utils.config import config

manager = SessionManager()
_app_log = logging.getLogger("app.server")
if not _app_log.handlers:
    from pathlib import Path
    log_dir = config.log_dir or "logs"
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(os.path.join(log_dir, "app.log"))
    fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
    _app_log.addHandler(fh)
    _app_log.setLevel(logging.INFO)

def handle_request(req: dict) -> dict:
    req_id = str(req.get("id"))
    method = req.get("method")
    params = req.get("params") or {}
    try:
        _app_log.info("request %s", json.dumps(req, ensure_ascii=False))
        if method == "initialize":
            session_id = manager.create_session()
            return make_response(req_id, {"sessionId": session_id})
        if method == "terminate":
            session_id = params.get("sessionId")
            if not session_id:
                return make_error(req_id, 1001, "Missing sessionId")
            manager.terminate_session(session_id)
            return make_response(req_id, {"ok": True})
        if method == "listSessions":
            return make_response(req_id, {"sessions": manager.list_sessions()})
        if method == "createTarget":
            session_id = params.get("sessionId")
            file = params.get("file")
            res = manager.create_target(
                session_id,
                file,
                params.get("arch"),
                params.get("triple"),
                params.get("platform"),
            )
            return make_response(req_id, res)
        if method == "launch":
            session_id = params.get("sessionId")
            if not config.allow_launch:
                return make_error(req_id, 7001, "Launch not allowed")
            res = manager.launch(
                session_id,
                params.get("args"),
                params.get("env"),
                params.get("cwd"),
                params.get("flags"),
            )
            return make_response(req_id, res)
        if method == "attach":
            session_id = params.get("sessionId")
            if not config.allow_attach:
                return make_error(req_id, 7002, "Attach not allowed")
            res = manager.attach(session_id, params.get("pid"), params.get("name"))
            return make_response(req_id, res)
        if method == "setBreakpoint":
            session_id = params.get("sessionId")
            res = manager.set_breakpoint(
                session_id,
                params.get("file"),
                params.get("line"),
                params.get("symbol"),
                params.get("address"),
            )
            return make_response(req_id, res)
        if method == "deleteBreakpoint":
            session_id = params.get("sessionId")
            res = manager.delete_breakpoint(session_id, params.get("breakpointId"))
            return make_response(req_id, res)
        if method == "listBreakpoints":
            session_id = params.get("sessionId")
            res = manager.list_breakpoints(session_id)
            return make_response(req_id, res)
        if method == "updateBreakpoint":
            session_id = params.get("sessionId")
            res = manager.update_breakpoint(
                session_id,
                params.get("breakpointId"),
                params.get("enabled"),
                params.get("ignoreCount"),
                params.get("condition"),
            )
            return make_response(req_id, res)
        if method == "continue":
            session_id = params.get("sessionId")
            res = manager.continue_process(session_id)
            return make_response(req_id, res)
        if method == "pause":
            session_id = params.get("sessionId")
            res = manager.pause_process(session_id)
            return make_response(req_id, res)
        if method == "stepIn":
            session_id = params.get("sessionId")
            res = manager.step_in(session_id)
            return make_response(req_id, res)
        if method == "stepOver":
            session_id = params.get("sessionId")
            res = manager.step_over(session_id)
            return make_response(req_id, res)
        if method == "stepOut":
            session_id = params.get("sessionId")
            res = manager.step_out(session_id)
            return make_response(req_id, res)
        if method == "threads":
            session_id = params.get("sessionId")
            res = manager.threads(session_id)
            return make_response(req_id, res)
        if method == "frames":
            session_id = params.get("sessionId")
            res = manager.frames(session_id, params.get("threadId"))
            return make_response(req_id, res)
        if method == "stackTrace":
            session_id = params.get("sessionId")
            res = manager.stack_trace(session_id, params.get("threadId"))
            return make_response(req_id, res)
        if method == "selectThread":
            session_id = params.get("sessionId")
            res = manager.select_thread(session_id, params.get("threadId"))
            return make_response(req_id, res)
        if method == "selectFrame":
            session_id = params.get("sessionId")
            res = manager.select_frame(session_id, params.get("threadId"), params.get("frameIndex"))
            return make_response(req_id, res)
        if method == "evaluate":
            session_id = params.get("sessionId")
            res = manager.evaluate(session_id, params.get("expr"), params.get("frameIndex"))
            return make_response(req_id, res)
        if method == "readMemory":
            session_id = params.get("sessionId")
            res = manager.read_memory(session_id, params.get("addr"), params.get("size"))
            return make_response(req_id, res)
        if method == "writeMemory":
            session_id = params.get("sessionId")
            res = manager.write_memory(session_id, params.get("addr"), params.get("bytes"))
            return make_response(req_id, res)
        if method == "setWatchpoint":
            session_id = params.get("sessionId")
            res = manager.set_watchpoint(
                session_id,
                params.get("addr"),
                params.get("size"),
                params.get("read", True),
                params.get("write", True),
            )
            return make_response(req_id, res)
        if method == "deleteWatchpoint":
            session_id = params.get("sessionId")
            res = manager.delete_watchpoint(session_id, params.get("watchpointId"))
            return make_response(req_id, res)
        if method == "listWatchpoints":
            session_id = params.get("sessionId")
            res = manager.list_watchpoints(session_id)
            return make_response(req_id, res)
        if method == "disassemble":
            session_id = params.get("sessionId")
            res = manager.disassemble(session_id, params.get("addr"), params.get("count") or 64)
            return make_response(req_id, res)
        if method == "signal":
            session_id = params.get("sessionId")
            res = manager.signal(session_id, params.get("sig"))
            return make_response(req_id, res)
        if method == "restart":
            session_id = params.get("sessionId")
            res = manager.restart(session_id)
            return make_response(req_id, res)
        if method == "pollEvents":
            session_id = params.get("sessionId")
            res = manager.poll_events(session_id, params.get("limit") or 32)
            return make_response(req_id, res)
        if method == "command":
            session_id = params.get("sessionId")
            res = manager.command(session_id, params.get("command"))
            return make_response(req_id, res)
        return make_error(req_id, 1001, "Unknown method", {"method": method})
    except Exception as e:
        code = getattr(e, "code", 9999)
        message = str(getattr(e, "message", str(e)))
        data = getattr(e, "data", None)
        resp = make_error(req_id, code, message, data)
        _app_log.info("response %s", json.dumps(resp, ensure_ascii=False))
        return resp

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            sys.stdout.write(json.dumps({"error": {"code": 1001, "message": "Invalid JSON"}}) + "\n")
            sys.stdout.flush()
            continue
        resp = handle_request(req)
        _app_log.info("response %s", json.dumps(resp, ensure_ascii=False))
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
