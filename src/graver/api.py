import importlib.metadata
import json
import logging
import math
import os
import re
import sqlite3
from collections import namedtuple
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from re import Match
from time import sleep
from typing import Any, Dict, List, Optional, cast
from urllib.parse import parse_qsl, urlparse, urlunparse

import cloudscraper25
from bs4 import BeautifulSoup, Tag
from requests.exceptions import RequestException
from tqdm import tqdm

from .constants import FINDAGRAVE_BASE_URL, FINDAGRAVE_ROWS_PER_PAGE


log = logging.getLogger(__name__)


class MemorialException(Exception):
    def __init__(self, message):
        super().__init__(message)


class MemorialParseException(MemorialException):
    def __init__(self, message):
        super().__init__(message)


class MemorialMergedException(MemorialException):
    def __init__(self, message, old_url, new_url):
        super().__init__(message)
        self.old_url = old_url
        self.new_url = new_url


class MemorialRemovedException(MemorialException):
    pass


class NotFound(MemorialException):
    pass


class ResearchTaskNotFound(Exception):
    pass


class MemorialAliasError(Exception):
    pass


RESEARCH_TASK_STATUSES = (
    "unprocessed",
    "researching",
    "ready_for_full_scrape",
    "full_scrape_complete",
    "ready_for_review",
    "completed",
    "unable_to_resolve",
)
MEMORIAL_ALIAS_TYPES = ("merged", "redirected")
MEMORIAL_ALIAS_STATUSES = ("active", "retracted")


class Driver:
    recoverable_errors: Dict[int, str] = {
        408: "Request Timeout",
        429: "Too Many Requests",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout",
        599: "Network Connect Timeout Error",
    }

    def __init__(self, **kwargs) -> None:
        self.num_retries = 0
        self.max_retries: int = int(kwargs.get("max_retries", 5))
        self.retry_ms: int = int(kwargs.get("retry_ms", 500))
        self.session = kwargs.get("session", cloudscraper25.create_scraper())

    def get(self, url: str, **kwargs) -> Any:
        retries = 0
        backoff_sec = self.retry_ms / 1000
        response = self.session.get(url, **kwargs)
        while (
            response.status_code in Driver.recoverable_errors.keys()
            and retries < self.max_retries
        ):
            retries += 1
            timeout_sec = backoff_sec
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if retry_after is not None:
                    try:
                        timeout_sec = float(retry_after)
                    except ValueError:
                        log.warning(
                            "Driver: invalid Retry-After header %r; using "
                            "exponential backoff",
                            retry_after,
                        )
                else:
                    backoff_sec *= 2
                    timeout_sec = backoff_sec
            log.warning(
                f"Driver: [{response.status_code}: {response.reason}] "
                f"{url} -- Retrying ({retries} of {self.max_retries}, "
                f"timeout={timeout_sec}s)"
            )

            sleep(timeout_sec)
            response = self.session.get(url, **kwargs)
        self.num_retries += retries
        return response


@dataclass
class Cemetery:
    """Class for keeping track of a Find A Grave cemetery."""

    cemetery_id: int
    findagrave_url: str
    name: str
    location: str
    coords: str
    num_memorials: int

    def __init__(self, findagrave_url: str, **kwargs) -> None:
        super().__init__()
        self.findagrave_url = findagrave_url
        self.cemetery_id = kwargs.get("cemetery_id", None)
        self.name = kwargs.get("name", None)
        self.location = kwargs.get("location", None)
        self.coords = kwargs.get("coords", None)
        self.num_memorials = kwargs.get("num_memorials", None)
        # behavior args
        self.driver = kwargs.get("driver", Driver())
        self.get = kwargs.get("get", True)
        self.scrape = kwargs.get("scrape", True)
        self.params: dict = {}
        self.search_url = (
            f"{FINDAGRAVE_BASE_URL}"
            f"/cemetery/{self.cemetery_id}"
            f"/memorial-search?"
        )

        if self.get:
            response = self.driver.get(findagrave_url, params=self.params)
            self.soup = BeautifulSoup(response.content, "html.parser")

        if self.scrape:
            self.scrape_cemetery_info()

    def scrape_cemetery_info(self):
        self.scrape_canonical_url()
        self.cemetery_id = int(
            re.match(
                "https://www.findagrave.com/cemetery/([0-9]+)/.*", self.findagrave_url
            ).group(1)
        )
        self.search_url = (
            f"{FINDAGRAVE_BASE_URL}"
            f"/cemetery/{self.cemetery_id}"
            f"/memorial-search?"
        )
        self.scrape_name()
        self.scrape_location()
        self.scrape_coords()
        self.scrape_num_memorials()

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return (
            self.cemetery_id == other.cemetery_id
            and self.findagrave_url == other.findagrave_url
            and self.name == other.name
            and self.location == other.location
            and self.coords == other.coords
        )

    @classmethod
    def from_dict(cls, d):
        return Cemetery(**d, get=False, scrape=False)

    def to_dict(self):
        d = asdict(self)
        return d

    @classmethod
    def create_table(cls, database_name="graves.db"):
        _initialize_database(database_name)

    def save(self, database_name=None) -> "Cemetery":
        timestamp = _utc_now_iso()
        database_name = database_name or os.getenv("DATABASE_NAME", "graves.db")
        _initialize_database(database_name)
        with _connect(database_name) as connection:
            connection.execute(
                """INSERT INTO cemeteries (
                    cemetery_id, url, name, location, coords,
                    first_observed_at, last_observed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(cemetery_id) DO UPDATE SET
                    url = excluded.url,
                    name = excluded.name,
                    location = excluded.location,
                    coords = excluded.coords,
                    last_observed_at = excluded.last_observed_at""",
                (
                    self.cemetery_id,
                    self.findagrave_url,
                    self.name,
                    self.location,
                    self.coords,
                    timestamp,
                    timestamp,
                ),
            )
        return self

    def scrape_canonical_url(self):
        link = self.soup.find("link", rel=re.compile("canonical"))
        if link is not None:
            self.findagrave_url = link["href"]

    def scrape_name(self):
        if (result := self.soup.find("h1", itemprop="name")) is not None:
            self.name = result.get_text().strip()

    def scrape_location(self):
        location = None
        if (result := self.soup.find("span", itemprop="addressLocality")) is not None:
            locality = result.get_text().strip()
            if (result := self.soup.find("span", itemprop="addressRegion")) is not None:
                region = result.get_text().strip()
                if (
                    result := self.soup.find("span", itemprop="addressCountry")
                ) is not None:
                    country = result.get_text().strip()
                    location = locality + ", " + region + ", " + country
        self.location = location

    def scrape_coords(self):
        lat = None
        lon = None
        result = self.soup.find("span", title="Latitude:")
        if result:
            lat = result.get_text()
        result = self.soup.find("span", title="Longitude:")
        if result:
            lon = result.get_text()
        if lat and lon:
            self.coords = lat + "," + lon

    def scrape_num_memorials(self):
        count = 0
        if (div := self.soup.find("div", id="MemorialsAll")) is not None:
            if (ul := div.find("ul")) is not None:
                if (a := ul.find("a")) is not None:
                    count = re.match("View Memorials ([0-9,]+)", a.get_text()).group(1)
                    count = int(count.replace(",", ""))
        self.num_memorials = count


SUMMARY_FIELDS = (
    "memorial_id",
    "findagrave_url",
    "prefix",
    "name",
    "suffix",
    "nickname",
    "maiden_name",
    "famous",
    "veteran",
    "birth",
    "death",
    "memorial_type",
    "cemetery_id",
    "burial_place",
    "plot",
)
FULL_ONLY_FIELDS = (
    "original_name",
    "birth_place",
    "death_place",
    "coords",
    "has_bio",
    "date_added",
)
FULL_FIELDS = SUMMARY_FIELDS + FULL_ONLY_FIELDS


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _connect(database_name: str) -> sqlite3.Connection:
    connection = sqlite3.connect(database_name)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _package_version() -> str:
    try:
        return importlib.metadata.version("graver")
    except importlib.metadata.PackageNotFoundError:  # pragma: no cover
        return "unknown"


def _create_graves_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """CREATE TABLE IF NOT EXISTS graves
            (
                memorial_id INTEGER PRIMARY KEY,
                findagrave_url TEXT,
                prefix TEXT,
                name TEXT,
                suffix TEXT,
                nickname TEXT,
                maiden_name TEXT,
                original_name TEXT,
                famous BOOL,
                veteran BOOL,
                birth TEXT,
                birth_place TEXT,
                death TEXT,
                death_place TEXT,
                memorial_type TEXT,
                cemetery_id INTEGER,
                burial_place TEXT,
                plot TEXT,
                coords TEXT,
                has_bio BOOL,
                date_added TEXT,
                detail_level TEXT CHECK (detail_level IN ('summary', 'full')),
                summary_fetched_at TEXT,
                full_fetched_at TEXT
            )"""
    )


