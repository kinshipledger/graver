"""Project existing evidence-domain records into validated internal packets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from graver.evidence import (
    CandidateSnapshotRecord,
    ComparisonSignalRecord,
    SourceObservationRecord,
)
from graver.evidence_packet import (
    CaptureCitation,
    ComparisonInput,
    ComparisonTrace,
    EvidenceAssertion,
    EvidenceItem,
    EvidencePacket,
    EvidencePacketError,
    InspectableContent,
    MaterialConflict,
    OrderingOverride,
    ReproducibilityContext,
    SourceIdentity,
)


@dataclass(frozen=True)
class AssertionProjectionMetadata:
    """Supply S1 attribution that an existing flexible assertion does not encode."""

    represented_supplier: str
    observed_role: str
    derivation_or_dependence: str
    information_quality: str = "undetermined"


@dataclass(frozen=True)
class ObservationProjection:
    """Pair one immutable application record with explicit packet metadata."""

    record_id: str
    observed_at: str
    citation: str
    assertions: Mapping[str, Any]
    identity: SourceIdentity
    content: InspectableContent
    assertion_metadata: Mapping[str, AssertionProjectionMetadata]
    capture_scope: str
    represented_locator: str
    snapshot_id: str | None = None

    @classmethod
    def from_source_observation(
        cls,
        record: SourceObservationRecord,
        *,
        identity: SourceIdentity,
        content: InspectableContent,
        assertion_metadata: Mapping[str, AssertionProjectionMetadata],
        capture_scope: str,
        represented_locator: str,
    ) -> ObservationProjection:
        """Describe a persisted source observation without rewriting its values."""
        return cls(
            record.observation_id,
            record.observed_at,
            record.citation,
            record.assertions,
            identity,
            content,
            assertion_metadata,
            capture_scope,
            represented_locator,
        )

    @classmethod
    def from_candidate_snapshot(
        cls,
        record: CandidateSnapshotRecord,
        *,
        citation: str,
        identity: SourceIdentity,
        content: InspectableContent,
        assertion_metadata: Mapping[str, AssertionProjectionMetadata],
        capture_scope: str,
        represented_locator: str,
    ) -> ObservationProjection:
        """Describe a candidate snapshot with an explicit capture-faithful citation."""
        return cls(
            record.snapshot_id,
            record.observed_at,
            citation,
            record.assertions,
            identity,
            content,
            assertion_metadata,
            capture_scope,
            represented_locator,
            record.snapshot_id,
        )


@dataclass(frozen=True)
class PacketProjectionRequest:
    """Request a validated packet projection from existing domain records."""

    packet_id: str
    subject_id: str
    observations: Sequence[ObservationProjection]
    comparison_signals: Sequence[ComparisonSignalRecord]
    algorithm_version: str
    material_conflicts: Sequence[MaterialConflict]
    ordering_overrides: Sequence[OrderingOverride]
    context: ReproducibilityContext


def _display_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _assertion_reference(
    value: Mapping[str, Any], side: str
) -> tuple[str, str, str, str]:
    try:
        record_id = value["record_id"]
        path = value["path"]
        captured_value = value["captured_value"]
    except KeyError as error:
        raise EvidencePacketError(
            f"{side} comparison input requires record_id, path, and captured_value"
        ) from error
    if not all(isinstance(item, str) and item.strip() for item in (record_id, path)):
        raise EvidencePacketError(f"{side} comparison reference must contain text")
    transformation = value.get("transformation", "none")
    compared_value = value.get("compared_value", captured_value)
    if not isinstance(transformation, str) or not transformation.strip():
        raise EvidencePacketError(f"{side} comparison transformation is required")
    return (
        f"{record_id}.{path}",
        _display_value(captured_value),
        _display_value(compared_value),
        transformation,
    )


def _project_item(projection: ObservationProjection) -> EvidenceItem:
    assertion_keys = set(projection.assertions)
    metadata_keys = set(projection.assertion_metadata)
    if assertion_keys != metadata_keys:
        missing = sorted(assertion_keys - metadata_keys)
        extra = sorted(metadata_keys - assertion_keys)
        raise EvidencePacketError(
            "Assertion metadata must match captured assertions exactly; "
            f"missing={missing}, extra={extra}"
        )
    assertions = tuple(
        EvidenceAssertion(
            assertion_id=f"{projection.record_id}.{path}",
            captured_value=_display_value(value),
            represented_supplier=projection.assertion_metadata[
                path
            ].represented_supplier,
            observed_role=projection.assertion_metadata[path].observed_role,
            derivation_or_dependence=projection.assertion_metadata[
                path
            ].derivation_or_dependence,
            information_quality=projection.assertion_metadata[path].information_quality,
        )
        for path, value in sorted(projection.assertions.items())
    )
    return EvidenceItem(
        item_id=projection.record_id,
        identity=projection.identity,
        citation=CaptureCitation(
            citation=projection.citation,
            observed_at=projection.observed_at,
            capture_scope=projection.capture_scope,
            represented_locator=projection.represented_locator,
            snapshot_id=projection.snapshot_id,
        ),
        content=projection.content,
        assertions=assertions,
    )


def project_evidence_packet(request: PacketProjectionRequest) -> EvidencePacket:
    """Build a validated packet without persisting or inventing evidence metadata."""
    items = tuple(_project_item(item) for item in request.observations)
    captured_values = {
        assertion.assertion_id: assertion.captured_value
        for item in items
        for assertion in item.assertions
    }
    comparisons = []
    for signal in request.comparison_signals:
        if signal.subject_assertion is None or signal.candidate_assertion is None:
            raise EvidencePacketError(
                f"Comparison {signal.signal_id} requires both inspectable inputs"
            )
        left_id, left_captured, left_value, left_transformation = _assertion_reference(
            signal.subject_assertion, "Subject"
        )
        right_id, right_captured, right_value, right_transformation = (
            _assertion_reference(signal.candidate_assertion, "Candidate")
        )
        for side, assertion_id, claimed_value in (
            ("Subject", left_id, left_captured),
            ("Candidate", right_id, right_captured),
        ):
            if assertion_id in captured_values and (
                captured_values[assertion_id] != claimed_value
            ):
                raise EvidencePacketError(
                    f"{side} comparison captured value does not match "
                    f"assertion {assertion_id}"
                )
        classification = (
            "material conflict"
            if signal.classification == "conflict"
            else signal.classification
        )
        comparisons.append(
            ComparisonTrace(
                trace_id=signal.signal_id,
                left=ComparisonInput(left_id, left_value, left_transformation),
                right=ComparisonInput(right_id, right_value, right_transformation),
                rule_id=request.algorithm_version,
                classification=classification,
                ordering_contribution=signal.ordering_contribution,
                explanation=signal.explanation,
            )
        )
    return EvidencePacket(
        packet_id=request.packet_id,
        subject_id=request.subject_id,
        items=items,
        comparisons=tuple(comparisons),
        material_conflicts=tuple(request.material_conflicts),
        ordering_overrides=tuple(request.ordering_overrides),
        context=request.context,
    )
