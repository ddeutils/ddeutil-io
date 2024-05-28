import shutil
from collections.abc import Generator
from pathlib import Path

import ddeutil.io.__base.files as fl
import pytest


@pytest.fixture(scope="module")
def csv_path(test_path) -> Generator[Path, None, None]:
    this_path: Path = test_path / "open_file"
    this_path.mkdir(parents=True, exist_ok=True)

    yield this_path

    shutil.rmtree(this_path)


def test_csv_read_and_write(csv_path):
    csv_data: list[str] = [
        {"Col01": "A", "Col02": "1", "Col03": "test1"},
        {"Col01": "B", "Col02": "2", "Col03": "test2"},
        {"Col01": "C", "Col02": "3", "Col03": "test3"},
    ]
    fl.CsvFl(csv_path / "test_file.csv").write(csv_data)
    assert csv_data == fl.CsvFl(csv_path / "test_file.csv").read()
