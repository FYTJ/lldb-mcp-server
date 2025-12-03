import json
import logging
import os
import sys
import argparse
import socket
import threading
import importlib
import subprocess
from pathlib import Path

from ..protocol.schema import make_error, make_response
from ..session.manager import SessionManager
from ..utils.config import config

manager = SessionManager()
_app_log = logging.getLogger("app.mcp")
if not _app_log.handlers:
    from pathlib import Path
    log_dir = config.log_dir or "logs"
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(os.path.join(log_dir, "app.log"))
    fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
    _app_log.addHandler(fh)
    _app_log.setLevel(logging.INFO)

def handle_tools_call(name: str, args: dict) -> dict:
    if name == "lldb.initialize":
        session_id = manager.create_session()
        return {"sessionId": session_id}
    if name == "lldb.terminate":
        session_id = args.get("sessionId")
        if not session_id:
            raise ValueError("Missing sessionId")
        manager.terminate_session(session_id)
        return {"ok": True}
    if name == "lldb.listSessions":
        return {"sessions": manager.list_sessions()}
    if name == "lldb.createTarget":
        res = manager.create_target(
            args.get("sessionId"),
            args.get("file"),
            args.get("arch"),
            args.get("triple"),
            args.get("platform"),
        )
        return res
    if name == "lldb.launch":
        if not config.allow_launch:
            return {"error": {"code": 7001, "message": "Launch not allowed"}}
        res = manager.launch(
            args.get("sessionId"),
            args.get("args"),
            args.get("env"),
            args.get("cwd"),
            args.get("flags"),
        )
        return res
    if name == "lldb.attach":
        if not config.allow_attach:
            return {"error": {"code": 7002, "message": "Attach not allowed"}}
        res = manager.attach(args.get("sessionId"), args.get("pid"), args.get("name"))
        return res
    if name == "lldb.setBreakpoint":
        res = manager.set_breakpoint(
            args.get("sessionId"),
            args.get("file"),
            args.get("line"),
            args.get("symbol"),
            args.get("address"),
        )
        return res
    if name == "lldb.deleteBreakpoint":
        res = manager.delete_breakpoint(args.get("sessionId"), args.get("breakpointId"))
        return res
    if name == "lldb.listBreakpoints":
        res = manager.list_breakpoints(args.get("sessionId"))
        return res
    if name == "lldb.updateBreakpoint":
        res = manager.update_breakpoint(
            args.get("sessionId"),
            args.get("breakpointId"),
            args.get("enabled"),
            args.get("ignoreCount"),
            args.get("condition"),
        )
        return res
    if name == "lldb.continue":
        return manager.continue_process(args.get("sessionId"))
    if name == "lldb.pause":
        return manager.pause_process(args.get("sessionId"))
    if name == "lldb.stepIn":
        return manager.step_in(args.get("sessionId"))
    if name == "lldb.stepOver":
        return manager.step_over(args.get("sessionId"))
    if name == "lldb.stepOut":
        return manager.step_out(args.get("sessionId"))
    if name == "lldb.threads":
        return manager.threads(args.get("sessionId"))
    if name == "lldb.frames":
        return manager.frames(args.get("sessionId"), args.get("threadId"))
    if name == "lldb.stackTrace":
        return manager.stack_trace(args.get("sessionId"), args.get("threadId"))
    if name == "lldb.selectThread":
        return manager.select_thread(args.get("sessionId"), args.get("threadId"))
    if name == "lldb.selectFrame":
        return manager.select_frame(args.get("sessionId"), args.get("threadId"), args.get("frameIndex"))
    if name == "lldb.evaluate":
        return manager.evaluate(args.get("sessionId"), args.get("expr"), args.get("frameIndex"))
    if name == "lldb.readMemory":
        return manager.read_memory(args.get("sessionId"), args.get("addr"), args.get("size"))
    if name == "lldb.writeMemory":
        return manager.write_memory(args.get("sessionId"), args.get("addr"), args.get("bytes"))
    if name == "lldb.pollEvents":
        return manager.poll_events(args.get("sessionId"), args.get("limit") or 32)
    if name == "lldb.setWatchpoint":
        return manager.set_watchpoint(
            args.get("sessionId"),
            args.get("addr"),
            args.get("size"),
            args.get("read", True),
            args.get("write", True),
        )
    if name == "lldb.deleteWatchpoint":
        return manager.delete_watchpoint(args.get("sessionId"), args.get("watchpointId"))
    if name == "lldb.listWatchpoints":
        return manager.list_watchpoints(args.get("sessionId"))
    if name == "lldb.disassemble":
        return manager.disassemble(args.get("sessionId"), args.get("addr"), args.get("count") or 64)
    if name == "lldb.signal":
        return manager.signal(args.get("sessionId"), args.get("sig"))
    if name == "lldb.restart":
        return manager.restart(args.get("sessionId"))
    if name == "lldb.command":
        return manager.command(args.get("sessionId"), args.get("command"))
    raise ValueError("Unknown tool")

