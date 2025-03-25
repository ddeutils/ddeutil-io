import shutil
from collections.abc import Generator
from pathlib import Path

import pytest
from ddeutil.io.dirs import Dir


@pytest.fixture(scope="module")
def target_path(test_path) -> Generator[Path, None, None]:
    target_path: Path = test_path / "open_dir"
    target_path.mkdir(parents=True, exist_ok=True)

    data_path: Path = test_path / "open_dir/data"
    data_path.mkdir(parents=True, exist_ok=True)

    with open(data_path / "test_file.json", mode="w") as f:
        f.write('{"key": "value"}')

    with open(data_path / "test_file_2.json", mode="w") as f:
        f.write('{"foo": "bar"}')

    yield target_path

    shutil.rmtree(target_path)


@pytest.fixture(scope="module")
def data_path(target_path):
    return target_path / "data"


def test_open_dir_common_zip(target_path, data_path):
    with Dir(
        path=target_path / "test_common_zip.zip",
        compress="zip",
    ).open(mode="w") as d:
        for data in data_path.rglob("*"):
            d.write(filename=data, arcname=data.relative_to(data_path))

    with Dir(
        path=target_path / "test_common_zip.zip",
        compress="zip",
    ).open(mode="r") as d:
        d.safe_extract(target_path / "test_common_zip_extract")

    assert {
        "test_file.json",
        "test_file_2.json",
    } == {f.name for f in (target_path / "test_common_zip_extract").rglob("*")}


def test_open_dir_common_tar(target_path, data_path):
    with Dir(
        path=target_path / "test_common_tar.tar.gz",
        compress="tar",
    ).open(mode="w") as d:
        for data in data_path.rglob("*"):
            d.write(name=data, arcname=data.relative_to(data_path))

    with Dir(
        path=target_path / "test_common_tar.tar.gz",
        compress="tar:gz",
    ).open(mode="r") as d:
        d.safe_extract(target_path / "test_common_tar_extract")

    assert {
        "test_file.json",
        "test_file_2.json",
    } == {f.name for f in (target_path / "test_common_tar_extract").rglob("*")}
