import pytest
from ddeutil.io.utils import map_func, template_func, template_secret


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
        "Test @function{ddeutil.io.files.add_newline:'a',newline='|'}"
    )

    reuse: str = "@function{ddeutil.io.files.add_newline:'a',newline='|'}"
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
