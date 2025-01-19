import shutil
from collections.abc import Generator
from pathlib import Path

import pytest
from ddeutil.io.files import PathSearch, touch


@pytest.fixture(scope="module")
def make_empty_path(test_path: Path) -> Generator[Path, None, None]:
    path_search = test_path / "test_empty_path_search"
    path_search.mkdir(exist_ok=True)

    yield path_search

    shutil.rmtree(path_search)


@pytest.fixture(scope="module")
def make_path(test_path: Path) -> Generator[Path, None, None]:
    path_search: Path = test_path / "test_path_search"
    path_search.mkdir(exist_ok=True)

    touch(path_search / "00_01_test.text")
    (path_search / "dir01").mkdir(exist_ok=True)
    touch(path_search / "dir01" / "01_01_test.text")
    touch(path_search / "dir01" / "01_02_test.text")
    (path_search / "dir02").mkdir(exist_ok=True)
    touch(path_search / "dir02" / "02_01_test.text")

    yield path_search

    shutil.rmtree(path_search)


def test_base_path_search_empty(make_empty_path):
    ps = PathSearch(make_empty_path)
    assert [] == ps.files
    assert 1 == ps.level


def test_base_path_search_raise(make_empty_path):
    with pytest.raises(FileNotFoundError):
        PathSearch(make_empty_path / "demo")


def test_base_path_search(make_path):
    ps = PathSearch(make_path)
    assert {
        make_path / "00_01_test.text",
        make_path / "dir01/01_01_test.text",
        make_path / "dir01/01_02_test.text",
        make_path / "dir02/02_01_test.text",
    } == set(ps.files)

    ps = PathSearch(make_path, exclude=["dir02"])
    assert {
        make_path / "00_01_test.text",
        make_path / "dir01/01_01_test.text",
        make_path / "dir01/01_02_test.text",
    } == set(ps.files)
