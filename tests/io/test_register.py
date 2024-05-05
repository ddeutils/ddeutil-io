import unittest
import warnings

import ddeutil.io.register as rgt
import pytest
from ddeutil.io.models import Params


@pytest.mark.usefixtures("test_path_to_cls")
class RegisterTestCase(unittest.TestCase):
    def setUp(self) -> None:
        warnings.simplefilter("ignore", category=ResourceWarning)
        self.param_config = Params.model_validate(
            {
                "engine": {
                    "paths": {
                        "conf": self.test_path / "examples/conf",
                        "data": self.root_path / "data",
                        "archive": self.root_path / "/data/.archive",
                    },
                    "flags": {"auto_update": True},
                },
                "stages": {
                    "raw": {"format": "{naming:%s}.{timestamp:%Y%m%d_%H%M%S}"},
                    "persisted": {"format": "{naming:%s}.{version:v%m.%n.%c}"},
                },
            }
        )

    def test_register_init(self):
        register = rgt.Register(
            name="demo:conn_local_file",
            config=self.param_config,
        )

        self.assertEqual("base", register.stage)
        self.assertDictEqual(
            {
                "alias": "conn_local_file",
                "type": "connection.LocalFileStorage",
                "endpoint": "file:///N%2FA/tests/examples/dummy",
            },
            register.data(),
        )

        self.assertDictEqual(
            {
                "alias": "62d877a16819c672578d7bded7f5903c",
                "type": "cece9f1b3f4791a04ec3d695cb5ba1a9",
                "endpoint": "853dd5b0a2a4c58d8be2babdff0d7da8",
            },
            register.data(hashing=True),
        )

        print("\nChange compare from metadata:", register.changed)

        rsg_raw = register.move(stage="raw")

        self.assertEqual("base", register.stage)
        self.assertEqual("raw", rsg_raw.stage)

        self.assertEqual(
            "62d877a16819c672578d7bded7f5903c",
            rsg_raw.data(hashing=True)["alias"],
        )

        rgt.Register.reset(
            name="demo:conn_local_file",
            config=self.param_config,
        )

    def test_register_without_config(self):
        with self.assertRaises(NotImplementedError) as context:
            rgt.Register(name="demo:conn_local_file")
        self.assertEqual(
            (
                "This register instance can not do any actions because config "
                "param does not set."
            ),
            str(context.exception),
        )
