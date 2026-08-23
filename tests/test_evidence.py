"""Contract tests for the completely offline evidence vertical slice."""

import json
import sqlite3
import uuid

import pytest

from graver import database as graver_database
from graver._sqlite import connect_database
from graver.evidence import (
    AssessmentUpdate,
    CandidateInput,
    ComparisonSignalInput,
    ConclusionRequest,
    DiscoveryRequest,
    EvidenceInputError,
    EvidenceNotFound,
    EvidenceService,
    SourceObservationInput,
    StaleAssessment,
)


def make_subject_database(tmp_path):
    """Create a current database with one honest subject and no memorial."""
    path = graver_database.create_database(str(tmp_path / "evidence.db"))
    subject_id = str(uuid.uuid4())
    with connect_database(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            "INSERT INTO research_subjects (subject_id, created_at) VALUES (?, ?)",
            (subject_id, "2026-08-23T10:00:00Z"),
        )
        connection.execute(
            """INSERT INTO research_subject_events
               (subject_id, event_type, occurred_at, reason, after_json)
               VALUES (?, 'subject_created', ?, 'manual_fixture', ?)""",
            (
                subject_id,
                "2026-08-23T10:00:00Z",
                json.dumps({"subject_id": subject_id}),
            ),
        )
    return path, subject_id


def discovery(subject_id, observed_at, candidates):
    """Build one deterministic, FamilySearch-shaped offline discovery request."""
    return DiscoveryRequest(
        subject_id=subject_id,
        provider="familysearch-fixture",
        query={"name": "Eleanor May Carter", "birth_year": 1892},
        started_at=observed_at,
        completed_at=observed_at,
        strategy_version="fixture-search/1",
        candidates=candidates,
    )


def test_schema_v2_upgrade_adds_empty_current_evidence_structures(tmp_path):
    path = graver_database.create_database(str(tmp_path / "v2.db"))
    with connect_database(path) as connection:
        for table in sorted(graver_database.EVIDENCE_TABLES):
            connection.execute(f"DROP TABLE {table}")
        connection.execute("UPDATE graver_schema SET version=2")

    assert graver_database.inspect_database(str(path)).state == "outdated"
    result = graver_database.upgrade_database(str(path))

    assert result.changed is True
    assert result.source.version == 2
    assert result.version == graver_database.CURRENT_SCHEMA_VERSION
    with connect_database(path) as connection:
        assert connection.execute("SELECT version FROM graver_schema").fetchone() == (
            graver_database.CURRENT_SCHEMA_VERSION,
        )
        for table in graver_database.EVIDENCE_TABLES:
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone() == (
                0,
            )
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_discovery_rejects_duplicate_provider_profiles():
    with pytest.raises(EvidenceInputError, match="same provider profile twice"):
        discovery(
            str(uuid.uuid4()),
            "2026-08-23T11:00:00Z",
            (
                CandidateInput("K1AB-CDE", "2026-08-23T11:00:00Z", {}),
                CandidateInput("K1AB-CDE", "2026-08-23T11:00:00Z", {}),
            ),
        )


@pytest.mark.parametrize(
    "factory, message",
    (
        (
            lambda: DiscoveryRequest(
                "subject", "provider", {}, "start", "end", "v1", outcome="invalid"
            ),
            "Invalid discovery outcome",
        ),
        (
            lambda: DiscoveryRequest(
                "subject",
                "provider",
                {},
                "start",
                "end",
                "v1",
                (CandidateInput("P1", "now", {}),),
                "no_results",
            ),
            "no-results",
        ),
        (
            lambda: DiscoveryRequest("", "provider", {}, "start", "end", "v1"),
            "Subject identifier",
        ),
        (
            lambda: ComparisonSignalInput("birth", "invalid", "explanation"),
            "Invalid signal classification",
        ),
        (
            lambda: AssessmentUpdate("candidate", 1, "invalid", "researcher"),
            "Invalid assessment state",
        ),
        (
            lambda: AssessmentUpdate("candidate", 1, "deferred", "researcher"),
            "reason is required",
        ),
        (
            lambda: AssessmentUpdate(
                "candidate", 1, "reopened", "researcher", "new evidence"
            ),
            "earlier record identifier",
        ),
        (
            lambda: ConclusionRequest(
                "candidate", "invalid", "researcher", "analysis", ({},), ()
            ),
            "Invalid conclusion disposition",
        ),
        (
            lambda: ConclusionRequest(
                "candidate",
                "unresolved",
                "researcher",
                "analysis",
                ({"record_id": "R1"},),
                (),
            ),
            "record_id, observed_at, and assertions",
        ),
        (
            lambda: ConclusionRequest(
                "candidate",
                "withdrawn",
                "researcher",
                "analysis",
                ({"record_id": "R1", "observed_at": "now", "assertions": ["name"]},),
                (),
            ),
            "prior conclusion",
        ),
    ),
)
def test_evidence_requests_reject_unsafe_inputs(factory, message):
    with pytest.raises(EvidenceInputError, match=message):
        factory()


