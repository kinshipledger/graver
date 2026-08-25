"""Tests for release-artifact verification helpers."""

from maintenance.release_smoke_test import versions_match


def test_release_versions_compare_as_pep_440_versions() -> None:
    """Accept the public and normalized spellings of the first release candidate."""
    assert versions_match("1.0.0rc1", "1.0.0-rc.1")
    assert not versions_match("1.0.0rc2", "1.0.0-rc.1")