def _migrate_graves_table(connection: sqlite3.Connection) -> None:
    grave_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(graves)").fetchall()
    }
    grave_migrations = {
        "cemetery_id": "INTEGER",
        "date_added": "TEXT",
        "detail_level": "TEXT CHECK (detail_level IN ('summary', 'full'))",
        "summary_fetched_at": "TEXT",
        "full_fetched_at": "TEXT",
    }
    for column_name, column_type in grave_migrations.items():
        if column_name not in grave_columns:
            connection.execute(
                f"ALTER TABLE graves ADD COLUMN {column_name} {column_type}"
            )


def _create_cemeteries_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """CREATE TABLE IF NOT EXISTS cemeteries
            (
                cemetery_id INTEGER PRIMARY KEY,
                url TEXT,
                name TEXT,
                location TEXT,
                coords TEXT,
                first_observed_at TEXT,
                last_observed_at TEXT
            )"""
    )


def _migrate_cemeteries_table(connection: sqlite3.Connection) -> None:
    cemetery_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(cemeteries)").fetchall()
    }
    for column_name in ("first_observed_at", "last_observed_at"):
        if column_name not in cemetery_columns:
            connection.execute(f"ALTER TABLE cemeteries ADD COLUMN {column_name} TEXT")


def _create_research_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """CREATE TABLE IF NOT EXISTS memorial_observations
            (
                observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                memorial_id INTEGER NOT NULL,
                cemetery_id INTEGER,
                acquisition_level TEXT NOT NULL
                    CHECK (acquisition_level IN ('summary', 'full')),
                observed_at TEXT NOT NULL,
                fetch_outcome TEXT NOT NULL,
                parser_version TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                FOREIGN KEY (memorial_id) REFERENCES graves(memorial_id),
                FOREIGN KEY (cemetery_id) REFERENCES cemeteries(cemetery_id)
            )"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS research_tasks
            (
                memorial_id INTEGER PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'unprocessed' CHECK (status IN (
                    'unprocessed',
                    'researching',
                    'ready_for_full_scrape',
                    'full_scrape_complete',
                    'ready_for_review',
                    'completed',
                    'unable_to_resolve'
                )),
                priority INTEGER NOT NULL DEFAULT 0
                    CHECK (typeof(priority) = 'integer'),
                owner TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_activity_at TEXT NOT NULL,
                review_note TEXT,
                FOREIGN KEY (memorial_id) REFERENCES graves(memorial_id)
            )"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS memorial_aliases
            (
                source_memorial_id INTEGER PRIMARY KEY,
                target_memorial_id INTEGER NOT NULL,
                alias_type TEXT NOT NULL CHECK (alias_type IN ('merged', 'redirected')),
                source_url TEXT,
                target_url TEXT,
                status TEXT NOT NULL CHECK (status IN ('active', 'retracted')),
                first_observed_at TEXT NOT NULL,
                last_observed_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CHECK (source_memorial_id <> target_memorial_id),
                FOREIGN KEY (source_memorial_id) REFERENCES graves(memorial_id)
            )"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS memorial_alias_observations
            (
                observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_memorial_id INTEGER NOT NULL,
                target_memorial_id INTEGER NOT NULL,
                alias_type TEXT NOT NULL CHECK (alias_type IN ('merged', 'redirected')),
                event_type TEXT NOT NULL CHECK (event_type IN ('observed', 'changed', 'retracted')),
                observed_at TEXT NOT NULL,
                source_url TEXT,
                target_url TEXT,
                parser_version TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                CHECK (source_memorial_id <> target_memorial_id),
                FOREIGN KEY (source_memorial_id) REFERENCES graves(memorial_id)
            )"""
    )
    connection.execute(
        """CREATE TRIGGER IF NOT EXISTS memorial_observations_no_update
            BEFORE UPDATE ON memorial_observations
            BEGIN
                SELECT RAISE(ABORT, 'memorial observations are immutable');
            END"""
    )
    connection.execute(
        """CREATE TRIGGER IF NOT EXISTS memorial_observations_no_delete
            BEFORE DELETE ON memorial_observations
            BEGIN
                SELECT RAISE(ABORT, 'memorial observations are immutable');
            END"""
    )
    for action in ("UPDATE", "DELETE"):
        connection.execute(
            f"""CREATE TRIGGER IF NOT EXISTS memorial_alias_observations_no_{action.lower()}
                BEFORE {action} ON memorial_alias_observations
                BEGIN
                    SELECT RAISE(ABORT, 'memorial alias observations are immutable');
                END"""
        )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_graves_cemetery_id ON graves(cemetery_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_memorial_observations_memorial_id "
        "ON memorial_observations(memorial_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_memorial_observations_cemetery_id "
        "ON memorial_observations(cemetery_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_research_tasks_status_priority "
        "ON research_tasks(status, priority DESC, created_at)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_memorial_aliases_target_status "
        "ON memorial_aliases(target_memorial_id, status)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_memorial_alias_observations_source "
        "ON memorial_alias_observations(source_memorial_id, observed_at)"
    )


def _create_current_schema(connection: sqlite3.Connection) -> None:
    """Create the complete current schema without performing legacy migrations."""
    _create_graves_table(connection)
    _create_cemeteries_table(connection)
    _create_research_schema(connection)


def _initialize_database(database_name="graves.db") -> None:
    """Retain implicit creation for writes, but never implicitly migrate."""
    from graver.database import initialize_current_schema, validate_current_database

    if not os.path.exists(database_name):
        with _connect(database_name) as connection:
            initialize_current_schema(connection)
        return
    from graver.database import inspect_database

    inspection = inspect_database(database_name)
    if inspection.state == "empty":
        with _connect(database_name) as connection:
            initialize_current_schema(connection)
        return
    validate_current_database(database_name)


def _require_current_database(database_name: str) -> None:
    """Require a current existing database for a read without side effects."""
    from graver.database import validate_current_database

    validate_current_database(database_name)


def _save_grave(
    values: dict,
    data_fields: tuple,
    detail_level: str,
    fetched_at_column: str,
    database_name: Optional[str] = None,
    connection: Optional[sqlite3.Connection] = None,
    timestamp: Optional[str] = None,
) -> None:
    database_name = database_name or os.getenv("DATABASE_NAME", "graves.db")
    _initialize_database(database_name)
    timestamp = timestamp or _utc_now_iso()
    parameters = {name: values[name] for name in data_fields}
    parameters.update(detail_level=detail_level, fetched_at=timestamp)
    insert_fields = data_fields + ("detail_level", fetched_at_column)
    placeholders = ", ".join(f":{name}" for name in data_fields)
    placeholders += ", :detail_level, :fetched_at"
    updates = [f"{name} = excluded.{name}" for name in data_fields]
    if detail_level == "summary":
        updates.append(
            "detail_level = CASE WHEN graves.detail_level = 'full' "
            "THEN 'full' ELSE 'summary' END"
        )
    else:
        updates.append("detail_level = 'full'")
    updates.append(f"{fetched_at_column} = excluded.{fetched_at_column}")
    sql = (
        f"INSERT INTO graves ({', '.join(insert_fields)}) "
        f"VALUES ({placeholders}) "
        "ON CONFLICT(memorial_id) DO UPDATE SET "
        f"{', '.join(updates)}"
    )
    payload = json.dumps(
        {name: values[name] for name in data_fields}, ensure_ascii=False
    )

    def persist(active_connection: sqlite3.Connection) -> None:
        active_connection.execute(sql, parameters)
        if values["cemetery_id"] is not None:
            active_connection.execute(
                """INSERT INTO cemeteries (
                    cemetery_id, first_observed_at, last_observed_at
                ) VALUES (?, ?, ?)
                ON CONFLICT(cemetery_id) DO UPDATE SET
                    last_observed_at = excluded.last_observed_at""",
                (values["cemetery_id"], timestamp, timestamp),
            )
        active_connection.execute(
            """INSERT INTO memorial_observations (
                memorial_id, cemetery_id, acquisition_level, observed_at,
                fetch_outcome, parser_version, payload_json
            ) VALUES (?, ?, ?, ?, 'success', ?, ?)""",
            (
                values["memorial_id"],
                values["cemetery_id"],
                detail_level,
                timestamp,
                _package_version(),
                payload,
            ),
        )

    if connection is not None:
        persist(connection)
    else:
        with _connect(database_name) as active_connection:
            persist(active_connection)


