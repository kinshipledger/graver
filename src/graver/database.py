"""Explicit creation of new Graver research databases."""

import os
import sqlite3
import stat
from pathlib import Path
from typing import Optional

from graver.api import _create_current_schema
from graver.config import DEFAULT_DATABASE, GraverConfigurationError
from graver.config import validate_graver_database as _validate_graver_database


class DatabaseInitializationError(Exception):
    """Raised when a new research database cannot be created safely."""


def _absolute_target(database: str) -> Path:
    return Path(os.path.abspath(Path(database).expanduser()))


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
            _create_current_schema(connection)
    except Exception as ex:
        _remove_created_file(path, created_stat)
        raise DatabaseInitializationError(
            f"Could not initialize research database at {path}: {ex}"
        ) from ex

    try:
        validated = _validate_graver_database(str(path))
    except GraverConfigurationError as ex:
        _remove_created_file(path, created_stat)
        raise DatabaseInitializationError(
            f"Could not validate research database at {path}: {ex}"
        ) from ex
    return validated
