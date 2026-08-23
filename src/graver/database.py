"""Explicit database creation, read-only inspection, and ordered upgrades."""

import json
import os
import sqlite3
import stat
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from graver._sqlite import connect_database
from graver.api import (
    _create_cemeteries_table,
    _create_current_schema,
    _create_research_schema,
    _create_subject_schema,
    _migrate_cemeteries_table,
    _migrate_graves_table,
)
from graver.config import DEFAULT_DATABASE

__all__ = (
    "DatabaseInitializationError",
    "DatabaseInspectionError",
    "DatabaseLifecycleError",
    "DatabaseUpgradeError",
    "create_database",
    "inspect_database",
    "upgrade_database",
    "validate_current_database",
)

CURRENT_SCHEMA_VERSION = 4
SCHEMA_TABLE = "graver_schema"
VERSION_1_TABLES = {
    "cemeteries",
    "graves",
    "memorial_alias_observations",
    "memorial_aliases",
    "memorial_observations",
    "research_tasks",
}
CURRENT_TABLES = VERSION_1_TABLES | {
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
}
CURRENT_GRAVE_COLUMNS = {
    "memorial_id",
    "findagrave_url",
    "name",
    "birth",
    "death",
    "cemetery_id",
    "date_added",
    "detail_level",
    "summary_fetched_at",
    "full_fetched_at",
}
CURRENT_INDEXES = {
    "idx_graves_cemetery_id",
    "idx_memorial_observations_memorial_id",
    "idx_memorial_observations_cemetery_id",
    "idx_research_tasks_status_priority",
    "idx_memorial_aliases_target_status",
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
}
CURRENT_TRIGGERS = {
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
}
EVIDENCE_TABLES = {
    "research_source_observations",
    "candidate_discovery_runs",
    "external_candidates",
    "candidate_snapshots",
    "comparison_signals",
    "candidate_assessments",
    "candidate_assessment_events",
    "identity_conclusions",
}
EVIDENCE_INDEXES = {
    "idx_source_observations_subject",
    "idx_discovery_runs_subject",
    "idx_candidates_subject",
    "idx_candidate_snapshots_candidate",
    "idx_comparison_signals_candidate",
    "idx_assessment_events_candidate",
    "idx_conclusions_candidate",
}
EVIDENCE_TRIGGERS = {
    "research_source_observations_no_update",
    "research_source_observations_no_delete",
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
}
VERSION_2_TABLES = CURRENT_TABLES - EVIDENCE_TABLES
VERSION_2_INDEXES = CURRENT_INDEXES - EVIDENCE_INDEXES
VERSION_2_TRIGGERS = CURRENT_TRIGGERS - EVIDENCE_TRIGGERS
VERSION_3_TABLES = CURRENT_TABLES - {"research_source_observations"}
VERSION_3_INDEXES = CURRENT_INDEXES - {"idx_source_observations_subject"}
VERSION_3_TRIGGERS = CURRENT_TRIGGERS - {
    "research_source_observations_no_update",
    "research_source_observations_no_delete",
}
VERSION_1_INDEXES = VERSION_2_INDEXES - {
    "idx_subject_memorials_subject",
    "idx_research_subject_events_subject",
    "idx_research_task_events_subject",
}
VERSION_1_TRIGGERS = VERSION_2_TRIGGERS - {
    "research_subject_events_no_update",
    "research_subject_events_no_delete",
    "research_task_events_no_update",
    "research_task_events_no_delete",
}
LEGACY_REQUIRED_COLUMNS = {"memorial_id", "findagrave_url", "name", "birth", "death"}
LEGACY_FULL_MARKERS = {"original_name", "birth_place", "death_place", "has_bio"}


class DatabaseLifecycleError(ValueError):
    """Base error for safe database lifecycle operations."""


class DatabaseInitializationError(DatabaseLifecycleError):
    """Raised when a new research database cannot be created safely."""


class DatabaseInspectionError(DatabaseLifecycleError):
    """Raised when a database cannot be classified safely."""


class DatabaseUpgradeError(DatabaseLifecycleError):
    """Raised when an explicit database upgrade cannot complete safely."""

    def __init__(self, message: str, backup_path: Optional[Path] = None):
        super().__init__(message)
        self.backup_path = backup_path


