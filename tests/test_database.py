import json
import os
import sqlite3
from pathlib import Path

import pytest

from graver import Memorial
from graver import config as graver_config
from graver import database as graver_database


CURRENT_TABLES = {
    "cemeteries",
    "graves",
    "memorial_alias_observations",
    "memorial_aliases",
    "memorial_observations",
    "research_tasks",
}


def test_create_database_builds_complete_current_schema(tmp_path):
    path = graver_database.create_database(str(tmp_path / "research.db"))

    assert path == (tmp_path / "research.db").resolve()
    assert graver_config.validate_graver_database(str(path)) == path
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        objects = connection.execute(
            "SELECT type, name FROM sqlite_master " "WHERE name NOT LIKE 'sqlite_%'"
        ).fetchall()
        tables = {name for kind, name in objects if kind == "table"}
        indexes = {name for kind, name in objects if kind == "index"}
        triggers = {name for kind, name in objects if kind == "trigger"}

        assert tables == CURRENT_TABLES
        assert {
            "idx_graves_cemetery_id",
            "idx_research_tasks_status_priority",
            "idx_memorial_alias_observations_source",
        } <= indexes
        assert {
            "memorial_observations_no_update",
            "memorial_observations_no_delete",
            "memorial_alias_observations_no_update",
            "memorial_alias_observations_no_delete",
        } == triggers
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO research_tasks "
                "(memorial_id, created_at, updated_at, last_activity_at) "
                "VALUES (999, 'now', 'now', 'now')"
            )


def test_create_database_requires_existing_parent(tmp_path):
    path = tmp_path / "missing" / "research.db"

    with pytest.raises(
        graver_database.DatabaseInitializationError,
        match="Parent directory does not exist",
    ):
        graver_database.create_database(str(path))

    assert not path.exists()
    assert not path.parent.exists()


@pytest.mark.parametrize(
    "kind", ["graver", "empty", "text", "binary", "sqlite", "directory", "symlink"]
)
def test_create_database_refuses_every_existing_path(tmp_path, kind):
    path = tmp_path / "research.db"
    if kind == "graver":
        Memorial.create_table(str(path))
    elif kind == "empty":
        path.touch()
    elif kind == "text":
        path.write_text("research notes")
    elif kind == "binary":
        path.write_bytes(b"\x00\x01\xff")
    elif kind == "sqlite":
        with sqlite3.connect(path) as connection:
            connection.execute("CREATE TABLE unrelated (value TEXT)")
    elif kind == "directory":
        path.mkdir()
    else:
        path.symlink_to(tmp_path / "missing-target.db")

    original_stat = path.lstat()
    original_bytes = (
        path.read_bytes() if path.is_file() and not path.is_symlink() else None
    )
    original_link = os.readlink(path) if path.is_symlink() else None

    with pytest.raises(
        graver_database.DatabaseInitializationError,
        match="Refusing to overwrite existing path",
    ) as error:
        graver_database.create_database(str(path))

    assert str(path.resolve(strict=False)) in str(error.value) or str(path) in str(
        error.value
    )
    assert path.lstat().st_ino == original_stat.st_ino
    if original_bytes is not None:
        assert path.read_bytes() == original_bytes
    if original_link is not None:
        assert os.readlink(path) == original_link


def test_create_database_reports_operating_system_creation_error(tmp_path, monkeypatch):
    path = tmp_path / "research.db"

    def deny_creation(*_args, **_kwargs):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(graver_database.os, "open", deny_creation)

    with pytest.raises(
        graver_database.DatabaseInitializationError, match="Permission denied"
    ) as error:
        graver_database.create_database(str(path))

    assert str(path) in str(error.value)
    assert not path.exists()


def test_schema_failure_removes_only_new_partial_file(tmp_path, monkeypatch):
    path = tmp_path / "research.db"
    neighbor = tmp_path / "keep.txt"
    neighbor.write_text("keep")

    def fail_schema(_connection):
        raise sqlite3.OperationalError("simulated schema failure")

    monkeypatch.setattr(graver_database, "_create_current_schema", fail_schema)

    with pytest.raises(
        graver_database.DatabaseInitializationError,
        match="simulated schema failure",
    ):
        graver_database.create_database(str(path))

    assert not path.exists()
    assert neighbor.read_text() == "keep"


