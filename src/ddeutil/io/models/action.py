# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, TypeVar

from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator

T = TypeVar("T")


class BaseAct(BaseModel):
    type: Annotated[str, Field(description="Activity Name")]
    desc: Annotated[Optional[str], Field(description="Description")] = None
    options: Annotated[dict[str, Any], Field(default_factory=dict)]


class Copy(BaseAct):
    type: Literal["copy"] = "copy"
    src: str
    sink: str


class Loop(BaseAct):
    type: Literal["forloop"] = "loop"
    elements: list[T]
    do: str

    @field_validator("elements")
    def __elements_validator(cls, values: list[T]) -> list[T]:
        if len(values) > 0:
            _first: Any = type(values[0])
            if any(not isinstance(value, _first) for value in values[1:]):
                raise TypeError(
                    "all element in loop activity must be the same type"
                )
        return values


class Until(BaseAct):
    type: Literal["forloop"] = "until"
    condition: str


class If(BaseAct):
    type: Literal["if"] = "if"
    condition: str
    right: str = Field(description="The right for correct with condition")
    left: str = Field(description="The left for wrong with condition")


class Sensor(BaseAct):
    type: Literal["sensor"] = "sensor"
    track: str


class Hook(BaseAct):
    type: Literal["hook"] = "hook"
    hook: str
