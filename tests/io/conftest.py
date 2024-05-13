import pathlib

import pytest


@pytest.fixture(scope="session")
def test_path() -> pathlib.Path:
    return pathlib.Path(__file__).parent.parent
