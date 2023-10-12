import os
import pathlib

import pytest

try:
    from dotenv import load_dotenv
except ImportError:

    def load_dotenv(path: str) -> None:
        _ = path
        return


load_dotenv("../.env")

collect_ignore = [
    "vendors",
    "test_loader.py",
    "test_connection.py",
]


@pytest.fixture(scope="class")
def test_path_to_cls(request):
    _test_path = pathlib.Path(
        os.path.dirname(os.path.abspath(__file__)).replace(os.sep, "/")
    )
    request.cls.test_path = _test_path.parent
    request.cls.root_path = _test_path.parent.parent