def test_service_lookup_failures_and_noop_assessment_are_safe(tmp_path):
    path, subject_id = make_subject_database(tmp_path)
    service = EvidenceService(str(path))
    with pytest.raises(EvidenceInputError, match="Algorithm version"):
        service.record_comparison("missing", "", ())
    with pytest.raises(EvidenceNotFound, match="Candidate snapshot"):
        service.record_comparison("missing", "fixture-ordering/1", ())
    with pytest.raises(EvidenceNotFound, match="Research subject"):
        service.record_discovery(
            discovery(str(uuid.uuid4()), "2026-08-23T11:00:00Z", ())
        )
    snapshot = service.record_discovery(
        discovery(
            subject_id,
            "2026-08-23T11:00:00Z",
            (CandidateInput("K1AB-CDE", "2026-08-23T11:00:00Z", {}),),
        )
    ).snapshots[0]
    unchanged = service.update_assessment(
        AssessmentUpdate(snapshot.candidate_id, 1, "new", "L. Researcher")
    )
    assert unchanged.version == 1
    assert len(service.assessment_history(snapshot.candidate_id)) == 1
    with pytest.raises(EvidenceNotFound, match="does not exist"):
        service.get_assessment("missing")
    with pytest.raises(EvidenceNotFound, match="does not exist"):
        service.update_assessment(
            AssessmentUpdate("missing", 1, "reviewing", "L. Researcher")
        )
    valid_reference = (
        {"record_id": "R1", "observed_at": "now", "assertions": ["name"]},
    )
    with pytest.raises(EvidenceNotFound, match="does not exist"):
        service.record_conclusion(
            ConclusionRequest(
                "missing",
                "unresolved",
                "L. Researcher",
                "analysis",
                valid_reference,
                (),
            )
        )
    with pytest.raises(EvidenceInputError, match="same candidate"):
        service.record_conclusion(
            ConclusionRequest(
                snapshot.candidate_id,
                "accepted",
                "L. Researcher",
                "analysis",
                valid_reference,
                (),
                "missing-conclusion",
            )
        )


def test_offline_discovery_preserves_changed_and_absent_candidates(tmp_path):
    path, subject_id = make_subject_database(tmp_path)
    service = EvidenceService(str(path))
    first = service.record_discovery(
        discovery(
            subject_id,
            "2026-08-23T11:00:00Z",
            (
                CandidateInput(
                    "K1AB-CDE",
                    "2026-08-23T11:00:00Z",
                    {
                        "name": "Eleanor M. Carter",
                        "father": "Henry Carter",
                        "relationships": [
                            {
                                "label": "Spouse",
                                "name": "William Reed",
                                "source_status": "provider_display_not_proven_kinship",
                            }
                        ],
                    },
                    "https://example.invalid/tree/person/K1AB-CDE",
                ),
                CandidateInput(
                    "L2FG-HJK",
                    "2026-08-23T11:00:00Z",
                    {"name": "Eleanor May Carter", "father": "Thomas Carter"},
                ),
            ),
        )
    )
    second = service.record_discovery(
        discovery(
            subject_id,
            "2026-08-24T11:00:00Z",
            (
                CandidateInput(
                    "K1AB-CDE",
                    "2026-08-24T11:00:00Z",
                    {
                        "name": "Eleanor M. Carter",
                        "father": "Henry Carter",
                        "spouse": "William Reed",
                    },
                ),
            ),
        )
    )

    assert first.run_id != second.run_id
    assert first.snapshots[0].candidate_id == second.snapshots[0].candidate_id
    assert first.snapshots[0].content_hash != second.snapshots[0].content_hash
    assert len(service.list_snapshots(first.snapshots[0].candidate_id)) == 2
    assert len(service.list_snapshots(first.snapshots[1].candidate_id)) == 1
    with connect_database(path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM external_candidates"
        ).fetchone() == (2,)
        assert connection.execute(
            "SELECT COUNT(*) FROM candidate_snapshots"
        ).fetchone() == (3,)
        assert connection.execute(
            "SELECT COUNT(*) FROM research_subjects"
        ).fetchone() == (1,)
        assert connection.execute(
            "SELECT COUNT(*) FROM subject_memorials"
        ).fetchone() == (0,)
        assert connection.execute(
            "SELECT COUNT(*) FROM identity_conclusions"
        ).fetchone() == (0,)


