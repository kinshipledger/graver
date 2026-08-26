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


def test_canonical_documents_are_linked_from_the_documentation_index() -> None:
    """Keep every top-level canonical document discoverable from the docs index."""
    index = (REPOSITORY_ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    unlisted = [
        document.name
        for document in sorted((REPOSITORY_ROOT / "docs").glob("*.md"))
        if document.name != "README.md" and document.name not in index
    ]

    assert (
        unlisted == []
    ), "Canonical documents missing from docs/README.md: " + ", ".join(unlisted)


def test_first_time_setup_is_researcher_facing_and_bounded() -> None:
    """Keep first-run guidance useful without leaking contributor setup into it."""
    guide = (REPOSITORY_ROOT / "docs" / "first-time-setup.md").read_text(
        encoding="utf-8"
    )

    for required in (
        "**Terminal**",
        "**uv**",
        "**Command path**",
        "**Local database**",
        "What installation changes",
        "Installation does **not**",
        "contains the research work",
        "graver use --show",
    ):
        assert required in guide

    for contributor_only in ("git clone", "uv sync", "pytest", "make lint"):
        assert contributor_only not in guide
