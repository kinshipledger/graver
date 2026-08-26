import hashlib
import json
import os
import sqlite3
import uuid
from pathlib import Path

import pytest
from click import unstyle

from graver import api as graver_api
from graver import config as graver_config
from graver import database as graver_database
from graver._sqlite import connect_database
from graver.api import Memorial

CURRENT_TABLES = {
    "cemeteries",
    "graves",
    "memorial_alias_observations",
    "memorial_aliases",
    "memorial_observations",
    "research_tasks",
    "research_subjects",
    "subject_memorials",
    "research_subject_events",
    "research_task_events",
    "candidate_discovery_runs",
    "external_candidates",
    "candidate_snapshots",
    "comparison_signals",
    "candidate_assessments",
    "candidate_assessment_events",
    "identity_conclusions",
    "research_source_observations",
    "graver_schema",
}


def normalized_cli_output(output: str) -> str:
    """Remove terminal styling/layout and collapse presentation whitespace."""
    without_layout = unstyle(output).translate(
        str.maketrans({character: " " for character in "│─╭╮╰╯"})
    )
    return " ".join(without_layout.split())


def test_create_database_builds_complete_current_schema(tmp_path):
    path = graver_database.create_database(str(tmp_path / "research.db"))

    assert path == (tmp_path / "research.db").resolve()
    assert graver_config.validate_graver_database(str(path)) == path
    with connect_database(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        objects = connection.execute(
            "SELECT type, name FROM sqlite_master " "WHERE name NOT LIKE 'sqlite_%'"
        ).fetchall()
        tables = {name for kind, name in objects if kind == "table"}
        indexes = {name for kind, name in objects if kind == "index"}
        triggers = {name for kind, name in objects if kind == "trigger"}

        assert tables == CURRENT_TABLES
        assert connection.execute("SELECT version FROM graver_schema").fetchone() == (
            graver_database.CURRENT_SCHEMA_VERSION,
        )
        assert {
            "idx_graves_cemetery_id",
            "idx_research_tasks_status_priority",
            "idx_memorial_alias_observations_source",
            "idx_subject_memorials_subject",
            "idx_research_subject_events_subject",
            "idx_research_task_events_subject",
            "idx_discovery_runs_subject",
            "idx_candidates_subject",
            "idx_candidate_snapshots_candidate",
            "idx_comparison_signals_candidate",
            "idx_assessment_events_candidate",
            "idx_conclusions_candidate",
            "idx_source_observations_subject",
        } <= indexes
        assert {
            "memorial_observations_no_update",
            "memorial_observations_no_delete",
            "memorial_alias_observations_no_update",
            "memorial_alias_observations_no_delete",
            "research_subject_events_no_update",
            "research_subject_events_no_delete",
            "research_task_events_no_update",
            "research_task_events_no_delete",
            "candidate_discovery_runs_no_update",
            "candidate_discovery_runs_no_delete",
            "external_candidates_no_update",
            "external_candidates_no_delete",
            "candidate_snapshots_no_update",
            "candidate_snapshots_no_delete",
            "comparison_signals_no_update",
            "comparison_signals_no_delete",
            "candidate_assessment_events_no_update",
            "candidate_assessment_events_no_delete",
            "identity_conclusions_no_update",
            "identity_conclusions_no_delete",
            "research_source_observations_no_update",
            "research_source_observations_no_delete",
        } == triggers
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO research_tasks "
                "(subject_id, created_at, updated_at, last_activity_at) "
                "VALUES ('00000000-0000-4000-8000-000000000000', "
                "'now', 'now', 'now')"
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
        with connect_database(path) as connection:
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
        raise graver_database.DatabaseInspectionError("simulated validation failure")

    monkeypatch.setattr(graver_database, "validate_current_database", fail_validation)

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
    monkeypatch.setenv("USERPROFILE", str(home))

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
    assert "Offline: create and select a new database" in rendered
    assert "without overwriting any path" in rendered
    assert "New research database to create" in rendered
    assert "./graves.db" in rendered
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


def make_legacy_database(path: Path, full: bool = False) -> Path:
    extra = (
        ", original_name TEXT, birth_place TEXT, death_place TEXT, has_bio BOOL"
        if full
        else ""
    )
    with connect_database(path) as connection:
        connection.execute(
            "CREATE TABLE graves (memorial_id INTEGER PRIMARY KEY, "
            "findagrave_url TEXT, name TEXT, birth TEXT, death TEXT, "
            f"legacy_note TEXT{extra})"
        )
        connection.executemany(
            "INSERT INTO graves (memorial_id, name, legacy_note) VALUES (?, ?, ?)",
            [(11, "First Person", "keep one"), (22, "Second Person", "keep two")],
        )
    return path


def make_version_1_database(path: Path, metadata: bool = True) -> Path:
    with connect_database(path) as connection:
        graver_api._create_graves_table(connection)
        graver_api._create_cemeteries_table(connection)
        graver_api._create_research_schema(connection, task_schema_version=1)
        if metadata:
            graver_database._record_schema_version(connection, 1)
    return path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize(
    ("kind", "state"),
    [
        ("summary", "legacy_summary"),
        ("full", "legacy_0_1"),
        ("current_unversioned", "current_unversioned"),
        ("version_1_unversioned", "current_unversioned"),
        ("version_1", "outdated"),
        ("current", "current"),
        ("empty", "empty"),
        ("unrelated", "non_graver"),
        ("unknown", "unknown"),
        ("newer", "newer"),
    ],
)
def test_read_only_schema_inspection_classifies_supported_shapes(tmp_path, kind, state):
    path = tmp_path / f"{kind}.db"
    if kind in {"summary", "full"}:
        make_legacy_database(path, full=kind == "full")
    elif kind == "current_unversioned":
        with connect_database(path) as connection:
            graver_database._create_current_schema(connection)
    elif kind in {"version_1", "version_1_unversioned"}:
        make_version_1_database(path, metadata=kind == "version_1")
    elif kind in {"current", "newer"}:
        graver_database.create_database(str(path))
        if kind == "newer":
            with connect_database(path) as connection:
                connection.execute(
                    "UPDATE graver_schema SET version = ?",
                    (graver_database.CURRENT_SCHEMA_VERSION + 1,),
                )
    elif kind == "empty":
        with connect_database(path):
            pass
    elif kind == "unrelated":
        with connect_database(path) as connection:
            connection.execute("CREATE TABLE notes (value TEXT)")
    else:
        with connect_database(path) as connection:
            connection.execute("CREATE TABLE graves (memorial_id INTEGER PRIMARY KEY)")
    before = digest(path)
    before_mtime = path.stat().st_mtime_ns

    inspection = graver_database.inspect_database(str(path))

    assert inspection.state == state
    assert digest(path) == before
    assert path.stat().st_mtime_ns == before_mtime


@pytest.mark.parametrize("kind", ["missing", "directory", "symlink", "malformed"])
def test_inspection_rejects_unsafe_inputs(tmp_path, kind):
    path = tmp_path / "research.db"
    if kind == "directory":
        path.mkdir()
    elif kind == "symlink":
        path.symlink_to(tmp_path / "target.db")
    elif kind == "malformed":
        path.write_text("not sqlite")
    with pytest.raises(graver_database.DatabaseInspectionError):
        graver_database.inspect_database(str(path))


def test_upgrade_current_database_is_noop_without_backup(tmp_path):
    path = graver_database.create_database(str(tmp_path / "research.db"))
    before = digest(path)

    result = graver_database.upgrade_database(str(path))

    assert result.changed is False
    assert result.backup_path is None
    assert digest(path) == before
    assert not graver_database.backup_path_for(path).exists()


@pytest.mark.parametrize("full", [False, True])
def test_upgrade_legacy_preserves_rows_values_and_creates_verified_backup(
    tmp_path, full
):
    path = make_legacy_database(tmp_path / "legacy.db", full=full)
    result = graver_database.upgrade_database(str(path))

    assert result.changed is True
    assert result.backup_path is not None
    assert graver_database.inspect_database(str(path)).current
    with connect_database(path) as connection:
        assert connection.execute(
            "SELECT memorial_id, name, legacy_note FROM graves ORDER BY memorial_id"
        ).fetchall() == [
            (11, "First Person", "keep one"),
            (22, "Second Person", "keep two"),
        ]
        assert connection.execute(
            "SELECT COUNT(detail_level), COUNT(summary_fetched_at), "
            "COUNT(full_fetched_at) FROM graves"
        ).fetchone() == (0, 0, 0)
        assert connection.execute(
            "SELECT COUNT(*) FROM memorial_observations"
        ).fetchone() == (0,)
        assert connection.execute(
            "SELECT COUNT(*) FROM memorial_aliases"
        ).fetchone() == (0,)
        assert connection.execute(
            "SELECT COUNT(*) FROM research_subjects"
        ).fetchone() == (2,)
        assert connection.execute(
            "SELECT COUNT(*) FROM subject_memorials"
        ).fetchone() == (2,)
        assert connection.execute("SELECT COUNT(*) FROM research_tasks").fetchone() == (
            0,
        )
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    assert graver_database.inspect_database(str(result.backup_path)).state == (
        "legacy_0_1" if full else "legacy_summary"
    )
    with connect_database(result.backup_path) as backup_connection:
        assert backup_connection.execute(
            "SELECT memorial_id, name, legacy_note FROM graves ORDER BY memorial_id"
        ).fetchall() == [
            (11, "First Person", "keep one"),
            (22, "Second Person", "keep two"),
        ]


def test_upgrade_current_unversioned_adds_only_metadata(tmp_path):
    path = tmp_path / "unversioned.db"
    with connect_database(path) as connection:
        graver_database._create_current_schema(connection)

    graver_database.upgrade_database(str(path))

    with connect_database(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM graves").fetchone() == (0,)
        assert connection.execute("SELECT version FROM graver_schema").fetchone() == (
            graver_database.CURRENT_SCHEMA_VERSION,
        )


def test_upgrade_version_1_creates_mechanical_subjects_and_preserves_tasks(tmp_path):
    path = make_version_1_database(tmp_path / "version-1.db")
    with connect_database(path) as connection:
        connection.executemany(
            "INSERT INTO graves (memorial_id, name) VALUES (?, ?)",
            [(11, "First Person"), (22, "Second Person")],
        )
        connection.execute("""INSERT INTO research_tasks
               (memorial_id, status, priority, owner, created_at, updated_at,
                last_activity_at, review_note)
               VALUES (11, 'researching', 7, 'reviewer', 'created', 'updated',
                       'active', 'preserve exactly')""")
        connection.execute("""INSERT INTO memorial_aliases
               (source_memorial_id, target_memorial_id, alias_type, status,
                first_observed_at, last_observed_at, updated_at)
               VALUES (11, 22, 'merged', 'active', 'first', 'last', 'updated')""")
        connection.execute("""INSERT INTO memorial_alias_observations
               (source_memorial_id, target_memorial_id, alias_type, event_type,
                observed_at, parser_version, payload_json)
               VALUES (11, 22, 'merged', 'observed', 'observed', '0.1', '{}')""")

    result = graver_database.upgrade_database(str(path))

    assert result.source.state == "outdated"
    assert result.source.version == 1
    with connect_database(path) as connection:
        connection.row_factory = sqlite3.Row
        subjects = connection.execute(
            "SELECT subject_id FROM research_subjects ORDER BY subject_id"
        ).fetchall()
        associations = connection.execute(
            "SELECT memorial_id, subject_id FROM subject_memorials ORDER BY memorial_id"
        ).fetchall()
        task = connection.execute("SELECT * FROM research_tasks").fetchone()
        migrated_event = connection.execute(
            "SELECT * FROM research_task_events WHERE event_type='task_migrated'"
        ).fetchone()

        assert len(subjects) == len(associations) == 2
        assert len({row["subject_id"] for row in associations}) == 2
        assert all(uuid.UUID(row["subject_id"]).version == 4 for row in subjects)
        assert task["subject_id"] == associations[0]["subject_id"]
        assert tuple(
            task[key] for key in task.keys() if key not in {"subject_id", "version"}
        ) == (
            "researching",
            7,
            "reviewer",
            "created",
            "updated",
            "active",
            "preserve exactly",
        )
        assert task["version"] == 1
        assert json.loads(migrated_event["after_json"])["memorial_id"] == 11
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM research_subject_events"
            ).fetchone()[0]
            == 4
        )
        assert (
            connection.execute("SELECT COUNT(*) FROM memorial_aliases").fetchone()[0]
            == 1
        )
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM memorial_alias_observations"
            ).fetchone()[0]
            == 1
        )
        assert (
            connection.execute("SELECT COUNT(*) FROM memorial_observations").fetchone()[
                0
            ]
            == 0
        )
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM subject_memorials WHERE memorial_id=22 "
                "AND subject_id=(SELECT subject_id FROM subject_memorials WHERE memorial_id=11)"
            ).fetchone()[0]
            == 0
        )
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM subject_memorials WHERE memorial_id=999"
            ).fetchone()[0]
            == 0
        )
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute("DELETE FROM research_task_events")
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute("UPDATE research_subject_events SET reason='changed'")

    with connect_database(result.backup_path) as backup:
        assert backup.execute("SELECT version FROM graver_schema").fetchone() == (1,)
        assert "research_subjects" not in {
            row[0]
            for row in backup.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }


