import gzip
import json
import os
import shutil
from collections.abc import Iterator
from pathlib import Path
from textwrap import dedent

import pytest
from ddeutil.io.files import JsonEnvFl, JsonFl, JsonLineFl


@pytest.fixture(scope="module")
def json_path(test_path) -> Iterator[Path]:
    this_path: Path = test_path / "json"
    this_path.mkdir(parents=True, exist_ok=True)

    with open(this_path / "test_simple.json", mode="w", encoding="utf-8") as f:
        f.write(
            dedent(
                """
            {
                "config": {
                    // Comment this line ...
                    "value": "foo"
                }
            }
            """
            ).strip()
        )

    with open(
        this_path / "test_simple_raise.json", mode="w", encoding="utf-8"
    ) as f:
        f.write(
            dedent(
                """
            {
                "config": {
                    // Comment this line ...
                    "value": "foo",
                    "value": "${TEST_JSON_ENV}"
                }
            """
            ).strip()
        )

    with open(this_path / "test_env.json", mode="w", encoding="utf-8") as f:
        f.write(
            dedent(
                """
            {
                "config": {
                    // Comment this line ...
                    "value": "foo is ${TEST_JSON_ENV}"
                }
            }
            """
            ).strip()
        )

    yield this_path

    shutil.rmtree(this_path)


def test_files_open_json(json_path):
    assert {"config": {"value": "foo"}} == JsonFl(
        path=json_path / "test_simple.json"
    ).read()


def test_files_open_json_raise(json_path):
    with pytest.raises(json.decoder.JSONDecodeError):
        JsonFl(path=json_path / "test_simple_raise.json").read()


def test_files_open_json_write(json_path):
    JsonFl(path=json_path / "test_simple_write.json").write(
        {"config": {"value": "foo"}},
        indent=0,
    )
    with open(json_path / "test_simple_write.json") as f:
        assert f.read() == '{\n"config": {\n"value": "foo"\n}\n}'


def test_files_open_json_write_compress(json_path):
    JsonFl(
        path=json_path / "test_simple_write.gz.json",
        compress="gz",
    ).write(
        {"config": {"value": "foo"}},
        indent=0,
    )
    with gzip.open(json_path / "test_simple_write.gz.json") as f:
        assert f.read() == b'{"config": {"value": "foo"}}'


def test_files_open_json_env_read(json_path):
    os.environ["TEST_JSON_ENV"] = "FOO"
    assert {"config": {"value": "foo is FOO"}} == JsonEnvFl(
        path=json_path / "test_env.json"
    ).read()


def test_files_open_json_env_read_raise(json_path):
    with pytest.raises(json.decoder.JSONDecodeError):
        JsonEnvFl(path=json_path / "test_simple_raise.json").read()


def test_files_open_json_line(json_path):
    with open(json_path / "test_write.line.json", mode="w") as f:
        f.write("")

    assert [] == JsonLineFl(path=json_path / "test_write.line.json").read()

    JsonLineFl(path=json_path / "test_write.line.json").write({"line": 1})
    JsonLineFl(path=json_path / "test_write.line.json").write(
        [{"line": 2}, {"line": 3}], mode="a"
    )

    assert [{"line": 1}, {"line": 2}, {"line": 3}] == JsonLineFl(
        path=json_path / "test_write.line.json"
    ).read()


def test_files_open_json_line_raise(json_path):
    with open(json_path / "test_write_raise.line.json", mode="w") as f:
        f.write("\n")

    with pytest.raises(json.decoder.JSONDecodeError):
        JsonLineFl(path=json_path / "test_write_raise.line.json").read()

    with pytest.raises(ValueError):
        JsonLineFl(path=json_path / "test_write_raise.line.json").write([])