@dataclass(frozen=True)
class SchemaInspection:
    path: Path
    state: str
    version: Optional[int] = None

    @property
    def current(self) -> bool:
        return self.state == "current"

    @property
    def source_label(self) -> str:
        labels = {
            "legacy_0_1": "legacy 0.1 schema",
            "legacy_summary": "legacy summary-only schema",
            "current_unversioned": "current pre-version-metadata schema",
            "outdated": f"schema version {self.version}",
            "current": f"schema version {self.version}",
        }
        return labels.get(self.state, self.state.replace("_", " "))


@dataclass(frozen=True)
class DatabaseUpgradeResult:
    path: Path
    source: SchemaInspection
    version: int
    backup_path: Optional[Path]
    changed: bool


def _absolute_target(database: str) -> Path:
    return Path(os.path.abspath(Path(database).expanduser()))


def _readonly_uri(path: Path) -> str:
    return f"file:{quote(str(path), safe='/')}?mode=ro"


def _remove_created_file(path: Path, created_stat: os.stat_result) -> None:
    """Remove only the same regular file reserved by this invocation."""
    try:
        current_stat = path.lstat()
        same_file = (current_stat.st_dev, current_stat.st_ino) == (
            created_stat.st_dev,
            created_stat.st_ino,
        )
        if same_file and stat.S_ISREG(current_stat.st_mode):
            path.unlink()
    except FileNotFoundError:
        pass


def _tables(connection: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'"
        )
    }


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}


def _schema_objects(connection: sqlite3.Connection) -> tuple[set[str], set[str]]:
    objects = connection.execute(
        "SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
    ).fetchall()
    indexes = {name for kind, name in objects if kind == "index"}
    triggers = {name for kind, name in objects if kind == "trigger"}
    return indexes, triggers


def _structurally_version_1(connection: sqlite3.Connection) -> bool:
    indexes, triggers = _schema_objects(connection)
    task_columns = _columns(connection, "research_tasks")
    return (
        VERSION_1_TABLES <= _tables(connection)
        and CURRENT_GRAVE_COLUMNS <= _columns(connection, "graves")
        and "memorial_id" in task_columns
        and "subject_id" not in task_columns
        and VERSION_1_INDEXES <= indexes
        and VERSION_1_TRIGGERS <= triggers
    )


def _structurally_current(connection: sqlite3.Connection) -> bool:
    indexes, triggers = _schema_objects(connection)
    return (
        CURRENT_TABLES <= _tables(connection)
        and CURRENT_GRAVE_COLUMNS <= _columns(connection, "graves")
        and "subject_id" in _columns(connection, "research_tasks")
        and "memorial_id" not in _columns(connection, "research_tasks")
        and CURRENT_INDEXES <= indexes
        and CURRENT_TRIGGERS <= triggers
        and _subject_invariants_hold(connection)
        and _evidence_invariants_hold(connection)
    )


def _structurally_version_2(connection: sqlite3.Connection) -> bool:
    indexes, triggers = _schema_objects(connection)
    return (
        VERSION_2_TABLES <= _tables(connection)
        and not (EVIDENCE_TABLES & _tables(connection))
        and CURRENT_GRAVE_COLUMNS <= _columns(connection, "graves")
        and "subject_id" in _columns(connection, "research_tasks")
        and "memorial_id" not in _columns(connection, "research_tasks")
        and VERSION_2_INDEXES <= indexes
        and VERSION_2_TRIGGERS <= triggers
        and _subject_invariants_hold(connection)
    )


def _structurally_version_3(connection: sqlite3.Connection) -> bool:
    indexes, triggers = _schema_objects(connection)
    return (
        VERSION_3_TABLES <= _tables(connection)
        and "research_source_observations" not in _tables(connection)
        and CURRENT_GRAVE_COLUMNS <= _columns(connection, "graves")
        and "subject_id" in _columns(connection, "research_tasks")
        and "memorial_id" not in _columns(connection, "research_tasks")
        and VERSION_3_INDEXES <= indexes
        and VERSION_3_TRIGGERS <= triggers
        and _subject_invariants_hold(connection)
        and _evidence_invariants_hold(connection)
    )


