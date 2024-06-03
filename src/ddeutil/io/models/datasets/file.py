# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from typing import Literal

from ..__base import BaseUpdatableModel
from .col import Col


class BaseFl(BaseUpdatableModel):
    name: str
    encoding: str = "utf-8"


class CsvFl(BaseFl):
    """Csv File Model"""

    type: Literal["csv"] = "csv"
    header: bool = True
    feature: list[Col]
    sep: str = ","
    comment: str = "#"
    skip_rows: int = 0
    skip_footer: int = 0
    quote_char: str = '"'


class JsonFl(BaseFl):
    """Json File Model"""

    type: Literal["json"] = "json"
    nestest: int = -1


class ParqFl(BaseFl):
    """Parquet File Model"""

    type: Literal["parquet"] = "parquet"
    compress: str = "gzip"
