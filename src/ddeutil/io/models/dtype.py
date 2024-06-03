# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

from typing import (
    Annotated,
    Literal,
    Union,
)

from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator


class BaseType(BaseModel):
    """Base Type"""

    type: str = "base"

    def __str__(self) -> str:
        return self.type


class StringType(BaseType):
    """String Type

    Note:
        This type will be the base of any string type that able to fixed length
    or not.
    """

    type: Literal["string", "str"] = "string"
    max_length: Annotated[int, Field(ge=-1)] = -1

    def __str__(self) -> str:
        _length: str = f"( {self.max_length} )" if self.max_length > -1 else ""
        return f"{self.type}{_length}"


class CharType(StringType):
    """Charactor Type

    Note: fixed-length strings
    """

    type: Literal["char"] = "char"


class VarcharType(StringType):
    """Variable Charactor Type

    Note: variable-length strings with limit
    """

    type: Literal["varchar"] = "varchar"


class TextType(StringType):
    """Text Type

    Note: variable unlimited length strings
    """

    type: Literal["text"] = "text"


class IntegerType(BaseType):
    """Integer Type

    Note: Storage size, 4 bytes, -2147483648 to +2147483647
    """

    type: Literal["integer", "int"] = "integer"

    @field_validator("type", mode="after")
    def prepare_for_short_name(
        cls,
        value: Literal["integer", "int"],
    ) -> Literal["integer"]:
        return "integer" if value == "int" else value


class SmallIntType(IntegerType):
    """Small Range Integer

    Note: Storage size, 2 bytes, -32768 to +32767
    """

    type: Literal["smallint"] = "smallint"


class BigIntType(IntegerType):
    """Big Range Integer

    Note: Storage size, 8 bytes, -9223372036854775808 to +9223372036854775807
    """

    type: Literal["bigint"] = "bigint"


class ShortType(SmallIntType):

    type: Literal["short"] = "short"


class LongType(BigIntType):

    type: Literal["long"] = "long"


class SerialType(IntegerType):
    """Serial Type"""

    type: Literal["serial"] = "serial"


class NumericType(BaseType):
    """Numeric Type"""

    type: Literal["numeric"] = "numeric"
    precision: Annotated[int, Field(ge=-1)] = -1
    scale: Annotated[int, Field(ge=-1)] = -1

    def __str__(self) -> str:
        if self.precision > -1:
            _scale: str = f", {self.scale}" if self.scale > -1 else ""
            return f"{self.type}( {self.precision}{_scale} )"
        return self.type


class DecimalType(NumericType):
    """Decimal Type"""

    type: Literal["decimal"] = "decimal"


class FloatType(BaseType):
    type: Literal["float"] = "float"


class RealType(BaseType):
    type: Literal["real"] = "real"


class DoublePrecisionType(BaseType): ...


class TimestampType(BaseType):
    """Timestamp Type"""

    type: Literal["timestamp"] = "timestamp"
    precision: Annotated[int, Field(ge=-1, le=6)] = -1
    timezone: Annotated[bool, Field(description="Timezone flag")] = False


class TimeType(BaseType):

    type: Literal["time"] = "time"


class DateType(BaseType):

    type: Literal["date"] = "date"


class DateTimeType(BaseType):

    type: Literal["datetime"] = "datetime"


Dtype = Union[
    StringType,
    CharType,
    VarcharType,
    TextType,
    NumericType,
    DecimalType,
    TimestampType,
    IntegerType,
    BigIntType,
    SmallIntType,
    BaseType,
]