def _evidence_invariants_hold(connection: sqlite3.Connection) -> bool:
    checks = [
        """SELECT 1 FROM external_candidates c LEFT JOIN research_subjects s
           ON s.subject_id=c.subject_id WHERE s.subject_id IS NULL LIMIT 1""",
        """SELECT 1 FROM candidate_snapshots cs LEFT JOIN external_candidates c
           ON c.candidate_id=cs.candidate_id WHERE c.candidate_id IS NULL LIMIT 1""",
        """SELECT 1 FROM candidate_snapshots cs LEFT JOIN candidate_discovery_runs r
           ON r.run_id=cs.run_id WHERE r.run_id IS NULL LIMIT 1""",
        """SELECT 1 FROM candidate_assessments a LEFT JOIN external_candidates c
           ON c.candidate_id=a.candidate_id WHERE c.candidate_id IS NULL LIMIT 1""",
        """SELECT 1 FROM external_candidates c
           WHERE NOT EXISTS (
               SELECT 1 FROM candidate_assessments a
               WHERE a.candidate_id=c.candidate_id
           ) LIMIT 1""",
        """SELECT 1 FROM candidate_assessments a
           WHERE NOT EXISTS (
               SELECT 1 FROM candidate_assessment_events e
               WHERE e.candidate_id=a.candidate_id
           ) LIMIT 1""",
        """SELECT 1 FROM candidate_snapshots cs
           JOIN external_candidates c ON c.candidate_id=cs.candidate_id
           JOIN candidate_discovery_runs r ON r.run_id=cs.run_id
           WHERE c.subject_id<>r.subject_id OR c.provider<>r.provider LIMIT 1""",
        """SELECT 1 FROM comparison_signals s
           JOIN external_candidates c ON c.candidate_id=s.candidate_id
           JOIN candidate_snapshots cs ON cs.snapshot_id=s.snapshot_id
           WHERE s.subject_id<>c.subject_id OR cs.candidate_id<>c.candidate_id LIMIT 1""",
        """SELECT 1 FROM identity_conclusions i LEFT JOIN external_candidates c
           ON c.candidate_id=i.candidate_id WHERE c.candidate_id IS NULL LIMIT 1""",
        """SELECT 1 FROM identity_conclusions i
           JOIN external_candidates c ON c.candidate_id=i.candidate_id
           WHERE i.subject_id<>c.subject_id LIMIT 1""",
    ]
    if "research_source_observations" in _tables(connection):
        checks.append("""SELECT 1 FROM research_source_observations o
               LEFT JOIN research_subjects s ON s.subject_id=o.subject_id
               WHERE s.subject_id IS NULL LIMIT 1""")
    return all(connection.execute(sql).fetchone() is None for sql in checks)


def _subject_invariants_hold(connection: sqlite3.Connection) -> bool:
    checks = (
        """SELECT 1 FROM graves g LEFT JOIN subject_memorials sm
           ON sm.memorial_id=g.memorial_id WHERE sm.memorial_id IS NULL LIMIT 1""",
        """SELECT 1 FROM subject_memorials sm LEFT JOIN research_subjects s
           ON s.subject_id=sm.subject_id WHERE s.subject_id IS NULL LIMIT 1""",
        """SELECT 1 FROM research_tasks t LEFT JOIN research_subjects s
           ON s.subject_id=t.subject_id WHERE s.subject_id IS NULL LIMIT 1""",
        """SELECT 1 FROM research_subjects s
           WHERE NOT EXISTS (
               SELECT 1 FROM research_subject_events e
               WHERE e.subject_id=s.subject_id AND e.event_type='subject_created'
           ) LIMIT 1""",
        """SELECT 1 FROM subject_memorials sm
           WHERE NOT EXISTS (
               SELECT 1 FROM research_subject_events e
               WHERE e.subject_id=sm.subject_id
                 AND e.memorial_id=sm.memorial_id
                 AND e.event_type='memorial_associated'
           ) LIMIT 1""",
        """SELECT 1 FROM research_tasks t
           WHERE NOT EXISTS (
               SELECT 1 FROM research_task_events e
               WHERE e.subject_id=t.subject_id
           ) LIMIT 1""",
    )
    return all(connection.execute(sql).fetchone() is None for sql in checks)


