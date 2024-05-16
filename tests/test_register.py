import shutil
from collections.abc import Generator
from pathlib import Path

import ddeutil.io.register as rgt
import pytest
import yaml
from ddeutil.io.models import Params


@pytest.fixture(scope="module")
def target_path(test_path) -> Generator[Path, None, None]:
    tgt_path: Path = test_path / "register_temp"
    tgt_path.mkdir(exist_ok=True)
    (tgt_path / "conf/demo").mkdir(parents=True)
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
    return Params.model_validate(
        {
            "engine": {
                "paths": {
                    "conf": target_path / "conf",
                    "data": root_path / "data",
                    "archive": root_path / "/data/.archive",
                },
                "flags": {"auto_update": True},
            },
            "stages": {
                "raw": {"format": "{naming:%s}.{timestamp:%Y%m%d_%H%M%S}"},
                "persisted": {"format": "{naming:%s}.{version:v%m.%n.%c}"},
            },
        }
    )


def test_register_init(params: Params):
    register = rgt.Register(name="demo:conn_local_file", params=params)

    assert "base" == register.stage
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

    print("\nChange compare from metadata:", register.changed)
    assert register.changed == 99

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
    rgt.Register.reset(name="demo:conn_local_file", params=params)


def test_register_without_params():
    try:
        rgt.Register(name="demo:conn_local_file")
    except NotImplementedError as err:
        assert (
            "This register instance can not do any actions because config "
            "param does not set."
        ) == str(err)
