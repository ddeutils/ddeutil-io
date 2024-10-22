import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from ddeutil.io.files import CsvFl, CsvPipeFl


@pytest.fixture(scope="module")
def csv_path(test_path) -> Iterator[Path]:
    this_path: Path = test_path / "csv"
    this_path.mkdir(parents=True, exist_ok=True)

    yield this_path

    shutil.rmtree(this_path)


@pytest.fixture(scope="module")
def csv_data() -> list[dict[str, str]]:
    return [
        {"Col01": "A", "Col02": "1", "Col03": "test1"},
        {"Col01": "B", "Col02": "2", "Col03": "test2"},
        {"Col01": "C", "Col02": "3", "Col03": "test3"},
    ]


def test_files_open_csv(csv_path, csv_data):
    CsvFl(csv_path / "test_file.csv").write(csv_data)
    assert csv_data == CsvFl(csv_path / "test_file.csv").read()


def test_files_open_csv_dict(csv_path, csv_data):
    CsvFl(csv_path / "test_file.dict.csv").write(
        {"Col01": "A", "Col02": "1", "Col03": "test1"}
    )
    assert [{"Col01": "A", "Col02": "1", "Col03": "test1"}] == CsvFl(
        csv_path / "test_file.dict.csv"
    ).read()

    CsvFl(csv_path / "test_file.dict.csv").write(
        {"Col01": "B", "Col02": "2", "Col03": "test2"}, mode="a"
    )
    CsvFl(csv_path / "test_file.dict.csv").write(
        [{"Col01": "C", "Col02": "3", "Col03": "test3"}], mode="a"
    )

    with pytest.raises(ValueError):
        CsvFl(csv_path / "test_file.dict.csv").write([])

    assert csv_data == CsvFl(csv_path / "test_file.dict.csv").read()


def test_files_open_csv_pipe_dict(csv_path, csv_data):
    CsvPipeFl(csv_path / "test_file_pipe.dict.csv").write(
        {"Col01": "A", "Col02": "1", "Col03": "test1"}
    )
    assert [{"Col01": "A", "Col02": "1", "Col03": "test1"}] == CsvPipeFl(
        csv_path / "test_file_pipe.dict.csv"
    ).read()

    CsvPipeFl(csv_path / "test_file_pipe.dict.csv").write(
        {"Col01": "B", "Col02": "2", "Col03": "test2"}, mode="a"
    )
    CsvPipeFl(csv_path / "test_file_pipe.dict.csv").write(
        [{"Col01": "C", "Col02": "3", "Col03": "test3"}], mode="a"
    )

    with pytest.raises(ValueError):
        CsvPipeFl(csv_path / "test_file_pipe.dict.csv").write([])

    assert csv_data == CsvPipeFl(csv_path / "test_file_pipe.dict.csv").read()


def test_files_open_csv_not_support(csv_path):
    with open(csv_path / "test_file_raise.csv", mode="w") as f:
        f.write("...")
    assert [] == CsvFl(csv_path / "test_file_raise.csv").read()
