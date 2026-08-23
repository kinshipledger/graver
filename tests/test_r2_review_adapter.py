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

    scenario.defer("L. Researcher")
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

    scenario.reopen("L. Researcher")
    scenario.conclude_unresolved("L. Researcher")
    scenario.supersede("L. Researcher")
    final = scenario.state()["candidates"][0]

    assert final["assessment"]["state"] == "reopened"
    assert len(final["assessment_history"]) == 3
    assert [item["disposition"] for item in final["conclusions"]] == [
        "unresolved",
        "accepted",
    ]
    assert (
        final["conclusions"][1]["supersedes_conclusion_id"]
        == final["conclusions"][0]["conclusion_id"]
    )
