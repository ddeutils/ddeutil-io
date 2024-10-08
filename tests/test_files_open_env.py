import os
import shutil
from collections.abc import Iterator
from pathlib import Path
from textwrap import dedent

import pytest
from ddeutil.io.files import EnvFl


@pytest.fixture(scope="module")
def env_path(test_path) -> Iterator[Path]:
    this_path: Path = test_path / "env"
    this_path.mkdir(parents=True, exist_ok=True)
    with open(this_path / ".env", mode="w", encoding="utf-8") as f:
        f.write(
            dedent(
                """TEST=This is common value test
            # Comment this line ...
            COMMENT_TEST='This is common value test'  # This is inline comment
            QUOTE='single quote'
            DOUBLE_QUOTE="double quote"
            PASSING=${DOUBLE_QUOTE}
            UN_PASSING='${DOUBLE_QUOTE}'
            """
            ).strip()
        )

    yield this_path / ".env"

    shutil.rmtree(this_path)


def test_files_open_env_read(env_path):
    assert {
        "TEST": "This is common value test",
        "COMMENT_TEST": "This is common value test",
        "QUOTE": "single quote",
        "DOUBLE_QUOTE": "double quote",
        "PASSING": "double quote",
        "UN_PASSING": "${DOUBLE_QUOTE}",
    } == EnvFl(path=env_path).read(update=False)


def test_files_open_env_read_update(env_path):
    EnvFl(path=env_path).read(update=True)

    assert os.getenv("TEST") == "This is common value test"
    assert os.getenv("COMMENT_TEST") == "This is common value test"
    assert os.getenv("DOUBLE_QUOTE") == "double quote"
    assert os.getenv("PASSING") == "double quote"
    assert os.getenv("UN_PASSING") == "${DOUBLE_QUOTE}"


def test_files_open_env_write(env_path):
    with pytest.raises(NotImplementedError):
        EnvFl(path=env_path).write({"TEST": "This is common value test"})