def _inspect_connection(path: Path, connection: sqlite3.Connection) -> SchemaInspection:
    tables = _tables(connection)
    if not tables:
        return SchemaInspection(path, "empty")
    if SCHEMA_TABLE in tables:
        if {"singleton", "version"} - _columns(connection, SCHEMA_TABLE):
            return SchemaInspection(path, "unknown")
        rows = connection.execute(
            f"SELECT singleton, version FROM {SCHEMA_TABLE}"
        ).fetchall()
        if len(rows) != 1 or rows[0][0] != 1 or not isinstance(rows[0][1], int):
            return SchemaInspection(path, "unknown")
        version = rows[0][1]
        if version > CURRENT_SCHEMA_VERSION:
            return SchemaInspection(path, "newer", version)
        if version == 1 and _structurally_version_1(connection):
            return SchemaInspection(path, "outdated", version)
        if version == 2 and _structurally_version_2(connection):
            return SchemaInspection(path, "outdated", version)
        if version == 3 and _structurally_version_3(connection):
            return SchemaInspection(path, "outdated", version)
        if version != CURRENT_SCHEMA_VERSION or not _structurally_current(connection):
            return SchemaInspection(path, "unknown", version)
        return SchemaInspection(path, "current", version)
    if "graves" not in tables:
        return SchemaInspection(path, "non_graver")
    grave_columns = _columns(connection, "graves")
    if _structurally_current(connection):
        return SchemaInspection(path, "current_unversioned", 4)
    if _structurally_version_3(connection):
        return SchemaInspection(path, "current_unversioned", 3)
    if _structurally_version_2(connection):
        return SchemaInspection(path, "current_unversioned", 2)
    if _structurally_version_1(connection):
        return SchemaInspection(path, "current_unversioned")
    if not LEGACY_REQUIRED_COLUMNS <= grave_columns:
        return SchemaInspection(path, "unknown")
    if LEGACY_FULL_MARKERS <= grave_columns:
        return SchemaInspection(path, "legacy_0_1")
    return SchemaInspection(path, "legacy_summary")


def inspect_database(database: str) -> SchemaInspection:
    """Classify an existing database without changing filesystem or SQLite state."""
    supplied_path = _absolute_target(database)
    if not supplied_path.exists():
        raise DatabaseInspectionError(f"Database does not exist: {supplied_path}")
    if supplied_path.is_symlink() or not supplied_path.is_file():
        raise DatabaseInspectionError(
            "Database must be an existing regular file (not a symlink): "
            f"{supplied_path}"
        )
    path = supplied_path.resolve()
    try:
        with connect_database(_readonly_uri(path), uri=True) as connection:
            connection.execute("PRAGMA query_only = ON")
            return _inspect_connection(path, connection)
    except sqlite3.Error as ex:
        raise DatabaseInspectionError(
            f"File is not a usable SQLite database: {path}. {ex}"
        ) from ex


def validate_current_database(database: str) -> Path:
    """Validate a current database read-only and reject legacy or unsafe shapes."""
    inspection = inspect_database(database)
    path = inspection.path
    if inspection.state == "newer":
        raise DatabaseInspectionError(
            f"Database schema version {inspection.version} is newer than this Graver "
            f"supports ({CURRENT_SCHEMA_VERSION}): {path}"
        )
    if inspection.state in {
        "legacy_0_1",
        "legacy_summary",
        "current_unversioned",
        "outdated",
    }:
        raise DatabaseInspectionError(
            f"Database requires an explicit upgrade ({inspection.source_label}): "
            f"{path}. Run `graver admin database upgrade {path}` to upgrade it safely."
        )
    if not inspection.current:
        raise DatabaseInspectionError(
            f"SQLite file is not a recognized current Graver database "
            f"({inspection.source_label}): {path}"
        )
    try:
        with connect_database(_readonly_uri(path), uri=True) as connection:
            connection.execute("PRAGMA query_only = ON")
            if connection.execute("PRAGMA quick_check").fetchone() != ("ok",):
                raise DatabaseInspectionError(
                    f"SQLite database failed its integrity check: {path}"
                )
            if connection.execute("PRAGMA foreign_key_check").fetchall():
                raise DatabaseInspectionError(
                    f"SQLite database has foreign-key violations: {path}"
                )
    except DatabaseInspectionError:
        raise
    except sqlite3.Error as ex:
        raise DatabaseInspectionError(
            f"Database validation failed for {path}: {ex}"
        ) from ex
    return path


def _record_schema_version(connection: sqlite3.Connection, version: int) -> None:
    connection.execute(f"""CREATE TABLE {SCHEMA_TABLE} (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                version INTEGER NOT NULL CHECK (version >= 1)
            )""")
    connection.execute(
        f"INSERT INTO {SCHEMA_TABLE} (singleton, version) VALUES (1, ?)", (version,)
    )


def initialize_current_schema(connection: sqlite3.Connection) -> None:
    """Initialize the complete current schema and its version metadata."""
    _create_current_schema(connection)
    _record_schema_version(connection, CURRENT_SCHEMA_VERSION)


