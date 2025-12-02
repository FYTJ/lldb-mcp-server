import threading
from collections import deque
from dataclasses import dataclass
from typing import Any
import threading

@dataclass
class Session:
    session_id: str
    debugger: Any = None
    target: Any = None
    process: Any = None
    listener: Any = None
    event_thread: Any = None
    events: Any = None
    last_launch_args: Any = None
    last_launch_env: Any = None
    last_launch_cwd: Any = None
    last_launch_flags: Any = None
