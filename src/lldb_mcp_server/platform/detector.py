"""Platform detection for LLDB MCP Server.

This module provides utilities for detecting the current operating system,
Linux distribution, and architecture.
"""

import platform
from pathlib import Path
from typing import Literal, Optional, Tuple

PlatformType = Literal["macos", "linux", "windows", "unknown"]
LinuxDistro = Literal["ubuntu", "fedora", "arch", "debian", "centos", "unknown"]


class PlatformDetector:
    """Detects the current operating system and platform characteristics."""

    @staticmethod
    def detect_platform(config_override: Optional[str] = None) -> PlatformType:
        """Detect the current platform with optional config override.

        Args:
            config_override: Optional platform type to override auto-detection.
                           Must be one of: "macos", "linux", "windows".

        Returns:
            Detected or overridden platform type. Returns "unknown" if detection fails
            or if an invalid override is provided.
        """
        if config_override:
            if config_override in ["macos", "linux", "windows"]:
                return config_override  # type: ignore
            return "unknown"

        system = platform.system().lower()
        if system == "darwin":
            return "macos"
        elif system == "linux":
            return "linux"
        elif system == "windows":
            return "windows"
        return "unknown"

    @staticmethod
    def detect_linux_distro() -> Tuple[LinuxDistro, str]:
        """Detect Linux distribution and version.

        Returns:
            A tuple of (distribution_name, version_string).
            Returns ("unknown", "") if detection fails or not on Linux.

        Examples:
            >>> PlatformDetector.detect_linux_distro()
            ("ubuntu", "24.04")
        """
        try:
            # Try /etc/os-release first (modern standard)
            os_release_path = Path("/etc/os-release")
            if os_release_path.exists():
                with open(os_release_path) as f:
                    lines = f.readlines()
                    distro_id = None
                    version_id = None
                    for line in lines:
                        if line.startswith("ID="):
                            distro_id = line.split("=")[1].strip().strip('"')
                        elif line.startswith("VERSION_ID="):
                            version_id = line.split("=")[1].strip().strip('"')

                    if distro_id:
                        distro_map = {
                            "ubuntu": "ubuntu",
                            "fedora": "fedora",
                            "arch": "arch",
                            "debian": "debian",
                            "centos": "centos",
                            "rhel": "centos",  # Treat RHEL like CentOS for path discovery
                        }
                        detected_distro = distro_map.get(distro_id, "unknown")
                        return (detected_distro, version_id or "")  # type: ignore
        except Exception:
            pass

        # Fallback: check common release files
        try:
            if Path("/etc/ubuntu-release").exists() or Path("/etc/debian_version").exists():
                return ("ubuntu", "")
            elif Path("/etc/fedora-release").exists():
                return ("fedora", "")
        except Exception:
            pass

        return ("unknown", "")

    @staticmethod
    def detect_architecture() -> str:
        """Detect CPU architecture.

        Returns:
            Architecture string (e.g., "x86_64", "arm64", "aarch64", "i386").

        Examples:
            >>> PlatformDetector.detect_architecture()
            "arm64"
        """
        return platform.machine()
