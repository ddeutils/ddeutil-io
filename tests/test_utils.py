import csv
import os
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from ddeutil.io.utils import (
    map_func,
    reverse_readline,
    search_env,
    search_env_replace,
    template_func,
    template_secret,
)


def test_template_secret():
    assert "Value include secrets: s3://bar" == template_secret(
        "Value include secrets: s3://@secrets{foo}",
        secrets={"foo": "bar"},
    )

    rs = template_secret(
        {
            "list": ["1", "2", "s3://@secrets{foo}"],
            "dict": {
                "tuple": ("1", "2", "s3://@secrets{foo}"),
                "key": 1,
                "boolean": True,
            },
            "default": "s3://@secrets{test:default}",
        },
        secrets={"foo": "bar"},
    )
    assert {
        "list": ["1", "2", "s3://bar"],
        "dict": {
            "tuple": ("1", "2", "s3://bar"),
            "key": 1,
            "boolean": True,
        },
        "default": "s3://default",
    } == rs


def test_template_secret_raise():
    with pytest.raises(ValueError):
        template_secret(
            "Value include secrets: s3://@secrets{foo.name}",
            secrets={"foo": "bar"},
        )


def test_template_func():
    assert "Test a|" == template_func(
        "Test @function{ddeutil.io.utils.add_newline:'a',newline='|'}"
    )

    reuse: str = "@function{ddeutil.io.utils.add_newline:'a',newline='|'}"
    assert {
        "list": ["a|", 1],
        "tuple": ("a|", 2, 3),
    } == template_func(
        {
            "list": [reuse, 1],
            "tuple": (reuse, 2, 3),
        }
    )


def test_template_func_raise():
    with pytest.raises(ValueError):
        template_func("@function{ddeutil.io.__version__:'a'}")


def test_map_func():
    assert {"foo": "bar!"} == map_func({"foo": "bar"}, lambda x: x + "!")
    assert ("foo!", "bar!", 1) == map_func(("foo", "bar", 1), lambda x: x + "!")


@pytest.fixture(scope="module")
def utils_path(test_path) -> Iterator[Path]:
    this_path: Path = test_path / "utils_reverse"
    this_path.mkdir(parents=True, exist_ok=True)

    yield this_path

    shutil.rmtree(this_path)


@pytest.fixture(scope="module")
def csv_data() -> list[dict[str, str]]:
    return [
        {"Col01": "A", "Col02": "1", "Col03": "test1"},
        {"Col01": "B", "Col02": "2", "Col03": "test2"},
        {"Col01": "C", "Col02": "3", "Col03": "test3"},
    ]


def test_files_utils_search_env_replace():
    os.environ["NAME"] = "foo"
    assert "Hello foo" == search_env_replace("Hello ${NAME}")
    assert "foo" == search_env_replace("${NAME}")
    assert "foo" == search_env_replace("${ NAME }")


def test_files_utils_search_env_replace_raise():
    with pytest.raises(ValueError):
        search_env_replace(
            "Hello ${NAME01}",
            raise_if_default_not_exists=True,
        )

    with pytest.raises(ValueError):
        search_env_replace("Hello ${:test}")


def test_files_utils_search_env():
    assert {
        "key": "demo",
        "hello": "demo-2",
        "escape": "${key}",
    } == search_env(
        "key='demo'\n# foo=bar\nhello=${key}-2\nescape=\\${key}\n",
    )


def test_files_utils_search_env_raise():
    with pytest.raises(ValueError):
        search_env("foo=")

    with pytest.raises(ValueError):
        search_env("foo=''")

    with pytest.raises(ValueError):
        search_env('foo=""')


def test_files_utils_reverse_read(utils_path, csv_data):
    test_file = utils_path / "file_reverse.csv"

    with open(test_file, mode="w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(csv_data[0].keys()),
            lineterminator="\n",
        )
        writer.writerows(csv_data)

    with open(test_file) as f:
        rs = list(reverse_readline(f))
    assert rs == [
        "C,3,test3\n",
        "B,2,test2\n",
        "A,1,test1\n",
    ]
