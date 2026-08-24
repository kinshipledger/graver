"""Integrate existing evidence-domain records with the internal packet validator."""

import json
import uuid
from dataclasses import replace

import pytest

from graver import database as graver_database
from graver._sqlite import connect_database
from graver.evidence import (
    CandidateInput,
    ComparisonSignalInput,
    DiscoveryRequest,
    EvidenceService,
    SourceObservationInput,
)
from graver.evidence_packet import (
    EvidencePacketError,
    InspectableContent,
    MaterialConflict,
    ReproducibilityContext,
    SourceIdentity,
)
from graver.evidence_projection import (
    AssertionProjectionMetadata,
    ObservationProjection,
    PacketProjectionRequest,
    project_evidence_packet,
)


def subject_database(tmp_path):
    """Create a current database with one source-neutral research subject."""
    path = graver_database.create_database(str(tmp_path / "projection.db"))
    subject_id = str(uuid.uuid4())
    with connect_database(path) as connection:
        connection.execute(
            "INSERT INTO research_subjects (subject_id, created_at) VALUES (?, ?)",
            (subject_id, "2026-08-23T10:00:00Z"),
        )
        connection.execute(
            """INSERT INTO research_subject_events
               (subject_id, event_type, occurred_at, reason, after_json)
               VALUES (?, 'subject_created', ?, 'projection_fixture', ?)""",
            (
                subject_id,
                "2026-08-23T10:00:00Z",
                json.dumps({"subject_id": subject_id}),
            ),
        )
    return path, subject_id


def identity(label: str) -> SourceIdentity:
    """Create complete source identity for one fictional representation."""
    return SourceIdentity(
        record_creator=f"{label} creator",
        repository_or_custodian=f"{label} custodian",
        access_surface="offline fixture",
        source_class=f"{label} descriptive class",
        carrier_or_record_form=f"{label} represented form",
        representation_examined="synthetic text; no real record examined",
        workflow_role="observation",
    )


def metadata() -> AssertionProjectionMetadata:
    """Describe an assertion whose represented supplier is unknown."""
    return AssertionProjectionMetadata(
        represented_supplier="unknown represented supplier",
        observed_role="source-displayed assertion",
        derivation_or_dependence="dependence unknown",
    )


def packet_context() -> ReproducibilityContext:
    """Create complete human-readable reproduction context."""
    return ReproducibilityContext(
        research_question="Who was Eleanor's father?",
        search_log="Synthetic offline fixture review; no live search.",
        researcher_analysis="The father assertions materially conflict.",
        evidence_selection="Both conflicting observations retained.",
        unresolved_questions="The father conflict remains unresolved.",
        decision_history="No identity or kinship conclusion recorded.",
    )


