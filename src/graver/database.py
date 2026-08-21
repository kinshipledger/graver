"""Explicit database creation, read-only inspection, and ordered upgrades."""

import os
import sqlite3
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from graver.api import (
    _create_cemeteries_table,
    _create_current_schema,
    _create_research_schema,
    _migrate_cemeteries_table,
    _migrate_graves_table,
)
from graver.config import DEFAULT_DATABASE


CURRENT_SCHEMA_VERSION = 1
SCHEMA_TABLE = "graver_schema"
CURRENT_TABLES = {
    "cemeteries",
    "graves",
    "memorial_alias_observations",
    "memorial_aliases",
    "memorial_observations",
    "research_tasks",
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
}
CURRENT_TRIGGERS = {
    "memorial_observations_no_update",
    "memorial_observations_no_delete",
    "memorial_alias_observations_no_update",
    "memorial_alias_observations_no_delete",
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


def _structurally_current(connection: sqlite3.Connection) -> bool:
    objects = connection.execute(
        "SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
    ).fetchall()
    indexes = {name for kind, name in objects if kind == "index"}
    triggers = {name for kind, name in objects if kind == "trigger"}
    return (
        CURRENT_TABLES <= _tables(connection)
        and CURRENT_GRAVE_COLUMNS <= _columns(connection, "graves")
        and CURRENT_INDEXES <= indexes
        and CURRENT_TRIGGERS <= triggers
    )


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
        if version != CURRENT_SCHEMA_VERSION or not _structurally_current(connection):
            return SchemaInspection(path, "unknown", version)
        return SchemaInspection(path, "current", version)
    if "graves" not in tables:
        return SchemaInspection(path, "non_graver")
    grave_columns = _columns(connection, "graves")
    if _structurally_current(connection):
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
        with sqlite3.connect(_readonly_uri(path), uri=True) as connection:
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
    if inspection.state in {"legacy_0_1", "legacy_summary", "current_unversioned"}:
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
        with sqlite3.connect(_readonly_uri(path), uri=True) as connection:
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
    connection.execute(
        f"""CREATE TABLE {SCHEMA_TABLE} (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                version INTEGER NOT NULL CHECK (version >= 1)
            )"""
    )
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
        with sqlite3.connect(path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            initialize_current_schema(connection)
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


MIGRATIONS = {0: _migration_0_to_1}


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
        with sqlite3.connect(_readonly_uri(source), uri=True) as source_connection:
            with sqlite3.connect(backup) as backup_connection:
                source_connection.backup(backup_connection)
        with sqlite3.connect(_readonly_uri(backup), uri=True) as connection:
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
    if source.state not in {"legacy_0_1", "legacy_summary", "current_unversioned"}:
        raise DatabaseUpgradeError(
            f"Database schema is not a recognized upgrade source "
            f"({source.source_label}): {path}"
        )
    backup = backup_path_for(path)
    _create_verified_backup(path, backup)
    try:
        with sqlite3.connect(path, isolation_level=None) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("BEGIN IMMEDIATE")
            try:
                version = 0
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
