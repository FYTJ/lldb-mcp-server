import os
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List


def _find_config_path() -> Optional[Path]:
    env_p = os.environ.get("LLDB_MCP_CONFIG")
    if env_p:
        p = Path(env_p).expanduser().resolve()
        if p.exists():
            return p
    here = Path(__file__).resolve()
    for i in range(1, 6):
        try:
            candidate = here.parents[i] / "config.json"
            if candidate.exists():
                return candidate
        except Exception:
            break
    cwd_c = Path.cwd() / "config.json"
    return cwd_c if cwd_c.exists() else None


def _load_config_json() -> dict:
    p = _find_config_path()
    if not p:
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


@dataclass
class Config:
    allow_launch: bool = os.environ.get("LLDB_MCP_ALLOW_LAUNCH", "0") == "1"
    allow_attach: bool = os.environ.get("LLDB_MCP_ALLOW_ATTACH", "0") == "1"
    allowed_root: Optional[str] = os.environ.get("LLDB_MCP_ALLOWED_ROOT")
    log_dir: str = "logs"
    server_host: str = "127.0.0.1"
    server_port: int = 8765
    preferred_python_executable: Optional[str] = None
    lldb_python_paths: Optional[List[str]] = None
    lldb_framework_paths: Optional[List[str]] = None
    project_root: Optional[str] = None
    src_path: Optional[str] = None


_raw = _load_config_json()

from typing import List as _ListType
def _get_nested(d: dict, path: _ListType[str], default=None):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


config = Config()
config.allowed_root = _raw.get("allowed_root") or config.allowed_root
config.log_dir = _raw.get("log_dir") or config.log_dir
config.server_host = _raw.get("server_host") or config.server_host
try:
    config.server_port = int(_raw.get("server_port") or config.server_port)
except Exception:
    pass
config.preferred_python_executable = _get_nested(_raw, ["lldb", "python_executable"], None)
ppaths = _get_nested(_raw, ["lldb", "python_paths"], []) or []
fpaths = _get_nested(_raw, ["lldb", "framework_paths"], []) or []
config.lldb_python_paths = list(ppaths)
config.lldb_framework_paths = list(fpaths)
config.project_root = _raw.get("project_root") or config.project_root
config.src_path = _raw.get("src_path") or config.src_path