def recorded_projection(tmp_path):
    """Persist ordinary evidence records, then describe them for packet projection."""
    path, subject_id = subject_database(tmp_path)
    service = EvidenceService(str(path))
    source = service.record_source_observation(
        SourceObservationInput(
            subject_id=subject_id,
            source_kind="fictional_memorial",
            title="Fictional memorial",
            citation="Capture-faithful citation for fictional memorial F1.",
            observed_at="2026-08-23T11:00:00Z",
            assertions={"father": "Thomas Carter"},
            provenance={"fixture": "F1"},
            actor="L. Researcher",
        )
    )
    discovery = service.record_discovery(
        DiscoveryRequest(
            subject_id=subject_id,
            provider="fictional-tree",
            query={"name": "Eleanor Carter"},
            started_at="2026-08-23T11:05:00Z",
            completed_at="2026-08-23T11:05:00Z",
            strategy_version="fixture/1",
            candidates=(
                CandidateInput(
                    provider_profile_id="X1",
                    observed_at="2026-08-23T11:05:00Z",
                    assertions={"father": "Henry Carter"},
                    profile_url="https://invalid.example/X1",
                ),
            ),
        )
    )
    snapshot = discovery.snapshots[0]
    signals = service.record_comparison(
        snapshot.snapshot_id,
        "relationship/conflicting-value/1",
        (
            ComparisonSignalInput(
                fact_type="father",
                classification="conflict",
                explanation="The affirmative father values materially conflict.",
                subject_assertion={
                    "record_id": source.observation_id,
                    "path": "father",
                    "captured_value": "Thomas Carter",
                    "compared_value": "Thomas Carter",
                    "transformation": "none",
                },
                candidate_assertion={
                    "record_id": snapshot.snapshot_id,
                    "path": "father",
                    "captured_value": "Henry Carter",
                    "compared_value": "Henry Carter",
                    "transformation": "none",
                },
            ),
        ),
    )
    source_projection = ObservationProjection.from_source_observation(
        source,
        identity=identity("F1"),
        content=InspectableContent(captured_content="Daughter of Thomas Carter."),
        assertion_metadata={"father": metadata()},
        capture_scope="father statement only; no image examined",
        represented_locator="fixture:F1",
    )
    candidate_projection = ObservationProjection.from_candidate_snapshot(
        snapshot,
        citation="Capture-faithful citation for fictional profile X1.",
        identity=identity("X1"),
        content=InspectableContent(captured_content="Father: Henry Carter"),
        assertion_metadata={"father": metadata()},
        capture_scope="profile father field only; no attached record examined",
        represented_locator="fixture:X1",
    )
    conflict = MaterialConflict(
        conflict_id="father-conflict",
        assertion_ids=(
            f"{source.observation_id}.father",
            f"{snapshot.snapshot_id}.father",
        ),
        research_question="Who was Eleanor's father?",
        treatment="unresolved and retained",
        identified_at="2026-08-23T11:10:00Z",
        actor="L. Researcher",
    )
    request = PacketProjectionRequest(
        packet_id="packet-1",
        subject_id=subject_id,
        observations=(source_projection, candidate_projection),
        comparison_signals=signals,
        algorithm_version="relationship/conflicting-value/1",
        material_conflicts=(conflict,),
        ordering_overrides=(),
        context=packet_context(),
    )
    return request


def test_projects_real_application_records_into_validated_packet(tmp_path) -> None:
    request = recorded_projection(tmp_path)
    packet = project_evidence_packet(request)

    assert packet.subject_id == request.subject_id
    assert len(packet.items) == 2
    assert packet.comparisons[0].classification == "material conflict"
    assert packet.material_conflicts[0].assertion_ids == (
        packet.comparisons[0].left.assertion_id,
        packet.comparisons[0].right.assertion_id,
    )


def test_projection_refuses_missing_assertion_metadata(tmp_path) -> None:
    request = recorded_projection(tmp_path)
    incomplete = replace(request.observations[0], assertion_metadata={})

    with pytest.raises(EvidencePacketError, match="must match captured assertions"):
        project_evidence_packet(
            replace(
                request, observations=(incomplete,) + tuple(request.observations[1:])
            )
        )


def test_projection_refuses_uninspectable_comparison_input(tmp_path) -> None:
    request = recorded_projection(tmp_path)
    signal = request.comparison_signals[0]
    broken = replace(signal, candidate_assertion={"record_id": "X1"})

    with pytest.raises(
        EvidencePacketError, match="record_id, path, and captured_value"
    ):
        project_evidence_packet(replace(request, comparison_signals=(broken,)))


def test_projection_refuses_comparison_value_that_rewrites_observation(
    tmp_path,
) -> None:
    request = recorded_projection(tmp_path)
    signal = request.comparison_signals[0]
    rewritten = dict(signal.subject_assertion or {})
    rewritten["captured_value"] = "Henry Carter"
    broken = replace(signal, subject_assertion=rewritten)

    with pytest.raises(EvidencePacketError, match="does not match assertion"):
        project_evidence_packet(replace(request, comparison_signals=(broken,)))
