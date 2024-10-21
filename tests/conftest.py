import shutil
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


@pytest.fixture(scope="session", autouse=True)
def drop_data(root_path: Path):
    yield

    if (root_path / "data").exists():
        shutil.rmtree(root_path / "data")
