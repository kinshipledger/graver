"""Local-only experiential adapter for the R2 professional-researcher review.

This module is deliberately not part of graver's installed package or public API.
It uses a disposable database and curated fictional data.  Every researcher action
is nevertheless applied through the real offline evidence application service.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import tempfile
import uuid
import webbrowser
from dataclasses import asdict, dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from graver.database import create_database
from graver.evidence import (
    AssessmentUpdate,
    CandidateFixture,
    ComparisonSignalInput,
    ConclusionRequest,
    DiscoveryRequest,
    EvidenceError,
    EvidenceService,
)

SUBJECT = {
    "name": "Eleanor May Carter",
    "birth": "14 March 1892, Missouri",
    "death": "8 November 1967, Boise, Idaho",
    "burial": "Morris Hill Cemetery, Boise, Idaho",
    "memorial_id": "12345678",
}

FIRST_CANDIDATES = (
    CandidateFixture(
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
    CandidateFixture(
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
    refreshed: bool = False

    @classmethod
    def create(cls, directory: Path) -> "ReviewScenario":
        """Create and seed a fresh fictional review case."""
        database = str(create_database(str(directory / "r2-review.db")))
        subject_id = str(uuid.uuid4())
        with sqlite3.connect(database) as connection:
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
                _signals(snapshot.provider_profile_id),
            )
        return cls(database, subject_id, service, candidate_ids)

    @property
    def primary_id(self) -> str:
        return self.candidate_ids["K1AB-CDE"]

    def defer(self, actor: str) -> None:
        """Record the required negative search, question, and deferral."""
        current = self.service.get_assessment(self.primary_id)
        self.service.update_assessment(
            AssessmentUpdate(
                self.primary_id,
                current.version,
                "deferred",
                actor,
                "Parentage conflict requires independent evidence.",
                "Check the marriage record and evaluate its informant and provenance.",
                negative_searches=(
                    {
                        "collection": "Ada County Probate Index, 1900–1970",
                        "searched_at": "2026-08-23",
                        "variants": [
                            "Eleanor Carter",
                            "Eleanor Reed",
                            "Eleanor M. Carter",
                        ],
                        "result": "no entry located",
                        "limitation": "Index may omit unindexed or out-of-county proceedings",
                    },
                ),
                unresolved_questions=(
                    "Which father is supported by an original or independently derived record?",
                ),
                follow_up_condition="Marriage record obtained",
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
                    CandidateFixture(
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
            _signals("K1AB-CDE"),
        )
        self.refreshed = True

    def reopen(self, actor: str) -> None:
        """Reopen the deferred assessment and link its prior event."""
        current = self.service.get_assessment(self.primary_id)
        event_id = self.service.assessment_history(self.primary_id)[-1]["event_id"]
        self.service.update_assessment(
            AssessmentUpdate(
                self.primary_id,
                current.version,
                "reopened",
                actor,
                "The marriage record is now available.",
                "Evaluate the new record without treating repeated claims as independent.",
                reopens_record_id=event_id,
            )
        )

    def conclude_unresolved(self, actor: str) -> None:
        """Append the first, deliberately unresolved conclusion."""
        if self.service.conclusion_history(self.primary_id):
            return
        snapshot = self.service.list_snapshots(self.primary_id)[0]
        self.service.record_conclusion(
            ConclusionRequest(
                self.primary_id,
                "unresolved",
                actor,
                "Parentage remains materially conflicting. Matching dates and burial place do not resolve identity.",
                (
                    {
                        "record_id": snapshot.snapshot_id,
                        "observed_at": snapshot.observed_at,
                        "assertions": ["birth", "death", "burial", "father"],
                    },
                ),
                ({"fact_type": "father", "treatment": "unresolved"},),
            )
        )

    def supersede(self, actor: str) -> None:
        """Append a same-person conclusion without editing the earlier decision."""
        history = self.service.conclusion_history(self.primary_id)
        if len(history) != 1:
            raise ValueError("Record the unresolved conclusion before superseding it")
        self.service.record_conclusion(
            ConclusionRequest(
                self.primary_id,
                "accepted",
                actor,
                "Correlated records support the same-person conclusion. The Thomas Carter assertion remains conflicting and its cause is unknown.",
                (
                    {
                        "record_id": "MR-014",
                        "observed_at": "2026-08-28",
                        "assertions": ["father", "spouse"],
                    },
                    {
                        "record_id": "DC-009",
                        "observed_at": "2026-08-30",
                        "assertions": ["identity", "father", "spouse", "informant"],
                    },
                ),
                (
                    {
                        "fact_type": "father",
                        "treatment": "Thomas remains conflicting and less reliable; cause unknown",
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
            "refreshed": self.refreshed,
            "notice": "Fictional offline review case; no live provider request is made.",
        }


def _signals(profile_id: str) -> tuple[ComparisonSignalInput, ...]:
    if profile_id == "K1AB-CDE":
        return (
            ComparisonSignalInput(
                "birth",
                "exact",
                "Exact value agreement; not proof of truth, independence, or identity.",
                ordering_contribution=1,
            ),
            ComparisonSignalInput(
                "death",
                "exact",
                "Exact value agreement; not proof of identity.",
                ordering_contribution=1,
            ),
            ComparisonSignalInput(
                "burial",
                "exact",
                "Exact value agreement in the displayed representations.",
                ordering_contribution=1,
            ),
            ComparisonSignalInput(
                "birthplace",
                "compatible",
                "Candidate is more specific; the memorial does not establish the city.",
            ),
            ComparisonSignalInput(
                "father",
                "conflict",
                "Thomas Carter and Henry Carter are affirmative, incompatible claims requiring research.",
                ordering_contribution=-1,
            ),
            ComparisonSignalInput(
                "mother",
                "missing",
                "Not stated in the comparison source; missing is not negative evidence.",
            ),
            ComparisonSignalInput(
                "spouse",
                "missing",
                "Not stated in the comparison source; external research is required.",
            ),
        )
    return (
        ComparisonSignalInput(
            "name",
            "exact",
            "Exact value agreement; not proof of identity.",
            ordering_contribution=1,
        ),
        ComparisonSignalInput(
            "birth", "compatible", "Birth year agrees but place conflicts."
        ),
        ComparisonSignalInput(
            "birthplace",
            "conflict",
            "Missouri and Kansas conflict.",
            ordering_contribution=-1,
        ),
        ComparisonSignalInput(
            "death", "conflict", "1967 and 1968 conflict.", ordering_contribution=-1
        ),
        ComparisonSignalInput(
            "burial", "missing", "Candidate supplies no burial value."
        ),
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
            "/api/defer": lambda: self.server.scenario.defer(actor),
            "/api/refresh": self.server.scenario.refresh,
            "/api/reopen": lambda: self.server.scenario.reopen(actor),
            "/api/conclude": lambda: self.server.scenario.conclude_unresolved(actor),
            "/api/supersede": lambda: self.server.scenario.supersede(actor),
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
