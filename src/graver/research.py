"""Internal subject-oriented research task repositories and services."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Optional

import graver.api as legacy_api
from graver.api import (
    RESEARCH_TASK_STATUSES,
    NotFound,
    ResearchTaskNotFound,
    _connect,
    _ensure_subject_for_memorial,
    _initialize_database,
    _record_task_event,
    _resolve_alias,
    _row_to_dict,
    _sources_for_canonical,
    _task_dict_for_memorial,
)
from graver.database import validate_current_database


class _ResearchTaskRepository:
    """Keep subject-task persistence details behind the application service."""

    @staticmethod
    def list_tasks(
        connection: sqlite3.Connection,
        status: Optional[str],
        cemetery_id: Optional[int],
        limit: int,
    ) -> list[sqlite3.Row]:
        clauses = []
        parameters = {"status": status, "cemetery_id": cemetery_id, "limit": limit}
        if status is not None:
            clauses.append("t.status = :status")
        if cemetery_id is not None:
            clauses.append(
                "EXISTS (SELECT 1 FROM subject_memorials filter_sm "
                "JOIN graves filter_g ON filter_g.memorial_id = filter_sm.memorial_id "
                "WHERE filter_sm.subject_id = t.subject_id "
                "AND filter_g.cemetery_id = :cemetery_id)"
            )
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return connection.execute(
            f"""SELECT g.memorial_id, g.name, g.birth, g.death,
                       g.cemetery_id, g.detail_level, t.status, t.priority,
                       t.owner, t.last_activity_at,
                       a.target_memorial_id AS alias_target_id,
                       a.status AS alias_status
                FROM research_tasks AS t
                JOIN (
                    SELECT subject_id, MIN(memorial_id) AS memorial_id
                    FROM subject_memorials GROUP BY subject_id
                ) AS display_sm ON display_sm.subject_id = t.subject_id
                JOIN graves AS g ON g.memorial_id = display_sm.memorial_id
                LEFT JOIN memorial_aliases AS a
                  ON a.source_memorial_id = g.memorial_id AND a.status = 'active'
                {where}
                ORDER BY t.priority DESC, t.last_activity_at ASC,
                         g.memorial_id ASC
                LIMIT :limit""",
            parameters,
        ).fetchall()

    @staticmethod
    def grave(
        connection: sqlite3.Connection, memorial_id: int
    ) -> Optional[sqlite3.Row]:
        return connection.execute(
            "SELECT * FROM graves WHERE memorial_id = ?", (memorial_id,)
        ).fetchone()

    @staticmethod
    def task_for_memorial(
        connection: sqlite3.Connection, memorial_id: int
    ) -> Optional[sqlite3.Row]:
        return connection.execute(
            """SELECT t.* FROM research_tasks AS t
               JOIN subject_memorials AS sm ON sm.subject_id = t.subject_id
               WHERE sm.memorial_id = ?""",
            (memorial_id,),
        ).fetchone()

    @staticmethod
    def task_for_subject(
        connection: sqlite3.Connection, subject_id: str
    ) -> Optional[sqlite3.Row]:
        return connection.execute(
            "SELECT * FROM research_tasks WHERE subject_id = ?", (subject_id,)
        ).fetchone()

    @staticmethod
    def cemetery(
        connection: sqlite3.Connection, cemetery_id: int
    ) -> Optional[sqlite3.Row]:
        return connection.execute(
            "SELECT * FROM cemeteries WHERE cemetery_id = ?", (cemetery_id,)
        ).fetchone()

    @staticmethod
    def observations(
        connection: sqlite3.Connection, memorial_id: int
    ) -> list[sqlite3.Row]:
        return connection.execute(
            """SELECT observation_id, memorial_id, cemetery_id,
                      acquisition_level, observed_at, fetch_outcome,
                      parser_version, payload_json
               FROM memorial_observations WHERE memorial_id = ?
               ORDER BY observed_at ASC, observation_id ASC""",
            (memorial_id,),
        ).fetchall()

    @staticmethod
    def subject_has_task_for_memorial(
        connection: sqlite3.Connection, memorial_id: int
    ) -> bool:
        return (
            connection.execute(
                """SELECT 1 FROM research_tasks AS t
                   JOIN subject_memorials AS sm ON sm.subject_id = t.subject_id
                   WHERE sm.memorial_id = ?""",
                (memorial_id,),
            ).fetchone()
            is not None
        )

    @staticmethod
    def update_task(
        connection: sqlite3.Connection, subject_id: str, changes: dict
    ) -> None:
        assignments = ", ".join(f"{key} = :{key}" for key in changes)
        connection.execute(
            f"UPDATE research_tasks SET {assignments} WHERE subject_id = :subject_id",
            {**changes, "subject_id": subject_id},
        )

    @staticmethod
    def memorial_ids(
        connection: sqlite3.Connection, cemetery_id: Optional[int]
    ) -> list[int]:
        if cemetery_id is None:
            rows = connection.execute(
                "SELECT memorial_id FROM graves ORDER BY memorial_id"
            )
        else:
            rows = connection.execute(
                """SELECT memorial_id FROM graves
                   WHERE cemetery_id = ? ORDER BY memorial_id""",
                (cemetery_id,),
            )
        return [row[0] for row in rows]

    @staticmethod
    def create_task(
        connection: sqlite3.Connection,
        subject_id: str,
        priority: int,
        timestamp: str,
    ) -> bool:
        cursor = connection.execute(
            """INSERT INTO research_tasks (
                   subject_id, status, priority, created_at, updated_at,
                   last_activity_at
               ) VALUES (?, 'unprocessed', ?, ?, ?, ?)
               ON CONFLICT(subject_id) DO NOTHING""",
            (subject_id, priority, timestamp, timestamp, timestamp),
        )
        return bool(cursor.rowcount)


@dataclass(frozen=True)
class ResearchService:
    """Coordinate subject-owned research work for one explicit database."""

    database_name: str

    def resolve_alias(self, memorial_id: int) -> dict:
        """Resolve platform redirect evidence without changing subject membership."""
        return legacy_api.resolve_memorial_alias(self.database_name, memorial_id)

    def list_tasks(
        self,
        status: Optional[str] = None,
        cemetery_id: Optional[int] = None,
        limit: int = 20,
    ) -> list[dict]:
        validate_current_database(self.database_name)
        if status is not None and status not in RESEARCH_TASK_STATUSES:
            raise ValueError(f"Invalid task status: {status}")
        if limit < 1:
            raise ValueError("Limit must be at least 1")
        with _connect(self.database_name) as connection:
            connection.row_factory = sqlite3.Row
            results = []
            for row in _ResearchTaskRepository.list_tasks(
                connection, status, cemetery_id, limit
            ):
                item = _row_to_dict(row)
                resolution = _resolve_alias(connection, item["memorial_id"])
                item["alias_canonical_id"] = resolution["canonical_memorial_id"]
                item["alias_path"] = resolution["path"]
                results.append(item)
        return results

    def show_task(self, memorial_id: int) -> dict:
        validate_current_database(self.database_name)
        with _connect(self.database_name) as connection:
            connection.row_factory = sqlite3.Row
            grave = _ResearchTaskRepository.grave(connection, memorial_id)
            if grave is None:
                raise NotFound(f"Memorial {memorial_id} does not exist")
            task = _ResearchTaskRepository.task_for_memorial(connection, memorial_id)
            if task is None:
                raise ResearchTaskNotFound(
                    f"Research task {memorial_id} does not exist"
                )
            cemetery = (
                _ResearchTaskRepository.cemetery(connection, grave["cemetery_id"])
                if grave["cemetery_id"] is not None
                else None
            )
            observations = _ResearchTaskRepository.observations(connection, memorial_id)
            resolution = _resolve_alias(connection, memorial_id)
            canonical_id = resolution["canonical_memorial_id"]
            canonical_grave = (
                _ResearchTaskRepository.grave(connection, canonical_id) is not None
            )
            canonical_task = _ResearchTaskRepository.subject_has_task_for_memorial(
                connection, canonical_id
            )
            related_sources = [
                source_id
                for source_id in _sources_for_canonical(connection, canonical_id)
                if source_id != memorial_id
            ]
        observation_dicts = []
        for row in observations:
            observation = _row_to_dict(row)
            observation["payload"] = json.loads(observation.pop("payload_json"))
            observation_dicts.append(observation)
        return {
            "task": _task_dict_for_memorial(task, memorial_id),
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

    def update_task(
        self,
        memorial_id: int,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        owner: Optional[str] = None,
        review_note: Optional[str] = None,
    ) -> dict:
        validate_current_database(self.database_name)
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
        with _connect(self.database_name) as connection:
            connection.row_factory = sqlite3.Row
            current = _ResearchTaskRepository.task_for_memorial(connection, memorial_id)
            if current is None:
                raise ResearchTaskNotFound(
                    f"Research task {memorial_id} does not exist"
                )
            changed = {
                key: value for key, value in requested.items() if current[key] != value
            }
            if changed:
                timestamp = legacy_api._utc_now_iso()
                before = _row_to_dict(current)
                changed["updated_at"] = timestamp
                if "status" in changed or "review_note" in changed:
                    changed["last_activity_at"] = timestamp
                _ResearchTaskRepository.update_task(
                    connection, current["subject_id"], changed
                )
                result = _ResearchTaskRepository.task_for_subject(
                    connection, current["subject_id"]
                )
                _record_task_event(
                    connection,
                    current["subject_id"],
                    "task_updated",
                    timestamp,
                    before,
                    _row_to_dict(result),
                    reason="researcher_update",
                )
            else:
                result = current
        return _task_dict_for_memorial(result, memorial_id)

    def queue_memorials(
        self, cemetery_id: Optional[int] = None, priority: int = 0
    ) -> tuple[int, int]:
        _initialize_database(self.database_name)
        timestamp = legacy_api._utc_now_iso()
        with _connect(self.database_name) as connection:
            connection.row_factory = sqlite3.Row
            subject_ids = [
                _ensure_subject_for_memorial(connection, memorial_id, timestamp)
                for memorial_id in _ResearchTaskRepository.memorial_ids(
                    connection, cemetery_id
                )
            ]
            eligible_subjects = list(dict.fromkeys(subject_ids))
            created = 0
            for subject_id in eligible_subjects:
                if not _ResearchTaskRepository.create_task(
                    connection, subject_id, priority, timestamp
                ):
                    continue
                created += 1
                task = _ResearchTaskRepository.task_for_subject(connection, subject_id)
                _record_task_event(
                    connection,
                    subject_id,
                    "task_created",
                    timestamp,
                    None,
                    _row_to_dict(task),
                    reason="queued_for_research",
                )
        return created, len(eligible_subjects) - created

    def complete_enrichment(self, memorial_id: int, memorial: object) -> dict:
        """Persist one successful approved memorial acquisition atomically."""
        return legacy_api.save_completed_task_scrape(
            self.database_name, memorial_id, memorial
        )

    def record_enrichment_failure(
        self, memorial_id: int, attempted_url: str, exception: Exception
    ) -> str:
        """Record one failed approved acquisition without advancing its task."""
        return legacy_api.record_failed_task_scrape(
            self.database_name, memorial_id, attempted_url, exception
        )

    def record_redirect_failure(
        self,
        memorial_id: int,
        target_memorial_id: int,
        source_url: str,
        target_url: str,
        exception: Exception,
    ) -> str:
        """Record redirect evidence discovered during an approved acquisition."""
        return legacy_api.record_merged_task_scrape(
            self.database_name,
            memorial_id,
            target_memorial_id,
            source_url,
            target_url,
            exception,
        )
