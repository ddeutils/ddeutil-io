import os
import pathlib
import shutil
import unittest

import ddeutil.io.__base.files as fl


class OpenDirTestCase(unittest.TestCase):
    root_path: str

    @classmethod
    def setUpClass(cls) -> None:
        _root_path: str = os.path.dirname(os.path.abspath(__file__)).replace(
            os.sep, "/"
        )
        os.makedirs(f"{_root_path}/open_dir", exist_ok=True)
        os.makedirs(f"{_root_path}/open_dir/data", exist_ok=True)

        cls.root_path: str = f"{_root_path}/open_dir"
        cls.data_path: str = f"{_root_path}/open_dir/data"

        with open(
            pathlib.Path(f"{_root_path}/open_dir/data/test_file.json"),
            mode="w",
        ) as f:
            f.write('{"key": "value"}')
        with open(
            pathlib.Path(f"{_root_path}/open_dir/data/test_file_2.json"),
            mode="w",
        ) as f:
            f.write('{"foo": "bar"}')

    def setUp(self) -> None:
        self.encoding = "utf-8"

    def test_open_dir_common_zip(self):
        data_dir = pathlib.Path(self.data_path)

        opd = fl.Dir(
            path=pathlib.Path(f"{self.root_path}/test_common_dir.zip"),
            compress="zip",
        )
        with opd.open(mode="w") as d:
            for data in data_dir.rglob("*"):
                d.write(filename=data, arcname=data.relative_to(data_dir))

    def test_open_dir_common_tar(self):
        data_dir = pathlib.Path(self.data_path)

        opd = fl.Dir(
            path=pathlib.Path(f"{self.root_path}/test_common_dir.tar.gz"),
            compress="tar",
        )
        with opd.open(mode="w") as d:
            for data in data_dir.rglob("*"):
                d.add(name=data, arcname=data.relative_to(data_dir))

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.root_path)