def test_comparison_orders_review_without_creating_a_conclusion(tmp_path):
    path, subject_id = make_subject_database(tmp_path)
    service = EvidenceService(str(path))
    result = service.record_discovery(
        discovery(
            subject_id,
            "2026-08-23T11:00:00Z",
            (
                CandidateInput(
                    "K1AB-CDE", "2026-08-23T11:00:00Z", {"birth": "14 Mar 1892"}
                ),
                CandidateInput("L2FG-HJK", "2026-08-23T11:00:00Z", {"birth": "1892"}),
            ),
        )
    )
    service.record_comparison(
        result.snapshots[0].snapshot_id,
        "fixture-ordering/1",
        (
            ComparisonSignalInput(
                "birth",
                "exact",
                "Displayed birth values agree; this does not establish identity.",
                {"record_id": "O-001", "path": "birth", "original": "14 Mar 1892"},
                {
                    "record_id": result.snapshots[0].snapshot_id,
                    "path": "birth",
                    "original": "14 Mar 1892",
                },
                "1892-03-14",
                "1892-03-14",
                1,
            ),
            ComparisonSignalInput(
                "father",
                "conflict",
                "Affirmative father assertions conflict and require research.",
                ordering_contribution=-1,
            ),
        ),
    )
    service.record_comparison(
        result.snapshots[1].snapshot_id,
        "fixture-ordering/1",
        (
            ComparisonSignalInput(
                "birth", "compatible", "Year agrees; precision differs."
            ),
        ),
    )

    ranked = service.ranked_candidates(subject_id, "fixture-ordering/1")

    assert [item.provider_profile_id for item in ranked] == ["K1AB-CDE", "L2FG-HJK"]
    assert ranked[0].agreement_count == 1
    assert ranked[0].material_conflict_count == 1
    assert not hasattr(ranked[0], "confidence")
    with connect_database(path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM identity_conclusions"
        ).fetchone() == (0,)
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute("UPDATE comparison_signals SET explanation='proof'")


def test_assessment_deferral_reopening_and_stale_edit_history(tmp_path):
    path, subject_id = make_subject_database(tmp_path)
    service = EvidenceService(str(path))
    snapshot = service.record_discovery(
        discovery(
            subject_id,
            "2026-08-23T11:00:00Z",
            (CandidateInput("K1AB-CDE", "2026-08-23T11:00:00Z", {"name": "Eleanor"}),),
        )
    ).snapshots[0]

    with pytest.raises(EvidenceInputError, match="follow-up"):
        AssessmentUpdate(
            snapshot.candidate_id, 1, "deferred", "L. Researcher", "Need records"
        )
    deferred = service.update_assessment(
        AssessmentUpdate(
            snapshot.candidate_id,
            1,
            "deferred",
            "L. Researcher",
            "Parentage conflict requires another record",
            "Check marriage record",
            negative_searches=(
                {
                    "collection": "Ada County Probate Index, 1900–1970",
                    "searched_at": "2026-08-23",
                    "variants": ["Eleanor Carter", "Eleanor Reed"],
                    "result": "no entry located",
                    "limitation": "Index may omit unindexed proceedings",
                },
            ),
            unresolved_questions=(
                "Which father is supported by an original or independently derived record?",
            ),
            follow_up_condition="Marriage record obtained",
        )
    )
    with pytest.raises(StaleAssessment):
        service.update_assessment(
            AssessmentUpdate(snapshot.candidate_id, 1, "reviewing", "Other Researcher")
        )
    reopened = service.update_assessment(
        AssessmentUpdate(
            snapshot.candidate_id,
            deferred.version,
            "reopened",
            "L. Researcher",
            "Marriage record is now available",
            "Evaluate informant and parentage",
            reopens_record_id=service.assessment_history(snapshot.candidate_id)[-1][
                "event_id"
            ],
        )
    )

    assert reopened.version == 3
    assert len(service.get_assessment(snapshot.candidate_id).negative_searches) == 1
    assert service.get_assessment(snapshot.candidate_id).unresolved_questions == (
        "Which father is supported by an original or independently derived record?",
    )
    history = service.assessment_history(snapshot.candidate_id)
    assert len(history) == 3
    assert history[-1]["actor"] == "L. Researcher"
    assert history[-1]["before"]["state"] == "deferred"
    assert history[-1]["after"]["state"] == "reopened"


