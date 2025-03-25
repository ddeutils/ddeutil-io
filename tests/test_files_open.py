import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from ddeutil.io.files import Fl
from ddeutil.io.utils import add_newline


@pytest.fixture(scope="module")
def target_path(test_path) -> Iterator[Path]:
    this_path: Path = test_path / "files"
    this_path.mkdir(parents=True, exist_ok=True)

    yield this_path

    shutil.rmtree(this_path)


def test_open_file_common(target_path, encoding):
    file = Fl(
        path=target_path / "test_common_file.text",
        encoding=encoding,
    )
    with file.open(mode="w") as f:
        f.write("Write data with common file in normal mode")

    with file.open(mode="r") as f:
        rs = f.read()

    assert "Write data with common file in normal mode" == rs


def test_open_file_common_with_open(target_path, encoding):
    file = Fl(
        path=target_path / "test_common_file.text",
        encoding=encoding,
    )
    with file.open(mode="w") as f:
        f.write("Write data with common file in normal mode")

    with file() as f:
        rs = f.read()

    assert "Write data with common file in normal mode" == rs


def test_open_file_common_append(target_path, encoding):
    file = Fl(
        path=target_path / "test_common_file_append.text",
        encoding=encoding,
    )
    with file.open(mode="w") as f:
        f.write(
            add_newline(
                "Write data with common file append in normal mode",
            )
        )

    with file.open(mode="a", newline="\n") as f:
        f.write("Write another line in the same file")

    with file.open(mode="r") as f:
        rs = f.read()

    assert (
        "Write data with common file append in normal mode\n"
        "Write another line in the same file"
    ) == rs


def test_open_file_common_gzip(target_path, encoding):
    file = Fl(
        path=target_path / "test_common_file.gz.text",
        encoding=encoding,
        compress="gzip",
    )
    with file.open(mode="w") as f:
        f.write("Write data with common file in gzip mode")

    with file.open(mode="r") as f:
        rs = f.read()

    assert "Write data with common file in gzip mode" == rs


def test_open_file_common_gz(target_path, encoding):
    file = Fl(
        path=target_path / "test_common_file.gz.text",
        encoding=encoding,
        compress="gz",
    )
    with file.open(mode="w") as f:
        f.write("Write data with common file in gz mode")

    with file.open(mode="r") as f:
        rs = f.read()

    assert "Write data with common file in gz mode" == rs


def test_open_file_common_xz(target_path, encoding):
    file = Fl(
        path=target_path / "test_common_file.xz.text",
        encoding=encoding,
        compress="xz",
    )
    with file.open(mode="w") as f:
        f.write("Write data with common file in xz mode")

    with file.open(mode="r") as f:
        rs = f.read()

    assert "Write data with common file in xz mode" == rs


def test_open_file_common_bz2(target_path, encoding):
    file = Fl(
        path=target_path / "test_common_file.bz2.text",
        encoding=encoding,
        compress="bz2",
    )
    with file.open(mode="w") as f:
        f.write("Write data with common file in bz2 mode")

    with file.open(mode="r") as f:
        assert "Write data with common file in bz2 mode" == f.read()


def test_open_file_binary(target_path, encoding):
    file = Fl(
        path=target_path / "test_binary_file.text",
        encoding=encoding,
    )
    with file.open(mode="wb") as f:
        f.write(b"Write data with binary file in normal mode")

    with file.open(mode="rb") as f:
        assert b"Write data with binary file in normal mode" == f.read()


def test_open_file_binary_gzip(target_path, encoding):
    file = Fl(
        path=target_path / "test_binary_file.gz.text",
        encoding=encoding,
        compress="gzip",
    )
    with file.open(mode="wb") as f:
        f.write(b"Write data with binary file in gzip mode")

    with file.open(mode="rb") as f:
        assert b"Write data with binary file in gzip mode" == f.read()


def test_open_file_binary_gz(target_path, encoding):
    file = Fl(
        path=target_path / "test_binary_file.gz.text",
        encoding=encoding,
        compress="gz",
    )
    with file.open(mode="wb") as f:
        f.write(b"Write data with binary file in gz mode")

    with file.open(mode="rb") as f:
        rs = f.read()

    assert b"Write data with binary file in gz mode" == rs


def test_open_file_binary_xz(target_path, encoding):
    file = Fl(
        path=target_path / "test_binary_file.xz.text",
        encoding=encoding,
        compress="xz",
    )
    with file.open(mode="wb") as f:
        f.write(b"Write data with binary file in xz mode")

    with file.open(mode="rb") as f:
        assert b"Write data with binary file in xz mode" == f.read()


def test_open_file_binary_bz2(target_path, encoding):
    file = Fl(
        path=target_path / "test_binary_file.bz2.text",
        encoding=encoding,
        compress="bz2",
    )
    with file.open(mode="wb") as f:
        f.write(b"Write data with binary file in bz2 mode")

    with file.open(mode="rb") as f:
        rs = f.read()

    assert b"Write data with binary file in bz2 mode" == rs
