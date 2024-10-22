import json
import shutil
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from ddeutil.io.config import Params
from ddeutil.io.register import Register


@pytest.fixture(scope="module")
def target_path(test_path) -> Generator[Path, None, None]:
    tgt_path: Path = test_path / "register_deploy_temp"
    tgt_path.mkdir(exist_ok=True)
    (tgt_path / "conf/demo").mkdir(parents=True, exist_ok=True)
    with open(tgt_path / "conf/demo/test_01_conn.yaml", mode="w") as f:
        yaml.dump(
            {
                "conn_local_file": {
                    "type": "conn.LocalFileStorage",
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
            "paths": {"root": target_path},
            "stages": {
                "raw": {"format": "{naming:%s}.{timestamp:%Y%m%d_%H%M%S}"},
                "staging": {"format": "{naming:%s}.{version:v%m.%n.%c}"},
                "persisted": {
                    "format": "{domain:%s}_{naming:%s}.{compress:%-g}",
                    "rule": {"compress": "gzip"},
                },
            },
        }
    )


@pytest.fixture(scope="module")
def mock_get_date():
    with patch(
        target="ddeutil.io.register.get_date",
        return_value=datetime(2024, 1, 1, 1),
    ) as mock:
        yield mock


def test_register_deploy(params, target_path, mock_get_date):
    assert mock_get_date.mocked

    data_path = target_path / "data"
    Register(name="demo:conn_local_file", params=params).deploy()
    assert (data_path / "staging/conn_local_file.v0.0.1.json").exists()
    assert (data_path / "raw/conn_local_file.20240101_010000.json").exists()
    assert (data_path / "persisted/demo_conn_local_file.gz.json").exists()


def test_register_multiple_files(params, target_path, root_path):
    data_path = target_path / "data"
    Register(name="demo:conn_local_file", params=params).deploy()

    with open(data_path / "raw/conn_local_file_new.json", mode="w") as f:
        json.dump({"foo": "bar"}, f)

    register = Register(name="demo:conn_local_file", stage="raw", params=params)
    assert str(register.version()) == "0.0.1"
