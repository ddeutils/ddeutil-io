from __future__ import annotations

import json
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
import yaml
from ddeutil.io.files import CsvPipeFl, JsonEnvFl
from ddeutil.io.stores import Store


@pytest.fixture(scope="module")
def target_path(test_path) -> Iterator[Path]:
    """Create ./conf_file_temp/test_01_conn.yaml file on the current test path.
    This file already add data 'conn_local_file' for the store object able to
    test getting and moving.
    """
    tgt_path: Path = test_path / "store_file"
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

    with open(tgt_path / "test_01_conn.json", mode="w") as f:
        json.dump(
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
def new_path(test_path: Path) -> Iterator[Path]:
    new_path = test_path / "store_file_new"
    yield new_path
    shutil.rmtree(new_path)


def test_store_init(new_path):
    store = Store(new_path)
    assert new_path == store.path
    assert store.path.exists()


def test_store_get(target_path):
    store = Store(target_path)

    assert {
        "alias": "conn_local_file",
        "endpoint": "file:///null/tests/examples/dummy",
        "type": "connection.LocalFileStorage",
    } == store.get(name="conn_local_file")

    assert {
        "alias": "conn_local_file",
        "endpoint": "file:///null/tests/examples/dummy",
        "type": "connection.LocalFileStorage",
    } == store.get(name="conn_local_file", order=1)

    assert {} == store.get(name="conn_local_file_not_found")
    assert {} == store.get(name="conn_local_file", order=2)
    assert {} == store.get(name="conn_local_file", order=10)


def test_store_move(target_path):
    store = Store(target_path)
    store.move(
        "test_01_conn.yaml",
        dest=target_path / "connections/test_01_conn_new.yaml",
    )
    assert (target_path / "connections/test_01_conn_new.yaml").exists()

    base_store_temp = Store(target_path)
    assert {
        "alias": "conn_local_file",
        "endpoint": "file:///null/tests/examples/dummy",
        "type": "connection.LocalFileStorage",
    } == base_store_temp.get(name="conn_local_file", order=1)
    assert {
        "alias": "conn_local_file",
        "endpoint": "file:///null/tests/examples/dummy",
        "type": "connection.LocalFileStorage",
    } == base_store_temp.get(name="conn_local_file", order=2)


def test_store_json(target_path):
    store = Store(
        target_path,
        open_file=JsonEnvFl,
        included_file_fmt=("*.json",),
        excluded_file_fmt=("*.yml", "*.yaml", "*.toml"),
    )
    assert {
        "alias": "conn_local_file",
        "endpoint": "file:///null/tests/examples/dummy",
        "type": "connection.LocalFileStorage",
    } == store.get(name="conn_local_file")


def test_store_csv_stage(target_path):
    store = Store(
        target_path,
        open_file=JsonEnvFl,
        open_file_stg=CsvPipeFl,
        included_file_fmt=("*.json",),
        excluded_file_fmt=("*.yml", "*.yaml", "*.toml"),
    )
    store.move(
        path="test_01_conn.json",
        dest=target_path / "connections/test_01_conn.json",
    )

    stage_path: Path = target_path / "connections/test_01_conn_stage.json"

    store.save(
        path=stage_path,
        data={"temp_additional": store.get("conn_local_file")},
        merge=True,
    )


def test_store(target_path):
    store = Store(target_path)
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

    assert {} == store.load(
        path=target_path / "connections/test_01_conn_stage_failed.json"
    )
    assert {"foo": "bar"} == store.load(
        path=target_path / "connections/test_01_conn_stage_failed.json",
        default={"foo": "bar"},
    )

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

    store.remove(
        target_path / "connections/test_01_conn_stage_not_fount.json",
        name="first",
    )


def test_store_save(target_path):
    store = Store(target_path)
    stage_path: Path = target_path / "connections/test_01_conn_stage.json"
    stage_path.parent.mkdir(parents=True, exist_ok=True)
    store.save(
        path=stage_path,
        data={"first": store.get("conn_local_file")} | {"version": 1},
        merge=True,
    )
    store.save(
        path=stage_path,
        data={"second": store.get("conn_local_file")} | {"version": 2},
        merge=True,
    )

    assert 2 == store.load(path=stage_path).get("version")


def test_store_save_raise(target_path):
    store = Store(target_path)
    stage_path: Path = target_path / "connections/test_01_conn_stage.json"
    stage_path.parent.mkdir(parents=True, exist_ok=True)
    store.save(
        path=stage_path,
        data={"first": store.get("conn_local_file")} | {"version": 1},
        merge=True,
    )

    with pytest.raises(TypeError):
        store.save(
            path=stage_path,
            data="conn_local_file",
            merge=True,
        )

    store.remove(stage_path, name="first")
