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
    request.cls.test_path = pathlib.Path(
        os.path.dirname(os.path.abspath(__file__)).replace(os.sep, "/")
    )
