import shutil
from collections.abc import Generator
from pathlib import Path

import ddeutil.io.config as conf
import pytest


@pytest.fixture(scope="module")
def sqlite_path(test_path) -> Generator[Path, None, None]:
    sqlite_path: Path = test_path / "conf_sqlite_temp"

    yield sqlite_path

    if sqlite_path.exists():
        shutil.rmtree(sqlite_path)


def test_base_conf_read_file(sqlite_path: Path):
    _schemas: dict[str, str] = {
        "name": "varchar(256) primary key",
        "shortname": "varchar(64) not null",
        "fullname": "varchar(256) not null",
        "data": "json not null",
        "updt": "datetime not null",
        "rtdt": "datetime not null",
        "author": "varchar(512) not null",
    }

    bc_sql = conf.ConfSQLite(sqlite_path)
    bc_sql.create(table="demo.db/temp_table", schemas=_schemas)

    assert (sqlite_path / "demo.db").exists()

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
