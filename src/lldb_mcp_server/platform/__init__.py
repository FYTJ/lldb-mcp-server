"""Platform abstraction for LLDB environment setup.

This package provides platform-specific implementations for discovering and configuring
LLDB Python bindings across different operating systems (macOS, Linux, Windows).
"""

from .detector import PlatformDetector
from .provider import AbstractPlatformProvider, get_provider

__all__ = ["PlatformDetector", "AbstractPlatformProvider", "get_provider"]
