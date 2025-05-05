import os
import shutil
import time
from collections.abc import Generator
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from textwrap import dedent
from typing import Any

import pytest
import yaml
from ddeutil.io.files import YamlEnvFl, YamlFl, YamlFlResolve


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
            statement: |
                # Comment ${DEMO_ENV_VALUE}
                This is a long statement with comment above
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
                "statement": (
                    "# Comment ${DEMO_ENV_VALUE}\n"
                    "This is a long statement with comment above"
                ),
            }
        }
    }


def test_write_yaml_file_with_safe(target_path, yaml_str_safe, yaml_data_safe):
    yaml_path: Path = target_path / "test_write_file.yaml"
    YamlFl(path=yaml_path).write(yaml_data_safe)
    assert yaml_path.exists()


def test_read_yaml_resolve_file(target_path, yaml_str_safe, yaml_data_safe):
    yaml_path: Path = target_path / "test_read_file_resolve.yaml"
    with open(yaml_path, mode="w", encoding="utf-8") as f:
        f.write(yaml_str_safe)

    data = YamlFlResolve(path=yaml_path).read(safe=False)
    assert data["main_key"]["sub_key"]["str2bool"] == "on"
    assert (
        "# Comment ${DEMO_ENV_VALUE}\n"
        "This is a long statement with comment above"
    ) == data["main_key"]["sub_key"]["statement"]


def test_read_yaml_resolve_file_multithread(target_path, yaml_str_safe, yaml_data_safe):
    yaml_path: Path = target_path / "test_read_file_resolve.yaml"
    with open(yaml_path, mode="w", encoding="utf-8") as f:
        f.write(yaml_str_safe)

    def read_task():  # pragma: no cov
        data = YamlFlResolve(path=yaml_path).read()
        time.sleep(0.5)
        assert data["main_key"]["sub_key"]["str2bool"] == "on"
        assert (
            "# Comment ${DEMO_ENV_VALUE}\n"
            "This is a long statement with comment above"
        ) == data["main_key"]["sub_key"]["statement"]

    with ThreadPoolExecutor() as executor:
        executor.submit(read_task)
        read_task()


def test_read_yaml_file_with_safe(target_path, yaml_str_safe, yaml_data_safe):
    yaml_path: Path = target_path / "test_read_file_safe.yaml"
    with open(yaml_path, mode="w", encoding="utf-8") as f:
        yaml.dump(yaml.safe_load(yaml_str_safe), f)

    data = YamlFl(path=yaml_path).read()
    assert yaml_data_safe == data


def test_read_yaml_file(target_path, yaml_str_safe, yaml_data_safe):
    yaml_path: Path = target_path / "test_read_file.yaml"
    with open(yaml_path, mode="w", encoding="utf-8") as f:
        f.write(yaml_str_safe)

    data = YamlFl(path=yaml_path).read(safe=False)
    assert yaml_data_safe == data


@pytest.fixture(scope="module")
def yaml_str_env_safe() -> str:
    return dedent(
        """
    main_key:
        sub_key:
            key01: 'test ${DEMO_ENV_VALUE} value'
            key02: $1 This is escape with number
            key03: $$ESCAPE This is escape with $
            key04: ['i1', 'i2', '${DEMO_ENV_VALUE}']
            key05: ${DEMO_ENV_VALUE_EMPTY:default}
            key06: $${DEMO_ENV_VALUE}
            key07: This ${DEMO_ENV_VALUE} ${{DEMO_ENV_VALUE}}
            key08: |
                # Comment
                statement ${DEMO_ENV_VALUE}
    """
    ).strip()


@pytest.fixture(scope="module")
def yaml_data_env_safe() -> dict[str, Any]:
    return {
        "main_key": {
            "sub_key": {
                "key01": "test demo value",
                "key02": "$1 This is escape with number",
                "key03": "$ESCAPE This is escape with $",
                "key04": ["i1", "i2", "demo"],
                "key05": "default",
                "key06": "${DEMO_ENV_VALUE}",
                "key07": "This demo ${{DEMO_ENV_VALUE}}",
                "key08": "# Comment\nstatement demo",
            },
        },
    }


def test_read_yaml_file_with_safe_mode(
    yaml_str_env_safe,
    yaml_data_env_safe,
    target_path,
):
    yaml_path: Path = target_path / "test_read_file_env.yaml"

    with open(yaml_path, mode="w", encoding="utf-8") as f:
        yaml.dump(yaml.safe_load(yaml_str_env_safe), f)

    os.environ["DEMO_ENV_VALUE"] = "demo"

    data = YamlEnvFl(path=yaml_path).read()
    assert yaml_data_env_safe == data


def test_read_yaml_file_with_safe_mode_and_prepare(
    target_path,
    yaml_str_env_safe,
):
    yaml_path: Path = target_path / "test_read_file_env_prepare.yaml"

    with open(yaml_path, mode="w", encoding="utf-8") as f:
        yaml.dump(yaml.safe_load(yaml_str_env_safe), f)

    os.environ["DEMO_ENV_VALUE"] = "demo"

    yml_loader = YamlEnvFl(path=yaml_path)
    yml_loader.prepare = lambda x: f"{x}!!"
    data = yml_loader.read()
    assert {
        "main_key": {
            "sub_key": {
                "key01": "test demo!! value",
                "key02": "$1 This is escape with number",
                "key03": "$ESCAPE This is escape with $",
                "key04": ["i1", "i2", "demo!!"],
                "key05": "default!!",
                "key06": "${DEMO_ENV_VALUE}",
                "key07": "This demo!! ${{DEMO_ENV_VALUE}}",
                "key08": "# Comment\nstatement demo!!",
            }
        }
    } == data


def test_read_yaml_file_with_safe_mode_and_prepare_2(
    target_path,
    yaml_str_env_safe,
):
    yaml_path: Path = target_path / "test_read_file_env_prepare_2.yaml"

    with open(yaml_path, mode="w", encoding="utf-8") as f:
        yaml.dump(yaml.safe_load(yaml_str_env_safe), f)

    os.environ["DEMO_ENV_VALUE"] = "P@ssW0rd"

    import urllib.parse

    yml_loader = YamlEnvFl
    yml_loader.prepare = staticmethod(lambda x: urllib.parse.quote_plus(str(x)))
    data = yml_loader(path=yaml_path).read()
    assert {
        "main_key": {
            "sub_key": {
                "key01": "test P%40ssW0rd value",
                "key02": "$1 This is escape with number",
                "key03": "$ESCAPE This is escape with $",
                "key04": ["i1", "i2", "P%40ssW0rd"],
                "key05": "default",
                "key06": "${DEMO_ENV_VALUE}",
                "key07": "This P%40ssW0rd ${{DEMO_ENV_VALUE}}",
                "key08": "# Comment\nstatement P%40ssW0rd",
            }
        }
    } == data
