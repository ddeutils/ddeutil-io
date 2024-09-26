import os
import shutil
from collections.abc import Generator
from pathlib import Path
from textwrap import dedent

import ddeutil.io.files as bfl
import pytest


@pytest.fixture(scope="module")
def toml_path(test_path) -> Generator[Path, None, None]:
    this_path: Path = test_path / "toml"
    this_path.mkdir(parents=True, exist_ok=True)

    yield this_path

    shutil.rmtree(this_path)


def test_toml(toml_path):
    toml_file_path: Path = toml_path / "test_simple.toml"

    with open(toml_file_path, mode="w", encoding="utf-8") as f:
        f.write(
            dedent(
                """
    [config]
    # Comment this line ...
    value = "foo"
    """
            ).strip()
        )

    assert {
        "config": {
            "value": "foo",
        },
    } == bfl.TomlFl(path=toml_file_path).read()


def test_toml_env(toml_path):
    toml_file_path: Path = toml_path / "test_env.toml"

    os.environ["TEST_TOML_ENV"] = "FOO"

    with open(toml_file_path, mode="w", encoding="utf-8") as f:
        f.write(
            dedent(
                """
    [config]
    # Comment this line ...
    value = "foo is ${TEST_TOML_ENV}"
    """
            ).strip()
        )

    assert {
        "config": {
            "value": "foo is FOO",
        },
    } == bfl.TomlEnvFl(path=toml_file_path).read()
