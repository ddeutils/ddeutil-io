import shutil
from collections.abc import Generator
from pathlib import Path

import pytest
import yaml
from ddeutil.io.param import Params
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
                "staging": {"format": "{naming:%s}.{version:v%m.%n.%c}"},
                "persisted": {
                    "format": "{domain:%s}_{naming:%s}.{compress:%-g}",
                    "rules": {
                        "compress": "gzip",
                    },
                },
            },
        }
    )


def test_register_deployment(params):
    rs = Register(name="demo:conn_local_file", params=params).deploy()
    assert "(demo:conn_local_file, persisted)" == str(rs)
