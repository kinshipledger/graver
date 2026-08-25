"""Documentation contract tests."""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPOSITORY_ROOT = Path(__file__).parents[1]
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def test_local_markdown_links_resolve() -> None:
    """Keep repository-local documentation references navigable."""
    documents = [
        REPOSITORY_ROOT / "README.md",
        REPOSITORY_ROOT / "CHANGELOG.md",
        REPOSITORY_ROOT / "CONTRIBUTING.md",
        REPOSITORY_ROOT / "SECURITY.md",
        *sorted((REPOSITORY_ROOT / "docs").rglob("*.md")),
    ]
    missing: list[str] = []

    for document in documents:
        for target in MARKDOWN_LINK.findall(document.read_text(encoding="utf-8")):
            target = target.strip("<>").split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            resolved = (document.parent / target).resolve()
            if not resolved.exists():
                missing.append(f"{document.relative_to(REPOSITORY_ROOT)} -> {target}")

    assert missing == [], "Missing local documentation links:\n" + "\n".join(missing)
