"""Local-only experiential adapter for the R2 professional-researcher review.

This module is deliberately not part of graver's installed package or public API.
It uses a disposable database and curated fictional data.  Every researcher action
is nevertheless applied through the real offline evidence application service.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import uuid
import webbrowser
from dataclasses import asdict, dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from graver._sqlite import connect_database
from graver.database import create_database
from graver.evidence import (
    AssessmentUpdate,
    CandidateInput,
    ComparisonSignalInput,
    ConclusionRequest,
    DiscoveryRequest,
    EvidenceError,
    EvidenceService,
    SourceObservationInput,
)

SUBJECT = {
    "name": "Eleanor May Carter",
    "birth": "14 March 1892, Missouri",
    "death": "8 November 1967, Boise, Idaho",
    "burial": "Morris Hill Cemetery, Boise, Idaho",
    "memorial_id": "12345678",
}

FIRST_CANDIDATES = (
    CandidateInput(
        "K1AB-CDE",
        "2026-08-21T16:00:00Z",
        {
            "name": "Eleanor M. Carter",
            "birth": "14 March 1892, St. Louis, Missouri",
            "death": "8 November 1967, Boise, Idaho",
            "burial": "Morris Hill Cemetery, Boise, Idaho",
            "father": "Henry Carter",
            "mother": "Alice Brown Carter",
            "spouse": "William Reed",
            "source_note": "Derivative family-group transcription; original record not linked",
        },
        "https://example.invalid/tree/person/K1AB-CDE",
    ),
    CandidateInput(
        "L2FG-HJK",
        "2026-08-21T16:00:00Z",
        {
            "name": "Eleanor May Carter",
            "birth": "1892, Kansas",
            "death": "1968, Oregon",
            "father": "Thomas Carter",
            "source_note": "User-contributed profile without attached records",
        },
        "https://example.invalid/tree/person/L2FG-HJK",
    ),
)


@dataclass
class ReviewScenario:
    """Own one disposable, deterministic R2 review session."""

    database: str
    subject_id: str
    service: EvidenceService
    candidate_ids: dict[str, str]
    source_ids: dict[str, str]
    refreshed: bool = False

    @classmethod
    def create(cls, directory: Path) -> "ReviewScenario":
        """Create and seed a fresh fictional review case."""
        database = str(create_database(str(directory / "r2-review.db")))
        subject_id = str(uuid.uuid4())
        with connect_database(database) as connection:
            connection.execute(
                "INSERT INTO research_subjects (subject_id, created_at) VALUES (?, ?)",
                (subject_id, "2026-08-21T15:55:00Z"),
            )
            connection.execute(
                """INSERT INTO research_subject_events
                   (subject_id, event_type, occurred_at, reason, after_json)
                   VALUES (?, 'subject_created', ?, 'r2_fixture', ?)""",
                (
                    subject_id,
                    "2026-08-21T15:55:00Z",
                    json.dumps({"subject_id": subject_id}),
                ),
            )
        service = EvidenceService(database)
        memorial = service.record_source_observation(
            SourceObservationInput(
                subject_id,
                "findagrave_memorial",
                "Find a Grave memorial for Eleanor May Carter",
                'Find a Grave, "Eleanor May Carter" (1892–1967), memorial '
                "12345678, Morris Hill Cemetery, Boise, Idaho; retained snapshot "
                "observed 21 August 2026.",
                "2026-08-21T15:58:00Z",
                {
                    "name": "Eleanor May Carter",
                    "birth": "14 March 1892, Missouri",
                    "death": "8 November 1967, Boise, Idaho",
                    "burial": "Morris Hill Cemetery, Boise, Idaho",
                    "father": "Thomas Carter",
                },
                {
                    "provider": "Find a Grave",
                    "memorial_id": "12345678",
                    "capture_scope": "displayed memorial fields; images and underlying records not collected",
                },
                "R2 fixture",
            )
        )
        result = service.record_discovery(
            DiscoveryRequest(
                subject_id,
                "familysearch-shaped-fixture",
                {"name": "Eleanor May Carter", "birth_year": 1892},
                "2026-08-21T16:00:00Z",
                "2026-08-21T16:00:00Z",
                "fixture-search/1",
                FIRST_CANDIDATES,
            )
        )
        candidate_ids = {
            snapshot.provider_profile_id: snapshot.candidate_id
            for snapshot in result.snapshots
        }
        for snapshot in result.snapshots:
            service.record_comparison(
                snapshot.snapshot_id,
                "fixture-ordering/1",
                _signals(
                    snapshot.provider_profile_id,
                    memorial.observation_id,
                    snapshot.snapshot_id,
                ),
            )
        return cls(
            database,
            subject_id,
            service,
            candidate_ids,
            {"memorial": memorial.observation_id},
        )

    @property
    def primary_id(self) -> str:
        return self.candidate_ids["K1AB-CDE"]

    def defer(self, actor: str, values: dict[str, Any]) -> None:
        """Record the required negative search, question, and deferral."""
        current = self.service.get_assessment(self.primary_id)
        self.service.update_assessment(
            AssessmentUpdate(
                self.primary_id,
                current.version,
                "deferred",
                actor,
                values.get("reason", ""),
                values.get("notes", ""),
                negative_searches=(
                    {
                        "repository": values.get("repository", ""),
                        "collection": values.get("collection", ""),
                        "coverage": values.get("coverage", ""),
                        "jurisdiction": values.get("jurisdiction", ""),
                        "searched_at": values.get("searched_at", ""),
                        "variants": [
                            item.strip()
                            for item in values.get("variants", "").split(";")
                            if item.strip()
                        ],
                        "method": values.get("method", ""),
                        "result": values.get("result", ""),
                        "limitation": values.get("limitation", ""),
                    },
                ),
                unresolved_questions=(values.get("question", ""),),
                follow_up_condition=values.get("follow_up", ""),
            )
        )

    def refresh(self) -> None:
        """Record a later run where one candidate changed and one is absent."""
        if self.refreshed:
            return
        result = self.service.record_discovery(
            DiscoveryRequest(
                self.subject_id,
                "familysearch-shaped-fixture",
                {"name": "Eleanor May Carter", "birth_year": 1892},
                "2026-08-28T16:00:00Z",
                "2026-08-28T16:00:00Z",
                "fixture-search/1",
                (
                    CandidateInput(
                        "K1AB-CDE",
                        "2026-08-28T16:00:00Z",
                        {
                            **FIRST_CANDIDATES[0].assertions,
                            "new_record": "1912 marriage record names Henry Carter and William Reed",
                            "record_note": "Original marriage register image; informant not stated",
                        },
                        FIRST_CANDIDATES[0].profile_url,
                    ),
                ),
            )
        )
        self.service.record_comparison(
            result.snapshots[0].snapshot_id,
            "fixture-ordering/1",
            _signals(
                "K1AB-CDE",
                self.source_ids["memorial"],
                result.snapshots[0].snapshot_id,
            ),
        )
        marriage = self.service.record_source_observation(
            SourceObservationInput(
                self.subject_id,
                "marriage_register",
                "Ada County marriage register entry for Eleanor Carter and William Reed",
                "Ada County, Idaho, marriage register 7:142, Carter–Reed, 12 June 1912; "
                "fictional retained record observation, 28 August 2026.",
                "2026-08-28T16:10:00Z",
                {
                    "bride": "Eleanor Carter",
                    "groom": "William Reed",
                    "father": "Henry Carter",
                },
                {"record_type": "original register image", "informant": "not stated"},
                "R2 fixture",
            )
        )
        death = self.service.record_source_observation(
            SourceObservationInput(
                self.subject_id,
                "death_certificate",
                "Idaho death certificate for Eleanor May Reed",
                "Idaho Department of Health, death certificate 1967-009, Eleanor May Reed, "
                "8 November 1967; fictional retained record observation, 30 August 2026.",
                "2026-08-30T14:00:00Z",
                {
                    "decedent": "Eleanor May Reed",
                    "father": "Henry Carter",
                    "spouse": "William Reed",
                    "informant": "William Reed",
                },
                {
                    "record_type": "death certificate",
                    "informant": "William Reed",
                    "dependence_note": "The spouse supplied the information; repeated assertions are not treated as independent corroboration.",
                },
                "R2 fixture",
            )
        )
        self.source_ids.update(
            {"marriage": marriage.observation_id, "death": death.observation_id}
        )
        self.refreshed = True

    def reopen(self, actor: str, values: dict[str, Any]) -> None:
        """Reopen the deferred assessment and link its prior event."""
        current = self.service.get_assessment(self.primary_id)
        event_id = self.service.assessment_history(self.primary_id)[-1]["event_id"]
        self.service.update_assessment(
            AssessmentUpdate(
                self.primary_id,
                current.version,
                "reopened",
                actor,
                values.get("reason", ""),
                values.get("notes", ""),
                reopens_record_id=event_id,
            )
        )

    def conclude_unresolved(self, actor: str, values: dict[str, Any]) -> None:
        """Append the first, deliberately unresolved conclusion."""
        if self.service.conclusion_history(self.primary_id):
            return
        selected = values.get("evidence_ids", [])
        if not selected:
            raise ValueError("Select at least one inspectable evidence record")
        references = []
        for record_id in selected:
            observation = self.service.get_source_observation(record_id)
            references.append(
                {
                    "record_id": observation.observation_id,
                    "observed_at": observation.observed_at,
                    "assertions": sorted(observation.assertions),
                }
            )
        self.service.record_conclusion(
            ConclusionRequest(
                self.primary_id,
                "unresolved",
                actor,
                values.get("analysis", ""),
                tuple(references),
                ({"fact_type": "father", "treatment": "unresolved"},),
            )
        )

    def supersede(self, actor: str, values: dict[str, Any]) -> None:
        """Append a same-person conclusion without editing the earlier decision."""
        history = self.service.conclusion_history(self.primary_id)
        if len(history) != 1:
            raise ValueError("Record the unresolved conclusion before superseding it")
        selected = values.get("evidence_ids", [])
        if len(selected) < 2:
            raise ValueError("Select at least two inspectable evidence records")
        references = []
        for record_id in selected:
            observation = self.service.get_source_observation(record_id)
            references.append(
                {
                    "record_id": observation.observation_id,
                    "observed_at": observation.observed_at,
                    "assertions": sorted(observation.assertions),
                }
            )
        conflict_treatment = values.get("conflict_treatment", "").strip()
        if not conflict_treatment:
            raise ValueError("Explain how the material father conflict was treated")
        self.service.record_conclusion(
            ConclusionRequest(
                self.primary_id,
                "accepted",
                actor,
                values.get("analysis", ""),
                tuple(references),
                (
                    {
                        "fact_type": "father",
                        "treatment": conflict_treatment,
                    },
                ),
                history[0].conclusion_id,
            )
        )

    def state(self) -> dict[str, Any]:
        """Build the experimental review view model from service results."""
        ranked = self.service.ranked_candidates(self.subject_id, "fixture-ordering/1")
        candidates = []
        for item in ranked:
            snapshots = self.service.list_snapshots(item.candidate_id)
            assessment = self.service.get_assessment(item.candidate_id)
            candidates.append(
                {
                    **asdict(item),
                    "signals": [asdict(signal) for signal in item.signals],
                    "latest": asdict(snapshots[-1]),
                    "snapshots": [asdict(snapshot) for snapshot in snapshots],
                    "assessment": asdict(assessment),
                    "assessment_history": list(
                        self.service.assessment_history(item.candidate_id)
                    ),
                    "conclusions": [
                        asdict(value)
                        for value in self.service.conclusion_history(item.candidate_id)
                    ],
                    "present_in_latest_run": not (
                        self.refreshed and item.provider_profile_id == "L2FG-HJK"
                    ),
                }
            )
        return {
            "subject": SUBJECT,
            "candidates": candidates,
            "sources": [
                asdict(self.service.get_source_observation(record_id))
                for record_id in self.source_ids.values()
            ],
            "change_summary": self._change_summary(),
            "refreshed": self.refreshed,
            "notice": "Fictional offline review case; no live provider request is made.",
        }

    def _change_summary(self) -> list[dict[str, Any]]:
        """Describe changed candidate values without hiding retained snapshots."""
        snapshots = self.service.list_snapshots(self.primary_id)
        if len(snapshots) < 2:
            return []
        before, after = snapshots[-2], snapshots[-1]
        fields = sorted(set(before.assertions) | set(after.assertions))
        return [
            {
                "field": field,
                "before": before.assertions.get(field),
                "after": after.assertions.get(field),
                "before_snapshot": before.snapshot_id,
                "after_snapshot": after.snapshot_id,
            }
            for field in fields
            if before.assertions.get(field) != after.assertions.get(field)
        ]


def _signals(
    profile_id: str, memorial_observation_id: str, candidate_snapshot_id: str
) -> tuple[ComparisonSignalInput, ...]:
    def signal(
        fact_type: str,
        classification: str,
        explanation: str,
        ordering_contribution: int = 0,
    ) -> ComparisonSignalInput:
        return ComparisonSignalInput(
            fact_type,
            classification,
            explanation,
            {"record_id": memorial_observation_id, "assertion": fact_type},
            {"record_id": candidate_snapshot_id, "assertion": fact_type},
            ordering_contribution=ordering_contribution,
        )

    if profile_id == "K1AB-CDE":
        return (
            signal(
                "birth",
                "exact",
                "Exact value agreement; not proof of truth, independence, or identity.",
                ordering_contribution=1,
            ),
            signal(
                "death",
                "exact",
                "Exact value agreement; not proof of identity.",
                ordering_contribution=1,
            ),
            signal(
                "burial",
                "exact",
                "Exact value agreement in the displayed representations.",
                ordering_contribution=1,
            ),
            signal(
                "birthplace",
                "compatible",
                "Candidate is more specific; the memorial does not establish the city.",
            ),
            signal(
                "father",
                "conflict",
                "Thomas Carter and Henry Carter are affirmative, incompatible claims requiring research.",
                ordering_contribution=-1,
            ),
            signal(
                "mother",
                "missing",
                "Not stated in the comparison source; missing is not negative evidence.",
            ),
            signal(
                "spouse",
                "missing",
                "Not stated in the comparison source; external research is required.",
            ),
        )
    return (
        signal(
            "name",
            "exact",
            "Exact value agreement; not proof of identity.",
            ordering_contribution=1,
        ),
        signal("birth", "compatible", "Birth year agrees but place conflicts."),
        signal(
            "birthplace",
            "conflict",
            "Missouri and Kansas conflict.",
            ordering_contribution=-1,
        ),
        signal(
            "death", "conflict", "1967 and 1968 conflict.", ordering_contribution=-1
        ),
        signal("burial", "missing", "Candidate supplies no burial value."),
    )


class ReviewServer(ThreadingHTTPServer):
    scenario: ReviewScenario
    page: bytes


class ReviewHandler(BaseHTTPRequestHandler):
    """Serve the review screen and its small action boundary."""

    def do_GET(self) -> None:  # noqa: N802 - standard-library handler API
        if self.path == "/":
            self._send(HTTPStatus.OK, self.server.page, "text/html; charset=utf-8")
        elif self.path == "/api/state":
            self._json(HTTPStatus.OK, self.server.scenario.state())
        else:
            self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802 - standard-library handler API
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        actor = payload.get("actor", "L. Researcher")
        actions = {
            "/api/defer": lambda: self.server.scenario.defer(actor, payload),
            "/api/refresh": self.server.scenario.refresh,
            "/api/reopen": lambda: self.server.scenario.reopen(actor, payload),
            "/api/conclude": lambda: self.server.scenario.conclude_unresolved(
                actor, payload
            ),
            "/api/supersede": lambda: self.server.scenario.supersede(actor, payload),
        }
        action = actions.get(self.path)
        if action is None:
            self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return
        try:
            action()
            self._json(HTTPStatus.OK, self.server.scenario.state())
        except (EvidenceError, ValueError) as error:
            self._json(HTTPStatus.CONFLICT, {"error": str(error)})

    def log_message(self, format: str, *args: Any) -> None:
        """Keep the moderated review terminal quiet."""

    def _json(self, status: HTTPStatus, value: Any) -> None:
        self._send(status, json.dumps(value).encode(), "application/json")

    def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def create_server(directory: Path, port: int = 0) -> ReviewServer:
    """Create a loopback-only review server for tests or moderated use."""
    server = ReviewServer(("127.0.0.1", port), ReviewHandler)
    server.scenario = ReviewScenario.create(directory)
    server.page = Path(__file__).with_name("r2_review.html").read_bytes()
    return server


def main() -> None:
    """Run one disposable review session until the facilitator stops it."""
    parser = argparse.ArgumentParser(description="Run the fictional offline R2 review")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="graver-r2-review-") as directory:
        server = create_server(Path(directory))
        url = f"http://127.0.0.1:{server.server_port}/"
        print(f"R2 review ready at {url}")
        print("The database is disposable. Press Control-C to end and delete it.")
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()


if __name__ == "__main__":
    main()
