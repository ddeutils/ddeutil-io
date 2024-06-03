# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import (
    Annotated,
    Any,
    Optional,
)
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator, model_validator

try:
    from .__base import BaseUpdatableModel
    from .__enums import Status
except ImportError:
    from __base import BaseUpdatableModel
    from __enums import Status


TZ: str = "Asia/Bangkok"


def dt_now() -> datetime:
    return datetime.now(timezone.utc)


class Ts(BaseModel):
    """Timestamp Model

    Examples:
        >>> from datetime import datetime
        >>> Ts(ts=datetime(2024, 1, 1, 5)).ts.tzinfo
        zoneinfo.ZoneInfo(key='Asia/Bangkok')
    """

    ts: Annotated[datetime, Field(default_factory=dt_now, alias="Timestamp")]
    tz: Annotated[str, Field(alias="TimeZone")] = TZ

    @model_validator(mode="after")
    def __prepare_time(self):
        self.ts: datetime = self.ts.astimezone(ZoneInfo(self.tz))
        return self

    def now(self) -> datetime:
        """Return updated timestamp"""
        return datetime.now(tz=self.tz)


class Tag(Ts):
    """Tag Model"""

    author: Annotated[
        Optional[str],
        Field(validate_default=True, description="Author"),
    ] = None
    desc: Annotated[
        Optional[str],
        Field(repr=False, description="Description"),
    ] = None
    labels: Annotated[
        list[str],
        Field(default_factory=list, description="Labels of Tag"),
    ]
    vs: Annotated[
        Optional[date],
        Field(validate_default=True, description="Version of Tag"),
    ] = None

    @field_validator("author")
    def __set_author(cls, value: str | None):
        return value or "undefined"

    @field_validator("vs")
    def __set_version(cls, value: Optional[date]):
        """Pre initialize the `version` value that parsing from default"""
        return value if value else date(year=1990, month=1, day=1)


class BaseTask(BaseUpdatableModel):
    """Base Task Model"""

    st: Status = Field(default=Status.WAITING, description="Status")
    dt: Annotated[
        datetime,
        Field(default_factory=dt_now, alias="Datetime"),
    ]


class Task(BaseTask): ...


class BaseMsg(BaseUpdatableModel):
    level: int
    msg: str


class Msg(BaseMsg): ...


class Log(BaseUpdatableModel):
    """Log Model"""

    msgs: list[Msg]


class BaseParam(BaseUpdatableModel):
    extras: dict[str, Any]

    @model_validator(mode="before")
    def __prepare_extras(cls, values):
        extras: dict[str, Any] = {
            k: values.pop(k) for k in values.copy() if k not in cls.model_fields
        } | values.pop("extras", {})
        return {
            "extras": extras,
            **values,
        }


class NormalParam(BaseParam):
    run_date: datetime
