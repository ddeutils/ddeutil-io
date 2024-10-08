import os

import ddeutil.io.files.utils as utils
import pytest


def test_files_utils_search_env_replace():
    os.environ["NAME"] = "foo"
    assert "Hello foo" == utils.search_env_replace("Hello ${NAME}")


def test_files_utils_search_env_replace_raise():
    with pytest.raises(ValueError):
        utils.search_env_replace(
            "Hello ${NAME01}",
            raise_if_default_not_exists=True,
        )

    with pytest.raises(ValueError):
        utils.search_env_replace("Hello ${:test}")


def test_files_utils_search_env():
    assert {
        "key": "demo",
        "hello": "demo-2",
        "escape": "${key}",
    } == utils.search_env(
        "key='demo'\n# foo=bar\nhello=${key}-2\nescape=\\${key}\n",
    )


def test_files_utils_search_env_raise():
    with pytest.raises(ValueError):
        utils.search_env("foo=")

    with pytest.raises(ValueError):
        utils.search_env("foo=''")

    with pytest.raises(ValueError):
        utils.search_env('foo=""')
