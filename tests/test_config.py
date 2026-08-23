import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from graver import Memorial
from graver import config as graver_config


def database_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_graver_database(path: Path) -> Path:
    Memorial.create_table(str(path))
    return path


def test_select_stores_resolved_absolute_path(tmp_path, isolate_graver_configuration):
    database = make_graver_database(tmp_path / "research.db")

    selected = graver_config.select_default_database(str(database))

    assert selected == database.resolve()
    saved = json.loads(isolate_graver_configuration.read_text())
    assert saved["default_database"] == str(database.resolve())


def test_relative_selection_survives_directory_change(
    tmp_path, monkeypatch, isolate_graver_configuration
):
    first_directory = tmp_path / "first"
    second_directory = tmp_path / "second"
    first_directory.mkdir()
    second_directory.mkdir()
    database = make_graver_database(first_directory / "research.db")
    monkeypatch.chdir(first_directory)

    graver_config.select_default_database("research.db")
    monkeypatch.chdir(second_directory)

    selection = graver_config.resolve_database(None, environment={})
    assert selection.path == str(database.resolve())


def test_tilde_is_expanded(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    database = make_graver_database(home / "research.db")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))

    selected = graver_config.select_default_database("~/research.db")

    assert selected == database.resolve()


def test_clear_preserves_unrelated_fields(isolate_graver_configuration):
    isolate_graver_configuration.parent.mkdir(parents=True)
    isolate_graver_configuration.write_text(
        json.dumps({"default_database": "/somewhere/research.db", "theme": "plain"})
    )

    assert graver_config.clear_default_database() is True
    assert graver_config.clear_default_database() is False
    assert json.loads(isolate_graver_configuration.read_text()) == {"theme": "plain"}


@pytest.mark.parametrize("kind", ["missing", "directory", "text", "sqlite"])
def test_validation_rejects_non_graver_inputs(tmp_path, kind):
    path = tmp_path / kind
    if kind == "directory":
        path.mkdir()
    elif kind == "text":
        path.write_text("not sqlite")
    elif kind == "sqlite":
        with sqlite3.connect(path) as connection:
            connection.execute("CREATE TABLE something_else (value TEXT)")

    with pytest.raises(graver_config.GraverConfigurationError):
        graver_config.validate_graver_database(str(path))


def test_validation_does_not_modify_or_migrate_database(tmp_path):
    database = tmp_path / "legacy.db"
    with sqlite3.connect(database) as connection:
        connection.execute("""CREATE TABLE graves (
                memorial_id INTEGER PRIMARY KEY, findagrave_url TEXT, name TEXT,
                birth TEXT, death TEXT, cemetery_id INTEGER
            )""")
    before_digest = database_digest(database)
    before_mtime = database.stat().st_mtime_ns

    with pytest.raises(
        graver_config.GraverConfigurationError, match="admin database upgrade"
    ):
        graver_config.validate_graver_database(str(database))

    assert database_digest(database) == before_digest
    assert database.stat().st_mtime_ns == before_mtime
    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    assert tables == {"graves"}


def test_malformed_configuration_is_reported(isolate_graver_configuration):
    isolate_graver_configuration.parent.mkdir(parents=True)
    isolate_graver_configuration.write_text("{not-json")

    with pytest.raises(graver_config.GraverConfigurationError, match="unreadable"):
        graver_config.resolve_database(None, environment={})


def test_database_precedence(tmp_path, isolate_graver_configuration):
    saved = make_graver_database(tmp_path / "saved.db")
    environment = make_graver_database(tmp_path / "environment.db")
    explicit = tmp_path / "explicit-new.db"
    graver_config.select_default_database(str(saved))

    assert graver_config.resolve_database(
        str(explicit), {"GRAVER_DB": str(environment)}
    ) == graver_config.DatabaseSelection(str(explicit), "command line")
    assert graver_config.resolve_database(
        None, {"GRAVER_DB": str(environment)}
    ) == graver_config.DatabaseSelection(str(environment.resolve()), "GRAVER_DB")
    assert graver_config.resolve_database(None, {}) == graver_config.DatabaseSelection(
        str(saved.resolve()), "saved preference"
    )
    graver_config.clear_default_database()
    assert graver_config.resolve_database(None, {}) == graver_config.DatabaseSelection(
        "graves.db", "built-in default"
    )


@pytest.mark.parametrize("source", ["environment", "saved"])
def test_invalid_selected_source_does_not_fall_back(
    tmp_path, source, isolate_graver_configuration
):
    missing = tmp_path / "missing.db"
    if source == "environment":
        environment = {"GRAVER_DB": str(missing)}
    else:
        isolate_graver_configuration.parent.mkdir(parents=True)
        isolate_graver_configuration.write_text(
            json.dumps({"default_database": str(missing)})
        )
        environment = {}

    with pytest.raises(graver_config.GraverConfigurationError, match="does not exist"):
        graver_config.resolve_database(None, environment)


def test_platform_configuration_locations(tmp_path):
    assert graver_config.configuration_path({}, "darwin", tmp_path) == (
        tmp_path / "Library" / "Application Support" / "graver" / "config.json"
    )
    assert graver_config.configuration_path(
        {"APPDATA": str(tmp_path / "appdata")}, "win32", tmp_path
    ) == (tmp_path / "appdata" / "graver" / "config.json")
    assert graver_config.configuration_path(
        {"XDG_CONFIG_HOME": str(tmp_path / "xdg")}, "linux", tmp_path
    ) == (tmp_path / "xdg" / "graver" / "config.json")
