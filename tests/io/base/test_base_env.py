import os
import shutil
import unittest
from textwrap import dedent

import ddeutil.io.base as bfl


class EnvTestCase(unittest.TestCase):
    root_path: str

    @classmethod
    def setUpClass(cls) -> None:
        _root_path: str = os.path.dirname(os.path.abspath(__file__)).replace(
            os.sep, "/"
        )
        os.makedirs(f"{_root_path}/env", exist_ok=True)

        cls.root_path: str = f"{_root_path}/env"

    def setUp(self) -> None:
        self.maxDiff = None
        self.env_str = dedent(
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

        self.env_data = {
            "TEST": "This is common value test",
            "COMMENT_TEST": "This is common value test",
            "QUOTE": "single quote",
            "DOUBLE_QUOTE": "double quote",
            "PASSING": "double quote",
            "UN_PASSING": "${DOUBLE_QUOTE}",
        }

    def test_env(self):
        env_path: str = f"{self.root_path}/.env"

        with open(env_path, mode="w", encoding="utf-8") as f:
            f.write(self.env_str)

        data = bfl.Env(path=env_path).read(update=False)

        self.assertDictEqual(self.env_data, data)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.root_path)
