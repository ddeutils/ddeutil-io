import shutil
from pathlib import Path

import ddeutil.io.config as conf
import pytest


@pytest.fixture(scope="module")
def target_path(test_path) -> Path:
    return test_path / "conf_sqlite_temp"


@pytest.fixture(scope="module")
def demo_path(test_path) -> Path:
    return test_path / "examples" / "conf" / "demo"


def test_base_conf_read_file(demo_path, target_path):
    _schemas: dict[str, str] = {
        "name": "varchar(256) primary key",
        "shortname": "varchar(64) not null",
        "fullname": "varchar(256) not null",
        "data": "json not null",
        "updt": "datetime not null",
        "rtdt": "datetime not null",
        "author": "varchar(512) not null",
    }

    bc_sql = conf.ConfSQLite(target_path)
    bc_sql.create(table="demo.db/temp_table", schemas=_schemas)

    assert (target_path / "demo.db").exists()

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

    assert _data == bc_sql.load_stage(table="demo.db/temp_table")
    if target_path.exists():
        shutil.rmtree(target_path)
