# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

from typing import (
    Annotated,
    Optional,
)

from pydantic import BaseModel, Field


class Const(BaseModel):
    """Constraint Model

    Examples:
        >>> Const(of='foo').name
        'foo_const'
    """

    of: Annotated[
        Optional[str],
        Field(description="Owner of Constraint"),
    ] = None

    @property
    def name(self) -> str:
        if not self.of:
            raise ValueError(
                "This constraint does not pass `of` value for take ownership."
            )
        return f"{self.of}_const"


class Pk(Const):
    """Primary Key Model.

    Examples:
        >>> Pk(of="foo", cols=["bar", "baz"]).name
        'foo_bar_baz_pk'
    """

    cols: Annotated[
        list[str],
        Field(default_factory=list, description="List of primary key columns"),
    ]

    @property
    def name(self) -> str:
        if not self.of:
            raise ValueError(
                "This constraint does not pass `of` value for take ownership."
            )
        if self.cols:
            return f'{self.of}_{"_".join(self.cols)}_pk'
        raise ValueError("This primary key does not have any columns.")


class Ref(BaseModel):
    """Reference Model

    Examples:
        >>> data = {
        ...     "tbl": "foo",
        ...     "col": "bar",
        ... }
        >>> Ref.model_validate(data).tbl
        'foo'
    """

    tbl: str
    col: str


class Fk(Const):
    """Foreign Key Model.

    Examples:
        >>> data = {
        ...     "of": "foo",
        ...     "to": "bar",
        ...     "ref": {
        ...         "tbl": "ref_table",
        ...         "col": "ref_column"
        ...     }
        ... }
        >>> Fk.model_validate(data).name
        'foo_bar_ref_table_ref_column_fk'
    """

    to: str
    ref: Ref

    @property
    def name(self) -> str:
        if not self.of:
            raise ValueError(
                "This constraint does not pass `of` value for take ownership."
            )
        return f"{self.of}_{self.to}_{self.ref.tbl}_{self.ref.col}_fk"