def queue_memorials(
    database_name: str, cemetery_id: Optional[int] = None, priority: int = 0
) -> tuple:
    _initialize_database(database_name)
    timestamp = _utc_now_iso()
    where_clause = (
        "WHERE 1 = 1" if cemetery_id is None else "WHERE cemetery_id = :cemetery_id"
    )
    parameters = {
        "cemetery_id": cemetery_id,
        "priority": priority,
        "timestamp": timestamp,
    }
    with _connect(database_name) as connection:
        eligible = connection.execute(
            f"SELECT COUNT(*) FROM graves {where_clause}", parameters
        ).fetchone()[0]
        cursor = connection.execute(
            f"""INSERT INTO research_tasks (
                memorial_id, status, priority, created_at, updated_at,
                last_activity_at
            )
            SELECT memorial_id, 'unprocessed', :priority, :timestamp,
                   :timestamp, :timestamp
            FROM graves
            {where_clause}
            ON CONFLICT(memorial_id) DO NOTHING""",
            parameters,
        )
        created = cursor.rowcount
    return created, eligible - created


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


def _resolve_alias(
    connection: sqlite3.Connection, memorial_id: int, limit=1000
) -> dict:
    path = [memorial_id]
    seen = {memorial_id}
    current = memorial_id
    for _ in range(limit):
        row = connection.execute(
            "SELECT target_memorial_id FROM memorial_aliases "
            "WHERE source_memorial_id = ? AND status = 'active'",
            (current,),
        ).fetchone()
        if row is None:
            return {"canonical_memorial_id": current, "path": path}
        current = row[0]
        path.append(current)
        if current in seen:
            raise MemorialAliasError(
                f"Alias cycle detected: {' -> '.join(map(str, path))}"
            )
        seen.add(current)
    raise MemorialAliasError("Alias resolution exceeded the safety limit")


def resolve_memorial_alias(database_name: str, memorial_id: int) -> dict:
    _require_current_database(database_name)
    with _connect(database_name) as connection:
        return _resolve_alias(connection, memorial_id)


