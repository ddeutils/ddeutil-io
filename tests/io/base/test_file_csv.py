import os
import unittest
import warnings
from textwrap import dedent

import ddeutil.io.__base.files as fl


class CSVTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root_path: str = os.path.dirname(os.path.abspath(__file__)).replace(
            os.sep, "/"
        )

    def setUp(self) -> None:
        warnings.simplefilter("ignore", category=ResourceWarning)
        self.csv_str: str = dedent(
            """Col01|Col02|Col03
        A|1|test1
        B|2|test2
        C|3|test3
        """
        )
        self.csv_data: list = [
            {"Col01": "A", "Col02": "1", "Col03": "test1"},
            {"Col01": "B", "Col02": "2", "Col03": "test2"},
            {"Col01": "C", "Col02": "3", "Col03": "test3"},
        ]
        self.csv_path: str = f"{self.root_path}/test_file.csv"
        self.csv_env_path: str = f"{self.root_path}/test_env_file.csv"
        # with open(self.csv_path, 'w', encoding='utf-8') as f:
        #     f.write(self.csv_str)
        fl.CSV(self.csv_path).write(self.csv_data)

    def test_load_csv(self):
        self.csv_data_from_load = fl.CSV(self.csv_path).read()
        self.assertListEqual(self.csv_data, self.csv_data_from_load)

    def tearDown(self) -> None:
        # for path in {self.csv_path, self.csv_env_path, }:
        for path in {
            self.csv_path,
        }:
            if os.path.exists(path):
                os.remove(path)
