from pathlib import Path

import ddeutil.io.models as md


def test_model_path_default(test_path):
    p = md.PathData.model_validate(
        {
            "root": test_path,
        }
    )
    print(p)


def test_model_path_data():
    p = md.PathData.model_validate(
        {
            "data": Path("."),
            "conf": Path("."),
            "archive": Path("."),
        }
    )

    assert {
        "data": Path("."),
        "conf": Path("."),
        "archive": Path("."),
        "root": Path("."),
    } == p.model_dump()


def test_model_path_data_with_root():
    p = md.PathData.model_validate({"root": "./src/"})
    assert {
        "data": Path("./src/data"),
        "conf": Path("./src/conf"),
        "archive": Path("./src/.archive"),
        "root": Path("./src/"),
    } == p.model_dump()


def test_model_rule_data():
    assert {
        "timestamp": {},
        "version": None,
        "excluded": [],
        "compress": None,
    } == md.RuleData.model_validate({}).model_dump()


def test_model_stage_data():
    stage = md.StageData.model_validate(
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
                "excluded": ("version", "updt"),
            },
            "flags": {
                "archive": False,
                "auto_update": False,
            },
            "paths": {
                "archive": Path(".archive"),
                "conf": Path("conf"),
                "data": Path("data"),
                "root": Path("."),
            },
        },
    } == params.model_dump()