def create_database(database: Optional[str] = None) -> Path:
    """Create and validate one new current-schema database without migration."""
    path = _absolute_target(DEFAULT_DATABASE if database is None else database)
    parent = path.parent
    if not parent.exists():
        raise DatabaseInitializationError(
            f"Parent directory does not exist for research database: {path}"
        )
    if not parent.is_dir():
        raise DatabaseInitializationError(
            f"Parent path is not a directory for research database: {path}"
        )
    if os.path.lexists(path):
        raise DatabaseInitializationError(
            f"Refusing to overwrite existing path: {path}"
        )

    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
    except FileExistsError as ex:
        raise DatabaseInitializationError(
            f"Refusing to overwrite existing path: {path}"
        ) from ex
    except OSError as ex:
        raise DatabaseInitializationError(
            f"Could not create research database at {path}: {ex}"
        ) from ex

    try:
        created_stat = os.fstat(descriptor)
    finally:
        os.close(descriptor)

    try:
        connection = connect_database(path)
        try:
            with connection:
                connection.execute("PRAGMA foreign_keys = ON")
                initialize_current_schema(connection)
        finally:
            connection.close()
    except Exception as ex:
        _remove_created_file(path, created_stat)
        raise DatabaseInitializationError(
            f"Could not initialize research database at {path}: {ex}"
        ) from ex

    try:
        validated = validate_current_database(str(path))
    except DatabaseInspectionError as ex:
        _remove_created_file(path, created_stat)
        raise DatabaseInitializationError(
            f"Could not validate research database at {path}: {ex}"
        ) from ex
    return validated


def _migration_0_to_1(connection: sqlite3.Connection) -> None:
    """Upgrade recognized unversioned schemas without inventing row values."""
    _migrate_graves_table(connection)
    _create_cemeteries_table(connection)
    _migrate_cemeteries_table(connection)
    _create_research_schema(connection)
    _record_schema_version(connection, 1)


def _migration_timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _migration_subject_id() -> str:
    return str(uuid.uuid4())