def test_upgrade_refuses_backup_collision_without_mutating_source(tmp_path):
    path = make_legacy_database(tmp_path / "legacy.db")
    backup = graver_database.backup_path_for(path)
    backup.write_text("preserve")
    before = digest(path)

    with pytest.raises(
        graver_database.DatabaseUpgradeError, match="Backup already exists"
    ):
        graver_database.upgrade_database(str(path))

    assert digest(path) == before
    assert backup.read_text() == "preserve"


def test_version_1_migration_failure_rolls_back_all_subject_changes(
    tmp_path, monkeypatch
):
    path = make_version_1_database(tmp_path / "version-1.db")
    with connect_database(path) as connection:
        connection.execute("INSERT INTO graves (memorial_id) VALUES (11)")
    before = digest(path)

    original = graver_database.MIGRATIONS[1]

    def fail_after_subject_changes(connection):
        original(connection)
        raise sqlite3.OperationalError("simulated version-2 failure")

    monkeypatch.setitem(graver_database.MIGRATIONS, 1, fail_after_subject_changes)
    with pytest.raises(graver_database.DatabaseUpgradeError, match="recovery") as error:
        graver_database.upgrade_database(str(path))

    assert digest(path) == before
    assert error.value.backup_path.exists()
    assert graver_database.inspect_database(str(path)).state == "outdated"
    with connect_database(path) as connection:
        assert "research_subjects" not in {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }


