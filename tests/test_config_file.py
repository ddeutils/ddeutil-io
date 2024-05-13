import shutil
from pathlib import Path

import ddeutil.io.config as conf
import pytest


@pytest.fixture(scope="module")
def target_path(test_path) -> Path:
    return test_path / "conf_file_temp"


@pytest.fixture(scope="module")
def demo_path(test_path) -> Path:
    return test_path / "examples" / "conf" / "demo"


def test_base_conf_read_file(demo_path, target_path):
    bcf = conf.BaseConfFile(demo_path)

    assert {
        "alias": "conn_local_file",
        "endpoint": "file:///N%2FA/tests/examples/dummy",
        "type": "connection.LocalFileStorage",
    } == bcf.load(name="conn_local_file")

    bcf.move(
        "demo_01_connections.yaml",
        destination=target_path / "demo_01_connections.yaml",
    )

    bcf_temp = conf.BaseConfFile(target_path)
    assert {
        "alias": "conn_local_file",
        "endpoint": "file:///N%2FA/tests/examples/dummy",
        "type": "connection.LocalFileStorage",
    } == bcf_temp.load(name="conn_local_file")

    assert (target_path / "demo_01_connections.yaml").exists()

    if target_path.exists():
        shutil.rmtree(target_path)


def test_conf_read_file(demo_path, target_path):
    cf = conf.ConfFile(demo_path)
    cf.move(
        path="demo_01_connections.yaml",
        destination=target_path / "demo_01_connections.yaml",
    )

    _stage_path = target_path / "demo_01_connections_stage.json"

    cf.create(path=_stage_path)
    assert _stage_path.exists()
    cf.save_stage(path=_stage_path, data=cf.load("conn_local_file"))

    assert {
        "alias": "conn_local_file",
        "endpoint": "file:///N%2FA/tests/examples/dummy",
        "type": "connection.LocalFileStorage",
    } == cf.load_stage(path=_stage_path)

    cf.save_stage(
        path=_stage_path,
        data={"temp_additional": cf.load("conn_local_file")},
        merge=True,
    )

    cf.remove_stage(
        path=_stage_path,
        name="temp_additional",
    )

    assert {
        "alias": "conn_local_file",
        "endpoint": "file:///N%2FA/tests/examples/dummy",
        "type": "connection.LocalFileStorage",
    } == cf.load_stage(path=_stage_path)

    if target_path.exists():
        shutil.rmtree(target_path)
