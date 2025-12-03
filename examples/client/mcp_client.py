import os
import json
import time
import threading
from pathlib import Path
import sys
import socket
here = Path(__file__).resolve().parent
sys.path.insert(0, str(here))
from config import load_config

class MCPClient:
    def __init__(self, timeout=30, host=None, port=None):
        cfg = load_config()
        self._sock = None
        host = host or os.environ.get("MCP_HOST") or cfg.get("server_host")
        port = port or os.environ.get("MCP_PORT") or cfg.get("server_port")
        if not host or not port:
            raise RuntimeError("TCP host/port required: set MCP_HOST/MCP_PORT or config.json")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((str(host), int(port)))
        self._sock = s
        self._cwd = os.getcwd()
        self.lock = threading.Lock()
        self.responses = {}
        self.notifications = []
        self.timeout = int(timeout or (cfg.get("client") or {}).get("timeout", 30))
        self._rid = 0
        self._stop = False
        self._t_sock = threading.Thread(target=self._read_loop_sock)
        self._t_sock.start()
        self._health_check()

    def _read_loop_err(self):
        pass

    def _next_id(self):
        self._rid += 1
        return str(self._rid)

    def _request(self, method, params, timeout=None):
        rid = self._next_id()
        msg = {"id": rid, "method": method, "params": params}
        try:
            wf = self._sock.makefile("w", encoding="utf-8")
            wf.write(json.dumps(msg) + "\n")
            wf.flush()
        finally:
            try:
                wf.close()
            except Exception:
                pass
        t = int(timeout or self.timeout)
        start = time.time()
        while time.time() - start < t:
            with self.lock:
                if rid in self.responses:
                    return self.responses.pop(rid)
            time.sleep(0.01)
        raise TimeoutError("MCP request timeout")

    def _health_check(self):
        self._request("tools.call", {"name": "lldb.listSessions", "arguments": {}}, timeout=10)

    def tools_call(self, name, arguments, timeout=None):
        resp = self._request("tools.call", {"name": name, "arguments": arguments}, timeout)
        return resp.get("result") or resp.get("error") or resp

    def init_session(self):
        r = self.tools_call("lldb.initialize", {})
        return r.get("sessionId")

    def create_target(self, session_id, file, arch=None, triple=None, platform=None):
        return self.tools_call("lldb.createTarget", {"sessionId": session_id, "file": file, "arch": arch, "triple": triple, "platform": platform})

    def attach(self, session_id, pid, name=None):
        return self.tools_call("lldb.attach", {"sessionId": session_id, "pid": int(pid), "name": name})

    def launch(self, session_id, args=None, env=None, cwd=None, flags=None):
        return self.tools_call("lldb.launch", {"sessionId": session_id, "args": args or [], "env": env or {}, "cwd": cwd or "", "flags": flags or {}})

    def command(self, session_id, command):
        return self.tools_call("lldb.command", {"sessionId": session_id, "command": command})

    def set_watchpoint(self, session_id, addr, size=4, read=True, write=True):
        return self.tools_call("lldb.setWatchpoint", {"sessionId": session_id, "addr": int(addr), "size": int(size), "read": bool(read), "write": bool(write)})

    def read_memory(self, session_id, addr, size):
        return self.tools_call("lldb.readMemory", {"sessionId": session_id, "addr": int(addr), "size": int(size)})

    def transcript_path(self, session_id):
        root = Path(self._cwd or ".")
        cfg = load_config()
        log_dir = (cfg.get("log_dir") or "logs")
        return str(root / log_dir / f"transcript_{session_id}.log")

    def close(self):
        self._stop = True
        try:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            self._sock.close()
        except Exception:
            pass
        try:
            self._t_sock.join(timeout=1.0)
        except Exception:
            pass
    def _read_loop_sock(self):
        rf = self._sock.makefile("r", encoding="utf-8")
        try:
            for line in rf:
                if self._stop:
                    break
                s = line.strip()
                if not s:
                    continue
                try:
                    msg = json.loads(s)
                except Exception:
                    continue
                rid = msg.get("id")
                with self.lock:
                    if rid is not None:
                        self.responses[rid] = msg
                    else:
                        self.notifications.append(msg)
        finally:
            try:
                rf.close()
            except Exception:
                pass
