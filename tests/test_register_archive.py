import shutil
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
import yaml
from ddeutil.io.config import Params
from ddeutil.io.exceptions import RegisterArgumentError
from ddeutil.io.register import ArchiveRegister, Register


@pytest.fixture(scope="module")
def target_path(test_path) -> Iterator[Path]:
    tgt_path: Path = test_path / "register_archive_temp"
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
                "raw": {
                    "format": "{naming:%s}.{timestamp:%Y%m%d_%H%M%S}",
                    "rule": {"timestamp": {"seconds": 2}},
                },
                "persisted": {"format": "{naming:%s}.{version:v%m.%n.%c}"},
            },
        }
    )


@pytest.fixture(scope="module")
def params_archive(target_path, root_path) -> Params:
    return Params(
        **{
            "paths": {
                "root": target_path,
                "data": target_path / "data_archive",
            },
            "stages": {
                "raw": {
                    "format": "{naming:%s}.{timestamp:%Y%m%d_%H%M%S}",
                    "rule": {"timestamp": {"seconds": 2}},
                },
                "persisted": {"format": "{naming:%s}.{version:v%m.%n.%c}"},
            },
        }
    )


def test_register_deploy(params, target_path):
    Register(name="demo:conn_local_file", params=params).deploy()
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

    time.sleep(1)

    register = Register(name="demo:conn_local_file", params=params).deploy()
    assert len(list((target_path / "data/raw").rglob("*"))) == 2

    time.sleep(2)

    register.purge(stage="persisted")

    with open(target_path / "conf/demo/test_01_conn.yaml", mode="w") as f:
        yaml.dump(
            {
                "conn_local_file": {
                    "type": "connection.LocalFileStorage",
                    "endpoint": "file:///${APP_PATH}/tests/examples/update",
                    "extra": {"foo": "baz"},
                }
            },
            f,
        )

    Register(name="demo:conn_local_file", params=params).deploy()
    assert len(list((target_path / "data/raw").rglob("*"))) != 3


def test_register_deploy_raise(params, target_path):
    with pytest.raises(RegisterArgumentError):
        Register(name="demo:conn_local_file", params=params).deploy(stop="foo")

    with pytest.raises(RegisterArgumentError):
        Register(name="demo:conn_local_file", params=params).remove()


def test_register_archive_deploy(params_archive, target_path):
    ArchiveRegister(name="demo:conn_local_file", params=params_archive).deploy()
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

    time.sleep(1)
    register = ArchiveRegister(
        name="demo:conn_local_file", params=params_archive
    ).deploy()
    assert len(list((target_path / "data_archive/raw").rglob("*"))) == 2

    time.sleep(2)

    register.purge(stage="persisted")

    with open(target_path / "conf/demo/test_01_conn.yaml", mode="w") as f:
        yaml.dump(
            {
                "conn_local_file": {
                    "type": "connection.LocalFileStorage",
                    "endpoint": "file:///${APP_PATH}/tests/examples/update",
                    "extra": {"foo": "baz"},
                }
            },
            f,
        )

    ArchiveRegister(name="demo:conn_local_file", params=params_archive).deploy()
    assert len(list((target_path / "data_archive/raw").rglob("*"))) != 3

    assert (
        len(
            list(
                (
                    target_path / f"data_archive/{ArchiveRegister.archiving}"
                ).rglob("*")
            )
        )
        > 0
    )

    register_persisted = ArchiveRegister(
        name="demo:conn_local_file", params=params_archive
    ).switch("persisted")

    register_persisted.remove()


def test_register_archive_deploy_raise(params_archive, target_path):
    with pytest.raises(RegisterArgumentError):
        ArchiveRegister(
            name="demo:conn_local_file", params=params_archive
        ).remove()
