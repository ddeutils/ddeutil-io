import os
import pathlib

import pytest


@pytest.fixture
def test_path() -> pathlib.Path:
    return pathlib.Path(
        os.path.dirname(os.path.abspath(__file__)).replace(os.sep, "/")
    )


@pytest.fixture(scope="class")
def test_path_to_cls(request):
    _test_path = pathlib.Path(
        os.path.dirname(os.path.abspath(__file__)).replace(os.sep, "/")
    )
    request.cls.test_path = _test_path
    request.cls.root_path = _test_path.parent
