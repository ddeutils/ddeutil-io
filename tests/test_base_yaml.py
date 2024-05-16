import os
import shutil
import unittest
import warnings
from collections.abc import Generator
from pathlib import Path
from textwrap import dedent
from typing import Any

import ddeutil.io.__base.files as fl
import pytest
import yaml


@pytest.fixture(scope="module")
def target_path(test_path) -> Generator[Path, None, None]:
    target_path: Path = test_path / "base_file_yaml"
    target_path.mkdir(parents=True, exist_ok=True)

    yield target_path

    shutil.rmtree(target_path)


@pytest.fixture(scope="module")
def yaml_str_safe() -> str:
    return dedent(
        """
    main_key:
        sub_key:
            string: 'test ${DEMO_ENV_VALUE} value'
            int: 0.001
            bool: false
            list: ['i1', 'i2', 'i3']
            str2bool: on
    """
    ).strip()


@pytest.fixture(scope="module")
def yaml_data_safe() -> dict[str, Any]:
    return {
        "main_key": {
            "sub_key": {
                "string": "test ${DEMO_ENV_VALUE} value",
                "int": 0.001,
                "bool": False,
                "list": ["i1", "i2", "i3"],
                "str2bool": True,
            }
        }
    }


def test_write_yaml_file_with_safe(target_path, yaml_str_safe, yaml_data_safe):
    yaml_path: Path = target_path / "test_write_file.yaml"
    fl.YamlFl(path=yaml_path).write(yaml_data_safe)
    assert yaml_path.exists()


def test_read_yaml_resolve_file(target_path, yaml_str_safe, yaml_data_safe):
    yaml_path: Path = target_path / "test_read_file_resolve.yaml"
    with open(yaml_path, mode="w", encoding="utf-8") as f:
        f.write(yaml_str_safe)

    data = fl.YamlFlResolve(path=yaml_path).read(safe=False)
    assert "on" == data["main_key"]["sub_key"]["str2bool"]


def test_read_yaml_file_with_safe(target_path, yaml_str_safe, yaml_data_safe):
    yaml_path: Path = target_path / "test_read_file_safe.yaml"
    with open(yaml_path, mode="w", encoding="utf-8") as f:
        yaml.dump(yaml.safe_load(yaml_str_safe), f)

    data = fl.YamlFl(path=yaml_path).read()
    assert yaml_data_safe == data


def test_read_yaml_file(target_path, yaml_str_safe, yaml_data_safe):
    yaml_path: Path = target_path / "test_read_file.yaml"
    with open(yaml_path, mode="w", encoding="utf-8") as f:
        f.write(yaml_str_safe)

    data = fl.YamlFl(path=yaml_path).read(safe=False)
    assert yaml_data_safe == data


class YamlEnvFileTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root_path: str = os.path.dirname(os.path.abspath(__file__)).replace(
            os.sep, "/"
        )

    def setUp(self) -> None:
        self.maxDiff = None
        warnings.simplefilter("ignore", category=ResourceWarning)
        self.yaml_str: str = dedent(
            """
        main_key:
            sub_key:
                key01: 'test ${DEMO_ENV_VALUE} value'
                key02: $1 This is escape with number
                key03: $$ESCAPE This is escape with $
                key04: ['i1', 'i2', '${DEMO_ENV_VALUE}']
                key05: ${DEMO_ENV_VALUE_EMPTY:default}
                key06: $${DEMO_ENV_VALUE}
        """
        ).strip()
        self.yaml_data: dict = {
            "main_key": {
                "sub_key": {
                    "key01": "test demo value",
                    "key02": "$1 This is escape with number",
                    "key03": "$ESCAPE This is escape with $",
                    "key04": ["i1", "i2", "demo"],
                    "key05": "default",
                    "key06": "${DEMO_ENV_VALUE}",
                }
            }
        }

    def test_read_yaml_file_with_safe_mode(self):
        yaml_path: str = f"{self.root_path}/test_read_file_env.yaml"

        with open(yaml_path, mode="w", encoding="utf-8") as f:
            yaml.dump(yaml.safe_load(self.yaml_str), f)

        os.environ["DEMO_ENV_VALUE"] = "demo"

        data = fl.YamlEnvFl(path=yaml_path).read()
        self.assertDictEqual(self.yaml_data, data)

        os.remove(yaml_path)

    def test_read_yaml_file_with_safe_mode_and_prepare(self):
        yaml_path: str = f"{self.root_path}/test_read_file_env_prepare.yaml"

        with open(yaml_path, mode="w", encoding="utf-8") as f:
            yaml.dump(yaml.safe_load(self.yaml_str), f)

        os.environ["DEMO_ENV_VALUE"] = "demo"

        yml_loader = fl.YamlEnvFl(path=yaml_path)
        yml_loader.prepare = lambda x: f"{x}!!"
        data = yml_loader.read()
        self.assertDictEqual(
            {
                "main_key": {
                    "sub_key": {
                        "key01": "test demo!! value",
                        "key02": "$1 This is escape with number",
                        "key03": "$ESCAPE This is escape with $",
                        "key04": ["i1", "i2", "demo!!"],
                        "key05": "default!!",
                        "key06": "${DEMO_ENV_VALUE}",
                    }
                }
            },
            data,
        )

        os.remove(yaml_path)

    def test_read_yaml_file_with_safe_mode_and_prepare_2(self):
        yaml_path: str = f"{self.root_path}/test_read_file_env_prepare_2.yaml"

        with open(yaml_path, mode="w", encoding="utf-8") as f:
            yaml.dump(yaml.safe_load(self.yaml_str), f)

        os.environ["DEMO_ENV_VALUE"] = "P@ssW0rd"

        import urllib.parse

        yml_loader = fl.YamlEnvFl
        yml_loader.prepare = staticmethod(
            lambda x: urllib.parse.quote_plus(str(x))
        )
        data = yml_loader(path=yaml_path).read()
        self.assertDictEqual(
            {
                "main_key": {
                    "sub_key": {
                        "key01": "test P%40ssW0rd value",
                        "key02": "$1 This is escape with number",
                        "key03": "$ESCAPE This is escape with $",
                        "key04": ["i1", "i2", "P%40ssW0rd"],
                        "key05": "default",
                        "key06": "${DEMO_ENV_VALUE}",
                    }
                }
            },
            data,
        )

        os.remove(yaml_path)
