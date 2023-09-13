import os
import unittest
import warnings
from textwrap import dedent

import ddeutil.io.base.files as fl
import yaml


class YamlFileTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root_path: str = os.path.dirname(os.path.abspath(__file__)).replace(
            os.sep, "/"
        )

    def setUp(self) -> None:
        warnings.simplefilter("ignore", category=ResourceWarning)
        self.yaml_str: str = dedent(
            """
        main_key:
            sub_key:
                string: 'test ${DEMO_ENV_VALUE} value'
                int: 0.001
                bool: false
                list: ['i1', 'i2', 'i3']
        """
        ).strip()
        self.yaml_data: dict = {
            "main_key": {
                "sub_key": {
                    "string": "test ${DEMO_ENV_VALUE} value",
                    "int": 0.001,
                    "bool": False,
                    "list": ["i1", "i2", "i3"],
                }
            }
        }

    def test_write_yaml_file_with_safe_mode(self):
        yaml_path: str = f"{self.root_path}/test_write_file.yaml"

        fl.Yaml(path=yaml_path).write(self.yaml_data)

        self.assertTrue(os.path.exists(yaml_path))

        os.remove(yaml_path)

    def test_read_yaml_file_with_safe_mode(self):
        yaml_path: str = f"{self.root_path}/test_read_file.yaml"

        with open(yaml_path, mode="w", encoding="utf-8") as f:
            yaml.dump(yaml.safe_load(self.yaml_str), f)

        data = fl.Yaml(path=yaml_path).read()
        self.assertDictEqual(self.yaml_data, data)

        os.remove(yaml_path)