def test_backup_failure_leaves_source_unchanged(tmp_path, monkeypatch):
    path = make_legacy_database(tmp_path / "legacy.db")
    before = digest(path)

    def fail_backup(_source, _backup):
        raise graver_database.DatabaseUpgradeError("simulated backup failure")

    monkeypatch.setattr(graver_database, "_create_verified_backup", fail_backup)
    with pytest.raises(graver_database.DatabaseUpgradeError, match="backup failure"):
        graver_database.upgrade_database(str(path))

    assert digest(path) == before
    assert graver_database.inspect_database(str(path)).state == "legacy_summary"


def test_migration_failure_rolls_back_and_preserves_backup(tmp_path, monkeypatch):
    path = make_legacy_database(tmp_path / "legacy.db")
    before = digest(path)

    def fail_migration(connection):
        connection.execute("ALTER TABLE graves ADD COLUMN should_rollback TEXT")
        raise sqlite3.OperationalError("simulated migration failure")

    monkeypatch.setitem(graver_database.MIGRATIONS, 0, fail_migration)
    with pytest.raises(graver_database.DatabaseUpgradeError, match="recovery") as error:
        graver_database.upgrade_database(str(path))

    assert digest(path) == before
    assert error.value.backup_path.exists()
    with connect_database(path) as connection:
        assert "should_rollback" not in {
            row[1] for row in connection.execute("PRAGMA table_info(graves)")
        }


