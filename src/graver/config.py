"""Per-user database selection without database initialization side effects."""

import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

DEFAULT_DATABASE = "graves.db"
DATABASE_ENVIRONMENT_VARIABLE = "GRAVER_DB"
DATABASE_CONFIG_KEY = "default_database"


class GraverConfigurationError(Exception):
    """Raised when configuration or a configured database cannot be used."""


@dataclass(frozen=True)
class DatabaseSelection:
    path: str
    source: str


def configuration_path(
    environment: Optional[Mapping[str, str]] = None,
    platform: Optional[str] = None,
    home: Optional[Path] = None,
) -> Path:
    """Return graver's platform-aware per-user JSON configuration path."""
    environment = os.environ if environment is None else environment
    platform = sys.platform if platform is None else platform
    home = Path.home() if home is None else home
    if platform == "darwin":
        root = home / "Library" / "Application Support"
    elif platform == "win32" and environment.get("APPDATA"):
        root = Path(environment["APPDATA"])
    else:
        root = Path(environment.get("XDG_CONFIG_HOME", home / ".config"))
    return root / "graver" / "config.json"


def load_configuration(config_path: Optional[Path] = None) -> dict:
    """Load configuration, distinguishing absence from malformed content."""
    config_path = configuration_path() if config_path is None else Path(config_path)
    if not config_path.exists():
        return {}
    try:
        with config_path.open(encoding="utf-8") as config_file:
            configuration = json.load(config_file)
    except (OSError, UnicodeError, json.JSONDecodeError) as ex:
        raise GraverConfigurationError(
            f"graver configuration is unreadable: {config_path}. {ex}"
        ) from ex
    if not isinstance(configuration, dict):
        raise GraverConfigurationError(
            f"graver configuration must contain a JSON object: {config_path}"
        )
    configured_database = configuration.get(DATABASE_CONFIG_KEY)
    if configured_database is not None and not isinstance(configured_database, str):
        raise GraverConfigurationError(
            f"The saved default database is invalid in {config_path}"
        )
    return configuration


def _write_configuration(configuration: dict, config_path: Path) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=config_path.parent, prefix=f".{config_path.name}.", text=True
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "w", encoding="utf-8") as config_file:
            json.dump(configuration, config_file, ensure_ascii=False, indent=2)
            config_file.write("\n")
            config_file.flush()
            os.fsync(config_file.fileno())
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, config_path)
    except OSError as ex:
        raise GraverConfigurationError(
            f"Could not save graver configuration at {config_path}: {ex}"
        ) from ex
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def validate_graver_database(database: str) -> Path:
    """Validate a current graver database without changing it."""
    # Imported lazily because database initialization reuses configuration constants.
    from graver.database import DatabaseInspectionError, validate_current_database

    try:
        return validate_current_database(database)
    except DatabaseInspectionError as ex:
        raise GraverConfigurationError(str(ex)) from ex


def select_default_database(database: str, config_path: Optional[Path] = None) -> Path:
    path = validate_graver_database(database)
    config_path = configuration_path() if config_path is None else Path(config_path)
    configuration = load_configuration(config_path)
    configuration[DATABASE_CONFIG_KEY] = str(path)
    _write_configuration(configuration, config_path)
    return path


def clear_default_database(config_path: Optional[Path] = None) -> bool:
    config_path = configuration_path() if config_path is None else Path(config_path)
    configuration = load_configuration(config_path)
    existed = DATABASE_CONFIG_KEY in configuration
    if existed:
        configuration.pop(DATABASE_CONFIG_KEY)
        _write_configuration(configuration, config_path)
    return existed


def configured_default_database(config_path: Optional[Path] = None) -> Optional[Path]:
    config_path = configuration_path() if config_path is None else Path(config_path)
    configured = load_configuration(config_path).get(DATABASE_CONFIG_KEY)
    if configured is None:
        return None
    return validate_graver_database(configured)


def resolve_database(
    explicit_database: Optional[str],
    environment: Optional[Mapping[str, str]] = None,
    config_path: Optional[Path] = None,
) -> DatabaseSelection:
    """Resolve one database source without falling through invalid preferences."""
    if explicit_database is not None:
        return DatabaseSelection(explicit_database, "command line")
    environment = os.environ if environment is None else environment
    environment_database = environment.get(DATABASE_ENVIRONMENT_VARIABLE)
    if environment_database:
        path = validate_graver_database(environment_database)
        return DatabaseSelection(str(path), DATABASE_ENVIRONMENT_VARIABLE)
    configured = configured_default_database(config_path)
    if configured is not None:
        return DatabaseSelection(str(configured), "saved preference")
    return DatabaseSelection(DEFAULT_DATABASE, "built-in default")
