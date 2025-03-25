import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from ddeutil.io import touch
from ddeutil.io.files import Fl, compress_lib


@pytest.fixture(scope="module")
def file_mem_path(test_path) -> Iterator[Path]:
    this_path: Path = test_path / "file_memory"
    this_path.mkdir(parents=True, exist_ok=True)

    yield this_path

    shutil.rmtree(this_path)


def test_compress_lib(file_mem_path):
    file = Fl(
        path=file_mem_path / "test_common_mem_file.gz.text",
        compress="gz",
    )

    assert compress_lib("gz").decompress == file.decompress


def test_compress_lib_raise(file_mem_path, encoding):
    file = Fl(
        path=file_mem_path / "test_common_mem_file.foo.text",
        encoding=encoding,
        compress="foo",
    )

    with pytest.raises(NotImplementedError):
        _ = file.decompress


def test_open_file_mem_common(file_mem_path, encoding):
    file = Fl(
        path=file_mem_path / "test_common_mem_file.text",
        encoding=encoding,
    )
    with file.mopen(mode="w") as f:
        f.write("Write data with common file in normal mode on memory")

    with file.mopen(mode="r") as f:
        assert (
            b"Write data with common file in normal mode on memory" == f.read()
        )


def test_open_file_mem_common_raise(file_mem_path, encoding):
    file = Fl(
        path=file_mem_path / "test_common_mem_file_raise.text",
        encoding=encoding,
    )
    with pytest.raises(FileNotFoundError):
        with file.mopen(mode="r") as f:
            f.read()

    touch(file_mem_path / "test_common_mem_file_raise.text")
    with file.mopen(mode="r") as f:
        assert f.read() == ""


def test_open_file_mem_common_gzip(file_mem_path, encoding):
    file = Fl(
        path=file_mem_path / "test_common_mem_file.gz.text",
        encoding=encoding,
        compress="gzip",
    )
    with file.mopen(mode="w") as f:
        f.write("Write data with common file in gzip mode on memory")

    with file.mopen(mode="r") as f:
        rs = compress_lib("gzip").decompress(f.read())

    assert b"Write data with common file in gzip mode on memory" == rs


def test_open_file_mem_common_xz(file_mem_path, encoding):
    file = Fl(
        path=file_mem_path / "test_common_mem_file.xz.text",
        encoding=encoding,
        compress="xz",
    )
    with file.mopen(mode="w") as f:
        f.write("Write data with common file in xz mode on memory")

    with file.mopen(mode="r") as f:
        rs = compress_lib("xz").decompress(f.read())

    assert b"Write data with common file in xz mode on memory" == rs


def test_open_file_mem_common_bz2(file_mem_path, encoding):
    file = Fl(
        path=file_mem_path / "test_common_mem_file.bz2.text",
        encoding=encoding,
        compress="bz2",
    )
    with file.mopen(mode="w") as f:
        f.write("Write data with common file in bz2 mode on memory")

    with file.mopen(mode="r") as f:
        rs = compress_lib("bz2").decompress(f.read())

    assert b"Write data with common file in bz2 mode on memory" == rs
