"""Abstract platform provider interface for LLDB environment setup.

This module defines the abstract base class that all platform-specific providers
must implement, as well as a factory function to get the appropriate provider.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class AbstractPlatformProvider(ABC):
    """Abstract base class for platform-specific LLDB environment setup.

    Each platform (macOS, Linux, Windows) implements this interface to provide
    platform-specific logic for discovering LLDB Python bindings, framework paths,
    and environment variable configuration.
    """

    def __init__(self, config: Optional[Any] = None):
        """Initialize provider with optional configuration object.

        Args:
            config: Optional Config object containing user preferences.
        """
        self.config = config

    @abstractmethod
    def get_lldb_python_paths(self) -> List[str]:
        """Get platform-specific paths to LLDB Python bindings.

        Returns:
            List of paths to check, in priority order. Each path should point to
            a directory containing the 'lldb' Python module (typically a site-packages
            directory).

        Examples:
            macOS: ["/opt/homebrew/opt/llvm/lib/python3.13/site-packages"]
            Linux: ["/usr/lib/llvm-18/lib/python3.12/site-packages"]
        """
        pass

    @abstractmethod
    def get_framework_paths(self) -> List[str]:
        """Get platform-specific LLDB framework/library paths.

        Returns:
            List of paths containing LLDB frameworks (macOS) or shared libraries (Linux).

        Examples:
            macOS: ["/opt/homebrew/opt/llvm/lib", "/Library/Developer/CommandLineTools/..."]
            Linux: ["/usr/lib/llvm-18/lib", "/usr/lib/x86_64-linux-gnu"]
        """
        pass

    @abstractmethod
    def get_library_path_env_name(self) -> str:
        """Get the environment variable name for library paths.

        Returns:
            "LD_LIBRARY_PATH" for Linux, "DYLD_LIBRARY_PATH" for macOS,
            "PATH" for Windows.
        """
        pass

    @abstractmethod
    def get_framework_path_env_name(self) -> Optional[str]:
        """Get the environment variable name for framework paths.

        Returns:
            "DYLD_FRAMEWORK_PATH" for macOS, None for Linux/Windows.
        """
        pass

    @abstractmethod
    def preload_lldb_library(self, framework_paths: List[str]) -> bool:
        """Attempt to preload LLDB library/framework using ctypes.

        This can help resolve dynamic linking issues on some systems.

        Args:
            framework_paths: List of paths to search for LLDB library.

        Returns:
            True if preloading succeeded, False otherwise.
        """
        pass

    @abstractmethod
    def get_lldb_command_paths(self) -> List[str]:
        """Get paths to check for lldb executable.

        Used for running 'lldb -P' command to discover Python paths.

        Returns:
            List of lldb command names or absolute paths to try.

        Examples:
            macOS: ["lldb"]
            Linux: ["lldb", "lldb-18", "/usr/lib/llvm-18/bin/lldb"]
        """
        pass

    def get_platform_specific_env(self) -> Dict[str, str]:
        """Get additional platform-specific environment variables.

        Returns:
            Dictionary of environment variable name -> value.
            Default implementation returns empty dict.
        """
        return {}


def get_provider(platform_type: str, config: Optional[Any] = None) -> AbstractPlatformProvider:
    """Factory method to get appropriate platform provider.

    Args:
        platform_type: One of "macos", "linux", "windows".
        config: Optional configuration object to pass to the provider.

    Returns:
        Appropriate provider instance for the platform.

    Raises:
        ValueError: If platform_type is unsupported or not yet implemented.

    Examples:
        >>> provider = get_provider("macos")
        >>> paths = provider.get_lldb_python_paths()
    """
    if platform_type == "macos":
        from .macos import MacOSProvider

        return MacOSProvider(config)
    elif platform_type == "linux":
        from .linux import LinuxProvider

        return LinuxProvider(config)
    elif platform_type == "windows":
        from .windows import WindowsProvider

        return WindowsProvider(config)
    else:
        raise ValueError(f"Unsupported platform: {platform_type}")
