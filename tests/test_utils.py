import ddeutil.io.utils as utils
import pytest


def test_map_secrets():
    rs = utils.map_secret(
        "Value include secrets: s3://@secrets{foo}",
        secrets={"foo": "bar"},
    )
    assert "Value include secrets: s3://bar" == rs

    rs = utils.map_secret(
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


def test_map_secrets_raise():
    with pytest.raises(ValueError):
        utils.map_secret(
            "Value include secrets: s3://@secrets{foo.name}",
            secrets={"foo": "bar"},
        )


def test_map_importer():
    rs = utils.map_importer(
        "Test @function{ddeutil.io.__base.add_newline:'a',newline='|'}"
    )
    assert "Test a|" == rs

    reuse: str = "@function{ddeutil.io.__base.add_newline:'a',newline='|'}"
    rs = utils.map_importer(
        {
            "list": [reuse, 1],
            "tuple": (reuse, 2, 3),
        }
    )
    assert {
        "list": ["a|", 1],
        "tuple": ("a|", 2, 3),
    } == rs


def test_map_importer_raise():
    with pytest.raises(ValueError):
        utils.map_importer("@function{ddeutil.io.__version__:'a'}")


def test_map_func():
    rs = utils.map_func({"foo": "bar"}, lambda x: x + "!")
    assert {"foo": "bar!"} == rs

    rs = utils.map_func(("foo", "bar", 1), lambda x: x + "!")
    assert ("foo!", "bar!", 1) == rs
