import shutil
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
import yaml
from ddeutil.io.config import Params
from ddeutil.io.exceptions import RegisterArgumentError
from ddeutil.io.register import Register


@pytest.fixture(scope="module")
def target_path(test_path) -> Iterator[Path]:
    tgt_path: Path = test_path / "register_temp"
    tgt_path.mkdir(exist_ok=True)
    (tgt_path / "conf/demo").mkdir(parents=True, exist_ok=True)
    with open(tgt_path / "conf/demo/test_01_conn.yaml", mode="w") as f:
        yaml.dump(
            {
                "conn_local_file": {
                    "type": "connection.LocalFileStorage",
                    "endpoint": "file:///${APP_PATH}/tests/examples/dummy",
                }
            },
            f,
        )
    yield tgt_path
    shutil.rmtree(tgt_path)


@pytest.fixture(scope="module")
def params(target_path, root_path) -> Params:
    return Params(
        **{
            "paths": {
                "conf": target_path / "conf",
                "data": root_path / "data",
            },
            "stages": {
                "raw": {"format": "{naming:%s}.{timestamp:%Y%m%d_%H%M%S}"},
                "persisted": {"format": "{naming:%s}.{version:v%m.%n.%c}"},
            },
        }
    )


@pytest.fixture(scope="module")
def mock_get_date():
    with patch(
        target="ddeutil.io.register.get_date",
        return_value=datetime(2024, 1, 1, 1, tzinfo=ZoneInfo("UTC")),
    ) as mock:
        yield mock


def test_register(params: Params, mock_get_date):
    assert mock_get_date.mocked

    register = Register(name="demo:conn_local_file", params=params)

    assert str(register) == "(demo:conn_local_file, base)"
    assert repr(register) == "<Register(name='demo:conn_local_file')>"
    assert register.stage == "base"
    assert register.shortname == "clf"
    assert register.fullname == "demo:conn_local_file"

    assert {
        "alias": "conn_local_file",
        "type": "connection.LocalFileStorage",
        "endpoint": "file:///null/tests/examples/dummy",
    } == register.data()

    assert {
        "alias": "62d877a16819c672578d7bded7f5903c",
        "type": "cece9f1b3f4791a04ec3d695cb5ba1a9",
        "endpoint": "0d1db48bb2425db014fc66734508098f",
    } == register.data(hashing=True)

    assert register.changed == 99
    assert str(register.version()) == "0.0.1"

    rsg_raw = register.move(stage="raw")

    assert register.stage != rsg_raw.stage
    assert (
        "62d877a16819c672578d7bded7f5903c"
        == rsg_raw.data(hashing=True)["alias"]
    )

    rsg_persisted = rsg_raw.move(stage="persisted")
    assert rsg_raw.stage != rsg_persisted.stage
    assert (
        "62d877a16819c672578d7bded7f5903c"
        == rsg_persisted.data(hashing=True)["alias"]
    )
    Register.reset(name="demo:conn_local_file", params=params)

    rsg_raw = register.move(stage="raw")
    assert rsg_raw.changed == 99
    assert rsg_raw.timestamp == datetime(2024, 1, 1, 1, tzinfo=ZoneInfo("UTC"))

    register = Register(name="demo:conn_local_file", params=params)
    register.move(stage="raw")

    Register.reset(name="demo:conn_local_file", params=params)


def test_register_compare(params, mock_get_date):
    assert mock_get_date.mocked

    register_01 = Register(name="demo:conn_local_file", params=params)
    register_02 = Register(name="demo:conn_local_file", params=params)
    assert register_01 == register_02
    assert register_01 != "demo:conn_local_file"


def test_register_reset(params: Params):
    Register.reset(name="demo:conn_local_file", params=params)

    register = Register(name="demo:conn_local_file", params=params)
    register.move("raw")
    register.reset(name="demo:conn_local_file", params=params)


def test_register_raise():
    with pytest.raises(RegisterArgumentError):
        Register(name="demo.conn_local_file")

    with pytest.raises(NotImplementedError):
        Register(name="demo:conn_local_file")


def test_register_change_data(params, target_path):
    register = Register(name="demo:conn_local_file", params=params)
    register_raw = register.move(stage="raw", retention=False)
    origin_updt = register_raw.timestamp
    register = Register(name="demo:conn_local_file", params=params)
    assert register.changed == 0

    register_raw = register.move(stage="raw")
    assert origin_updt == register_raw.timestamp

    with open(target_path / "conf/demo/test_01_conn.yaml", mode="w") as f:
        yaml.dump(
            {
                "conn_local_file": {
                    "type": "connection.LocalFileStorage",
                    "endpoint": "file:///${APP_PATH}/tests/examples/new",
                }
            },
            f,
        )
    register = Register(name="demo:conn_local_file", params=params)
    assert register.changed == 1

    register_raw = register.move(stage="raw")
    assert register_raw.data()["__version"] == "v0.0.2"

    with open(target_path / "conf/demo/test_01_conn.yaml", mode="w") as f:
        yaml.dump(
            {
                "conn_local_file": {
                    "type": "connection.LocalFileStorage",
                    "endpoint": "file:///${APP_PATH}/tests/examples/new",
                    "extra": {"foo": "bar"},
                }
            },
            f,
        )

    register = Register(name="demo:conn_local_file", params=params)
    assert register.changed == 2

    register_raw = register.move(stage="raw")
    assert register_raw.data()["__version"] == "v0.1.0"