def test_validation_failure_preserves_backup_and_reports_recovery(
    tmp_path, monkeypatch
):
    path = make_legacy_database(tmp_path / "legacy.db")

    def fail_validation(_connection):
        raise graver_database.DatabaseUpgradeError("simulated validation failure")

    monkeypatch.setattr(
        graver_database, "_validate_migrated_connection", fail_validation
    )
    with pytest.raises(graver_database.DatabaseUpgradeError, match="recovery") as error:
        graver_database.upgrade_database(str(path))
    assert error.value.backup_path.exists()
    assert graver_database.inspect_database(str(path)).state == "legacy_summary"


def test_post_migration_validation_failure_preserves_upgraded_data_and_backup(
    tmp_path, monkeypatch
):
    path = make_legacy_database(tmp_path / "legacy.db")

    def fail_final_validation(_database):
        raise graver_database.DatabaseInspectionError("simulated final failure")

    monkeypatch.setattr(
        graver_database, "validate_current_database", fail_final_validation
    )
    with pytest.raises(graver_database.DatabaseUpgradeError, match="recovery") as error:
        graver_database.upgrade_database(str(path))

    assert error.value.backup_path.exists()
    with connect_database(path) as connection:
        assert connection.execute("SELECT version FROM graver_schema").fetchone() == (
            graver_database.CURRENT_SCHEMA_VERSION,
        )
        assert connection.execute("SELECT COUNT(*) FROM graves").fetchone() == (2,)


