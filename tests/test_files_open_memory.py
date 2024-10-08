import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from ddeutil.io.files.file import Fl, compress_lib


@pytest.fixture(scope="module")
def openfile_mem_path(test_path) -> Iterator[Path]:
    this_path: Path = test_path / "open_file_mem"
    this_path.mkdir(parents=True, exist_ok=True)

    yield this_path

    shutil.rmtree(this_path)


def test_open_file_mem_common(openfile_mem_path, encoding):
    opf = Fl(
        path=openfile_mem_path / "test_common_mem_file.text",
        encoding=encoding,
    )
    with opf.mopen(mode="w") as f:
        f.write("Write data with common file in normal mode on memory")

    with opf.mopen(mode="r") as f:
        rs = f.read()

    assert b"Write data with common file in normal mode on memory" == rs


def test_open_file_mem_common_gzip(openfile_mem_path, encoding):
    opf = Fl(
        path=openfile_mem_path / "test_common_mem_file.gz.text",
        encoding=encoding,
        compress="gzip",
    )
    with opf.mopen(mode="w") as f:
        f.write("Write data with common file in gzip mode on memory")

    with opf.mopen(mode="r") as f:
        rs = compress_lib("gzip").decompress(f.read())

    assert b"Write data with common file in gzip mode on memory" == rs


def test_open_file_mem_common_xz(openfile_mem_path, encoding):
    opf = Fl(
        path=openfile_mem_path / "test_common_mem_file.xz.text",
        encoding=encoding,
        compress="xz",
    )
    with opf.mopen(mode="w") as f:
        f.write("Write data with common file in xz mode on memory")

    with opf.mopen(mode="r") as f:
        rs = compress_lib("xz").decompress(f.read())

    assert b"Write data with common file in xz mode on memory" == rs


def test_open_file_mem_common_bz2(openfile_mem_path, encoding):
    opf = Fl(
        path=openfile_mem_path / "test_common_mem_file.bz2.text",
        encoding=encoding,
        compress="bz2",
    )
    with opf.mopen(mode="w") as f:
        f.write("Write data with common file in bz2 mode on memory")

    with opf.mopen(mode="r") as f:
        rs = compress_lib("bz2").decompress(f.read())

    assert b"Write data with common file in bz2 mode on memory" == rs
