# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

from enum import Enum, IntEnum
from functools import total_ordering
from typing import TypeVar

T = TypeVar("T")


def enum_ordering(cls: T) -> T:
    """Add order property to Enum object."""

    def __lt__(self, other) -> bool:
        if isinstance(other, type(self)):
            return self.value < other.value
        raise ValueError("Cannot compare different Enums")

    cls.__lt__ = __lt__
    return total_ordering(cls)


class StrEnum(str, Enum):
    """StrEnum where enum.auto() returns the field name.

    Reference:
        (https://docs.python.org/3.9/library/enum.html#using-automatic-values)
    """

    @staticmethod
    def _generate_next_value_(
        name: str,
        start: int,
        count: int,
        last_values: list,
    ) -> str:
        return name

    def __str__(self) -> str:
        return self.value


class Status(StrEnum):
    SUCCESS: str = "SUCCESS"
    APPROVED: str = "APPROVED"
    FAILED: str = "FAILED"
    WAITING: str = "WAITING"
    PROCESSING: str = "PROCESSING"
    TRIGGERED: str = "TRIGGERED"

    def in_process(self) -> bool:
        return self.value in ("WAITING", "PROCESSING")

    def is_done(self) -> bool:
        return self.value == "SUCCESS"

    def is_failed(self) -> bool:
        return self.value == "FAILED"


class Loading(StrEnum):
    FULL_DUMP = "F"
    DELTA = "D"
    MERGE = "D"
    TRANSACTION = "T"
    SCD_DELTA = "SCD_D"
    SCD_DUMP = "SCD_F"
    SCD_TRANS = "SCD_T"

    def is_delta(self) -> bool:
        return self.value == "D" or self.value == "SCD_D"

    def is_scd(self) -> bool:
        return self.value.startswith("SCD")


class DataLayer(IntEnum):
    RAW: int = 0
    STAGING: int = 1
    PERSISTED: int = 2
    CURATED: int = 3
    MART: int = 4
    REPORT: int = 5
