"""Internal SQLite connection lifecycle helpers."""

from __future__ import annotations

import sqlite3
from os import PathLike
from typing import Any


class ClosingConnection(sqlite3.Connection):
    """Commit or roll back on context exit, then always close the connection."""

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def connect_database(
    database: str | PathLike[str], **kwargs: Any
) -> sqlite3.Connection:
    """Return a SQLite connection with deterministic context-manager closure."""
    kwargs.setdefault("factory", ClosingConnection)
    return sqlite3.connect(database, **kwargs)
