"""Exercise the local R2 review adapter against the real evidence service."""

from review.r2_adapter import ReviewScenario


def test_r2_scenario_preserves_context_and_decision_history(tmp_path):
    """Complete the moderated sequence without network or production state."""
    scenario = ReviewScenario.create(tmp_path)

    initial = scenario.state()
    assert initial["subject"]["name"] == "Eleanor May Carter"
    assert [item["provider_profile_id"] for item in initial["candidates"]] == [
        "K1AB-CDE",
        "L2FG-HJK",
    ]
    assert initial["candidates"][0]["material_conflict_count"] == 1
    assert "confidence" not in initial["candidates"][0]

    scenario.defer(
        "L. Researcher",
        {
            "reason": "Parentage conflict requires further research.",
            "notes": "Evaluate original records and informants.",
            "repository": "Ada County records portal",
            "collection": "Ada County Probate Index",
            "coverage": "1900–1970",
            "jurisdiction": "Ada County, Idaho",
            "searched_at": "2026-08-23",
            "variants": "Eleanor Carter; Eleanor Reed",
            "method": "Exact and variant surname searches",
            "result": "no entry located",
            "limitation": "Index may omit unindexed proceedings",
            "question": "Which father is supported by the best evidence?",
            "follow_up": "Marriage record obtained",
        },
    )
    deferred = scenario.state()["candidates"][0]["assessment"]
    assert deferred["state"] == "deferred"
    assert deferred["negative_searches"][0]["result"] == "no entry located"
    assert deferred["unresolved_questions"]

    scenario.refresh()
    refreshed = scenario.state()
    absent = next(
        item
        for item in refreshed["candidates"]
        if item["provider_profile_id"] == "L2FG-HJK"
    )
    changed = refreshed["candidates"][0]
    assert absent["present_in_latest_run"] is False
    assert len(absent["snapshots"]) == 1
    assert len(changed["snapshots"]) == 2
    assert "new_record" in changed["latest"]["assertions"]
    assert refreshed["change_summary"]
    assert len(refreshed["sources"]) == 3

    scenario.reopen(
        "L. Researcher",
        {
            "reason": "New cited observations are available.",
            "notes": "Evaluate informant knowledge and dependence.",
        },
    )
    scenario.conclude_unresolved(
        "L. Researcher",
        {
            "analysis": "The father conflict remains unresolved despite matching vital details.",
            "evidence_ids": [scenario.source_ids["memorial"]],
        },
    )
    scenario.supersede(
        "L. Researcher",
        {
            "analysis": "The correlated marriage and death records support the same-person conclusion.",
            "conflict_treatment": "Thomas remains conflicting and less reliable; its cause is unknown.",
            "evidence_ids": [
                scenario.source_ids["marriage"],
                scenario.source_ids["death"],
            ],
        },
    )
    final = scenario.state()["candidates"][0]

    assert final["assessment"]["state"] == "reopened"
    assert len(final["assessment_history"]) == 3
    assert [item["disposition"] for item in final["conclusions"]] == [
        "unresolved",
        "accepted",
    ]
    assert final["conclusions"][0]["evidence_references"][0]["record_id"] == (
        scenario.source_ids["memorial"]
    )
    negative_search = final["assessment"]["negative_searches"][0]
    assert negative_search["searched_at"] == "2026-08-23"
    assert negative_search["variants"] == ["Eleanor Carter", "Eleanor Reed"]
    assert negative_search["method"] == "Exact and variant surname searches"
    assert (
        final["conclusions"][1]["supersedes_conclusion_id"]
        == final["conclusions"][0]["conclusion_id"]
    )
    assert len(final["conclusions"][1]["evidence_references"]) == 2
    assert final["conclusions"][1]["material_conflicts"][0]["fact_type"] == "father"