def test_validation_failure_removes_only_new_partial_file(tmp_path, monkeypatch):
    path = tmp_path / "research.db"

    def fail_validation(_database):
        raise graver_config.GraverConfigurationError("simulated validation failure")

    monkeypatch.setattr(graver_database, "_validate_graver_database", fail_validation)

    with pytest.raises(
        graver_database.DatabaseInitializationError,
        match="simulated validation failure",
    ):
        graver_database.create_database(str(path))

    assert not path.exists()


def test_cli_init_default_creates_and_selects_absolute_path(
    helpers, tmp_path, monkeypatch, isolate_graver_configuration
):
    monkeypatch.chdir(tmp_path)
    isolate_graver_configuration.parent.mkdir(parents=True)
    isolate_graver_configuration.write_text(json.dumps({"theme": "plain"}))

    result = helpers.graver_cli("init")

    expected = (tmp_path / "graves.db").resolve()
    assert result.exit_code == 0
    assert result.output == (
        f"Initialized and selected research database: {expected}\n"
    )
    saved = json.loads(isolate_graver_configuration.read_text())
    assert saved == {"theme": "plain", "default_database": str(expected)}
    assert graver_config.validate_graver_database(str(expected)) == expected


def test_cli_init_named_relative_path_survives_directory_change(
    helpers, tmp_path, monkeypatch
):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    monkeypatch.chdir(first)

    initialized = helpers.graver_cli("init research.db")
    monkeypatch.chdir(second)
    monkeypatch.delenv("GRAVER_DB")
    shown = helpers.graver_cli("use --show")

    expected = (first / "research.db").resolve()
    assert initialized.exit_code == shown.exit_code == 0
    assert str(expected) in initialized.output
    assert str(expected) in shown.output


def test_cli_init_expands_tilde(helpers, tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    result = helpers.graver_cli("init ~/research.db")

    assert result.exit_code == 0
    assert str((home / "research.db").resolve()) in result.output


def test_cli_initialization_failure_preserves_saved_selection(
    helpers, tmp_path, monkeypatch, isolate_graver_configuration
):
    previous = tmp_path / "previous.db"
    Memorial.create_table(str(previous))
    graver_config.select_default_database(str(previous))
    target = tmp_path / "new.db"

    def fail_schema(_connection):
        raise sqlite3.OperationalError("simulated schema failure")

    monkeypatch.setattr(graver_database, "_create_current_schema", fail_schema)

    result = helpers.graver_cli(f"init '{target}'")

    assert result.exit_code == 1
    assert "simulated schema failure" in result.output
    assert "Traceback" not in result.output
    assert not target.exists()
    saved = json.loads(isolate_graver_configuration.read_text())
    assert saved["default_database"] == str(previous.resolve())


def test_cli_preference_failure_keeps_database_and_previous_selection(
    helpers, tmp_path, monkeypatch, isolate_graver_configuration
):
    previous = tmp_path / "previous.db"
    Memorial.create_table(str(previous))
    graver_config.select_default_database(str(previous))
    target = tmp_path / "new.db"

    def fail_preference(*_args, **_kwargs):
        raise graver_config.GraverConfigurationError("simulated preference failure")

    monkeypatch.setattr(
        "graver.cli.graver_config.select_default_database", fail_preference
    )

    result = helpers.graver_cli(f"init '{target}'")

    assert result.exit_code == 1
    assert "Database was initialized" in result.output
    assert "could not be selected" in result.output
    assert "Initialized and selected research database" not in result.output
    assert "Traceback" not in result.output
    assert graver_config.validate_graver_database(str(target)) == target.resolve()
    saved = json.loads(isolate_graver_configuration.read_text())
    assert saved["default_database"] == str(previous.resolve())


def test_init_help_has_no_side_effects_and_describes_default(
    helpers, tmp_path, monkeypatch, isolate_graver_configuration
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "graver.cli.create_database",
        lambda *_args, **_kwargs: pytest.fail("initialization invoked during help"),
    )

    root = helpers.graver_cli("--help")
    command = helpers.graver_cli("init --help")
    rendered = " ".join(command.output.split())

    assert root.exit_code == command.exit_code == 0
    assert "init" in root.output
    assert "Create and select a new database" in rendered
    assert "omit DATABASE to create ./graves.db" in rendered
    assert not (tmp_path / "graves.db").exists()
    assert not isolate_graver_configuration.exists()


def test_cli_init_is_network_free(helpers, tmp_path, monkeypatch):
    monkeypatch.setattr(
        Memorial,
        "parse",
        lambda *_args, **_kwargs: pytest.fail("network acquisition path invoked"),
    )

    result = helpers.graver_cli(f"init '{tmp_path / 'research.db'}'")

    assert result.exit_code == 0
