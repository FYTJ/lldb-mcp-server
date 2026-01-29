"""Linux platform provider for LLDB environment setup.

This module provides Linux-specific logic for discovering LLDB Python bindings
across different distributions (Ubuntu, Fedora, Arch, etc.).
"""

from pathlib import Path
from typing import List, Optional

from .detector import PlatformDetector
from .provider import AbstractPlatformProvider


class LinuxProvider(AbstractPlatformProvider):
    """Linux platform provider for LLDB environment setup.

    Supports multiple Linux distributions with distribution-specific path discovery:
    - Ubuntu/Debian: /usr/lib/llvm-{version}/lib/python3.X/site-packages
    - Fedora/RHEL: /usr/lib64/llvm{version}/lib/python3.X/site-packages
    - Arch: /usr/lib/python3.X/site-packages
    """

    def __init__(self, config: Optional[object] = None):
        """Initialize Linux provider.

        Args:
            config: Optional Config object with user preferences.
        """
        super().__init__(config)
        self.distro, self.version = PlatformDetector.detect_linux_distro()
        self.arch = PlatformDetector.detect_architecture()

    def get_lldb_python_paths(self) -> List[str]:
        """Get LLDB Python paths for various Linux distributions.

        Returns:
            List of discovered LLDB Python binding paths, ordered by preference.
        """
        paths = []

        if self.distro in ["ubuntu", "debian"]:
            paths.extend(self._get_ubuntu_paths())
        elif self.distro in ["fedora", "centos"]:
            paths.extend(self._get_fedora_paths())
        elif self.distro == "arch":
            paths.extend(self._get_arch_paths())
        else:
            # Generic Linux fallbacks
            paths.extend(self._get_generic_linux_paths())

        return paths

    def _get_ubuntu_paths(self) -> List[str]:
        """Get Ubuntu/Debian-specific LLDB Python paths.

        Returns:
            List of Ubuntu/Debian LLDB paths.
        """
        paths = []

        # Ubuntu LLVM packages: llvm-20, llvm-19, llvm-18, etc.
        for version in [20, 19, 18, 17, 16, 15, 14]:
            for pyver in ["3.13", "3.12", "3.11", "3.10"]:
                # Standard apt installation (site-packages)
                path = f"/usr/lib/llvm-{version}/lib/python{pyver}/site-packages"
                if Path(path).exists():
                    paths.append(path)

                # Dist-packages (Debian convention)
                path = f"/usr/lib/llvm-{version}/lib/python{pyver}/dist-packages"
                if Path(path).exists():
                    paths.append(path)

        # Also check without specific Python version (for some installations)
        for version in [20, 19, 18, 17, 16, 15, 14]:
            base_path = f"/usr/lib/llvm-{version}/lib"
            if Path(base_path).exists():
                # Try to find any python* subdirectory
                import os
                try:
                    for item in os.listdir(base_path):
                        if item.startswith("python"):
                            site_pkg = Path(base_path) / item / "site-packages"
                            dist_pkg = Path(base_path) / item / "dist-packages"
                            if site_pkg.exists() and str(site_pkg) not in paths:
                                paths.append(str(site_pkg))
                            if dist_pkg.exists() and str(dist_pkg) not in paths:
                                paths.append(str(dist_pkg))
                except Exception:
                    pass

        return paths

    def _get_fedora_paths(self) -> List[str]:
        """Get Fedora/RHEL-specific LLDB Python paths.

        Returns:
            List of Fedora/RHEL LLDB paths.
        """
        paths = []

        # Fedora uses lib64 on x86_64
        lib_dir = "lib64" if self.arch == "x86_64" else "lib"

        for version in [20, 19, 18, 17, 16, 15, 14]:
            for pyver in ["3.13", "3.12", "3.11", "3.10"]:
                # Standard pattern: /usr/lib64/llvm{version}/lib/python3.X/site-packages
                path = f"/usr/{lib_dir}/llvm{version}/lib/python{pyver}/site-packages"
                if Path(path).exists():
                    paths.append(path)

                # Alternative pattern with slash
                path = f"/usr/{lib_dir}/llvm/{version}/lib/python{pyver}/site-packages"
                if Path(path).exists():
                    paths.append(path)

        return paths

    def _get_arch_paths(self) -> List[str]:
        """Get Arch Linux-specific LLDB Python paths.

        Returns:
            List of Arch Linux LLDB paths.
        """
        paths = []

        # Arch installs LLDB Python bindings in standard Python site-packages
        for pyver in ["3.13", "3.12", "3.11", "3.10"]:
            path = f"/usr/lib/python{pyver}/site-packages"
            if Path(path).exists():
                paths.append(path)

        return paths

    def _get_generic_linux_paths(self) -> List[str]:
        """Get generic Linux LLDB Python paths as fallback.

        Returns:
            List of common Linux LLDB paths.
        """
        paths = []

        # Check common base directories
        common_bases = [
            "/usr/local/lib",
            "/usr/lib",
            "/opt/llvm/lib",
        ]

        for base in common_bases:
            if not Path(base).exists():
                continue

            # Try to find llvm directories
            for version in range(20, 13, -1):
                for pyver in ["3.13", "3.12", "3.11", "3.10"]:
                    patterns = [
                        f"llvm-{version}/lib/python{pyver}/site-packages",
                        f"llvm{version}/lib/python{pyver}/site-packages",
                        f"python{pyver}/site-packages",
                    ]
                    for pattern in patterns:
                        path = Path(base) / pattern
                        if path.exists():
                            paths.append(str(path))

        return paths

    def get_framework_paths(self) -> List[str]:
        """Get LLDB library paths on Linux.

        Note: Linux doesn't use frameworks like macOS, but uses shared libraries (.so).

        Returns:
            List of library paths containing liblldb.so.
        """
        paths = []

        if self.distro in ["ubuntu", "debian"]:
            for version in [20, 19, 18, 17, 16, 15, 14]:
                lib_path = f"/usr/lib/llvm-{version}/lib"
                if Path(lib_path).exists():
                    paths.append(lib_path)
        elif self.distro in ["fedora", "centos"]:
            lib_dir = "lib64" if self.arch == "x86_64" else "lib"
            for version in [20, 19, 18, 17, 16, 15, 14]:
                lib_path = f"/usr/{lib_dir}/llvm{version}/lib"
                if Path(lib_path).exists():
                    paths.append(lib_path)

        # Common fallback paths
        for common in ["/usr/lib/x86_64-linux-gnu", "/usr/lib", "/usr/local/lib"]:
            if Path(common).exists():
                paths.append(common)

        return paths

    def get_library_path_env_name(self) -> str:
        """Get library path environment variable name for Linux.

        Returns:
            "LD_LIBRARY_PATH" for Linux dynamic linker.
        """
        return "LD_LIBRARY_PATH"

    def get_framework_path_env_name(self) -> Optional[str]:
        """Get framework path environment variable name for Linux.

        Returns:
            None (Linux doesn't use framework paths).
        """
        return None

    def preload_lldb_library(self, framework_paths: List[str]) -> bool:
        """Preload LLDB shared library using ctypes.

        Args:
            framework_paths: List of paths to search for liblldb.so.

        Returns:
            True if liblldb.so was successfully preloaded, False otherwise.
        """
        try:
            import ctypes

            # On Linux, LLDB is typically liblldb.so or liblldb.so.1
            for lib_path in framework_paths:
                for lib_name in ["liblldb.so", "liblldb.so.1", "liblldb.so.18", "liblldb.so.19"]:
                    lib = Path(lib_path) / lib_name
                    if lib.exists():
                        try:
                            ctypes.CDLL(str(lib))
                            return True
                        except Exception:
                            # Try next library if this one fails
                            continue
        except Exception:
            # ctypes import failed or other error
            pass

        return False

    def get_lldb_command_paths(self) -> List[str]:
        """Get paths to lldb executable on Linux.

        Returns:
            List of lldb command names and paths to try, including version-specific variants.
        """
        paths = ["lldb"]  # Try PATH first

        # Add version-specific paths for Ubuntu/Debian
        if self.distro in ["ubuntu", "debian"]:
            for version in [20, 19, 18, 17, 16, 15, 14]:
                paths.append(f"lldb-{version}")
                paths.append(f"/usr/lib/llvm-{version}/bin/lldb")
        # Add version-specific paths for Fedora/RHEL
        elif self.distro in ["fedora", "centos"]:
            for version in [20, 19, 18, 17, 16, 15, 14]:
                paths.append(f"lldb-{version}")

        return paths

    def get_install_instructions(self) -> str:
        """Get Linux distribution-specific installation instructions.

        Returns:
            Multi-line string with installation guidance based on detected distribution.
        """
        if self.distro == "ubuntu":
            return """
LLDB Python module not found. To fix this on Ubuntu:

1. Install LLDB (choose a version, 18 or newer recommended):
   sudo apt update
   sudo apt install lldb-18 python3-lldb-18

2. Alternatively, set LLDB_PYTHON_PATH environment variable:
   export LLDB_PYTHON_PATH="/usr/lib/llvm-18/lib/python3.12/site-packages"
   (Adjust the LLVM and Python versions as needed)

For more details, see: https://github.com/FYTJ/lldb-mcp-server#prerequisites
"""
        elif self.distro == "fedora":
            return """
LLDB Python module not found. To fix this on Fedora:

1. Install LLDB:
   sudo dnf install lldb lldb-devel python3-lldb

2. Alternatively, set LLDB_PYTHON_PATH environment variable:
   export LLDB_PYTHON_PATH="/usr/lib64/llvm/lib/python3.12/site-packages"
   (Adjust the Python version as needed)

For more details, see: https://github.com/FYTJ/lldb-mcp-server#prerequisites
"""
        elif self.distro == "arch":
            return """
LLDB Python module not found. To fix this on Arch Linux:

1. Install LLDB:
   sudo pacman -S lldb

2. The Python bindings should be in /usr/lib/python3.X/site-packages

For more details, see: https://github.com/FYTJ/lldb-mcp-server#prerequisites
"""
        else:
            return """
LLDB Python module not found. To fix this on Linux:

1. Install LLDB using your distribution's package manager
2. Set LLDB_PYTHON_PATH to point to the LLDB Python bindings

Example:
   export LLDB_PYTHON_PATH="/usr/lib/llvm-18/lib/python3.12/site-packages"

For more details, see: https://github.com/FYTJ/lldb-mcp-server#prerequisites
"""
