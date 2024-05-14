from pathlib import Path

import ddeutil.io.register as rgt
import pytest
from ddeutil.io.models import Params


@pytest.fixture(scope="module")
def target_path(test_path) -> Path:
    return test_path / "conf_file_temp"


@pytest.fixture(scope="module")
def root_path(test_path) -> Path:
    return test_path.parent.parent


@pytest.fixture(scope="module")
def param_config(test_path, root_path) -> Params:
    return Params.model_validate(
        {
            "engine": {
                "paths": {
                    "conf": test_path / "examples/conf",
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


def test_register_init(param_config):
    register = rgt.Register(
        name="demo:conn_local_file",
        params=param_config,
    )

    assert "base" == register.stage
    assert {
        "alias": "conn_local_file",
        "type": "connection.LocalFileStorage",
        "endpoint": "file:///N%2FA/tests/examples/dummy",
    } == register.data()

    assert {
        "alias": "62d877a16819c672578d7bded7f5903c",
        "type": "cece9f1b3f4791a04ec3d695cb5ba1a9",
        "endpoint": "853dd5b0a2a4c58d8be2babdff0d7da8",
    } == register.data(hashing=True)

    print("\nChange compare from metadata:", register.changed)

    rsg_raw = register.move(stage="raw")

    assert "base" == register.stage
    assert "raw" == rsg_raw.stage

    assert (
        "62d877a16819c672578d7bded7f5903c"
        == rsg_raw.data(hashing=True)["alias"]
    )

    rgt.Register.reset(
        name="demo:conn_local_file",
        params=param_config,
    )


def test_register_without_config():
    try:
        rgt.Register(name="demo:conn_local_file")
    except NotImplementedError as err:
        assert (
            "This register instance can not do any actions because config "
            "param does not set."
        ) == str(err)
