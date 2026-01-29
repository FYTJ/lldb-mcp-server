"""macOS platform provider for LLDB environment setup.

This module provides macOS-specific logic for discovering LLDB Python bindings
from Homebrew LLVM and Xcode Command Line Tools.
"""

import subprocess
from pathlib import Path
from typing import List, Optional

from .detector import PlatformDetector
from .provider import AbstractPlatformProvider


class MacOSProvider(AbstractPlatformProvider):
    """macOS platform provider for LLDB environment setup.

    Supports both Intel and Apple Silicon Macs, with automatic detection of:
    - Homebrew LLVM installations
    - Xcode Command Line Tools
    - LLDB.framework locations
    """

    def __init__(self, config: Optional[object] = None):
        """Initialize macOS provider.

        Args:
            config: Optional Config object with user preferences.
        """
        super().__init__(config)
        self.arch = PlatformDetector.detect_architecture()
        self.is_apple_silicon = self.arch in ["arm64", "aarch64"]

    def get_lldb_python_paths(self) -> List[str]:
        """Get Homebrew LLVM Python paths for macOS.

        Checks both Intel and Apple Silicon Homebrew locations, trying
        multiple Python versions (3.13, 3.12, 3.11, 3.10) for each.

        Returns:
            List of discovered LLDB Python binding paths, ordered by preference.
        """
        paths = []

        # Check both Intel and Apple Silicon Homebrew locations
        bases = [
            "/usr/local/opt/llvm/lib",  # Intel Mac
            "/opt/homebrew/opt/llvm/lib",  # Apple Silicon Mac
        ]

        for base in bases:
            if Path(base).exists():
                # Try common Python versions (newest first)
                for pyver in ["3.13", "3.12", "3.11", "3.10"]:
                    lldb_path = f"{base}/python{pyver}/site-packages"
                    if Path(lldb_path).exists():
                        paths.append(lldb_path)

        return paths

    def get_framework_paths(self) -> List[str]:
        """Get LLDB framework paths from Homebrew and Xcode.

        Returns:
            List of framework paths including:
            - Homebrew LLVM lib directories
            - Xcode SharedFrameworks
            - Xcode PrivateFrameworks
        """
        paths = []

        # Homebrew LLVM frameworks
        for base in ["/usr/local/opt/llvm/lib", "/opt/homebrew/opt/llvm/lib"]:
            if Path(base).exists():
                paths.append(base)

        # Xcode Command Line Tools frameworks
        try:
            devroot = subprocess.check_output(
                ["xcode-select", "-p"], text=True, stderr=subprocess.DEVNULL
            ).strip()
            if devroot:
                shared = str(Path(devroot) / "../SharedFrameworks")
                private = str(Path(devroot) / "Library" / "PrivateFrameworks")
                if Path(shared).exists():
                    paths.append(shared)
                if Path(private).exists():
                    paths.append(private)
        except Exception:
            # xcode-select may not be available or may fail
            pass

        return paths

    def get_library_path_env_name(self) -> str:
        """Get library path environment variable name for macOS.

        Returns:
            "DYLD_LIBRARY_PATH" for macOS dynamic linker.
        """
        return "DYLD_LIBRARY_PATH"

    def get_framework_path_env_name(self) -> Optional[str]:
        """Get framework path environment variable name for macOS.

        Returns:
            "DYLD_FRAMEWORK_PATH" for macOS framework paths.
        """
        return "DYLD_FRAMEWORK_PATH"

    def preload_lldb_library(self, framework_paths: List[str]) -> bool:
        """Preload LLDB.framework using ctypes.

        Args:
            framework_paths: List of paths to search for LLDB.framework.

        Returns:
            True if LLDB.framework was successfully preloaded, False otherwise.
        """
        try:
            import ctypes

            for fp in framework_paths:
                lib = Path(fp) / "LLDB.framework" / "LLDB"
                if lib.exists():
                    try:
                        ctypes.CDLL(str(lib))
                        return True
                    except Exception:
                        # Try next path if this one fails
                        continue
        except Exception:
            # ctypes import failed or other error
            pass

        return False

    def get_lldb_command_paths(self) -> List[str]:
        """Get paths to lldb executable on macOS.

        Returns:
            List containing "lldb" (assumes it's in PATH from Xcode or Homebrew).
        """
        return ["lldb"]

    def get_install_instructions(self) -> str:
        """Get macOS-specific installation instructions.

        Returns:
            Multi-line string with installation guidance for macOS users.
        """
        return """
LLDB Python module not found. To fix this on macOS:

1. Install Homebrew LLVM:
   brew install llvm

2. Add LLVM to your PATH (add to ~/.zshrc):
   export PATH="$(brew --prefix llvm)/bin:$PATH"

3. Alternatively, set LLDB_PYTHON_PATH environment variable:
   export LLDB_PYTHON_PATH="/opt/homebrew/opt/llvm/lib/python3.13/site-packages"
   (Adjust the Python version and architecture as needed)

For more details, see: https://github.com/FYTJ/lldb-mcp-server#prerequisites
"""
