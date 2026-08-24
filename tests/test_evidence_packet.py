"""Contract tests for the bounded internal source-neutral evidence packet."""

from dataclasses import replace

import pytest

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


def source_identity(item_id: str) -> SourceIdentity:
    """Create complete, explicitly synthetic item provenance."""
    return SourceIdentity(
        record_creator=f"{item_id} represented creator",
        repository_or_custodian=f"{item_id} represented custodian",
        access_surface="local offline fixture",
        source_class=f"{item_id} descriptive source class",
        carrier_or_record_form=f"{item_id} represented record form",
        representation_examined="synthetic captured text; no real record examined",
        workflow_role="observation",
    )


def item(item_id: str, *assertions: EvidenceAssertion) -> EvidenceItem:
    """Create one inspectable fictional packet item."""
    return EvidenceItem(
        item_id=item_id,
        identity=source_identity(item_id),
        citation=CaptureCitation(
            citation=f"Capture-faithful synthetic citation for {item_id}",
            observed_at="2026-08-23T12:00:00Z",
            capture_scope="quoted fictional values only; no image examined",
            represented_locator=f"fixture:{item_id}",
            snapshot_id=f"{item_id}-SNAP-1" if item_id in {"F1", "X1"} else None,
        ),
        content=InspectableContent(
            captured_content=f"Human-readable fictional content for {item_id}"
        ),
        assertions=tuple(assertions),
    )


def assertion(
    assertion_id: str,
    value: str,
    *,
    supplier: str = "unknown represented supplier",
    dependence: str = "dependence unknown",
) -> EvidenceAssertion:
    """Create an explicitly attributed fictional assertion."""
    return EvidenceAssertion(
        assertion_id=assertion_id,
        captured_value=value,
        represented_supplier=supplier,
        observed_role="source-displayed assertion",
        derivation_or_dependence=dependence,
    )


def s1_packet() -> EvidencePacket:
    """Build the smallest packet exercising every reviewed S1 source item."""
    items = (
        item("M1", assertion("M1.father", "Henry Carter")),
        item(
            "M2",
            assertion(
                "M2.name",
                "Eleanor M. Carter",
                dependence="derived from M1",
            ),
        ),
        item("D1", assertion("D1.birth", "14 Mar. 1892")),
        item("C1", assertion("C1.age", "18")),
        item("P1", assertion("P1.relationship", "daughter")),
        item("P2", assertion("P2.signature", "Eleanor M. Reed")),
        item("F1", assertion("F1.father", "Thomas Carter")),
        item("X1", assertion("X1.father", "Henry Carter")),
    )
    comparison = ComparisonTrace(
        trace_id="T5",
        left=ComparisonInput("F1.father", "Thomas Carter", "none"),
        right=ComparisonInput("X1.father", "Henry Carter", "none"),
        rule_id="relationship/conflicting-value/1",
        classification="material conflict",
        ordering_contribution=0,
        explanation="Two affirmative father values conflict; no conclusion made.",
    )
    conflict = MaterialConflict(
        conflict_id="CONFLICT-1",
        assertion_ids=("F1.father", "X1.father"),
        research_question="Who was Eleanor's father?",
        treatment="unresolved and retained for every later review",
        identified_at="2026-08-23T12:00:00Z",
        actor="L. Researcher",
    )
    return EvidencePacket(
        packet_id="S1-PACKET-1",
        subject_id="SUBJECT-1",
        items=items,
        comparisons=(comparison,),
        material_conflicts=(conflict,),
        ordering_overrides=(),
        context=ReproducibilityContext(
            research_question="Is the candidate the same Eleanor Carter?",
            search_log="Synthetic offline fixture review; no live search.",
            researcher_analysis="The conflicting father assertions remain open.",
            evidence_selection="All eight S1 items retained for review.",
            unresolved_questions="Father identity and source dependence remain open.",
            decision_history="No identity or kinship conclusion recorded.",
        ),
    )


def test_s1_packet_is_complete_and_source_neutral() -> None:
    packet = s1_packet()

    assert tuple(item.item_id for item in packet.items) == (
        "M1",
        "M2",
        "D1",
        "C1",
        "P1",
        "P2",
        "F1",
        "X1",
    )
    assert packet.material_conflicts[0].assertion_ids == (
        "F1.father",
        "X1.father",
    )
    assert packet.ordering_overrides == ()


def test_missing_source_identity_is_rejected() -> None:
    with pytest.raises(EvidencePacketError, match="Repository or custodian"):
        replace(source_identity("M1"), repository_or_custodian="")


def test_uninspectable_content_requires_disclosure() -> None:
    with pytest.raises(EvidencePacketError, match="reason and reviewability impact"):
        InspectableContent(omission_reason="copyright restriction")

    disclosed = InspectableContent(
        omission_reason="copyright restriction",
        reviewability_impact="recipient must obtain the cited representation",
    )
    assert disclosed.captured_content is None


def test_comparison_and_conflict_references_must_resolve() -> None:
    packet = s1_packet()
    broken_trace = replace(
        packet.comparisons[0],
        right=ComparisonInput("missing.assertion", "unknown", "none"),
    )
    with pytest.raises(EvidencePacketError, match="unknown assertion"):
        replace(packet, comparisons=(broken_trace,))

    broken_conflict = replace(
        packet.material_conflicts[0],
        assertion_ids=("F1.father", "missing.assertion"),
    )
    with pytest.raises(EvidencePacketError, match="unknown assertions"):
        replace(packet, material_conflicts=(broken_conflict,))


def test_material_conflict_requires_two_distinct_assertions() -> None:
    conflict = s1_packet().material_conflicts[0]
    with pytest.raises(EvidencePacketError, match="two distinct assertions"):
        replace(conflict, assertion_ids=("F1.father", "F1.father"))


def test_material_conflict_trace_cannot_be_omitted_from_lifecycle() -> None:
    packet = s1_packet()
    with pytest.raises(EvidencePacketError, match="material conflict record"):
        replace(packet, material_conflicts=())


def test_ordering_override_is_attributed_and_trace_bounded() -> None:
    packet = s1_packet()
    override = OrderingOverride(
        override_id="OVERRIDE-1",
        trace_id="T5",
        ordering_contribution=-1,
        actor="L. Researcher",
        reason="Review the material conflict first",
        recorded_at="2026-08-23T12:30:00Z",
        version="ordering-override/1",
    )
    updated = replace(packet, ordering_overrides=(override,))
    assert updated.ordering_overrides == (override,)

    with pytest.raises(EvidencePacketError, match="unknown trace"):
        replace(updated, ordering_overrides=(replace(override, trace_id="missing"),))


def test_assertion_identifiers_are_unique_across_items() -> None:
    packet = s1_packet()
    duplicate = item("EXTRA", assertion("M1.father", "Henry Carter"))
    with pytest.raises(EvidencePacketError, match="unique across the packet"):
        replace(packet, items=packet.items + (duplicate,))