def test_upgrade_rejects_newer_schema_without_backup(tmp_path):
    path = graver_database.create_database(str(tmp_path / "future.db"))
    with connect_database(path) as connection:
        connection.execute("UPDATE graver_schema SET version = 99")
    before = digest(path)

    with pytest.raises(graver_database.DatabaseUpgradeError, match="newer"):
        graver_database.upgrade_database(str(path))

    assert digest(path) == before
    assert not graver_database.backup_path_for(path).exists()


def test_version_three_upgrade_adds_empty_source_observations(tmp_path):
    path = graver_database.create_database(str(tmp_path / "version-three.db"))
    with connect_database(path) as connection:
        connection.execute("DROP TRIGGER research_source_observations_no_update")
        connection.execute("DROP TRIGGER research_source_observations_no_delete")
        connection.execute("DROP INDEX idx_source_observations_subject")
        connection.execute("DROP TABLE research_source_observations")
        connection.execute("UPDATE graver_schema SET version = 3")

    assert graver_database.inspect_database(str(path)).state == "outdated"
    result = graver_database.upgrade_database(str(path))

    assert result.source.version == 3
    assert result.version == graver_database.CURRENT_SCHEMA_VERSION


def test_version_four_upgrade_adds_task_revisions_without_changing_task_state(
    tmp_path,
):
    path = graver_database.create_database(str(tmp_path / "version-four.db"))
    with connect_database(path) as connection:
        connection.execute("ALTER TABLE research_tasks DROP COLUMN version")
        connection.execute("UPDATE graver_schema SET version = 4")

    assert graver_database.inspect_database(str(path)).state == "outdated"
    result = graver_database.upgrade_database(str(path))

    assert result.version == graver_database.CURRENT_SCHEMA_VERSION
    with connect_database(path) as connection:
        columns = {
            row[1]: row
            for row in connection.execute("PRAGMA table_info(research_tasks)")
        }
    assert columns["version"][3] == 1
    assert columns["version"][4] == "1"
    with connect_database(path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM research_source_observations"
        ).fetchone() == (0,)
    assert graver_database.inspect_database(str(path)).state == "current"


def test_cli_upgrade_reports_source_target_backup_and_preserves_preference(
    helpers, tmp_path, isolate_graver_configuration, monkeypatch
):
    path = make_legacy_database(tmp_path / "legacy.db")
    isolate_graver_configuration.parent.mkdir(parents=True, exist_ok=True)
    isolate_graver_configuration.write_text(json.dumps({"theme": "plain"}))

    result = helpers.graver_cli(f"admin database upgrade '{path}'")

    assert result.exit_code == 0
    assert "legacy summary-only schema" in result.output
    assert f"schema version {graver_database.CURRENT_SCHEMA_VERSION}" in result.output
    assert "Verified backup:" in result.output
    assert json.loads(isolate_graver_configuration.read_text()) == {"theme": "plain"}


def test_ordinary_read_rejects_legacy_without_mutation(helpers, tmp_path):
    path = make_legacy_database(tmp_path / "legacy.db")
    before = digest(path)

    with pytest.raises(graver_database.DatabaseInspectionError) as service_error:
        graver_database.validate_current_database(str(path))

    assert str(path.resolve()) in str(service_error.value)
    assert "admin database upgrade" in str(service_error.value)

    result = helpers.graver_cli(f"work list --db '{path}'")
    rendered = normalized_cli_output(result.output)

    assert result.exit_code != 0
    assert "admin database upgrade" in rendered
    assert path.name in rendered
    assert "Traceback" not in result.output
    assert digest(path) == before


def test_database_upgrade_help_is_specialist_and_meaningful(helpers):
    admin = helpers.graver_cli("admin --help")
    database = helpers.graver_cli("admin database --help")
    upgrade = helpers.graver_cli("admin database upgrade --help")

    assert admin.exit_code == database.exit_code == upgrade.exit_code == 0
    assert "database" in admin.output
    assert "upgrade" in database.output
    assert "Existing graver database to back up and upgrade" in " ".join(
        upgrade.output.split()
    )
