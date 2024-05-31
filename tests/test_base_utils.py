import os

import ddeutil.io.__base.utils as utils
import pytest


def test_search_env_replace():
    os.environ["NAME"] = "foo"
    rs = utils.search_env_replace("Hello ${NAME}")
    assert "Hello foo" == rs


def test_search_env_replace_raise():
    with pytest.raises(ValueError):
        utils.search_env_replace(
            "Hello ${NAME01}", raise_if_default_not_exists=True
        )

    with pytest.raises(ValueError):
        utils.search_env_replace("Hello ${:test}")


def test_search_env():
    rs = utils.search_env(
        ("key='demo'\n" "# foo=bar\n" "hello=${key}-2\n" "escape=\\${key}\n"),
    )
    assert {"key": "demo", "hello": "demo-2", "escape": "${key}"} == rs


def test_search_env_raise():
    with pytest.raises(ValueError):
        utils.search_env("foo=")

    with pytest.raises(ValueError):
        utils.search_env("foo=''")

    with pytest.raises(ValueError):
        utils.search_env('foo=""')
