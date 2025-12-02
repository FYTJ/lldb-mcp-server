import os
import json
from pathlib import Path
from typing import Optional


def find_config_path() -> Optional[Path]:
    env_p = os.environ.get("LLDB_MCP_CONFIG")
    if env_p:
        p = Path(env_p).expanduser().resolve()
        if p.exists():
            return p
    here = Path(__file__).resolve()
    for i in range(1, 5):
        try:
            candidate = here.parents[i] / "config.json"
            if candidate.exists():
                return candidate
        except Exception:
            break
    cwd_c = Path.cwd() / "config.json"
    return cwd_c if cwd_c.exists() else None


def load_config() -> dict:
    p = find_config_path()
    if not p:
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

