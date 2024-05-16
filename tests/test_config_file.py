import shutil
from collections.abc import Generator
from pathlib import Path

import ddeutil.io.config as conf
import pytest
import yaml


@pytest.fixture(scope="module")
def target_path(test_path) -> Generator[Path, None, None]:
    tgt_path: Path = test_path / "conf_file_temp"
    tgt_path.mkdir(exist_ok=True)
    with open(tgt_path / "test_01_conn.yaml", mode="w") as f:
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


def test_base_conf_read_file(target_path):
    bcf = conf.BaseConfFl(target_path)

    assert {
        "alias": "conn_local_file",
        "endpoint": "file:///null/tests/examples/dummy",
        "type": "connection.LocalFileStorage",
    } == bcf.load(name="conn_local_file")

    bcf.move(
        "test_01_conn.yaml",
        destination=target_path / "connections/test_01_conn.yaml",
    )

    bcf_temp = conf.BaseConfFl(target_path)
    assert {
        "alias": "conn_local_file",
        "endpoint": "file:///null/tests/examples/dummy",
        "type": "connection.LocalFileStorage",
    } == bcf_temp.load(name="conn_local_file")

    assert (target_path / "connections/test_01_conn.yaml").exists()


def test_conf_read_file(target_path):
    cf = conf.ConfFl(target_path)
    cf.move(
        path="test_01_conn.yaml",
        destination=target_path / "connections/test_01_conn.yaml",
    )

    _stage_path: Path = target_path / "connections/test_01_conn_stage.json"

    cf.create(path=_stage_path)
    assert _stage_path.exists()
    cf.save_stage(path=_stage_path, data=cf.load("conn_local_file"))

    assert {
        "alias": "conn_local_file",
        "endpoint": "file:///null/tests/examples/dummy",
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
        "endpoint": "file:///null/tests/examples/dummy",
        "type": "connection.LocalFileStorage",
    } == cf.load_stage(path=_stage_path)
