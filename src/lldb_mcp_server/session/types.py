from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class Session:
    session_id: str
    debugger: Any = None
    target: Any = None
    process: Any = None
    listener: Any = None
    event_thread: Any = None
    events: Any = None
    event_stop: Any = None
    last_launch_args: Any = None
    last_launch_env: Any = None
    last_launch_cwd: Any = None
    last_launch_flags: Any = None
    core_path: Optional[str] = None
    core_executable: Optional[str] = None
    core_pid: Optional[int] = None
    core_signal: Optional[str] = None
    is_core_session: bool = False
