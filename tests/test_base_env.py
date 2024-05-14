import shutil
from collections.abc import Generator
from pathlib import Path
from textwrap import dedent

import ddeutil.io.__base as bfl
import pytest


@pytest.fixture(scope="module")
def env_path(test_path) -> Generator[Path, None, None]:
    this_path: Path = test_path / "env"
    this_path.mkdir(parents=True, exist_ok=True)

    yield this_path

    shutil.rmtree(this_path)


def test_env(env_path):
    env_path: Path = env_path / ".env"

    with open(env_path, mode="w", encoding="utf-8") as f:
        f.write(
            dedent(
                """
    TEST=This is common value test
    # Comment this line ...
    COMMENT_TEST='This is common value test'  # This is inline comment
    QUOTE='single quote'
    DOUBLE_QUOTE="double quote"
    PASSING=${DOUBLE_QUOTE}
    UN_PASSING='${DOUBLE_QUOTE}'
    """
            ).strip()
        )

    assert {
        "TEST": "This is common value test",
        "COMMENT_TEST": "This is common value test",
        "QUOTE": "single quote",
        "DOUBLE_QUOTE": "double quote",
        "PASSING": "double quote",
        "UN_PASSING": "${DOUBLE_QUOTE}",
    } == bfl.EnvFl(path=env_path).read(update=False)
