import os.path
import pathlib
import shutil
import unittest
from typing import Dict

import ddeutil.io.config as conf
import pytest


@pytest.mark.usefixtures("test_path_to_cls")
class BaseConfigSQLiteTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.demo_path: pathlib.Path = (
            self.test_path / "examples" / "conf" / "demo"
        )
        self.target_path: pathlib.Path = self.test_path / "conf_sqlite_temp"

    def test_base_conf_read_file(self):
        _schemas: Dict[str, str] = {
            "name": "varchar(256) primary key",
            "shortname": "varchar(64) not null",
            "fullname": "varchar(256) not null",
            "data": "json not null",
            "updt": "datetime not null",
            "rtdt": "datetime not null",
            "author": "varchar(512) not null",
        }

        bc_sql = conf.ConfSQLite(self.target_path)
        bc_sql.create(table="demo.db/temp_table", schemas=_schemas)

        self.assertTrue(os.path.exists(self.target_path / "demo.db"))

        _data = {
            "conn_local_data_landing": {
                "name": "conn_local_data_landing",
                "shortname": "cldl",
                "fullname": "conn_local_data_landing",
                "data": {"first_row": {"key": "value"}},
                "updt": "2023-01-01 00:00:00",
                "rtdt": "2023-01-01 00:00:00",
                "author": "unknown",
            },
        }

        bc_sql.save_stage(table="demo.db/temp_table", data=_data)

        self.assertDictEqual(
            _data,
            bc_sql.load_stage(
                table="demo.db/temp_table",
            ),
        )
        if os.path.exists(self.target_path):
            shutil.rmtree(self.target_path)
