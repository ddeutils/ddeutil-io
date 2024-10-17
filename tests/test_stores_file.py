import shutil
from collections.abc import Generator
from pathlib import Path

import pytest
import yaml
from ddeutil.io.stores import BaseStoreFl, StoreFl


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
    base_store = BaseStoreFl(target_path)

    assert {
        "alias": "conn_local_file",
        "endpoint": "file:///null/tests/examples/dummy",
        "type": "connection.LocalFileStorage",
    } == base_store.get(name="conn_local_file")

    base_store.move(
        "test_01_conn.yaml",
        dest=target_path / "connections/test_01_conn.yaml",
    )

    base_store_temp = BaseStoreFl(target_path)
    assert {
        "alias": "conn_local_file",
        "endpoint": "file:///null/tests/examples/dummy",
        "type": "connection.LocalFileStorage",
    } == base_store_temp.get(name="conn_local_file")

    assert (target_path / "connections/test_01_conn.yaml").exists()


def test_conf_read_file(target_path):
    store = StoreFl(target_path)
    store.move(
        path="test_01_conn.yaml",
        dest=target_path / "connections/test_01_conn.yaml",
    )

    stage_path: Path = target_path / "connections/test_01_conn_stage.json"

    store.create(path=stage_path)
    assert stage_path.exists()
    store.save(path=stage_path, data=store.get("conn_local_file"))

    assert {
        "alias": "conn_local_file",
        "endpoint": "file:///null/tests/examples/dummy",
        "type": "connection.LocalFileStorage",
    } == store.load(path=stage_path)

    store.save(
        path=stage_path,
        data={"temp_additional": store.get("conn_local_file")},
        merge=True,
    )

    store.remove(
        path=stage_path,
        name="temp_additional",
    )

    assert {
        "alias": "conn_local_file",
        "endpoint": "file:///null/tests/examples/dummy",
        "type": "connection.LocalFileStorage",
    } == store.load(path=stage_path)
