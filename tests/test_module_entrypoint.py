import os
import subprocess
import sys

import graver.__main__ as module_entrypoint


def run_module(*arguments: str, working_directory: str) -> subprocess.CompletedProcess:
    """Run the installed module entry point in an isolated child process."""
    environment = os.environ.copy()
    environment.pop("GRAVER_DB", None)
    return subprocess.run(
        [sys.executable, "-m", "graver", *arguments],
        cwd=working_directory,
        env=environment,
        capture_output=True,
        check=False,
        text=True,
    )


def test_module_entrypoint_reports_version(tmp_path):
    result = run_module("--version", working_directory=str(tmp_path))

    assert result.returncode == 0
    assert "graver v" in result.stdout
    assert result.stderr == ""


def test_main_delegates_to_command_application(monkeypatch):
    calls = []
    monkeypatch.setattr(module_entrypoint, "app", lambda: calls.append("called"))

    module_entrypoint.main()

    assert calls == ["called"]


def test_module_entrypoint_exposes_same_root_commands(tmp_path):
    result = run_module("--help", working_directory=str(tmp_path))

    assert result.returncode == 0
    assert all(command in result.stdout for command in ("init", "search", "work"))
    assert result.stderr == ""
