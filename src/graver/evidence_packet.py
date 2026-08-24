"""Internal source-neutral evidence packet types and validation.

The packet is an offline application-domain boundary. It preserves evidence needed
for professional review without defining persistence, a public interchange format,
or a universal genealogy ontology.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence


class EvidencePacketError(ValueError):
    """Report an invalid or non-reviewable evidence packet."""


def _require_text(value: str, label: str) -> None:
    if not value or not value.strip():
        raise EvidencePacketError(f"{label} is required")


def _require_distinct(values: Sequence[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise EvidencePacketError(f"{label} must be unique")


@dataclass(frozen=True)
class SourceIdentity:
    """Describe who created, holds, and exposes one represented source."""

    record_creator: str
    repository_or_custodian: str
    access_surface: str
    source_class: str
    carrier_or_record_form: str
    representation_examined: str
    workflow_role: str

    def __post_init__(self) -> None:
        for value, label in (
            (self.record_creator, "Record creator"),
            (self.repository_or_custodian, "Repository or custodian"),
            (self.access_surface, "Access surface"),
            (self.source_class, "Source class"),
            (self.carrier_or_record_form, "Carrier or record form"),
            (self.representation_examined, "Representation examined"),
            (self.workflow_role, "Workflow role"),
        ):
            _require_text(value, label)


@dataclass(frozen=True)
class CaptureCitation:
    """Identify the exact represented item and the scope actually examined."""

    citation: str
    observed_at: str
    capture_scope: str
    represented_locator: str
    snapshot_id: Optional[str] = None

    def __post_init__(self) -> None:
        for value, label in (
            (self.citation, "Citation"),
            (self.observed_at, "Observation time"),
            (self.capture_scope, "Capture scope"),
            (self.represented_locator, "Represented locator"),
        ):
            _require_text(value, label)
        if self.snapshot_id is not None:
            _require_text(self.snapshot_id, "Snapshot identifier")


@dataclass(frozen=True)
class InspectableContent:
    """Carry readable captured content or disclose why review is limited."""

    captured_content: Optional[str] = None
    omission_reason: Optional[str] = None
    reviewability_impact: Optional[str] = None

    def __post_init__(self) -> None:
        if self.captured_content:
            if self.omission_reason or self.reviewability_impact:
                raise EvidencePacketError(
                    "Included content cannot also be described as omitted"
                )
            return
        if not self.omission_reason or not self.reviewability_impact:
            raise EvidencePacketError(
                "Omitted content requires a reason and reviewability impact"
            )


@dataclass(frozen=True)
class EvidenceAssertion:
    """Preserve one captured assertion and its attribution without inference."""

    assertion_id: str
    captured_value: str
    represented_supplier: str
    observed_role: str
    derivation_or_dependence: str
    information_quality: str = "undetermined"

    def __post_init__(self) -> None:
        for value, label in (
            (self.assertion_id, "Assertion identifier"),
            (self.captured_value, "Captured value"),
            (self.represented_supplier, "Represented supplier"),
            (self.observed_role, "Observed role"),
            (self.derivation_or_dependence, "Derivation or dependence"),
            (self.information_quality, "Information-quality evaluation"),
        ):
            _require_text(value, label)


@dataclass(frozen=True)
class EvidenceItem:
    """Group one represented source item with inspectable assertions."""

    item_id: str
    identity: SourceIdentity
    citation: CaptureCitation
    content: InspectableContent
    assertions: tuple[EvidenceAssertion, ...]

    def __post_init__(self) -> None:
        _require_text(self.item_id, "Item identifier")
        _require_distinct(
            tuple(assertion.assertion_id for assertion in self.assertions),
            f"Assertion identifiers in {self.item_id}",
        )


@dataclass(frozen=True)
class ComparisonInput:
    """Reference one assertion and disclose its comparison transformation."""

    assertion_id: str
    compared_value: str
    transformation: str

    def __post_init__(self) -> None:
        for value, label in (
            (self.assertion_id, "Comparison assertion identifier"),
            (self.compared_value, "Compared value"),
            (self.transformation, "Comparison transformation"),
        ):
            _require_text(value, label)


@dataclass(frozen=True)
class ComparisonTrace:
    """Explain one deterministic review-order signal without claiming proof."""

    trace_id: str
    left: ComparisonInput
    right: ComparisonInput
    rule_id: str
    classification: str
    ordering_contribution: int
    explanation: str

    def __post_init__(self) -> None:
        for value, label in (
            (self.trace_id, "Trace identifier"),
            (self.rule_id, "Rule identifier"),
            (self.classification, "Classification"),
            (self.explanation, "Comparison explanation"),
        ):
            _require_text(value, label)


@dataclass(frozen=True)
class MaterialConflict:
    """Keep one material conflict visible throughout its research lifecycle."""

    conflict_id: str
    assertion_ids: tuple[str, ...]
    research_question: str
    treatment: str
    identified_at: str
    actor: str

    def __post_init__(self) -> None:
        for value, label in (
            (self.conflict_id, "Conflict identifier"),
            (self.research_question, "Conflict research question"),
            (self.treatment, "Conflict treatment"),
            (self.identified_at, "Conflict identification time"),
            (self.actor, "Conflict actor"),
        ):
            _require_text(value, label)
        if len(set(self.assertion_ids)) < 2:
            raise EvidencePacketError(
                "A material conflict requires at least two distinct assertions"
            )


@dataclass(frozen=True)
class OrderingOverride:
    """Record an attributable override that changes review ordering only."""

    override_id: str
    trace_id: str
    ordering_contribution: int
    actor: str
    reason: str
    recorded_at: str
    version: str

    def __post_init__(self) -> None:
        for value, label in (
            (self.override_id, "Override identifier"),
            (self.trace_id, "Override trace identifier"),
            (self.actor, "Override actor"),
            (self.reason, "Override reason"),
            (self.recorded_at, "Override time"),
            (self.version, "Override version"),
        ):
            _require_text(value, label)


@dataclass(frozen=True)
class ReproducibilityContext:
    """Carry human-readable context required for genealogical reproduction."""

    research_question: str
    search_log: str
    researcher_analysis: str
    evidence_selection: str
    unresolved_questions: str
    decision_history: str

    def __post_init__(self) -> None:
        for value, label in (
            (self.research_question, "Research question"),
            (self.search_log, "Search log"),
            (self.researcher_analysis, "Researcher analysis"),
            (self.evidence_selection, "Evidence selection"),
            (self.unresolved_questions, "Unresolved questions"),
            (self.decision_history, "Decision history"),
        ):
            _require_text(value, label)


@dataclass(frozen=True)
class EvidencePacket:
    """Represent a self-contained, source-neutral internal evidence packet."""

    packet_id: str
    subject_id: str
    items: tuple[EvidenceItem, ...]
    comparisons: tuple[ComparisonTrace, ...]
    material_conflicts: tuple[MaterialConflict, ...]
    ordering_overrides: tuple[OrderingOverride, ...]
    context: ReproducibilityContext

    def __post_init__(self) -> None:
        _require_text(self.packet_id, "Packet identifier")
        _require_text(self.subject_id, "Subject identifier")
        _require_distinct(
            tuple(item.item_id for item in self.items), "Packet item identifiers"
        )
        _require_distinct(
            tuple(trace.trace_id for trace in self.comparisons),
            "Comparison trace identifiers",
        )
        _require_distinct(
            tuple(conflict.conflict_id for conflict in self.material_conflicts),
            "Material conflict identifiers",
        )
        _require_distinct(
            tuple(override.override_id for override in self.ordering_overrides),
            "Ordering override identifiers",
        )
        assertion_ids = {
            assertion.assertion_id
            for item in self.items
            for assertion in item.assertions
        }
        if sum(len(item.assertions) for item in self.items) != len(assertion_ids):
            raise EvidencePacketError(
                "Assertion identifiers must be unique across the packet"
            )
        trace_ids = {trace.trace_id for trace in self.comparisons}
        for trace in self.comparisons:
            for comparison_input in (trace.left, trace.right):
                if comparison_input.assertion_id not in assertion_ids:
                    raise EvidencePacketError(
                        f"Comparison {trace.trace_id} references unknown assertion "
                        f"{comparison_input.assertion_id}"
                    )
        for conflict in self.material_conflicts:
            unknown = set(conflict.assertion_ids) - assertion_ids
            if unknown:
                raise EvidencePacketError(
                    f"Conflict {conflict.conflict_id} references unknown assertions"
                )
        recorded_conflict_pairs = {
            frozenset(conflict.assertion_ids) for conflict in self.material_conflicts
        }
        for trace in self.comparisons:
            if (
                trace.classification == "material conflict"
                and frozenset((trace.left.assertion_id, trace.right.assertion_id))
                not in recorded_conflict_pairs
            ):
                raise EvidencePacketError(
                    f"Comparison {trace.trace_id} requires a material conflict record"
                )
        for override in self.ordering_overrides:
            if override.trace_id not in trace_ids:
                raise EvidencePacketError(
                    f"Override {override.override_id} references unknown trace "
                    f"{override.trace_id}"
                )
