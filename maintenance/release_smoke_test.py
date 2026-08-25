"""Smoke-test an installed graver release artifact outside its source tree."""

from __future__ import annotations

import subprocess
import sys
import tomllib
from importlib.metadata import version
from pathlib import Path
from shutil import which

import graver
import graver.application as application


def main() -> None:
    """Verify distribution metadata, imports, and both supported entry points."""
    if graver.__name__ != "graver":  # pragma: no cover - import itself is the check
        raise RuntimeError("graver import resolved to an unexpected module")
    installed_version = version("graver-genealogy")
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    if installed_version != project["project"]["version"]:
        raise RuntimeError("installed and project versions differ")
    if "open_workspace" not in application.__all__:
        raise RuntimeError("public application facade is incomplete")
    expected = f"graver v{installed_version}"
    console_entrypoint = which("graver")
    if console_entrypoint is None:
        raise RuntimeError("graver console entry point is unavailable")
    console_result = subprocess.run(  # noqa: S603 - resolved installed entry point
        [console_entrypoint, "--version"], check=True, capture_output=True, text=True
    )
    module_result = subprocess.run(
        [sys.executable, "-m", "graver", "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    if console_result.stdout.strip() != expected:
        raise RuntimeError("console entry point reports an unexpected version")
    if module_result.stdout.strip() != expected:
        raise RuntimeError("module entry point reports an unexpected version")


if __name__ == "__main__":
    main()
