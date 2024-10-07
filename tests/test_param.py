from pathlib import Path

import ddeutil.io.param as md
import pytest
from ddeutil.io.conf import UPDATE_KEY, VERSION_KEY
from ddeutil.io.exceptions import ConfigArgumentError


def test_param_path_data_default(test_path):
    param = md.PathData.model_validate({"root": test_path})
    assert param.root == test_path


def test_param_path_data():
    p = md.PathData.model_validate({"data": Path("."), "conf": Path(".")})
    assert {
        "data": Path("."),
        "conf": Path("."),
        "root": Path("."),
    } == p.model_dump()


def test_model_path_data_with_root():
    p = md.PathData.model_validate({"root": "./src/"})
    assert {
        "data": Path("./src/data"),
        "conf": Path("./src/conf"),
        "root": Path("./src/"),
    } == p.model_dump()


def test_model_rule_data():
    assert {
        "timestamp": {},
        "version": None,
        "excluded": [],
        "compress": None,
    } == md.Rule.model_validate({}).model_dump()


def test_model_stage_data():
    stage = md.Stage.model_validate(
        {
            "alias": "persisted",
            "format": "{timestamp:%Y-%m-%d}{naming:%c}.json",
            "rules": {
                "timestamp": {"minutes": 15},
            },
        }
    )

    assert {
        "alias": "persisted",
        "format": "{timestamp:%Y-%m-%d}{naming:%c}.json",
        "rules": {
            "timestamp": {"minutes": 15},
            "version": None,
            "excluded": [],
            "compress": None,
        },
        "layer": 0,
    } == stage.model_dump()

    with pytest.raises(ConfigArgumentError):
        md.Stage.model_validate(
            {
                "alias": "persisted",
                "format": "timestamp.json",
                "rules": {
                    "timestamp": {"minutes": 15},
                },
            }
        )

    with pytest.raises(ConfigArgumentError):
        md.Stage.model_validate(
            {
                "alias": "persisted",
                "format": "{datetime:%Y%m%d}.json",
                "rules": {
                    "timestamp": {"minutes": 15},
                },
            }
        )


def test_model_params():
    params = md.Params.model_validate(
        {
            "stages": {
                "raw": {"format": "{naming:%s}.{timestamp:%Y%m%d_%H%M%S}"},
                "persisted": {"format": "{naming:%s}.{version:v%m.%n.%c}"},
                "curated": {"format": "{domain:%s}_{naming:%s}.{compress:%-g}"},
            }
        }
    )
    assert {
        "stages": {
            "raw": {
                "format": "{naming:%s}.{timestamp:%Y%m%d_%H%M%S}",
                "alias": "raw",
                "rules": {
                    "timestamp": {},
                    "version": None,
                    "excluded": [],
                    "compress": None,
                },
                "layer": 1,
            },
            "persisted": {
                "format": "{naming:%s}.{version:v%m.%n.%c}",
                "alias": "persisted",
                "rules": {
                    "timestamp": {},
                    "version": None,
                    "excluded": [],
                    "compress": None,
                },
                "layer": 2,
            },
            "curated": {
                "format": "{domain:%s}_{naming:%s}.{compress:%-g}",
                "alias": "curated",
                "rules": {
                    "timestamp": {},
                    "version": None,
                    "excluded": [],
                    "compress": None,
                },
                "layer": 3,
            },
        },
        "engine": {
            "values": {
                "dt_fmt": "%Y-%m-%d %H:%M:%S",
                "excluded": (VERSION_KEY, UPDATE_KEY),
            },
            "paths": {
                "conf": Path("conf"),
                "data": Path("data"),
                "root": Path("."),
            },
        },
    } == params.model_dump()
