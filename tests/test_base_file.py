import shutil
from collections.abc import Generator
from pathlib import Path

import ddeutil.io.__base.files as fl
import ddeutil.io.__base.utils as utils
import pytest


@pytest.fixture(scope="module")
def openfile_path(test_path) -> Generator[Path, None, None]:
    this_path: Path = test_path / "open_file"
    this_path.mkdir(parents=True, exist_ok=True)

    yield this_path

    shutil.rmtree(this_path)


@pytest.fixture(scope="module")
def encoding() -> str:
    return "utf-8"


def test_open_file_common(openfile_path, encoding):
    opf = fl.Fl(
        path=openfile_path / "test_common_file.text",
        encoding=encoding,
    )
    with opf.open(mode="w") as f:
        f.write("Write data with common file in normal mode")

    with opf.open(mode="r") as f:
        rs = f.read()

    assert "Write data with common file in normal mode" == rs


def test_open_file_common_append(openfile_path, encoding):
    opf = fl.Fl(
        path=openfile_path / "test_common_file_append.text",
        encoding=encoding,
    )
    with opf.open(mode="w") as f:
        f.write(
            utils.add_newline(
                "Write data with common file append in normal mode",
            )
        )

    with opf.open(mode="a", newline="\n") as f:
        f.write("Write another line in the same file")

    with opf.open(mode="r") as f:
        rs = f.read()

    assert (
        "Write data with common file append in normal mode\n"
        "Write another line in the same file"
    ) == rs


def test_open_file_common_gzip(openfile_path, encoding):
    opf = fl.Fl(
        path=openfile_path / "test_common_file.gz.text",
        encoding=encoding,
        compress="gzip",
    )
    with opf.open(mode="w") as f:
        f.write("Write data with common file in gzip mode")

    with opf.open(mode="r") as f:
        rs = f.read()

    assert "Write data with common file in gzip mode" == rs


def test_open_file_common_xz(openfile_path, encoding):
    opf = fl.Fl(
        path=openfile_path / "test_common_file.xz.text",
        encoding=encoding,
        compress="xz",
    )
    with opf.open(mode="w") as f:
        f.write("Write data with common file in xz mode")

    with opf.open(mode="r") as f:
        rs = f.read()

    assert "Write data with common file in xz mode" == rs


def test_open_file_common_bz2(openfile_path, encoding):
    opf = fl.Fl(
        path=openfile_path / "test_common_file.bz2.text",
        encoding=encoding,
        compress="bz2",
    )
    with opf.open(mode="w") as f:
        f.write("Write data with common file in bz2 mode")

    with opf.open(mode="r") as f:
        rs = f.read()

    assert "Write data with common file in bz2 mode" == rs


def test_open_file_binary(openfile_path, encoding):
    opf = fl.Fl(
        path=openfile_path / "test_binary_file.text",
        encoding=encoding,
    )
    with opf.open(mode="wb") as f:
        f.write(b"Write data with binary file in normal mode")

    with opf.open(mode="rb") as f:
        rs = f.read()

    assert b"Write data with binary file in normal mode" == rs


def test_open_file_binary_gzip(openfile_path, encoding):
    opf = fl.Fl(
        path=openfile_path / "test_binary_file.gz.text",
        encoding=encoding,
        compress="gzip",
    )
    with opf.open(mode="wb") as f:
        f.write(b"Write data with binary file in gzip mode")

    with opf.open(mode="rb") as f:
        rs = f.read()

    assert b"Write data with binary file in gzip mode" == rs


def test_open_file_binary_xz(openfile_path, encoding):
    opf = fl.Fl(
        path=openfile_path / "test_binary_file.xz.text",
        encoding=encoding,
        compress="xz",
    )
    with opf.open(mode="wb") as f:
        f.write(b"Write data with binary file in xz mode")

    with opf.open(mode="rb") as f:
        rs = f.read()

    assert b"Write data with binary file in xz mode" == rs


def test_open_file_binary_bz2(openfile_path, encoding):
    opf = fl.Fl(
        path=openfile_path / "test_binary_file.bz2.text",
        encoding=encoding,
        compress="bz2",
    )
    with opf.open(mode="wb") as f:
        f.write(b"Write data with binary file in bz2 mode")

    with opf.open(mode="rb") as f:
        rs = f.read()

    assert b"Write data with binary file in bz2 mode" == rs


@pytest.fixture(scope="module")
def openfile_mem_path(test_path) -> Generator[Path, None, None]:
    this_path: Path = test_path / "open_file_mem"
    this_path.mkdir(parents=True, exist_ok=True)

    yield this_path

    shutil.rmtree(this_path)


def test_open_file_mem_common(openfile_mem_path, encoding):
    opf = fl.Fl(
        path=openfile_mem_path / "test_common_mem_file.text",
        encoding=encoding,
    )
    with opf.mopen(mode="w") as f:
        f.write("Write data with common file in normal mode on memory")

    with opf.mopen(mode="r") as f:
        rs = f.read()

    assert b"Write data with common file in normal mode on memory" == rs


def test_open_file_mem_common_gzip(openfile_mem_path, encoding):
    opf = fl.Fl(
        path=openfile_mem_path / "test_common_mem_file.gz.text",
        encoding=encoding,
        compress="gzip",
    )
    with opf.mopen(mode="w") as f:
        f.write("Write data with common file in gzip mode on memory")

    with opf.mopen(mode="r") as f:
        rs = fl.compress_lib("gzip").decompress(f.read())

    assert b"Write data with common file in gzip mode on memory" == rs


def test_open_file_mem_common_xz(openfile_mem_path, encoding):
    opf = fl.Fl(
        path=openfile_mem_path / "test_common_mem_file.xz.text",
        encoding=encoding,
        compress="xz",
    )
    with opf.mopen(mode="w") as f:
        f.write("Write data with common file in xz mode on memory")

    with opf.mopen(mode="r") as f:
        rs = fl.compress_lib("xz").decompress(f.read())

    assert b"Write data with common file in xz mode on memory" == rs


def test_open_file_mem_common_bz2(openfile_mem_path, encoding):
    opf = fl.Fl(
        path=openfile_mem_path / "test_common_mem_file.bz2.text",
        encoding=encoding,
        compress="bz2",
    )
    with opf.mopen(mode="w") as f:
        f.write("Write data with common file in bz2 mode on memory")

    with opf.mopen(mode="r") as f:
        rs = fl.compress_lib("bz2").decompress(f.read())

    assert b"Write data with common file in bz2 mode on memory" == rs
