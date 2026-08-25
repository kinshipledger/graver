import json
import os

import pytest

from graver.api import Memorial


@pytest.mark.usefixtures("helpers")
class Test:
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

    @pytest.mark.usefixtures("faker")
    def test_gen_memorial(self, faker):
        num_memorials = 50
        memorials = [faker.memorial(faker) for _ in range(num_memorials)]

        assert len(memorials) == num_memorials
        assert all(isinstance(memorial, Memorial) for memorial in memorials)
