"""Versioned JSON projections for graver command-line clients."""

from typing import Any

SCHEMA_VERSION = 1


def result_envelope(command: str, data: Any) -> dict[str, Any]:
    """Build a successful command-result envelope.

    Args:
        command: Stable dotted command identifier, such as ``work.show``.
        data: Command-specific JSON-compatible payload.

    Returns:
        A versioned envelope whose top-level shape is stable for schema version 1.
    """
    if not command or command.strip() != command:
        raise ValueError("command must be a non-empty normalized identifier")
    return {
        "command": command,
        "data": data,
        "schema_version": SCHEMA_VERSION,
    }
