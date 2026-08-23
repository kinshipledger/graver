"""Connection lifecycle tests for graver's internal SQLite boundary."""

import sqlite3

import pytest

from graver._sqlite import connect_database


def test_connection_context_commits_and_closes(tmp_path):
    database = tmp_path / "managed.db"

    with connect_database(database) as connection:
        connection.execute("CREATE TABLE example (value TEXT NOT NULL)")
        connection.execute("INSERT INTO example VALUES ('saved')")

    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
        connection.execute("SELECT 1")

    with connect_database(database) as verification:
        assert verification.execute("SELECT value FROM example").fetchone() == (
            "saved",
        )


def test_connection_context_rolls_back_and_closes(tmp_path):
    database = tmp_path / "managed.db"
    with connect_database(database) as setup:
        setup.execute("CREATE TABLE example (value TEXT NOT NULL)")

    with pytest.raises(RuntimeError, match="stop transaction"):
        with connect_database(database) as connection:
            connection.execute("INSERT INTO example VALUES ('discarded')")
            raise RuntimeError("stop transaction")

    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
        connection.execute("SELECT 1")

    with connect_database(database) as verification:
        assert verification.execute("SELECT COUNT(*) FROM example").fetchone() == (0,)
