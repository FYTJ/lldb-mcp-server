"""Windows platform provider for LLDB environment setup.

This module provides Windows-specific logic for discovering LLDB Python bindings
from LLVM (Chocolatey installer) and Visual Studio LLVM toolsets.
"""

import os
from pathlib import Path
from typing import List, Optional

from .detector import PlatformDetector
from .provider import AbstractPlatformProvider


class WindowsProvider(AbstractPlatformProvider):
    """Windows platform provider for LLDB environment setup."""

    def __init__(self, config: Optional[object] = None):
        super().__init__(config)
        self.arch = PlatformDetector.detect_architecture()

    def get_lldb_python_paths(self) -> List[str]:
        paths: List[str] = []
        candidates: List[Path] = []

        pyvers = ["3.13", "3.12", "3.11", "3.10"]
        for root in self._candidate_llvm_roots():
            candidates.append(root / "lib" / "site-packages")
            for pyver in pyvers:
                candidates.append(root / "lib" / f"python{pyver}" / "site-packages")

        for p in candidates:
            if self._looks_like_lldb_python_path(p):
                paths.append(str(p))

        return self._dedupe_preserve_order(paths)

    def get_framework_paths(self) -> List[str]:
        paths: List[str] = []

        for root in self._candidate_llvm_roots():
            for p in [root / "bin", root / "lib"]:
                if p.exists():
                    paths.append(str(p))

        for py_path in self.get_lldb_python_paths():
            base = Path(py_path) / "lldb"
            for p in [base / "bin", base / "lib"]:
                if p.exists():
                    paths.append(str(p))

        for vs_bin in self._candidate_vs_lldb_bin_dirs():
            if vs_bin.exists():
                paths.append(str(vs_bin))

        return self._dedupe_preserve_order(paths)

    def get_library_path_env_name(self) -> str:
        return "PATH"

    def get_framework_path_env_name(self) -> Optional[str]:
        return None

    def preload_lldb_library(self, framework_paths: List[str]) -> bool:
        try:
            import ctypes
        except Exception:
            return False

        for fp in framework_paths:
            base = Path(fp)
            for lib_name in ["liblldb.dll", "lldb.dll"]:
                lib = base / lib_name
                if lib.exists():
                    try:
                        ctypes.CDLL(str(lib))
                        return True
                    except Exception:
                        continue

        for lib_name in ["liblldb.dll", "lldb.dll"]:
            try:
                ctypes.CDLL(lib_name)
                return True
            except Exception:
                continue

        return False

    def get_lldb_command_paths(self) -> List[str]:
        paths: List[str] = ["lldb.exe", "lldb"]

        for root in self._candidate_llvm_roots():
            lldb_exe = root / "bin" / "lldb.exe"
            if lldb_exe.exists():
                paths.append(str(lldb_exe))

        for vs_bin in self._candidate_vs_lldb_bin_dirs():
            lldb_exe = vs_bin / "lldb.exe"
            if lldb_exe.exists():
                paths.append(str(lldb_exe))

        return self._dedupe_preserve_order(paths)

    def get_install_instructions(self) -> str:
        return """
LLDB Python module not found. To fix this on Windows:

1. Install LLVM (includes LLDB) and Python using Chocolatey:
   choco install -y llvm python

2. Ensure LLVM is on PATH:
   - Restart your terminal after installation
   - Verify: lldb --version

3. Verify LLDB Python bindings:
   python -c "import lldb; print(lldb.__file__)"

4. If import still fails, set LLDB_PYTHON_PATH to your LLVM site-packages directory.
   Common location (Chocolatey LLVM):
   C:\\Program Files\\LLVM\\lib\\site-packages

If you use Visual Studio's LLVM toolset, ensure its bin directory is in PATH.
"""

    def _candidate_llvm_roots(self) -> List[Path]:
        roots: List[Path] = []

        for key in ["LLVM_ROOT", "LLVM_DIR", "LLVM_INSTALL_DIR"]:
            val = os.environ.get(key)
            if val:
                roots.append(Path(val))
                roots.append(Path(val) / "LLVM")

        for key in ["ProgramW6432", "ProgramFiles", "ProgramFiles(x86)"]:
            val = os.environ.get(key)
            if val:
                roots.append(Path(val) / "LLVM")

        roots.extend(
            [
                Path(r"C:\Program Files\LLVM"),
                Path(r"C:\LLVM"),
            ]
        )

        existing: List[Path] = []
        for r in roots:
            if r.exists():
                existing.append(r)
        return self._dedupe_preserve_order(existing)

    def _candidate_vs_lldb_bin_dirs(self) -> List[Path]:
        bins: List[Path] = []

        vs_install_dir = os.environ.get("VSINSTALLDIR")
        if vs_install_dir:
            bins.extend(self._llvm_bins_from_vs_root(Path(vs_install_dir)))

        pf = os.environ.get("ProgramFiles")
        if pf:
            vs_base = Path(pf) / "Microsoft Visual Studio"
            if vs_base.exists():
                for year in ["2022", "2019"]:
                    for edition in ["Community", "Professional", "Enterprise", "BuildTools"]:
                        candidate = vs_base / year / edition
                        bins.extend(self._llvm_bins_from_vs_root(candidate))

        return self._dedupe_preserve_order(bins)

    def _llvm_bins_from_vs_root(self, vs_root: Path) -> List[Path]:
        llvm_root = vs_root / "VC" / "Tools" / "Llvm"
        return [
            llvm_root / "bin",
            llvm_root / "x64" / "bin",
            llvm_root / self.arch / "bin",
        ]

    @staticmethod
    def _looks_like_lldb_python_path(path: Path) -> bool:
        if not path.exists():
            return False

        lldb_pkg = path / "lldb"
        if lldb_pkg.exists():
            return True

        for name in ["lldb.pyd", "_lldb.pyd", "lldb.py"]:
            if (path / name).exists():
                return True

        return False

    @staticmethod
    def _dedupe_preserve_order(items: List[str] | List[Path]) -> List:
        seen = set()
        out = []
        for x in items:
            key = str(x)
            if key in seen:
                continue
            seen.add(key)
            out.append(x)
        return out
