import json
import os
import urllib.request
from pathlib import Path

from config import load_config


class MCPClient:
    def __init__(self, timeout=30, host=None, port=None):
        cfg = load_config()
        host = host or os.environ.get("MCP_HOST") or cfg.get("server_host") or "127.0.0.1"
        port = port or os.environ.get("MCP_PORT") or cfg.get("server_port") or 8765
        self.base_url = f"http://{host}:{int(port)}"
        self.timeout = int(timeout or (cfg.get("client") or {}).get("timeout", 30))
        self._health_check()

    def _post(self, path, payload=None):
        data = json.dumps(payload or {}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            raw = resp.read()
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def _health_check(self):
        try:
            self._post("/tools/list")
        except Exception as exc:
            raise RuntimeError(f"FastMCP server not reachable: {exc}")

    def tools_call(self, name, arguments, timeout=None):
        if timeout is not None:
            self.timeout = int(timeout)
        resp = self._post("/tools/call", {"name": name, "arguments": arguments})
        if isinstance(resp, dict) and "result" in resp:
            return resp.get("result")
        return resp

    def init_session(self):
        r = self.tools_call("lldb_initialize", {})
        return r.get("sessionId")

    def create_target(self, session_id, file, arch=None, triple=None, platform=None):
        return self.tools_call(
            "lldb_createTarget",
            {"sessionId": session_id, "file": file, "arch": arch, "triple": triple, "platform": platform},
        )

    def attach(self, session_id, pid=None, name=None):
        return self.tools_call("lldb_attach", {"sessionId": session_id, "pid": pid, "name": name})

    def launch(self, session_id, args=None, env=None, cwd=None, flags=None):
        return self.tools_call(
            "lldb_launch",
            {
                "sessionId": session_id,
                "args": args or [],
                "env": env or {},
                "cwd": cwd,
                "flags": flags or {},
            },
        )

    def command(self, session_id, command):
        return self.tools_call("lldb_command", {"sessionId": session_id, "command": command})

    def set_watchpoint(self, session_id, addr, size=4, read=True, write=True):
        return self.tools_call(
            "lldb_setWatchpoint",
            {"sessionId": session_id, "addr": int(addr), "size": int(size), "read": bool(read), "write": bool(write)},
        )

    def read_memory(self, session_id, addr, size):
        return self.tools_call("lldb_readMemory", {"sessionId": session_id, "addr": int(addr), "size": int(size)})

    def transcript_path(self, session_id):
        root = Path.cwd()
        cfg = load_config()
        log_dir = cfg.get("log_dir") or "logs"
        return str(root / log_dir / f"transcript_{session_id}.log")
