"""Validate documentation scope and run the pinned Vale policy."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = ROOT / "docs" / "documentation-scope.json"
PASS_FIXTURE = "maintenance/vale-fixtures/pass.md"
FAIL_FIXTURE = "maintenance/vale-fixtures/fail.md"
VALE_REPOSITORY = "https://github.com/vale-cli/vale"
VALE_RELEASE = "3.22.0"
VALE_REVISION = "e109c06297dc58a513f10691a275f3a9465584a1"
EXPECTED_FAILURE_RULES = {"Graver.Headings", "Graver.Terms"}


def run(*args: str, expect_success: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a repository command and return its captured result."""
    result = subprocess.run(
        args,
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if expect_success and result.returncode != 0:
        print(result.stdout, end="")
        raise SystemExit(result.returncode)
    return result


def load_scope() -> tuple[list[str], list[str]]:
    """Return all inventoried and enforced Markdown paths after validation."""
    data: dict[str, dict[str, Any]] = json.loads(SCOPE_PATH.read_text())
    inventoried: list[str] = []
    enforced: list[str] = []
    for category, details in data.items():
        files = details.get("files")
        if not isinstance(files, list) or not all(
            isinstance(item, str) for item in files
        ):
            raise SystemExit(f"{category}: files must be a list of paths")
        if not details.get("enforced") and not details.get("review_trigger"):
            raise SystemExit(
                f"{category}: excluded categories require a review_trigger"
            )
        inventoried.extend(files)
        if details.get("enforced"):
            enforced.extend(files)

    duplicates = sorted({path for path in inventoried if inventoried.count(path) > 1})
    if duplicates:
        raise SystemExit(
            f"Duplicate documentation-scope entries: {', '.join(duplicates)}"
        )

    tracked_result = run(
        "git", "ls-files", "--cached", "--others", "--exclude-standard", "--", "*.md"
    )
    tracked = sorted(line for line in tracked_result.stdout.splitlines() if line)
    inventoried_sorted = sorted(inventoried)
    missing = sorted(set(tracked) - set(inventoried_sorted))
    stale = sorted(set(inventoried_sorted) - set(tracked))
    if missing or stale:
        if missing:
            print("Unclassified tracked Markdown (fully enforced until classified):")
            for path in missing:
                print(f"  {path}")
        if stale:
            print("Stale documentation-scope entries:")
            for path in stale:
                print(f"  {path}")
        raise SystemExit(1)
    return inventoried_sorted, sorted(enforced)


def run_hook(
    alias: str,
    *files: str,
    hook_stage: str | None = None,
    verbose: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run one pre-commit hook against explicit files."""
    args = [
        sys.executable,
        "-m",
        "pre_commit",
        "run",
        alias,
        "--files",
        *files,
    ]
    if hook_stage is not None:
        args.extend(["--hook-stage", hook_stage])
    if verbose:
        args.append("--verbose")
    return run(*args, expect_success=False)


def check_vale_pin() -> None:
    """Verify the official hook source pin and its built executable."""
    config = (ROOT / ".pre-commit-config.yaml").read_text()
    expected_pin = re.compile(
        rf"(?m)^\s*- repo: {re.escape(VALE_REPOSITORY)}\s*$\n"
        rf"^\s+rev: {VALE_REVISION}\s*$"
    )
    if not expected_pin.search(config):
        raise SystemExit(
            f"Vale {VALE_RELEASE} must remain pinned to official revision "
            f"{VALE_REVISION}."
        )

    result = run_hook("vale-version", PASS_FIXTURE, hook_stage="manual", verbose=True)
    if result.returncode != 0 or not re.search(
        r"(?m)^vale version \S+\s*$", result.stdout
    ):
        print(result.stdout, end="")
        raise SystemExit("Pinned Vale executable did not return a version response.")


def check_fixtures() -> None:
    """Prove legitimate examples pass and violations exercise every rule."""
    passing = run_hook("vale-fixture", PASS_FIXTURE, hook_stage="manual")
    if passing.returncode != 0:
        print(passing.stdout, end="")
        raise SystemExit("Vale positive fixture failed.")

    failing = run_hook("vale-fixture", FAIL_FIXTURE, hook_stage="manual")
    observed = {rule for rule in EXPECTED_FAILURE_RULES if rule in failing.stdout}
    if failing.returncode == 0 or observed != EXPECTED_FAILURE_RULES:
        print(failing.stdout, end="")
        missing = ", ".join(sorted(EXPECTED_FAILURE_RULES - observed))
        raise SystemExit(f"Vale negative fixture did not exercise: {missing}")


def main() -> None:
    """Run fail-closed scope, version, fixture, and corpus checks."""
    _, enforced = load_scope()
    if "--scope-only" in sys.argv[1:]:
        print("Documentation scope inventory is complete and unique.")
        return
    check_vale_pin()
    check_fixtures()
    corpus = run_hook("vale", *enforced, hook_stage="manual")
    if corpus.returncode != 0:
        print(corpus.stdout, end="")
        raise SystemExit("Vale documentation corpus check failed.")
    print(f"Documentation style passed for {len(enforced)} enforced Markdown files.")


if __name__ == "__main__":
    main()