def test_conclusions_require_inspectable_evidence_and_supersede_immutably(tmp_path):
    path, subject_id = make_subject_database(tmp_path)
    service = EvidenceService(str(path))
    snapshot = service.record_discovery(
        discovery(
            subject_id,
            "2026-08-23T11:00:00Z",
            (CandidateInput("K1AB-CDE", "2026-08-23T11:00:00Z", {"name": "Eleanor"}),),
        )
    ).snapshots[0]
    with pytest.raises(EvidenceInputError, match="inspectable"):
        ConclusionRequest(
            snapshot.candidate_id,
            "unresolved",
            "L. Researcher",
            "Conflict remains",
            (),
            (),
        )

    unresolved = service.record_conclusion(
        ConclusionRequest(
            snapshot.candidate_id,
            "unresolved",
            "L. Researcher",
            "Parentage remains materially conflicting.",
            (
                {
                    "record_id": snapshot.snapshot_id,
                    "observed_at": snapshot.observed_at,
                    "assertions": ["father"],
                },
            ),
            ({"fact_type": "father", "treatment": "unresolved"},),
        )
    )
    marriage = service.record_source_observation(
        SourceObservationInput(
            subject_id,
            "civil_marriage_register",
            "Eleanor Carter–William Reed marriage entry",
            "Ada County, Idaho, marriage register 12:47, Carter–Reed, 1912; fictional R2 fixture.",
            "2026-08-28",
            {"father": "Henry Carter", "spouse": "William Reed"},
            {
                "repository": "Ada County Recorder",
                "locator": "Marriage register 12:47",
                "image_examined": True,
                "informant": "not stated",
            },
            "L. Researcher",
        )
    )
    accepted = service.record_conclusion(
        ConclusionRequest(
            snapshot.candidate_id,
            "accepted",
            "L. Researcher",
            "Correlated records support the same-person conclusion; individual assertions retain their status.",
            (
                {
                    "record_id": marriage.observation_id,
                    "observed_at": marriage.observed_at,
                    "assertions": ["father", "spouse", "informant"],
                },
            ),
            (
                {
                    "fact_type": "father",
                    "treatment": "Thomas remains conflicting and less reliable; cause unknown",
                },
            ),
            unresolved.conclusion_id,
        )
    )

    history = service.conclusion_history(snapshot.candidate_id)
    assert [item.disposition for item in history] == ["unresolved", "accepted"]
    assert accepted.supersedes_conclusion_id == unresolved.conclusion_id
    assert history[1].evidence_references[0]["record_id"] == marriage.observation_id
    assert service.get_source_observation(marriage.observation_id).citation.startswith(
        "Ada County"
    )
    with connect_database(path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM identity_conclusions"
        ).fetchone() == (2,)
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute("UPDATE identity_conclusions SET disposition='rejected'")
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(
                "UPDATE research_source_observations SET citation='rewritten'"
            )


def test_conclusion_rejects_missing_and_cross_subject_evidence(tmp_path):
    path, subject_id = make_subject_database(tmp_path)
    service = EvidenceService(str(path))
    candidate = service.record_discovery(
        discovery(
            subject_id,
            "2026-08-23T11:00:00Z",
            (CandidateInput("K1AB-CDE", "2026-08-23T11:00:00Z", {}),),
        )
    ).snapshots[0]
    with pytest.raises(EvidenceInputError, match="not an inspectable observation"):
        service.record_conclusion(
            ConclusionRequest(
                candidate.candidate_id,
                "unresolved",
                "L. Researcher",
                "The available evidence is insufficient.",
                (
                    {
                        "record_id": "invented-reference",
                        "observed_at": "2026-08-23",
                        "assertions": ["identity"],
                    },
                ),
                (),
            )
        )

    other_subject = str(uuid.uuid4())
    with connect_database(path) as connection:
        connection.execute(
            "INSERT INTO research_subjects (subject_id, created_at) VALUES (?, ?)",
            (other_subject, "2026-08-23T12:00:00Z"),
        )
        connection.execute(
            """INSERT INTO research_subject_events
               (subject_id, event_type, occurred_at, reason, after_json)
               VALUES (?, 'subject_created', ?, 'test', ?)""",
            (
                other_subject,
                "2026-08-23T12:00:00Z",
                json.dumps({"subject_id": other_subject}),
            ),
        )
    unrelated = service.record_source_observation(
        SourceObservationInput(
            other_subject,
            "record",
            "Unrelated record",
            "A complete but unrelated citation.",
            "2026-08-23",
            {"name": "Someone Else"},
            {"repository": "Archive"},
            "L. Researcher",
        )
    )
    with pytest.raises(EvidenceInputError, match="not an inspectable observation"):
        service.record_conclusion(
            ConclusionRequest(
                candidate.candidate_id,
                "unresolved",
                "L. Researcher",
                "The available evidence is insufficient.",
                (
                    {
                        "record_id": unrelated.observation_id,
                        "observed_at": unrelated.observed_at,
                        "assertions": ["name"],
                    },
                ),
                (),
            )
        )
