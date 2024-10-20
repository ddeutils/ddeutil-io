import csv
import os
import shutil
from collections.abc import Iterator
from pathlib import Path

import ddeutil.io.files.utils as utils
import pytest


@pytest.fixture(scope="module")
def utils_path(test_path) -> Iterator[Path]:
    this_path: Path = test_path / "utils_reverse"
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


def test_files_utils_search_env_replace():
    os.environ["NAME"] = "foo"
    assert "Hello foo" == utils.search_env_replace("Hello ${NAME}")


def test_files_utils_search_env_replace_raise():
    with pytest.raises(ValueError):
        utils.search_env_replace(
            "Hello ${NAME01}",
            raise_if_default_not_exists=True,
        )

    with pytest.raises(ValueError):
        utils.search_env_replace("Hello ${:test}")


def test_files_utils_search_env():
    assert {
        "key": "demo",
        "hello": "demo-2",
        "escape": "${key}",
    } == utils.search_env(
        "key='demo'\n# foo=bar\nhello=${key}-2\nescape=\\${key}\n",
    )


def test_files_utils_search_env_raise():
    with pytest.raises(ValueError):
        utils.search_env("foo=")

    with pytest.raises(ValueError):
        utils.search_env("foo=''")

    with pytest.raises(ValueError):
        utils.search_env('foo=""')


def test_files_utils_reverse_read(utils_path, csv_data):
    test_file = utils_path / "file_reverse.csv"

    with open(test_file, mode="w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(csv_data[0].keys()),
            lineterminator="\n",
        )
        writer.writerows(csv_data)

    with open(test_file) as f:
        rs = list(utils.reverse_readline(f))
    assert rs == [
        "C,3,test3\n",
        "B,2,test2\n",
        "A,1,test1\n",
    ]
