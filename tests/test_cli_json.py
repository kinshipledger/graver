import pytest

from graver.cli_json import SCHEMA_VERSION, result_envelope


def test_result_envelope_preserves_command_and_payload():
    payload = {"tasks": [1, 2]}

    result = result_envelope("work.list", payload)

    assert result == {
        "command": "work.list",
        "data": payload,
        "schema_version": SCHEMA_VERSION,
    }
    assert result["data"] is payload


@pytest.mark.parametrize("command", ["", " work.list", "work.list "])
def test_result_envelope_rejects_invalid_command_identifiers(command):
    with pytest.raises(ValueError, match="normalized identifier"):
        result_envelope(command, None)
