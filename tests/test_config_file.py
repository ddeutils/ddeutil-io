import os.path
import pathlib
import shutil
import unittest

import ddeutil.io.config as conf
import pytest


@pytest.mark.usefixtures("test_path_to_cls")
class BaseConfigFileTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.demo_path: pathlib.Path = (
            self.test_path / "examples" / "conf" / "demo"
        )
        self.target_path: pathlib.Path = self.test_path / "conf_file_temp"

    def test_base_conf_read_file(self):
        bcf = conf.BaseConfFile(self.demo_path)

        self.assertDictEqual(
            {
                "alias": "conn_local_data_landing",
                "endpoint": "file:///N/A/data/demo/landing",
                "type": "connection.LocalSystem",
            },
            bcf.load(name="conn_local_data_landing"),
        )

        bcf.move(
            "demo_01_connections.yaml",
            destination=self.target_path / "demo_01_connections.yaml",
        )

        bcf_temp = conf.BaseConfFile(self.target_path)
        self.assertDictEqual(
            {
                "alias": "conn_local_data_landing",
                "endpoint": "file:///N/A/data/demo/landing",
                "type": "connection.LocalSystem",
            },
            bcf_temp.load(name="conn_local_data_landing"),
        )

        self.assertTrue(
            os.path.exists(self.target_path / "demo_01_connections.yaml")
        )

        if os.path.exists(self.target_path):
            shutil.rmtree(self.target_path)


@pytest.mark.usefixtures("test_path_to_cls")
class ConfigFileTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.demo_path: pathlib.Path = (
            self.test_path / "examples" / "conf" / "demo"
        )
        self.target_path: pathlib.Path = self.test_path / "conf_file_temp"

    def test_base_conf_read_file(self):
        cf = conf.ConfFile(self.demo_path)
        cf.move(
            path="demo_01_connections.yaml",
            destination=self.target_path / "demo_01_connections.yaml",
        )

        _stage_path = self.target_path / "demo_01_connections_stage.json"

        cf.create(path=_stage_path)
        self.assertTrue(os.path.exists(_stage_path))
        cf.save_stage(path=_stage_path, data=cf.load("conn_local_data_landing"))

        self.assertDictEqual(
            {
                "alias": "conn_local_data_landing",
                "endpoint": "file:///N/A/data/demo/landing",
                "type": "connection.LocalSystem",
            },
            cf.load_stage(path=_stage_path),
        )

        cf.save_stage(
            path=_stage_path,
            data={"temp_additional": cf.load("conn_local_data_landing")},
            merge=True,
        )

        cf.remove_stage(
            path=_stage_path,
            name="temp_additional",
        )

        self.assertDictEqual(
            {
                "alias": "conn_local_data_landing",
                "endpoint": "file:///N/A/data/demo/landing",
                "type": "connection.LocalSystem",
            },
            cf.load_stage(path=_stage_path),
        )

        if os.path.exists(self.target_path):
            shutil.rmtree(self.target_path)