def _process_message(line: str) -> str:
    line = line.strip()
    if not line:
        return ""
    try:
        req = json.loads(line)
    except Exception:
        return json.dumps({"error": {"code": 1001, "message": "Invalid JSON"}})
    req_id = str(req.get("id"))
    method = req.get("method")
    params = req.get("params") or {}
    try:
        if method == "tools.call":
            name = params.get("name")
            args = params.get("arguments") or {}
            _app_log.info("request %s", json.dumps({"name": name, "arguments": args}, ensure_ascii=False))
            result = handle_tools_call(name, args)
            resp = make_response(req_id, result)
        else:
            resp = make_error(req_id, 1001, "Unknown method", {"method": method})
    except Exception as e:
        code = getattr(e, "code", 9999)
        message = str(getattr(e, "message", str(e)))
        data = getattr(e, "data", None)
        resp = make_error(req_id, code, message, data)
    _app_log.info("response %s", json.dumps(resp, ensure_ascii=False))
    return json.dumps(resp)

def _serve_socket(host: str, port: int):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(16)
    _app_log.info("listening tcp %s:%d", host, port)

    def handle(conn: socket.socket, addr):
        try:
            rf = conn.makefile("r", encoding="utf-8")
            wf = conn.makefile("w", encoding="utf-8")
            for line in rf:
                out = _process_message(line)
                if out:
                    wf.write(out + "\n")
                    wf.flush()
            try:
                rf.close()
            except Exception:
                pass
            try:
                wf.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
        except Exception as e:
            _app_log.info("socket error %s", str(e))

    while True:
        c, a = srv.accept()
        t = threading.Thread(target=handle, args=(c, a), daemon=True)
        t.start()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen", help="host:port to listen on")
    args = parser.parse_args()

    def ensure_lldb_env(reexec=False):
        try:
            importlib.import_module("lldb")
            _app_log.info("lldb import ok")
            return True
        except Exception as e:
            _app_log.info("lldb import failed: %s", str(e))
            if reexec and os.environ.get("LLDB_MCP_REEXECED") != "1":
                candidates_py = []
                if config.preferred_python_executable:
                    candidates_py.append(config.preferred_python_executable)
                if sys.executable not in candidates_py:
                    candidates_py.append(sys.executable)
                env = os.environ.copy()
                try:
                    out = subprocess.check_output(["lldb", "-P"], text=True).strip()
                    if out:
                        env["PYTHONPATH"] = out + (os.pathsep + env.get("PYTHONPATH", ""))
                except Exception:
                    pass
                for p in (config.lldb_python_paths or []):
                    try:
                        if Path(p).exists():
                            env["PYTHONPATH"] = p + (os.pathsep + env.get("PYTHONPATH", ""))
                    except Exception:
                        pass
                devroot = None
                try:
                    devroot = subprocess.check_output(["xcode-select", "-p"], text=True).strip()
                except Exception:
                    pass
                fwpaths = list(config.lldb_framework_paths or [])
                if devroot:
                    sf = str(Path(devroot) / "../SharedFrameworks")
                    pf = str(Path(devroot) / "Library" / "PrivateFrameworks")
                    if Path(sf).exists():
                        fwpaths.append(sf)
                    if Path(pf).exists():
                        fwpaths.append(pf)
                for fp in fwpaths:
                    if Path(fp).exists():
                        env["DYLD_FRAMEWORK_PATH"] = fp + (os.pathsep + env.get("DYLD_FRAMEWORK_PATH", ""))
                        env["DYLD_LIBRARY_PATH"] = fp + (os.pathsep + env.get("DYLD_LIBRARY_PATH", ""))
                env["PYTHONUNBUFFERED"] = "1"
                env["LLDB_MCP_REEXECED"] = "1"
                for exe in candidates_py:
                    if Path(exe).exists() or exe == sys.executable:
                        try:
                            listen_arg = args.listen or f"{config.server_host or '127.0.0.1'}:{getattr(config, 'server_port', 8765) or 8765}"
                            os.execvpe(exe, [exe, "-u", "-m", "lldb_mcp_server.mcp.server", "--listen", listen_arg], env)
                        except Exception:
                            continue
            return False
        candidates = []
        try:
            out = subprocess.check_output(["lldb", "-P"], text=True).strip()
            if out:
                candidates.append(out)
        except Exception:
            pass
        candidates.extend(list(config.lldb_python_paths or []))
        added = []
        for p in candidates:
            if p and Path(p).exists() and p not in sys.path:
                sys.path.insert(0, p)
                added.append(p)
        fw_candidates = list(config.lldb_framework_paths or [])
        try:
            devroot = subprocess.check_output(["xcode-select", "-p"], text=True).strip()
            if devroot:
                x_sf = str(Path(devroot) / "../SharedFrameworks")
                clt_pf = str(Path(devroot) / "Library" / "PrivateFrameworks")
                if Path(x_sf).exists():
                    fw_candidates.append(x_sf)
                if Path(clt_pf).exists():
                    fw_candidates.append(clt_pf)
        except Exception:
            pass
        def _prepend_env(key: str, val: str):
            cur = os.environ.get(key)
            os.environ[key] = val if not cur else (val + os.pathsep + cur)
        for fp in fw_candidates:
            if Path(fp).exists():
                _prepend_env("DYLD_FRAMEWORK_PATH", fp)
                _prepend_env("DYLD_LIBRARY_PATH", fp)
        try:
            import ctypes
            for fp in fw_candidates:
                ll = Path(fp) / "LLDB.framework" / "LLDB"
                if ll.exists():
                    try:
                        ctypes.CDLL(str(ll))
                        _app_log.info("preloaded LLDB framework from %s", str(ll))
                        break
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            importlib.import_module("lldb")
            _app_log.info("lldb import configured: sys.path added=%s; DYLD_FRAMEWORK_PATH=%s; DYLD_LIBRARY_PATH=%s", ",".join(added), os.environ.get("DYLD_FRAMEWORK_PATH", ""), os.environ.get("DYLD_LIBRARY_PATH", ""))
        except Exception as e:
            _app_log.info("lldb import still failed: %s", str(e))

    ensure_lldb_env(reexec=True)

    listen_str = args.listen or f"{config.server_host or '127.0.0.1'}:{getattr(config, 'server_port', 8765) or 8765}"
    hp = listen_str.split(":")
    host = hp[0] or (config.server_host or "127.0.0.1")
    port = int(hp[1]) if len(hp) > 1 else int(getattr(config, "server_port", 8765) or 8765)
    _serve_socket(host, port)

if __name__ == "__main__":
    main()
