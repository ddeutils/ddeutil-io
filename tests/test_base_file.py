import os
import pathlib
import shutil
import unittest

import ddeutil.io.__base.files as fl
import ddeutil.io.__base.utils as utils


class OpenFileTestCase(unittest.TestCase):
    root_path: str

    @classmethod
    def setUpClass(cls) -> None:
        _root_path: str = os.path.dirname(os.path.abspath(__file__)).replace(
            os.sep, "/"
        )
        os.makedirs(f"{_root_path}/open_file", exist_ok=True)

        cls.root_path: str = f"{_root_path}/open_file"

    def setUp(self) -> None:
        self.encoding = "utf-8"

    def test_open_file_common(self):
        opf = fl.Fl(
            path=pathlib.Path(f"{self.root_path}/test_common_file.text"),
            encoding="utf-8",
        )
        with opf.open(mode="w") as f:
            f.write("Write data with common file in normal mode")

        with opf.open(mode="r") as f:
            rs = f.read()

        self.assertEqual("Write data with common file in normal mode", rs)

    def test_open_file_common_append(self):
        opf = fl.Fl(
            path=pathlib.Path(f"{self.root_path}/test_common_file_append.text"),
            encoding="utf-8",
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

        self.assertEqual(
            (
                "Write data with common file append in normal mode\n"
                "Write another line in the same file"
            ),
            rs,
        )

    def test_open_file_common_gzip(self):
        opf = fl.Fl(
            path=pathlib.Path(f"{self.root_path}/test_common_file.gz.text"),
            encoding="utf-8",
            compress="gzip",
        )
        with opf.open(mode="w") as f:
            f.write("Write data with common file in gzip mode")

        with opf.open(mode="r") as f:
            rs = f.read()

        self.assertEqual("Write data with common file in gzip mode", rs)

    def test_open_file_common_xz(self):
        opf = fl.Fl(
            path=f"{self.root_path}/test_common_file.xz.text",
            encoding="utf-8",
            compress="xz",
        )
        with opf.open(mode="w") as f:
            f.write("Write data with common file in xz mode")

        with opf.open(mode="r") as f:
            rs = f.read()

        self.assertEqual("Write data with common file in xz mode", rs)

    def test_open_file_common_bz2(self):
        opf = fl.Fl(
            path=f"{self.root_path}/test_common_file.bz2.text",
            encoding="utf-8",
            compress="bz2",
        )
        with opf.open(mode="w") as f:
            f.write("Write data with common file in bz2 mode")

        with opf.open(mode="r") as f:
            rs = f.read()

        self.assertEqual("Write data with common file in bz2 mode", rs)

    def test_open_file_binary(self):
        opf = fl.Fl(
            path=f"{self.root_path}/test_binary_file.text",
            encoding="utf-8",
        )
        with opf.open(mode="wb") as f:
            f.write(b"Write data with binary file in normal mode")

        with opf.open(mode="rb") as f:
            rs = f.read()

        self.assertEqual(b"Write data with binary file in normal mode", rs)

    def test_open_file_binary_gzip(self):
        opf = fl.Fl(
            path=f"{self.root_path}/test_binary_file.gz.text",
            encoding="utf-8",
            compress="gzip",
        )
        with opf.open(mode="wb") as f:
            f.write(b"Write data with binary file in gzip mode")

        with opf.open(mode="rb") as f:
            rs = f.read()

        self.assertEqual(b"Write data with binary file in gzip mode", rs)

    def test_open_file_binary_xz(self):
        opf = fl.Fl(
            path=f"{self.root_path}/test_binary_file.xz.text",
            encoding="utf-8",
            compress="xz",
        )
        with opf.open(mode="wb") as f:
            f.write(b"Write data with binary file in xz mode")

        with opf.open(mode="rb") as f:
            rs = f.read()

        self.assertEqual(b"Write data with binary file in xz mode", rs)

    def test_open_file_binary_bz2(self):
        opf = fl.Fl(
            path=f"{self.root_path}/test_binary_file.bz2.text",
            encoding="utf-8",
            compress="bz2",
        )
        with opf.open(mode="wb") as f:
            f.write(b"Write data with binary file in bz2 mode")

        with opf.open(mode="rb") as f:
            rs = f.read()

        self.assertEqual(b"Write data with binary file in bz2 mode", rs)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.root_path)


class OpenFileMemoryTestCase(unittest.TestCase):
    root_path: str

    @classmethod
    def setUpClass(cls) -> None:
        _root_path: str = os.path.dirname(os.path.abspath(__file__)).replace(
            os.sep, "/"
        )
        os.makedirs(f"{_root_path}/open_file_mem", exist_ok=True)

        cls.root_path: str = f"{_root_path}/open_file_mem"

    def setUp(self) -> None:
        self.encoding = "utf-8"

    def test_open_file_mem_common(self):
        opf = fl.Fl(
            path=f"{self.root_path}/test_common_mem_file.text",
            encoding="utf-8",
        )
        with opf.mopen(mode="w") as f:
            f.write("Write data with common file in normal mode on memory")

        with opf.mopen(mode="r") as f:
            rs = f.read()

        self.assertEqual(
            b"Write data with common file in normal mode on memory", rs
        )

    def test_open_file_mem_common_gzip(self):
        opf = fl.Fl(
            path=f"{self.root_path}/test_common_mem_file.gz.text",
            encoding="utf-8",
            compress="gzip",
        )
        with opf.mopen(mode="w") as f:
            f.write("Write data with common file in gzip mode on memory")

        with opf.mopen(mode="r") as f:
            rs = fl.compress_lib("gzip").decompress(f.read())

        self.assertEqual(
            b"Write data with common file in gzip mode on memory", rs
        )

    def test_open_file_mem_common_xz(self):
        opf = fl.Fl(
            path=f"{self.root_path}/test_common_mem_file.xz.text",
            encoding="utf-8",
            compress="xz",
        )
        with opf.mopen(mode="w") as f:
            f.write("Write data with common file in xz mode on memory")

        with opf.mopen(mode="r") as f:
            rs = fl.compress_lib("xz").decompress(f.read())

        self.assertEqual(
            b"Write data with common file in xz mode on memory", rs
        )

    def test_open_file_mem_common_bz2(self):
        opf = fl.Fl(
            path=f"{self.root_path}/test_common_mem_file.bz2.text",
            encoding="utf-8",
            compress="bz2",
        )
        with opf.mopen(mode="w") as f:
            f.write("Write data with common file in bz2 mode on memory")

        with opf.mopen(mode="r") as f:
            rs = fl.compress_lib("bz2").decompress(f.read())

        self.assertEqual(
            b"Write data with common file in bz2 mode on memory", rs
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.root_path)
