import json
import os


class Test:
    """Load deterministic domain fixtures for the test suite."""

    ROOT = os.path.dirname(os.path.abspath(__file__))

    @staticmethod
    def load_memorial_from_json(filename: str):
        json_path = f"{Test.ROOT}/fixtures/memorials/{filename}.json"
        with open(json_path) as f:
            return json.load(f)

    @staticmethod
    def load_cemetery_from_json(filename: str):
        json_path = f"{Test.ROOT}/fixtures/cemeteries/{filename}.json"
        with open(json_path) as f:
            return json.load(f)
