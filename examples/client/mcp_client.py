import os
import json
import time
import threading
import subprocess
import shlex
from pathlib import Path
from config import load_config
import socket

class MCPClient:
    def __init__(self, server_cmd=None, cwd=None, extra_env=None, timeout=30, project_root=None, src_path=None, host=None, port=None, unix_socket=None):
        cfg = load_config()
        src = src_path or os.environ.get("LLDB_MCP_SRC") or cfg.get("src_path")
        if not src:
            if project_root or os.environ.get("LLDB_MCP_PROJECT_ROOT") or cfg.get("project_root"):
                root = Path(project_root or os.environ.get("LLDB_MCP_PROJECT_ROOT") or cfg.get("project_root"))
                cand = root / "src"
                src = str(cand) if cand.exists() else None
        if not src:
            raise RuntimeError("src path not found, set LLDB_MCP_SRC or LLDB_MCP_PROJECT_ROOT")
        env = os.environ.copy()
        env["PYTHONPATH"] = src + (os.pathsep + env.get("PYTHONPATH", "")) if env.get("PYTHONPATH") else src
        if extra_env:
            env.update(extra_env)
        if server_cmd is None:
            server_cmd = ["python3", "-u", "-m", "lldb_mcp_server.mcp.server"]
        elif isinstance(server_cmd, str):
            server_cmd = shlex.split(server_cmd)
        self._sock = None
        host = host or os.environ.get("MCP_HOST") or cfg.get("server_host")
        port = port or os.environ.get("MCP_PORT") or cfg.get("server_port")
        unix_socket = unix_socket or os.environ.get("MCP_UNIX_SOCKET") or (cfg.get("client") or {}).get("unix_socket")
        if host or unix_socket:
            if unix_socket:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.connect(unix_socket)
            else:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((host or "127.0.0.1", int(port or 8765)))
            self._sock = s
            self._cwd = os.getcwd()
            self._stdio = False
        else:
            used_cwd = cwd or project_root or cfg.get("project_root") or str(Path(src).parents[1])
            self.proc = subprocess.Popen(
                server_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=used_cwd,
                env=env,
                bufsize=1,
            )
            self._cwd = used_cwd
            self._stdio = True
        self.lock = threading.Lock()
        self.responses = {}
        self.notifications = []
        self.stderr_lines = []
        self.timeout = int(timeout or (cfg.get("client") or {}).get("timeout", 30))
        self._rid = 0
        self._stop = False
        if self._stdio:
            self._t_out = threading.Thread(target=self._read_loop_out)
            self._t_err = threading.Thread(target=self._read_loop_err)
            self._t_out.start()
            self._t_err.start()
        else:
            self._t_sock = threading.Thread(target=self._read_loop_sock)
            self._t_sock.start()
        self._health_check()

    def _read_loop_out(self):
        for line in self.proc.stdout:
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

    def _read_loop_err(self):
        for line in self.proc.stderr:
            s = line.rstrip("\n")
            if s:
                with self.lock:
                    self.stderr_lines.append(s)
                    if len(self.stderr_lines) > 200:
                        self.stderr_lines.pop(0)

    def _next_id(self):
        self._rid += 1
        return str(self._rid)

    def _request(self, method, params, timeout=None):
        rid = self._next_id()
        msg = {"id": rid, "method": method, "params": params}
        if self._stdio:
            self.proc.stdin.write(json.dumps(msg) + "\n")
            self.proc.stdin.flush()
        else:
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
        try:
            self._request("tools.call", {"name": "lldb.listSessions", "arguments": {}}, timeout=10)
        except Exception:
            with self.lock:
                err = "\n".join(self.stderr_lines[-20:])
            raise RuntimeError("Server not responding; stderr:\n" + err)

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
        if self._stdio:
            try:
                self.proc.terminate()
            except Exception:
                pass
            try:
                self._t_out.join(timeout=1.0)
            except Exception:
                pass
            try:
                self._t_err.join(timeout=1.0)
            except Exception:
                pass
        else:
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

