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
            name="demo:conn_local_data_landing",
            config=self.param_config,
        )

        self.assertEqual("base", register.stage)
        self.assertDictEqual(
            {
                "alias": "conn_local_data_landing",
                "type": "connection.LocalSystem",
                "endpoint": "file:///N/A/data/demo/landing",
            },
            register.data(),
        )

        self.assertDictEqual(
            {
                "alias": "8568c1f93ae0441b5648ad7768c16c66",
                "type": "4a5a116820c0ae3f54269945c1d81863",
                "endpoint": "0e029e878279e73aba794c90cce8e48c",
            },
            register.data(hashing=True),
        )

        print("\nChange compare from metadata:", register.changed)

        rsg_raw = register.move(stage="raw")

        self.assertEqual("base", register.stage)
        self.assertEqual("raw", rsg_raw.stage)

        self.assertEqual(
            "8568c1f93ae0441b5648ad7768c16c66",
            rsg_raw.data(hashing=True)["alias"],
        )

        rgt.Register.reset(
            name="demo:conn_local_data_landing",
            config=self.param_config,
        )

    def test_register_without_config(self):
        with self.assertRaises(NotImplementedError) as context:
            rgt.Register(name="demo:conn_local_data_landing")
        self.assertEqual(
            (
                "This register instance can not do any actions because config "
                "param does not set."
            ),
            str(context.exception),
        )
