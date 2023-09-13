import unittest

import ddeutil.io.models as md


class ModelTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None

    def test_model_rule_data(self):
        rule = md.RuleData.model_validate({})

        self.assertDictEqual(
            {
                "timestamp": 0,
                "timestamp_metric": "minutes",
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
                    "timestamp": 15,
                },
            }
        )

        self.assertDictEqual(
            {
                "alias": "persisted",
                "format": "{timestamp:%Y-%m-%d}{naming:%c}.json",
                "rules": {
                    "timestamp": 15,
                    "timestamp_metric": "minutes",
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
                            "timestamp": 0,
                            "timestamp_metric": "minutes",
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
                            "timestamp": 0,
                            "timestamp_metric": "minutes",
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
                            "timestamp": 0,
                            "timestamp_metric": "minutes",
                            "version": None,
                            "excluded": [],
                            "compress": None,
                        },
                        "layer": 3,
                    },
                },
                "engine": {},
            },
            params.model_dump(),
        )