def _record_alias(
    connection,
    source_memorial_id,
    target_memorial_id,
    alias_type,
    source_url,
    target_url,
    reason,
    timestamp,
    require_change_reason=False,
):
    if alias_type not in MEMORIAL_ALIAS_TYPES:
        raise MemorialAliasError(f"Invalid alias type: {alias_type}")
    if source_memorial_id == target_memorial_id:
        raise MemorialAliasError("A memorial cannot alias itself")
    if (
        connection.execute(
            "SELECT 1 FROM graves WHERE memorial_id = ?", (source_memorial_id,)
        ).fetchone()
        is None
    ):
        raise NotFound(f"Memorial {source_memorial_id} does not exist")
    if source_memorial_id in _resolve_alias(connection, target_memorial_id)["path"]:
        raise MemorialAliasError("Alias would create a cycle")
    current = connection.execute(
        "SELECT target_memorial_id, first_observed_at FROM memorial_aliases WHERE source_memorial_id = ?",
        (source_memorial_id,),
    ).fetchone()
    changed = current is not None and current[0] != target_memorial_id
    if changed and require_change_reason and not reason:
        raise MemorialAliasError("A reason is required when replacing an alias target")
    event_type = "changed" if changed else "observed"
    first_observed_at = current[1] if current is not None else timestamp
    connection.execute(
        """INSERT INTO memorial_aliases (
               source_memorial_id, target_memorial_id, alias_type, source_url,
               target_url, status, first_observed_at, last_observed_at, updated_at
           ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?)
           ON CONFLICT(source_memorial_id) DO UPDATE SET
               target_memorial_id=excluded.target_memorial_id,
               alias_type=excluded.alias_type, source_url=excluded.source_url,
               target_url=excluded.target_url, status='active',
               last_observed_at=excluded.last_observed_at,
               updated_at=excluded.updated_at""",
        (
            source_memorial_id,
            target_memorial_id,
            alias_type,
            source_url,
            target_url,
            first_observed_at,
            timestamp,
            timestamp,
        ),
    )
    payload = {
        "source_memorial_id": source_memorial_id,
        "target_memorial_id": target_memorial_id,
        "alias_type": alias_type,
        "source_url": source_url,
        "target_url": target_url,
        "reason": reason,
    }
    connection.execute(
        """INSERT INTO memorial_alias_observations (
               source_memorial_id, target_memorial_id, alias_type, event_type,
               observed_at, source_url, target_url, parser_version, payload_json
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            source_memorial_id,
            target_memorial_id,
            alias_type,
            event_type,
            timestamp,
            source_url,
            target_url,
            _package_version(),
            json.dumps(payload, ensure_ascii=False),
        ),
    )


def record_memorial_alias(
    database_name: str,
    source_memorial_id: int,
    target_memorial_id: int,
    alias_type: str,
    source_url: Optional[str] = None,
    target_url: Optional[str] = None,
    reason: Optional[str] = None,
) -> dict:
    _initialize_database(database_name)
    with _connect(database_name) as connection:
        _record_alias(
            connection,
            source_memorial_id,
            target_memorial_id,
            alias_type,
            source_url,
            target_url,
            reason,
            _utc_now_iso(),
            True,
        )
    return get_memorial_alias(database_name, source_memorial_id)


def retract_memorial_alias(
    database_name: str, source_memorial_id: int, reason: str
) -> dict:
    if not reason or not reason.strip():
        raise MemorialAliasError("A retraction reason is required")
    _initialize_database(database_name)
    timestamp = _utc_now_iso()
    with _connect(database_name) as connection:
        connection.row_factory = sqlite3.Row
        current = connection.execute(
            "SELECT * FROM memorial_aliases WHERE source_memorial_id=? AND status='active'",
            (source_memorial_id,),
        ).fetchone()
        if current is None:
            raise MemorialAliasError(
                f"Memorial {source_memorial_id} has no active alias"
            )
        connection.execute(
            "UPDATE memorial_aliases SET status='retracted', updated_at=? WHERE source_memorial_id=?",
            (timestamp, source_memorial_id),
        )
        connection.execute(
            """INSERT INTO memorial_alias_observations
               (source_memorial_id,target_memorial_id,alias_type,event_type,observed_at,
                source_url,target_url,parser_version,payload_json)
               VALUES (?,?,?,'retracted',?,?,?,?,?)""",
            (
                source_memorial_id,
                current["target_memorial_id"],
                current["alias_type"],
                timestamp,
                current["source_url"],
                current["target_url"],
                _package_version(),
                json.dumps({"reason": reason}, ensure_ascii=False),
            ),
        )
    return get_memorial_alias(database_name, source_memorial_id)


def alias_history(database_name: str, source_memorial_id: int) -> list:
    _require_current_database(database_name)
    with _connect(database_name) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM memorial_alias_observations WHERE source_memorial_id=? "
            "ORDER BY observed_at, observation_id",
            (source_memorial_id,),
        ).fetchall()
    result = []
    for row in rows:
        item = _row_to_dict(row)
        item["payload"] = json.loads(item.pop("payload_json"))
        result.append(item)
    return result


def reverse_alias_lookup(database_name: str, target_memorial_id: int) -> list:
    _require_current_database(database_name)
    with _connect(database_name) as connection:
        rows = connection.execute(
            "SELECT source_memorial_id FROM memorial_aliases "
            "WHERE target_memorial_id=? AND status='active' "
            "ORDER BY source_memorial_id",
            (target_memorial_id,),
        ).fetchall()
    return [row[0] for row in rows]


def _sources_for_canonical(connection: sqlite3.Connection, canonical_id: int) -> list:
    sources = connection.execute(
        "SELECT source_memorial_id FROM memorial_aliases "
        "WHERE status='active' ORDER BY source_memorial_id"
    ).fetchall()
    return [
        row[0]
        for row in sources
        if _resolve_alias(connection, row[0])["canonical_memorial_id"] == canonical_id
    ]


def list_memorial_aliases(
    database_name: str,
    status: Optional[str] = None,
    target_memorial_id: Optional[int] = None,
    limit: int = 20,
) -> list:
    _require_current_database(database_name)
    if status is not None and status not in MEMORIAL_ALIAS_STATUSES:
        raise MemorialAliasError(f"Invalid alias status: {status}")
    if limit < 1:
        raise MemorialAliasError("Limit must be at least 1")
    clauses, params = [], {
        "status": status,
        "target": target_memorial_id,
        "limit": limit,
    }
    if status:
        clauses.append("a.status=:status")
    if target_memorial_id is not None:
        clauses.append("a.target_memorial_id=:target")
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    with _connect(database_name) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            f"""SELECT a.*, sg.name AS source_name, tg.name AS target_name,
                       CASE WHEN tg.memorial_id IS NULL THEN 0 ELSE 1 END AS target_exists_locally
                FROM memorial_aliases a JOIN graves sg ON sg.memorial_id=a.source_memorial_id
                LEFT JOIN graves tg ON tg.memorial_id=a.target_memorial_id {where}
                ORDER BY a.source_memorial_id LIMIT :limit""",
            params,
        ).fetchall()
        results = []
        for row in rows:
            item = _row_to_dict(row)
            resolution = _resolve_alias(connection, item["source_memorial_id"])
            item["alias_canonical_id"] = resolution["canonical_memorial_id"]
            item["alias_path"] = resolution["path"]
            results.append(item)
    return results


def get_memorial_alias(database_name: str, memorial_id: int) -> dict:
    _require_current_database(database_name)
    history = alias_history(database_name, memorial_id)
    with _connect(database_name) as connection:
        connection.row_factory = sqlite3.Row
        current = connection.execute(
            "SELECT * FROM memorial_aliases WHERE source_memorial_id=?", (memorial_id,)
        ).fetchone()
        if current is None and not history:
            raise NotFound(f"Memorial {memorial_id} has no alias information")
        resolution = _resolve_alias(connection, memorial_id)
        path_info = []
        for item_id in resolution["path"]:
            grave = connection.execute(
                "SELECT * FROM graves WHERE memorial_id=?", (item_id,)
            ).fetchone()
            task = connection.execute(
                "SELECT * FROM research_tasks WHERE memorial_id=?", (item_id,)
            ).fetchone()
            path_info.append(
                {
                    "memorial_id": item_id,
                    "grave": _row_to_dict(grave) if grave else None,
                    "task": _row_to_dict(task) if task else None,
                }
            )
    return {
        "current": _row_to_dict(current) if current else None,
        **resolution,
        "path_records": path_info,
        "history": history,
    }


def list_research_tasks(
    database_name: str,
    status: Optional[str] = None,
    cemetery_id: Optional[int] = None,
    limit: int = 20,
) -> list:
    _require_current_database(database_name)
    if status is not None and status not in RESEARCH_TASK_STATUSES:
        raise ValueError(f"Invalid task status: {status}")
    if limit < 1:
        raise ValueError("Limit must be at least 1")
    clauses = []
    parameters = {"status": status, "cemetery_id": cemetery_id, "limit": limit}
    if status is not None:
        clauses.append("t.status = :status")
    if cemetery_id is not None:
        clauses.append("g.cemetery_id = :cemetery_id")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with _connect(database_name) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            f"""SELECT g.memorial_id, g.name, g.birth, g.death,
                       g.cemetery_id, g.detail_level, t.status, t.priority,
                       t.owner, t.last_activity_at,
                       a.target_memorial_id AS alias_target_id,
                       a.status AS alias_status
                FROM research_tasks AS t
                JOIN graves AS g ON g.memorial_id = t.memorial_id
                LEFT JOIN memorial_aliases AS a
                  ON a.source_memorial_id = g.memorial_id AND a.status = 'active'
                {where}
                ORDER BY t.priority DESC, t.last_activity_at ASC,
                         g.memorial_id ASC
                LIMIT :limit""",
            parameters,
        ).fetchall()
        results = []
        for row in rows:
            item = _row_to_dict(row)
            resolution = _resolve_alias(connection, item["memorial_id"])
            item["alias_canonical_id"] = resolution["canonical_memorial_id"]
            item["alias_path"] = resolution["path"]
            results.append(item)
    return results


def show_research_task(database_name: str, memorial_id: int) -> dict:
    _require_current_database(database_name)
    with _connect(database_name) as connection:
        connection.row_factory = sqlite3.Row
        grave = connection.execute(
            "SELECT * FROM graves WHERE memorial_id = ?", (memorial_id,)
        ).fetchone()
        if grave is None:
            raise NotFound(f"Memorial {memorial_id} does not exist")
        task = connection.execute(
            "SELECT * FROM research_tasks WHERE memorial_id = ?", (memorial_id,)
        ).fetchone()
        if task is None:
            raise ResearchTaskNotFound(f"Research task {memorial_id} does not exist")
        cemetery = None
        if grave["cemetery_id"] is not None:
            cemetery = connection.execute(
                "SELECT * FROM cemeteries WHERE cemetery_id = ?",
                (grave["cemetery_id"],),
            ).fetchone()
        observations = connection.execute(
            """SELECT observation_id, memorial_id, cemetery_id,
                      acquisition_level, observed_at, fetch_outcome,
                      parser_version, payload_json
               FROM memorial_observations WHERE memorial_id = ?
               ORDER BY observed_at ASC, observation_id ASC""",
            (memorial_id,),
        ).fetchall()
    observation_dicts = []
    for row in observations:
        observation = _row_to_dict(row)
        observation["payload"] = json.loads(observation.pop("payload_json"))
        observation_dicts.append(observation)
    resolution = resolve_memorial_alias(database_name, memorial_id)
    canonical_id = resolution["canonical_memorial_id"]
    with _connect(database_name) as connection:
        canonical_grave = (
            connection.execute(
                "SELECT 1 FROM graves WHERE memorial_id=?", (canonical_id,)
            ).fetchone()
            is not None
        )
        canonical_task = (
            connection.execute(
                "SELECT 1 FROM research_tasks WHERE memorial_id=?", (canonical_id,)
            ).fetchone()
            is not None
        )
        related_sources = [
            source_id
            for source_id in _sources_for_canonical(connection, canonical_id)
            if source_id != memorial_id
        ]
    return {
        "task": _row_to_dict(task),
        "grave": _row_to_dict(grave),
        "cemetery": _row_to_dict(cemetery) if cemetery is not None else None,
        "observations": observation_dicts,
        "alias": {
            "is_active_source": len(resolution["path"]) > 1,
            **resolution,
            "canonical_target_exists": canonical_grave,
            "canonical_target_has_task": canonical_task,
            "other_active_sources": related_sources,
        },
    }


def update_research_task(
    database_name: str,
    memorial_id: int,
    status: Optional[str] = None,
    priority: Optional[int] = None,
    owner: Optional[str] = None,
    review_note: Optional[str] = None,
) -> dict:
    _initialize_database(database_name)
    if status is not None and status not in RESEARCH_TASK_STATUSES:
        raise ValueError(f"Invalid task status: {status}")
    requested = {
        key: value
        for key, value in {
            "status": status,
            "priority": priority,
            "owner": owner,
            "review_note": review_note,
        }.items()
        if value is not None
    }
    if not requested:
        raise ValueError("At least one task change is required")
    with _connect(database_name) as connection:
        connection.row_factory = sqlite3.Row
        current = connection.execute(
            "SELECT * FROM research_tasks WHERE memorial_id = ?", (memorial_id,)
        ).fetchone()
        if current is None:
            raise ResearchTaskNotFound(f"Research task {memorial_id} does not exist")
        changed = {
            key: value for key, value in requested.items() if current[key] != value
        }
        if changed:
            timestamp = _utc_now_iso()
            changed["updated_at"] = timestamp
            if "status" in changed or "review_note" in changed:
                changed["last_activity_at"] = timestamp
            assignments = ", ".join(f"{key} = :{key}" for key in changed)
            connection.execute(
                f"UPDATE research_tasks SET {assignments} WHERE memorial_id = :memorial_id",
                {**changed, "memorial_id": memorial_id},
            )
        result = connection.execute(
            "SELECT * FROM research_tasks WHERE memorial_id = ?", (memorial_id,)
        ).fetchone()
    return _row_to_dict(result)


def save_completed_task_scrape(
    database_name: str, requested_memorial_id: int, memorial: "Memorial"
) -> dict:
    if memorial.memorial_id != requested_memorial_id:
        raise ValueError(
            f"Requested memorial {requested_memorial_id}, but parsed {memorial.memorial_id}"
        )
    _initialize_database(database_name)
    timestamp = _utc_now_iso()
    with _connect(database_name) as connection:
        task = connection.execute(
            "SELECT status FROM research_tasks WHERE memorial_id = ?",
            (requested_memorial_id,),
        ).fetchone()
        if task is None:
            raise ResearchTaskNotFound(
                f"Research task {requested_memorial_id} does not exist"
            )
        if task[0] != "ready_for_full_scrape":
            raise ValueError("Task is not ready for a full scrape")
        memorial.save(
            database_name=database_name, connection=connection, timestamp=timestamp
        )
        connection.execute(
            """UPDATE research_tasks
               SET status = 'full_scrape_complete', updated_at = ?,
                   last_activity_at = ? WHERE memorial_id = ?""",
            (timestamp, timestamp, requested_memorial_id),
        )
    return {
        "memorial_id": requested_memorial_id,
        "status": "full_scrape_complete",
        "full_observed_at": timestamp,
    }


def record_failed_task_scrape(
    database_name: str,
    memorial_id: int,
    attempted_url: str,
    exception: Exception,
) -> str:
    _initialize_database(database_name)
    timestamp = _utc_now_iso()
    error_message = " ".join(str(exception).split())[:500]
    payload = json.dumps(
        {
            "attempted_url": attempted_url,
            "exception_type": type(exception).__name__,
            "error_message": error_message,
        },
        ensure_ascii=False,
    )
    with _connect(database_name) as connection:
        row = connection.execute(
            """SELECT g.cemetery_id, t.status
               FROM graves AS g JOIN research_tasks AS t
                 ON t.memorial_id = g.memorial_id
               WHERE g.memorial_id = ?""",
            (memorial_id,),
        ).fetchone()
        if row is None:
            raise ResearchTaskNotFound(f"Research task {memorial_id} does not exist")
        cemetery_id, status = row
        if status != "ready_for_full_scrape":
            raise ValueError("Task is not ready for a full scrape")
        if cemetery_id is not None:
            connection.execute(
                """INSERT INTO cemeteries (
                       cemetery_id, first_observed_at, last_observed_at
                   ) VALUES (?, ?, ?)
                   ON CONFLICT(cemetery_id) DO UPDATE SET
                       last_observed_at = excluded.last_observed_at""",
                (cemetery_id, timestamp, timestamp),
            )
        connection.execute(
            """INSERT INTO memorial_observations (
                   memorial_id, cemetery_id, acquisition_level, observed_at,
                   fetch_outcome, parser_version, payload_json
               ) VALUES (?, ?, 'full', ?, 'failure', ?, ?)""",
            (memorial_id, cemetery_id, timestamp, _package_version(), payload),
        )
        connection.execute(
            """UPDATE research_tasks SET updated_at = ?, last_activity_at = ?
               WHERE memorial_id = ?""",
            (timestamp, timestamp, memorial_id),
        )
    return timestamp


def record_merged_task_scrape(
    database_name: str,
    memorial_id: int,
    target_memorial_id: int,
    source_url: str,
    target_url: str,
    exception: Exception,
) -> str:
    """Atomically record an unsuccessful acquisition and its discovered alias."""
    _initialize_database(database_name)
    timestamp = _utc_now_iso()
    error_message = " ".join(str(exception).split())[:500]
    with _connect(database_name) as connection:
        row = connection.execute(
            """SELECT g.cemetery_id, t.status FROM graves g JOIN research_tasks t
               ON t.memorial_id=g.memorial_id WHERE g.memorial_id=?""",
            (memorial_id,),
        ).fetchone()
        if row is None:
            raise ResearchTaskNotFound(f"Research task {memorial_id} does not exist")
        if row[1] != "ready_for_full_scrape":
            raise ValueError("Task is not ready for a full scrape")
        if row[0] is not None:
            connection.execute(
                """INSERT INTO cemeteries
                   (cemetery_id, first_observed_at, last_observed_at)
                   VALUES (?, ?, ?) ON CONFLICT(cemetery_id) DO UPDATE SET
                   last_observed_at=excluded.last_observed_at""",
                (row[0], timestamp, timestamp),
            )
        _record_alias(
            connection,
            memorial_id,
            target_memorial_id,
            "merged",
            source_url,
            target_url,
            None,
            timestamp,
            False,
        )
        connection.execute(
            """INSERT INTO memorial_observations
               (memorial_id,cemetery_id,acquisition_level,observed_at,fetch_outcome,
                parser_version,payload_json) VALUES (?,?,'full',?,'failure',?,?)""",
            (
                memorial_id,
                row[0],
                timestamp,
                _package_version(),
                json.dumps(
                    {
                        "attempted_url": source_url,
                        "exception_type": type(exception).__name__,
                        "error_message": error_message,
                        "target_url": target_url,
                        "target_memorial_id": target_memorial_id,
                    },
                    ensure_ascii=False,
                ),
            ),
        )
        connection.execute(
            "UPDATE research_tasks SET updated_at=?, last_activity_at=? WHERE memorial_id=?",
            (timestamp, timestamp, memorial_id),
        )
    return timestamp


@dataclass(frozen=True)
class _MemorialSummaryFields:
    """Fields observable in Find A Grave search results."""

    memorial_id: int
    findagrave_url: str
    prefix: str
    name: str
    suffix: str
    nickname: str
    maiden_name: str
    famous: bool
    veteran: bool
    birth: str
    death: str
    memorial_type: str
    cemetery_id: int
    burial_place: str
    plot: str


@dataclass(frozen=True)
class Memorial(_MemorialSummaryFields):
    """Complete data parsed from an individual Find A Grave memorial page."""

    original_name: str
    birth_place: str
    death_place: str
    coords: str
    has_bio: bool
    date_added: Optional[str] = None

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return (
            self.memorial_id == other.memorial_id
            and self.findagrave_url == other.findagrave_url
            and self.prefix == other.prefix
            and self.name == other.name
            and self.suffix == other.suffix
            and self.nickname == other.nickname
            and self.maiden_name == other.maiden_name
            and self.original_name == other.original_name
            and self.famous == other.famous
            and self.veteran == other.veteran
            and self.birth == other.birth
            and self.birth_place == other.birth_place
            and self.death == other.death
            and self.death_place == other.death_place
            and self.memorial_type == other.memorial_type
            and self.burial_place == other.burial_place
            and self.cemetery_id == other.cemetery_id
            and self.plot == other.plot
            and self.coords == other.coords
            and self.has_bio == other.has_bio
            and self.date_added == other.date_added
        )

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    def to_dict(self):
        d = asdict(self)
        return d

    def to_json(self, **kwargs):
        return json.dumps(self.to_dict(), ensure_ascii=False, **kwargs)

    @staticmethod
    def search(cemetery: Cemetery = cast(Cemetery, None), **kwargs):
        return _SearchWorker(cemetery, **kwargs).search()

    @classmethod
    def create_table(cls, database_name="graves.db"):
        _initialize_database(database_name)

    def save(
        self,
        database_name: Optional[str] = None,
        connection: Optional[sqlite3.Connection] = None,
        timestamp: Optional[str] = None,
    ) -> "Memorial":
        _save_grave(
            self.__dict__,
            FULL_FIELDS,
            "full",
            "full_fetched_at",
            database_name=database_name,
            connection=connection,
            timestamp=timestamp,
        )
        return self

    @classmethod
    def parse(cls, findagrave_url: str, **kwargs):
        return _MemorialParser(findagrave_url, **kwargs).parse()

    @classmethod
    def get_by_id(cls, memorial_id: int):
        dbname = os.getenv("DATABASE_NAME", "graves.db")
        _require_current_database(dbname)
        con = _connect(dbname)
        con.row_factory = sqlite3.Row

        cur = con.cursor()
        cur.execute(
            f"SELECT {', '.join(FULL_FIELDS)} FROM graves WHERE memorial_id=?",
            (memorial_id,),
        )

        record = cur.fetchone()

        if record is None:
            raise NotFound(f"memorial_id={memorial_id} not present in {dbname}")

        memorial = Memorial(**record)  # Row can be unpacked as dict

        con.close()

        return memorial


class _MemorialParser:
    def __init__(self, findagrave_url: str, **kwargs) -> None:
        self.memorial_id = kwargs.get("memorial_id", None)
        self.findagrave_url = findagrave_url
        self.prefix = kwargs.get("prefix", None)
        self.name = kwargs.get("name", None)
        self.suffix = kwargs.get("suffix", None)
        self.nickname = kwargs.get("nickname", None)
        self.maiden_name = kwargs.get("maiden_name", None)
        self.original_name = kwargs.get("original_name", None)
        self.famous = kwargs.get("famous", None)
        self.veteran = kwargs.get("veteran", None)
        self.birth = kwargs.get("birth", None)
        self.birth_place = kwargs.get("birth_place", None)
        self.death = kwargs.get("death", None)
        self.death_place = kwargs.get("death_place", None)
        self.memorial_type = kwargs.get("memorial_type", None)
        self.burial_place = kwargs.get("burial_place", None)
        self.cemetery_id = kwargs.get("cemetery_id", None)
        self.plot = kwargs.get("plot", None)
        self.coords = kwargs.get("coords", None)
        self.has_bio = kwargs.get("has_bio", None)
        self.date_added = kwargs.get("date_added", None)
        # # behavior/instance args
        self.driver = kwargs.get("driver", Driver())
        self.get = kwargs.get("get", True)
        self.scrape = kwargs.get("scrape", True)
        # self.soup: Optional[Tag] = None
        self.soup = None
        self.m: dict = {}

        # Valid URL but not a Memorial
        # if "/memorial/" not in self.findagrave_url:
        #     raise MemorialException(f"Invalid memorial URL: {self.findagrave_url}")

        if self.get:
            try:
                response = self.driver.get(self.findagrave_url)
                self.soup = BeautifulSoup(response.content, "html.parser")

                if response.ok:
                    self.scrape_canonical_url()
                else:
                    if response.status_code == 404:
                        if self.check_removed():
                            msg = f"{self.findagrave_url} has been removed"
                            raise MemorialRemovedException(msg)
                        elif (new_url := self.check_merged()) is not None:
                            msg = (
                                f"{self.findagrave_url} has been merged into {new_url}"
                            )
                            raise MemorialMergedException(
                                msg, self.findagrave_url, new_url
                            )
                        else:
                            response.raise_for_status()
                    else:
                        response.raise_for_status()
            except RequestException as ex:
                raise MemorialParseException(ex) from ex

        if self.scrape:
            self.scrape_page()

    def parse(self):
        pass
        return Memorial(
            memorial_id=self.memorial_id,
            findagrave_url=self.findagrave_url,
            prefix=self.prefix,
            name=self.name,
            suffix=self.suffix,
            nickname=self.nickname,
            maiden_name=self.maiden_name,
            original_name=self.original_name,
            famous=self.famous,
            veteran=self.veteran,
            birth=self.birth,
            birth_place=self.birth_place,
            death=self.death,
            death_place=self.death_place,
            memorial_type=self.memorial_type,
            burial_place=self.burial_place,
            cemetery_id=self.cemetery_id,
            plot=self.plot,
            coords=self.coords,
            has_bio=self.has_bio,
            date_added=self.date_added,
        )

    def check_removed(self):
        popup = self.soup.find("div", class_="jumbotron text-center")
        if popup is not None:
            if "This memorial has been removed." in popup.get_text(strip=True):
                return True
        return False

    def check_merged(self) -> Optional[str]:
        merged_url: Optional[str] = None
        if self.soup is not None:
            popup = cast(Tag, self.soup.find("div", class_="jumbotron text-center"))
            if popup is not None:
                if "Memorial has been merged" in popup.get_text(strip=True):
                    for p in popup.find_all("p"):
                        anchor = p.find("a")
                        if anchor is not None:
                            new_path: str = p.find("a")["href"]
                            parsed = urlparse(self.findagrave_url)
                            merged_url = urlunparse(parsed._replace(path=new_path))
        return merged_url

    def scrape_canonical_url(self):
        self.findagrave_url = self.soup.find("link", rel=re.compile("canonical"))[
            "href"
        ]

    @staticmethod
    def scrape_name(name_tag: Tag, memorial_link: str):
        NameParts = namedtuple(
            "NameParts", "prefix, name, nickname, maiden_name, suffix"
        )
        name = name_tag.get_text()
        name = name.replace("Famous memorial", "")
        name = name.replace("VVeteran", "")
        name = name.strip()

        prefix, suffix = _MemorialParser.get_prefix_suffix(name, memorial_link)
        if prefix is not None:
            name = name.replace(f"{prefix} ", "")
        if suffix is not None:
            name = name.replace(f" {suffix}", "")
        if (nickname := _MemorialParser.get_nickname(name)) is not None:
            name = name.replace(f" \u201c{nickname}\u201d", "")
        if name_tag.i is not None:
            maiden_name = name_tag.i.get_text(strip=True)
            name = name.replace(f" {maiden_name} ", " ")
        else:
            maiden_name = None

        return NameParts(prefix, name, nickname, maiden_name, suffix)

    @staticmethod
    def get_prefix_suffix(name: str, memorial_link: str):
        # simple name is derived from the final path component in a memorial link
        # e.g. /memorial/12345/john-q-smith (simple name is "john q smith")
        log.debug(
            f"in get_prefix_suffix, name=[{name}] memorial_link=[{memorial_link}]"
        )
        prefix = None
        suffix = None

        elements = memorial_link.split("/")
        simple_name = elements[len(elements) - 1]
        full_name_tokens = name.split(" ")
        normalized_simple_name = re.sub(r"[\W_]", "", simple_name).casefold()

        for idx in range(0, len(full_name_tokens)):
            normalized_token = re.sub(r"[\W_]", "", full_name_tokens[idx]).casefold()
            if not normalized_simple_name.startswith(normalized_token):
                if prefix is None:
                    prefix = full_name_tokens[idx]
                else:
                    prefix += f" {full_name_tokens[idx]}"
            else:
                break

        tok = full_name_tokens[len(full_name_tokens) - 1]
        normalized_tok = re.sub(r"[\W_]", "", tok).casefold()
        if not normalized_simple_name.endswith(normalized_tok):
            suffix = full_name_tokens[len(full_name_tokens) - 1]
        return prefix, suffix

    @staticmethod
    def get_nickname(name: str):
        nick = None
        pattern = r"\u201c(.*)\u201d"
        if (match := re.search(pattern, name)) is not None:
            nick = match.group(1)
        return nick

    def scrape_names(self, tag):
        parts = _MemorialParser.scrape_name(tag, self.findagrave_url)
        self.name = parts.name
        self.maiden_name = parts.maiden_name
        self.nickname = parts.nickname
        self.prefix = parts.prefix
        self.suffix = parts.suffix

    def scrape_famous(self, tag):
        if tag.find("span", title="Famous memorial") is not None:
            self.famous = True

    def scrape_veteran(self, tag):
        if tag.find("span", string=re.compile("Veteran")) is not None:
            self.veteran = True

    def scrape_birth_info(self, tag: Tag):
        birth_info = cast(Tag, tag.find_next("dd"))
        self.birth = cast(Tag, birth_info.find("time", itemprop="birthDate")).get_text()
        if (birth_place := birth_info.find("div", itemprop="birthPlace")) is not None:
            self.birth_place = birth_place.get_text(strip=True)

    def scrape_death_info(self, tag: Tag):
        death_info = cast(Tag, tag.find_next("dd"))
        self.death = (
            cast(Tag, death_info.find("span", itemprop="deathDate"))
            .get_text()
            .split("(")[0]
            .strip()
        )
        if (death_place := death_info.find("div", itemprop="deathPlace")) is not None:
            self.death_place = death_place.get_text(strip=True)

    def scrape_coords(self, tag: Tag):
        """Returns Google Map coordinates, if any, as a string 'nn.nnnnnnn,nn.nnnnnn'"""
        latlon = None
        if (
            span := tag.find("span", itemtype=re.compile("https://schema.org/Map"))
        ) is not None:
            anchor: Tag = cast(Tag, span.find("a"))
            href: str = cast(str, anchor["href"])
            # just for fun
            query = urlparse(href).query
            query_args = parse_qsl(query)
            name, latlon = query_args[0]
        self.coords = latlon

    def scrape_burial_info(self, tag: Tag):
        self.memorial_type = tag.get_text(strip=True).replace("Read More", "")

        dd = cast(Tag, tag.find_next("dd"))

        # Coords can exist regardless of burial type (which may be a site bug)
        self.scrape_coords(dd)
        if (cemetery := dd.find("div", itemtype="https://schema.org/Cemetery")) is None:
            if (place := dd.find("span", id="otherPlace")) is not None:
                self.burial_place = place.get_text(strip=True)
        else:
            # Known location
            cemetery = cast(Tag, cemetery)
            self.scrape_cemetery_id(cemetery)
            cemetery_name: str = cemetery.get_text(strip=True)
            cemetery_address = cast(Tag, dd.find("span", itemprop="address")).get_text(
                strip=True
            )
            cemetery_address = cemetery_address.replace(",", ", ")
            self.burial_place = ", ".join([cemetery_name, cemetery_address])

    def scrape_cemetery_id(self, cem: Tag):
        if (href := cast(str, cast(Tag, cem.find("a"))["href"])) is not None:
            match: Optional[Match[str]] = re.search("/([0-9]+)/", href)
            assert match is not None
            self.cemetery_id = int(match.group(1))

    def scrape_plot_info(self, dt: Tag):
        self.plot = cast(Tag, dt.find_next("dd")).get_text(strip=True)

    def scrape_memorial_id(self, dt: Tag):
        dd = cast(Tag, dt.find_next("dd"))
        m_id = cast(Tag, dd.find("span", id="memNumberLabel"))
        self.memorial_id = int(m_id.get_text(strip=True))

    def scrape_vitals(self):
        for div in self.soup.find_all("div"):
            if div.find("h1", id="bio-name"):
                return div

    def scrape_has_bio(self):
        element = self.soup.find("meta", property="og:description")
        if element is not None and not element.get("content", "").startswith(
            "Find a Grave memorial for"
        ):
            self.has_bio = True

    def scrape_date_added(self):
        element = self.soup.find("input", id="addedDate")
        if element is not None:
            value = element.get("value", "")
            self.date_added = value.removeprefix("Added: ") or None

    def scrape_page(self):
        self.scrape_has_bio()
        self.scrape_date_added()

        # Get vital statistics and burial info
        vitals = self.scrape_vitals()
        headline = vitals.find("h1", id="bio-name")
        self.scrape_famous(headline)
        self.scrape_veteran(headline)
        self.scrape_names(headline)
        dt_list = vitals.find("dl").find_all("dt")
        for dt in dt_list:
            text = dt.get_text(strip=True)
            if text.startswith("Original Name"):
                oname = dt.find_next("dd")
                self.original_name = oname.get_text()
            # elif dt.find("span", id="birthLabel") is not None:
            elif text == "Birth":
                self.scrape_birth_info(dt)
            elif text == "Death":
                self.scrape_death_info(dt)
            elif (
                text == "Burial"
                or text.startswith("Cenotaph")
                or text.startswith("Monument")
            ):
                self.scrape_burial_info(dt)
            elif text == "Plot":
                self.scrape_plot_info(dt)
            elif text == "Memorial ID":
                self.scrape_memorial_id(dt)


class _SearchWorker:
    def __init__(  # noqa: max-complexity=23
        self, cemetery: Cemetery = cast(Cemetery, None), **kwargs
    ) -> None:
        self.cemetery: Cemetery = cemetery
        self.params: dict = {}

        self.max_results: int = kwargs.pop("max_results", 0)
        self.page: int = kwargs.get("page", None)
        self.driver: Driver
        self.search_url: str

        if self.cemetery is None:
            self.driver = kwargs.pop("driver", Driver())
            self.search_url = f"{FINDAGRAVE_BASE_URL}/memorial/search?"
            self.add_optional_text_params(
                kwargs, "fulltext", "memorialid", "bio", "tags"
            )
            self.params["firstname"] = kwargs.get("firstname", "")
            self.params["middlename"] = kwargs.get("middlename", "")
            self.params["lastname"] = kwargs.get("lastname", "")
            self.process_birth_year(**kwargs)
            self.process_death_year(**kwargs)
            self.params["location"] = kwargs.get("location", "")
            self.params["locationId"] = kwargs.get("locationId", "")
            self.params["mcid"] = kwargs.get("mcid", "")
            self.params["linkedToName"] = kwargs.get("linkedToName", "")
            self.params["datefilter"] = kwargs.get("datefilter", "")
            self.params["orderby"] = kwargs.get("orderby", "r")
            self.params["plot"] = kwargs.get("plot", "")
            self.process_famous(**kwargs) or self.process_sponsored(**kwargs)
            self.process_no_cemetery(**kwargs)
            self.process_cenotaph(**kwargs) or self.process_monument(**kwargs)
            self.process_veteran(**kwargs)
        else:
            self.driver = cemetery.driver
            self.search_url = cemetery.search_url
            # query params
            self.add_optional_text_params(
                kwargs, "fulltext", "memorialid", "bio", "tags"
            )
            self.params["firstname"] = kwargs.get("firstname", "")
            self.params["middlename"] = kwargs.get("middlename", "")
            self.params["lastname"] = kwargs.get("lastname", "")
            self.params["cemeteryName"] = self.cemetery.name
            self.process_birth_year(**kwargs)
            self.process_death_year(**kwargs)
            self.params["mcid"] = kwargs.get("mcid", "")
            self.params["linkedToName"] = kwargs.get("linkedToName", "")
            # Date added. "all" or n (where n = last n days)
            self.params["datefilter"] = kwargs.get("datefilter", "")
            # orderby: r (random?), n/n- (newest first/oldest first), b/b- (birth),
            # d/d- (death), pl (plot)
            self.params["orderby"] = kwargs.get("orderby", "r")
            self.params["plot"] = kwargs.get("plot", "")
            # famous and sponsored are mutually exclusive
            self.process_famous(**kwargs) or self.process_sponsored(**kwargs)
            # cenotaph and monument are mutually exclusive
            self.process_cenotaph(**kwargs) or self.process_monument(**kwargs)
            self.process_veteran(**kwargs)

        # Memorial types
        # Not buried in a cemetery

        # Include:
        self.process_include_nickname(**kwargs)
        self.process_include_maiden_name(**kwargs)
        self.process_include_titles(**kwargs)
        self.process_exact_name(**kwargs) or self.process_fuzzy_names(**kwargs)

        # Filters
        self.process_photo_filter(**kwargs)
        self.process_gps_filter(**kwargs)
        self.process_flowers(**kwargs)
        self.process_has_plot(**kwargs)

        # get the page requested
        self.process_page(**kwargs)

    def add_optional_text_params(self, kwargs, *names):
        for name in names:
            if value := kwargs.get(name, ""):
                self.params[name] = value

    def process_birth_year(self, **kwargs):
        # date filters are:
        # "unknown" (looks for value="unknown"), "before", "after",
        # or n (i.e. +/- n years)
        if (datefilter := kwargs.get("birthyearfilter", "")) != "unknown":
            self.params["birthyear"] = kwargs.get("birthyear", "")
        self.params["birthyearfilter"] = datefilter
        return True

    def process_death_year(self, **kwargs):
        # date filters are:
        # "unknown" (looks for value="unknown"), "before", "after",
        # or n (i.e. +/- n years)
        if (datefilter := kwargs.get("deathyearfilter", "")) != "unknown":
            self.params["deathyear"] = kwargs.get("deathyear", "")
        self.params["deathyearfilter"] = datefilter
        return True

    def process_no_cemetery(self, **kwargs):
        if self.cemetery is None:
            if "noCemetery" in kwargs:
                # location is mutually exclusive with noCemetery
                self.params.pop("location")
                self.params.pop("locationId")
                self.params["noCemetery"] = str(kwargs.get("noCemetery")).lower()

    def process_famous(self, **kwargs):
        if "famous" in kwargs:
            self.params["famous"] = str(kwargs.get("famous")).lower()
            return True
        return False

    def process_sponsored(self, **kwargs):
        if "sponsored" in kwargs:
            self.params["sponsored"] = str(kwargs.get("sponsored")).lower()
            return True
        return False

    def process_cenotaph(self, **kwargs):
        if "cenotaph" in kwargs:
            self.params["cenotaph"] = str(kwargs.get("cenotaph")).lower()
            return True
        return False

    def process_monument(self, **kwargs):
        if "monument" in kwargs:
            self.params["monument"] = str(kwargs.get("monument")).lower()
            return True
        return False

    def process_veteran(self, **kwargs):
        if "isVeteran" in kwargs:
            self.params["isVeteran"] = str(kwargs.get("isVeteran")).lower()
            return True
        return False

    def process_include_nickname(self, **kwargs):
        if "includeNickName" in kwargs:
            self.params["includeNickName"] = str(kwargs.get("includeNickName")).lower()
            return True
        return False

    def process_include_maiden_name(self, **kwargs):
        if "includeMaidenName" in kwargs:
            self.params["includeMaidenName"] = str(
                kwargs.get("includeMaidenName")
            ).lower()
            return True
        return False

    def process_include_titles(self, **kwargs):
        if "includeTitles" in kwargs:
            self.params["includeTitles"] = str(kwargs.get("includeTitles")).lower()
            return True
        return False

    def process_exact_name(self, **kwargs):
        if "exactName" in kwargs:
            self.params["exactName"] = str(kwargs.get("exactName")).lower()
            return True
        return False

    def process_fuzzy_names(self, **kwargs):
        if "fuzzyNames" in kwargs:
            self.params["fuzzyNames"] = str(kwargs.get("fuzzyNames")).lower()
            return True
        return False

    def process_photo_filter(self, **kwargs):
        # "photos"/"nophotos" (mutex)
        if "photofilter" in kwargs:
            self.params["photofilter"] = kwargs.get("photofilter")
            return True
        return False

    def process_gps_filter(self, **kwargs):
        # "gps"/"nogps"
        if "gpsfilter" in kwargs:
            self.params["gpsfilter"] = kwargs.get("gpsfilter")
            return True
        return False

    def process_flowers(self, **kwargs):
        # "true"/""
        if "flowers" in kwargs:
            self.params["flowers"] = str(kwargs.get("flowers")).lower()
            return True
        return False

    def process_has_plot(self, **kwargs):
        if "hasPlot" in kwargs:
            value = str(kwargs.get("hasPlot")).lower()
            if value == "false":
                self.params.pop("plot")
            self.params["hasPlot"] = value
            return True
        return False

    def process_page(self, **kwargs):
        # page of search results
        if self.page is not None:
            self.params["page"] = self.page
            return True
        return False

    def search(self):
        rs = []
        # Load the first page to learn how many results there may be
        log.debug(f"Search params={self.params}")
        response = self.driver.get(self.search_url, params=self.params)
        soup = BeautifulSoup(response.content, "html.parser")

        # If this query isn't for a specific page, calculate how many
        # pages the results will span
        if self.page is not None:
            count = FINDAGRAVE_ROWS_PER_PAGE
        else:
            count = self.scrape_count(soup)

        # limit results to user specified maximum
        if 0 < self.max_results < count:
            count = self.max_results

        num_pages = math.ceil(count / FINDAGRAVE_ROWS_PER_PAGE)

        disable_progress = bool(os.getenv("TQDM_DISABLE"))
        with tqdm(
            total=count,
            desc="Searching memorials",
            unit="memorial",
            disable=disable_progress,
        ) as progress:
            # scrape the page we already have (page 1)
            results = self.scrape_results_page(soup, max_results=(count - len(rs)))
            rs.extend(results)
            progress.update(len(results))

            # scrape additional pages, if there are any left to get
            for i in range(2, num_pages + 1):
                self.params["page"] = i
                response = self.driver.get(self.search_url, params=self.params)
                soup = BeautifulSoup(response.content, "html.parser")

                results = self.scrape_results_page(soup, max_results=(count - len(rs)))
                rs.extend(results)
                progress.update(len(results))

        return ResultSet(response.request.url, rs)

    def scrape_count(self, soup: BeautifulSoup) -> int:
        count = 0
        if (
            tag := soup.find("h1", string=re.compile("[0-9,]+ matching records? found"))
        ) is not None:
            line = tag.get_text(strip=True)
            match: Optional[Match[str]] = re.match("[0-9,]+", line)
            assert match is not None
            num_str = match.group(0)
            num_str = num_str.replace(",", "")
            count = int(num_str)
        return count

    def scrape_memorial_url(self, tag: Tag, mem: dict) -> Optional[str]:
        path = None
        if (anchor := cast(Tag, tag.find("a"))) is not None:
            path = cast(str, anchor["href"])
            path = f"{FINDAGRAVE_BASE_URL}{path}"
        mem["findagrave_url"] = path
        match: Optional[Match[str]] = re.match(".*/([0-9]+)/.*", path)
        assert match is not None
        mid = match.group(1)
        mem["memorial_id"] = int(mid)
        return path

    def scrape_memorial_type(self, tag: Tag, mem: dict):
        if (h2 := tag.find("h2")) is not None:
            if (button := cast(Tag, h2.find("button"))) is not None:
                if button.get_text() == "Cenotaph":
                    mem["memorial_type"] = "Cenotaph"
                elif button.get_text() == "Monument":
                    mem["memorial_type"] = "Monument"
            else:
                mem["memorial_type"] = "Burial"

    def scrape_memorial_names(self, tag: Tag, mem: dict):
        name_grave = cast(Tag, tag.find("h2", {"class": "name-grave"}))
        # get the full name
        name_tag = cast(Tag, name_grave.find("i", {"class": "pe-2"}))
        parts = _MemorialParser.scrape_name(name_tag, mem["findagrave_url"])
        mem["name"] = parts.name
        mem["maiden_name"] = parts.maiden_name
        mem["suffix"] = parts.suffix
        mem["prefix"] = parts.prefix
        mem["nickname"] = parts.nickname

    def scrape_memorial_dates(self, tag: Tag, mem: dict):
        grave = cast(Tag, tag.find("div", {"class": "memorial-item---grave"}))
        birth_death = cast(
            Tag, grave.find("b", {"class": re.compile("birthDeathDates.*")})
        ).get_text(strip=True)
        # pattern is "date" endash "date"
        dates = birth_death.split(" \u2013 ")
        if len(dates) == 2:
            mem["birth"] = dates[0]
            mem["death"] = dates[1]

    def scrape_memorial_famous(self, tag: Tag, mem: dict) -> None:
        if tag.find("span", title="Famous Memorial") is not None:
            mem["famous"] = True

    def scrape_memorial_veteran(self, tag: Tag, mem: dict):
        if (h2 := cast(Tag, tag.find("h2", {"class": "name-grave"}))) is not None:
            if h2.find("span", title="Veteran") is not None:
                mem["veteran"] = True

    def scrape_memorial_cemetery_info(self, tag, mem):
        if self.cemetery is not None:
            mem["cemetery_id"] = self.cemetery.cemetery_id
            mem["burial_place"] = f"{self.cemetery.name}, {self.cemetery.location}"

        # Cemetery info and optional plot info
        if (form := tag.form) is not None:
            # Get the cemetery path e.g. '/cemetery/12345/the-cemetery-name'
            path = form.get("action")
            cem_name = form.get_text(strip=True)
            if self.cemetery is None:
                mem["cemetery_id"] = int(re.match(".*/([0-9]+)/.*$", path).group(1))
                if (p := form.find_next("p")) is not None:
                    cem_location = p.get_text(strip=True)
                    cem_location = " ".join(cem_location.split())
                    mem["burial_place"] = f"{cem_name}, {cem_location}"
                if (p := p.find_next_sibling("p")) is not None:
                    mem["plot"] = p.get_text(strip=True).replace("Plot info:", "")
        elif tag.p is not None:
            mem["plot"] = tag.p.get_text(strip=True).replace("Plot info: ", "")

    def scrape_results_page(
        self, page_soup: BeautifulSoup, cemetery=None, max_results=0
    ) -> List["MemorialSummary"]:
        divs = page_soup.find_all("div", role="group")
        results: List[MemorialSummary] = []

        for div in divs:
            # mem = {}
            mem = {
                "memorial_id": None,
                "findagrave_url": None,
                "prefix": None,
                "name": None,
                "suffix": None,
                "nickname": None,
                "maiden_name": None,
                "famous": None,
                "veteran": None,
                "birth": None,
                "death": None,
                "memorial_type": None,
                "burial_place": None,
                "cemetery_id": None,
                "plot": None,
            }

            self.scrape_memorial_url(div, mem)
            mem_item_info = div.find("div", {"class": "memorial-item--info"})
            mem_item_grave = div.find("div", {"class": "memorial-item---grave"})
            self.scrape_memorial_type(mem_item_grave, mem)
            self.scrape_memorial_names(mem_item_info, mem)
            self.scrape_memorial_dates(mem_item_info, mem)
            self.scrape_memorial_famous(mem_item_info, mem)
            self.scrape_memorial_veteran(mem_item_info, mem)
            mem_cem_info = div.find("div", {"class": "memorial-item---cemet"})
            self.scrape_memorial_cemetery_info(mem_cem_info, mem)
            results.append(MemorialSummary.from_dict(mem))
            if 0 < max_results == len(results):
                break

        return results


class ResultSet(list):
    """A ResultSet is just a list that keeps track of the object
    that created it."""

    def __init__(self, source, result=()) -> None:
        super(ResultSet, self).__init__(result)
        self.source = source


@dataclass(frozen=True)
class MemorialSummary(_MemorialSummaryFields):
    """Partial memorial data parsed from a search result."""

    @classmethod
    def from_dict(cls, d):
        return cls(**{name: d[name] for name in SUMMARY_FIELDS})

    def to_dict(self):
        d = asdict(self)
        return d

    def to_json(self, **kwargs):
        return json.dumps(self.to_dict(), ensure_ascii=False, **kwargs)

    def save(self) -> "MemorialSummary":
        _save_grave(self.__dict__, SUMMARY_FIELDS, "summary", "summary_fetched_at")
        return self
