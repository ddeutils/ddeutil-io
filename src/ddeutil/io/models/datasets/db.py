# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from typing import Annotated, Optional, Union

from pydantic import (
    Field,
    ValidationInfo,
)
from pydantic.functional_validators import field_validator
from pydantic.types import SecretStr

from ..__base import BaseUpdatableModel
from ..const import Fk, Pk
from .col import Col


class BaseDef(BaseUpdatableModel):
    """Base Definition"""

    name: Annotated[
        str,
        Field(description="Name"),
    ]
    desc: Annotated[
        Optional[str],
        Field(default=None, description="Description of Object"),
    ]


class BaseTbl(BaseDef):
    """Base Table Model"""

    features: Annotated[
        list[Col],
        Field(
            default_factory=list,
            description="Schema of this Table",
        ),
    ]


class Tbl(BaseTbl):
    """Table Model"""

    pk: Annotated[
        Pk,
        Field(validate_default=True, description="Primary Key"),
    ] = Pk()
    fk: Annotated[
        list[Fk],
        Field(default_factory=list, description="Foreign Key"),
    ]

    consts: Annotated[
        list[str],
        Field(default_factory=list),
    ]

    @field_validator("pk")
    def __receive_pk_from_schemas(
        cls,
        value: Pk,
        info: ValidationInfo,
    ) -> Pk:
        # NOTE:
        #   we respect that `info.data` should contain schema before `pk`
        #   validation.
        pks: list[str] = [
            i.name for i in filter(lambda x: x.pk, info.data["features"])
        ]
        if pks and not value.cols:
            # Note: pass primary key cols if `pk` does not set.
            value = Pk(cols=list(pks))

        # NOTE: change name of `pk` with parent Tbl class name
        value.of = info.data["name"]
        return value

    @field_validator("fk")
    def __prepare_fk(cls, value: list[Fk], info: ValidationInfo) -> list[Fk]:
        # NOTE: change name of `fk` with parent Tbl class name
        for fk in value:
            fk.of = info.data["name"]
        return value


class BaseFunc(BaseDef):
    definition: str


class Func(BaseFunc): ...


class BaseProc(BaseDef):
    definition: str


class Proc(BaseProc): ...


class BaseView(BaseDef):
    definition: str


class View(BaseView): ...


class BaseScm(BaseUpdatableModel):
    """Base Schema Model"""

    name: str
    tables: Annotated[
        list[Tbl],
        Field(default_factory=list, description="Collection of Tables"),
    ]


class Scm(BaseScm):
    """Schema Model"""

    views: Annotated[
        list[View],
        Field(default_factory=list, description="Collection of Views"),
    ]
    funcs: Annotated[
        list[Func],
        Field(default_factory=list, description="Collection of Functions"),
    ]
    procs: Annotated[
        list[Proc],
        Field(default_factory=list, description="Collection of Procedures"),
    ]


class BaseUser(BaseUpdatableModel):
    name: str


class SQLUser(BaseUser):
    pwd: Annotated[Optional[SecretStr], Field(description="Password")] = None


class Role(BaseUpdatableModel):
    name: str
    members: list[SQLUser] = Field(default_factory=list)


User = Union[SQLUser, BaseUser]


class BaseDb(BaseUpdatableModel):
    schemas: Annotated[
        list[Scm],
        Field(default_factory=list, description="Collection of Schemas"),
    ]


class Db(BaseDb):
    users: list[User]
    roles: list[Role]
    policies: list[str]
