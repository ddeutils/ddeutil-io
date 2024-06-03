import ddeutil.io.models.__base as base
import pytest


@pytest.fixture(scope="module")
def name():
    class Name(base.BaseUpdatableModel):
        name: str
        nickname: str

    return Name


def test_initialize(name):
    people = name(name="foo", nickname="bar")
    assert "foo" == people.name
    assert "bar" == people.nickname


def test_update(name):
    people = name(name="foo", nickname="bar")
    people.update(data={"name": "new foo", "nickname": "new bar"})
    assert "new foo" == people.name
    assert "new bar" == people.nickname