def _migration_1_to_2(connection: sqlite3.Connection) -> None:
    """Create mechanical subjects and re-key tasks without identity inference."""
    timestamp = _migration_timestamp()
    connection.execute("DROP INDEX IF EXISTS idx_research_tasks_status_priority")
    connection.execute("ALTER TABLE research_tasks RENAME TO research_tasks_v1")
    _create_subject_schema(connection)

    memorial_subjects = {}
    for (memorial_id,) in connection.execute(
        "SELECT memorial_id FROM graves ORDER BY memorial_id"
    ):
        subject_id = _migration_subject_id()
        memorial_subjects[memorial_id] = subject_id
        connection.execute(
            "INSERT INTO research_subjects (subject_id, created_at) VALUES (?, ?)",
            (subject_id, timestamp),
        )
        connection.execute(
            """INSERT INTO subject_memorials
               (memorial_id, subject_id, associated_at, association_reason)
               VALUES (?, ?, ?, 'migration')""",
            (memorial_id, subject_id, timestamp),
        )
        connection.execute(
            """INSERT INTO research_subject_events
               (subject_id, event_type, occurred_at, reason, after_json)
               VALUES (?, 'subject_created', ?, 'schema_v2_migration', ?)""",
            (
                subject_id,
                timestamp,
                json.dumps(
                    {"subject_id": subject_id, "creation": "mechanical_migration"},
                    sort_keys=True,
                ),
            ),
        )
        connection.execute(
            """INSERT INTO research_subject_events
               (subject_id, event_type, occurred_at, reason, memorial_id, after_json)
               VALUES (?, 'memorial_associated', ?, 'schema_v2_migration', ?, ?)""",
            (
                subject_id,
                timestamp,
                memorial_id,
                json.dumps(
                    {
                        "memorial_id": memorial_id,
                        "association": "mechanical_migration",
                    },
                    sort_keys=True,
                ),
            ),
        )

    connection.row_factory = sqlite3.Row
    tasks = connection.execute(
        "SELECT * FROM research_tasks_v1 ORDER BY memorial_id"
    ).fetchall()
    for task in tasks:
        subject_id = memorial_subjects[task["memorial_id"]]
        connection.execute(
            """INSERT INTO research_tasks
               (subject_id, status, priority, owner, created_at, updated_at,
                last_activity_at, review_note)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                subject_id,
                task["status"],
                task["priority"],
                task["owner"],
                task["created_at"],
                task["updated_at"],
                task["last_activity_at"],
                task["review_note"],
            ),
        )
        snapshot = {key: task[key] for key in task.keys()}
        connection.execute(
            """INSERT INTO research_task_events
               (subject_id, event_type, occurred_at, reason, after_json)
               VALUES (?, 'task_migrated', ?, 'schema_v2_migration', ?)""",
            (subject_id, timestamp, json.dumps(snapshot, sort_keys=True)),
        )
    connection.row_factory = None
    connection.execute("DROP TABLE research_tasks_v1")
    connection.execute(f"UPDATE {SCHEMA_TABLE} SET version = 2 WHERE singleton = 1")


def _migration_2_to_3(connection: sqlite3.Connection) -> None:
    """Add empty evidence structures without inventing candidate research."""
    from graver.evidence import create_evidence_schema

    create_evidence_schema(connection)
    connection.execute(f"UPDATE {SCHEMA_TABLE} SET version = 3 WHERE singleton = 1")


def _migration_3_to_4(connection: sqlite3.Connection) -> None:
    """Add citation-bearing source observations without inventing evidence."""
    from graver.evidence import create_evidence_schema

    create_evidence_schema(connection)
    connection.execute(f"UPDATE {SCHEMA_TABLE} SET version = 4 WHERE singleton = 1")


MIGRATIONS = {
    0: _migration_0_to_1,
    1: _migration_1_to_2,
    2: _migration_2_to_3,
    3: _migration_3_to_4,
}


def backup_path_for(path: Path) -> Path:
    return path.with_name(path.name + f".pre-upgrade-v{CURRENT_SCHEMA_VERSION}.backup")


def _create_verified_backup(source: Path, backup: Path) -> None:
    if os.path.lexists(backup):
        raise DatabaseUpgradeError(
            f"Backup already exists: {backup}. Preserve or rename it before retrying."
        )
    descriptor = None
    created_stat = None
    try:
        descriptor = os.open(backup, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
        created_stat = os.fstat(descriptor)
        os.close(descriptor)
        descriptor = None
        with connect_database(_readonly_uri(source), uri=True) as source_connection:
            with connect_database(backup) as backup_connection:
                source_connection.backup(backup_connection)
        with connect_database(_readonly_uri(backup), uri=True) as connection:
            if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise sqlite3.DatabaseError("backup integrity check failed")
    except Exception as ex:
        if descriptor is not None:
            os.close(descriptor)
        if created_stat is not None:
            _remove_created_file(backup, created_stat)
        raise DatabaseUpgradeError(
            f"Could not create verified backup {backup}: {ex}"
        ) from ex


def _validate_migrated_connection(connection: sqlite3.Connection) -> None:
    if not _inspect_connection(Path("<upgrade>"), connection).current:
        raise DatabaseUpgradeError("Migrated schema is not current")
    if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
        raise DatabaseUpgradeError("Migrated database failed its integrity check")
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise DatabaseUpgradeError("Migrated database has foreign-key violations")


def upgrade_database(database: str) -> DatabaseUpgradeResult:
    """Back up and explicitly migrate one recognized database in ordered steps."""
    try:
        source = inspect_database(database)
    except DatabaseInspectionError as ex:
        raise DatabaseUpgradeError(str(ex)) from ex
    path = source.path
    if source.current:
        return DatabaseUpgradeResult(path, source, CURRENT_SCHEMA_VERSION, None, False)
    if source.state == "newer":
        raise DatabaseUpgradeError(
            f"Database schema version {source.version} is newer than supported "
            f"version {CURRENT_SCHEMA_VERSION}: {path}"
        )
    if source.state not in {
        "legacy_0_1",
        "legacy_summary",
        "current_unversioned",
        "outdated",
    }:
        raise DatabaseUpgradeError(
            f"Database schema is not a recognized upgrade source "
            f"({source.source_label}): {path}"
        )
    backup = backup_path_for(path)
    _create_verified_backup(path, backup)
    try:
        with connect_database(path, isolation_level=None) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("BEGIN IMMEDIATE")
            try:
                version = source.version or 0
                if source.state == "current_unversioned" and version in {2, 3, 4}:
                    _record_schema_version(connection, version)
                while version < CURRENT_SCHEMA_VERSION:
                    migration = MIGRATIONS.get(version)
                    if migration is None:
                        raise DatabaseUpgradeError(
                            f"No migration is available from schema version {version}"
                        )
                    migration(connection)
                    version += 1
                _validate_migrated_connection(connection)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        validate_current_database(str(path))
    except Exception as ex:
        raise DatabaseUpgradeError(
            f"Upgrade failed for {path}: {ex}. The verified backup remains at "
            f"{backup}; recovery is a deliberate manual action.",
            backup,
        ) from ex
    return DatabaseUpgradeResult(path, source, CURRENT_SCHEMA_VERSION, backup, True)
