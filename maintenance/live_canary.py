#!/usr/bin/env python3
"""Run graver's one-request live Find a Grave compatibility canary."""

from __future__ import annotations

import argparse
import json

from graver._live_contract import LiveContractResult, run_live_contract


def main() -> int:
    """Run the probe, print a safe report, and return its compatibility status."""

    parser = argparse.ArgumentParser(
        description=(
            "Make one live request to the designated public memorial and verify "
            "graver's minimum transport and parsing contract."
        )
    )
    parser.add_argument(
        "--json", action="store_true", help="Write the versioned result as JSON."
    )
    args = parser.parse_args()
    result = run_live_contract()
    print(_render_json(result) if args.json else _render_human(result))
    return 0 if result.compatible else 1


def _render_json(result: LiveContractResult) -> str:
    return json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True)


def _render_human(result: LiveContractResult) -> str:
    details = [
        f"Live canary: {result.classification}",
        result.message,
        f"Target: {result.target_url}",
        f"Checked: {result.checked_at}",
        f"Requests: {result.request_count} (retries disabled)",
    ]
    if result.status_code is not None:
        details.append(f"HTTP status: {result.status_code}")
    if result.memorial_id is not None:
        details.append(f"Parsed memorial: {result.memorial_id} | {result.name}")
    if result.missing_invariants:
        details.append("Missing: " + ", ".join(result.missing_invariants))
    return "\n".join(details)


if __name__ == "__main__":
    raise SystemExit(main())
