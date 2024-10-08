from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def test_path() -> Path:
    return Path(__file__).parent


@pytest.fixture(scope="session")
def root_path(test_path: Path) -> Path:
    return test_path.parent


@pytest.fixture(scope="session")
def encoding() -> str:
    return "utf-8"
