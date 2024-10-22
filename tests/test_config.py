import os
from dataclasses import asdict
from pathlib import Path
from textwrap import dedent

import pytest
from ddeutil.io.config import Params, Paths, Rule, Stage
from ddeutil.io.exceptions import ConfigArgumentError


@pytest.fixture(scope="module")
def toml_conf_path(test_path):
    with open(test_path / "io-register.toml", mode="w") as f:
        f.write(
            dedent(
                """
                [tool.io.register.paths]
                root = "./"
                data = "./data"
                conf = "./conf"

                [tool.io.register.stages]
                raw = {format = "{naming:%s}.{timestamp:%Y%m%d_%H%M%S}"}
                persisted = {format = "{naming:%s}.{version:v%m.%n.%c}"}
                """.strip(
                    "\n"
                )
            )
        )
    yield test_path / "io-register.toml"
    os.unlink(test_path / "io-register.toml")


@pytest.fixture(scope="module")
def yaml_conf_path(test_path):
    with open(test_path / "io-register.yaml", mode="w") as f:
        f.write(
            dedent(
                """
            tool:
                io:
                    register:
                        paths:
                            root: "./"
                            data: "./data"
                            conf: "./conf"
                        stages:
                            raw:
                                layer: 1
                                format: "{naming:%s}.{timestamp:%Y%m%d_%H%M%S}"
                            persisted:
                                layer: 2
                                format: "{naming:%s}.{version:v%m.%n.%c}"
                """.strip(
                    "\n"
                )
            )
        )
    yield test_path / "io-register.yaml"
    os.unlink(test_path / "io-register.yaml")


def test_config_rule():
    assert {
        "timestamp": {},
        "excluded": [],
        "compress": None,
    } == asdict(Rule())


def test_config_stage():
    stage: Stage = Stage(
        **{
            "alias": "persisted",
            "format": "{timestamp:%Y-%m-%d}{naming:%c}.json",
            "rule": {
                "timestamp": {"minutes": 15},
            },
        }
    )
    assert stage.rule.compress is None
    assert stage.alias == "persisted"
    assert stage.format == "{timestamp:%Y-%m-%d}{naming:%c}.json"


def test_config_stage_raise():
    with pytest.raises(ConfigArgumentError):
        Stage(
            **{
                "alias": "persisted",
                "format": "{ts:%Y-%m-%d}{naming:%c}.json",
            }
        )

    with pytest.raises(ConfigArgumentError):
        Stage(
            **{
                "alias": "persisted",
                "format": "fix_format_name.json",
            }
        )

    with pytest.raises(ConfigArgumentError):
        Stage(
            **{
                "alias": "persisted",
                "format": "{naming:%c}.json",
                "rule": {
                    "timestamp": {"minutes": 15},
                },
            }
        )


def test_config_paths():
    paths = Paths()
    assert Path() == paths.root
    assert Path() / "data" == paths.data
    assert Path() / "conf" == paths.conf

    os.environ["IO_REGISTER_ROOT_PATH"] = "./core"
    paths = Paths()
    assert Path("./core") == paths.root

    os.environ.pop("IO_REGISTER_ROOT_PATH")

    paths = Paths(
        root="./core",
        data="./core/data",
        conf="../conf",
    )
    assert Path("./core") == paths.root
    assert Path("./core/data") == paths.data
    assert Path("../conf") == paths.conf


def test_config_params():
    params: Params = Params(
        **{
            "stages": {
                "raw": {"format": "{naming:%s}.{timestamp:%Y%m%d_%H%M%S}"},
                "persisted": {"format": "{naming:%s}.{version:v%m.%n.%c}"},
                "curated": Stage(
                    **{"format": "{domain:%s}_{naming:%s}.{compress:%-g}"}
                ),
            }
        }
    )
    assert {
        "stages": {
            "raw": {
                "format": "{naming:%s}.{timestamp:%Y%m%d_%H%M%S}",
                "alias": "raw",
                "rule": {
                    "timestamp": {},
                    "excluded": [],
                    "compress": None,
                },
                "layer": 1,
            },
            "persisted": {
                "format": "{naming:%s}.{version:v%m.%n.%c}",
                "alias": "persisted",
                "rule": {
                    "timestamp": {},
                    "excluded": [],
                    "compress": None,
                },
                "layer": 2,
            },
            "curated": {
                "format": "{domain:%s}_{naming:%s}.{compress:%-g}",
                "alias": "curated",
                "rule": {
                    "timestamp": {},
                    "excluded": [],
                    "compress": None,
                },
                "layer": 3,
            },
        },
        "paths": {
            "conf": Path() / "./conf",
            "data": Path() / "./data",
            "root": Path(),
        },
    } == asdict(params)

    assert params.stage_first == "raw"
    assert params.stage_final == "curated"
    assert params.get_stage(name="base").alias == "base"

    with pytest.raises(ConfigArgumentError):
        params.get_stage("not_found")


def test_config_params_raise():
    with pytest.raises(ConfigArgumentError):
        Params(**{"stages": {"raw": "{naming:%s}.{timestamp:%Y%m%d_%H%M%S}"}})


def test_config_params_toml(toml_conf_path):
    params = Params.from_toml(toml_conf_path)
    assert {
        "stages": {
            "raw": {
                "format": "{naming:%s}.{timestamp:%Y%m%d_%H%M%S}",
                "alias": "raw",
                "rule": {
                    "timestamp": {},
                    "excluded": [],
                    "compress": None,
                },
                "layer": 1,
            },
            "persisted": {
                "format": "{naming:%s}.{version:v%m.%n.%c}",
                "alias": "persisted",
                "rule": {
                    "timestamp": {},
                    "excluded": [],
                    "compress": None,
                },
                "layer": 2,
            },
        },
        "paths": {
            "conf": Path("conf"),
            "data": Path("data"),
            "root": Path("."),
        },
    } == params.to_dict()


def test_config_params_yaml(yaml_conf_path):
    params = Params.from_yaml(yaml_conf_path)
    assert {
        "stages": {
            "raw": {
                "format": "{naming:%s}.{timestamp:%Y%m%d_%H%M%S}",
                "alias": "raw",
                "rule": {
                    "timestamp": {},
                    "excluded": [],
                    "compress": None,
                },
                "layer": 1,
            },
            "persisted": {
                "format": "{naming:%s}.{version:v%m.%n.%c}",
                "alias": "persisted",
                "rule": {
                    "timestamp": {},
                    "excluded": [],
                    "compress": None,
                },
                "layer": 2,
            },
        },
        "paths": {
            "conf": Path("conf"),
            "data": Path("data"),
            "root": Path("."),
        },
    } == asdict(params)
