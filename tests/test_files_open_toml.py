import os
import shutil
from collections.abc import Iterator
from pathlib import Path
from textwrap import dedent

import pytest
from ddeutil.io.files import TomlEnvFl, TomlFl


@pytest.fixture(scope="module")
def toml_path(test_path) -> Iterator[Path]:
    this_path: Path = test_path / "toml"
    this_path.mkdir(parents=True, exist_ok=True)

    with open(this_path / "test_simple.toml", mode="w", encoding="utf-8") as f:
        f.write(
            dedent(
                """[config]
            # Comment this line ...
            value = "foo"
            """
            ).strip()
        )

    with open(this_path / "test_env.toml", mode="w", encoding="utf-8") as f:
        f.write(
            dedent(
                """[config]
            # Comment this line ...
            value = "foo is ${TEST_TOML_ENV}"
            """
            ).strip()
        )

    yield this_path

    shutil.rmtree(this_path)


def test_files_open_toml(toml_path):
    assert {"config": {"value": "foo"}} == TomlFl(
        path=toml_path / "test_simple.toml"
    ).read()


def test_files_open_toml_env(toml_path):
    os.environ["TEST_TOML_ENV"] = "FOO"
    assert {"config": {"value": "foo is FOO"}} == TomlEnvFl(
        path=toml_path / "test_env.toml"
    ).read()
