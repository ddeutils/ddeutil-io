import pathlib
import unittest

import ddeutil.io.models as md


class ModelTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None

    def test_model_path_data(self):
        p = md.PathData.model_validate(
            {
                "data": pathlib.Path(".."),
                "conf": pathlib.Path(".."),
                "archive": pathlib.Path(".."),
            }
        )

        self.assertDictEqual(
            {
                "data": pathlib.Path(".."),
                "conf": pathlib.Path(".."),
                "archive": pathlib.Path(".."),
                "root": pathlib.Path("."),
            },
            p.model_dump(),
        )

    def test_model_path_data_with_root(self):
        p = md.PathData.model_validate(
            {
                "root": "./src/",
            }
        )

        self.assertDictEqual(
            {
                "data": pathlib.Path("./src/data"),
                "conf": pathlib.Path("./src/conf"),
                "archive": pathlib.Path("./src/.archive"),
                "root": pathlib.Path("./src/"),
            },
            p.model_dump(),
        )

    def test_model_rule_data(self):
        rule = md.RuleData.model_validate({})

        self.assertDictEqual(
            {
                "timestamp": {},
                "version": None,
                "excluded": [],
                "compress": None,
            },
            rule.model_dump(),
        )

    def test_model_stage_data(self):
        stage = md.StageData.model_validate(
            {
                "alias": "persisted",
                "format": "{timestamp:%Y-%m-%d}{naming:%c}.json",
                "rules": {
                    "timestamp": {"minutes": 15},
                },
            }
        )

        self.assertDictEqual(
            {
                "alias": "persisted",
                "format": "{timestamp:%Y-%m-%d}{naming:%c}.json",
                "rules": {
                    "timestamp": {"minutes": 15},
                    "version": None,
                    "excluded": [],
                    "compress": None,
                },
                "layer": 0,
            },
            stage.model_dump(),
        )

    def test_model_params(self):
        params = md.Params.model_validate(
            {
                "stages": {
                    "raw": {"format": "{naming:%s}.{timestamp:%Y%m%d_%H%M%S}"},
                    "persisted": {"format": "{naming:%s}.{version:v%m.%n.%c}"},
                    "curated": {
                        "format": "{domain:%s}_{naming:%s}.{compress:%-g}"
                    },
                }
            }
        )
        self.assertDictEqual(
            {
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
                        "datetime_fmt": "%Y-%m-%d %H:%M:%S",
                        "excluded_keys": ("version", "updt"),
                    },
                    "flags": {
                        "archive": False,
                        "auto_update": False,
                    },
                    "paths": {
                        "archive": pathlib.Path(".archive"),
                        "conf": pathlib.Path("conf"),
                        "data": pathlib.Path("data"),
                        "root": pathlib.Path("."),
                    },
                },
            },
            params.model_dump(),
        )
