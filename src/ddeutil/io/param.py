# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

import re
from pathlib import Path
from typing import (
    Annotated,
    Any,
    Optional,
    Union,
)

from pydantic import BaseModel, Field, ValidationInfo
from pydantic.functional_validators import field_validator

from .__base import YamlEnvFl
from .__conf import UPDATE_KEY, VERSION_KEY
from .exceptions import ConfigArgumentError

TupleStr = tuple[str, ...]


FMT_NAMES: TupleStr = (
    "naming",
    "domain",
    "environ",
    "timestamp",
    "version",
    "compress",
    "extension",
)

RULE_FIX: TupleStr = (
    "timestamp",
    "version",
    "compress",
)


class Rule(BaseModel):
    """Rule Model that keep rule setting data for Register object.
    .. example::
        {
            "timestamp": {
                "minutes": 15
            },
            "excluded": [],
            "compress": None,
        }
    """

    timestamp: Optional[dict[str, int]] = Field(default_factory=dict)
    version: Annotated[Optional[str], Field()] = None
    excluded: Optional[list[str]] = Field(default_factory=list)
    compress: Annotated[
        Optional[str],
        Field(description="Compress type"),
    ] = None


class Stage(BaseModel):
    """Stage Model that keep stage data for transition data.

    Examples:
        >>> stage = {
        ...     "raw": {
        ...         "format": "",
        ...         "rules": {},
        ...     },
        ... }
    """

    alias: str
    format: str
    rules: Rule = Field(default_factory=Rule, description="Rule of stage")
    layer: int = Field(default=0)

    @field_validator("format", mode="before")
    def validate_format(cls, value, info: ValidationInfo):
        # NOTE:
        #   Validate the name in format string should contain any format name.
        if not (
            _searches := re.findall(
                r"{(?P<name>\w+):?(?P<format>[^{}]+)?}",
                value,
            )
        ):
            raise ConfigArgumentError(
                "format",
                (
                    f'This `{info.data["alias"]}` stage format dose not '
                    f"include any format name, the stage file was duplicated."
                ),
            )

        # NOTE: Validate the name in format string should exist in `FMT_NAMES`.
        if any((_search[0] not in FMT_NAMES) for _search in _searches):
            raise ConfigArgumentError(
                "format",
                "This stage have an unsupported format name.",
            )
        return value

    @field_validator("format", mode="after")
    def validate_rule_relate_with_format(cls, value, info: ValidationInfo):
        # NOTE: Validate a format of stage that relate with rules.
        for validator in RULE_FIX:
            if getattr(info.data.get("rules", {}), validator, None) and (
                validator not in value
            ):
                raise ConfigArgumentError(
                    (
                        "format",
                        validator,
                    ),
                    (
                        f"This stage set `{validator}` rule but does not have "
                        f"a `{validator}` format name in the format."
                    ),
                )
        return value


class PathData(BaseModel):
    root: Path = Field(default_factory=Path)
    data: Path = Field(default=None, validate_default=True)
    conf: Path = Field(default=None, validate_default=True)
    archive: Path = Field(default=None, validate_default=True)

    @field_validator("root", mode="before")
    def prepare_root(cls, v: Union[str, Path]) -> Path:
        return Path(v) if isinstance(v, str) else v

    @field_validator("data", "conf", "archive", mode="before")
    def prepare_path_from_path_str(cls, v, info: ValidationInfo) -> Path:
        if v is not None:
            return Path(v) if isinstance(v, str) else v
        if info.field_name == "archive":
            return info.data["root"] / ".archive"
        return info.data["root"] / info.field_name


class Flag(BaseModel):
    archive: bool = Field(default=False)


class Value(BaseModel):
    dt_fmt: str = Field(default="%Y-%m-%d %H:%M:%S")
    excluded: TupleStr = Field(default=(VERSION_KEY, UPDATE_KEY))


class Engine(BaseModel):
    paths: PathData = Field(default_factory=PathData)
    values: Value = Field(default_factory=Value)
    flags: Flag = Field(default_factory=Flag)


class Params(BaseModel, validate_assignment=True):
    stages: dict[str, Stage] = Field(default_factory=dict)
    engine: Engine = Field(default_factory=Engine)

    @classmethod
    def from_yaml(cls, path: Union[str, Path]):
        """Load params from .yaml file"""
        cls._origin_path = path
        return cls.model_validate(YamlEnvFl(path).read())

    @field_validator("stages", mode="before")
    def prepare_order_layer(cls, value: dict[str, dict[Any, Any]]):
        for i, k in enumerate(value, start=1):
            value[k] = value[k].copy() | {"layer": i, "alias": k}
        return value

    @property
    def stage_final(self) -> str:
        """Return the final stage name that ordered from layer value."""
        return max(self.stages.items(), key=lambda i: i[1].layer)[0]

    @property
    def stage_first(self) -> str:
        """Return the first stage name that ordered from layer value which
        does not be the base stage.
        """
        return min(self.stages.items(), key=lambda i: i[1].layer)[0]

    def get_stage(self, name: str) -> Stage:
        """Return Stage model that match with stage name."""
        if name == "base":
            return Stage.model_validate(
                {
                    "format": "{naming}_{timestamp}",
                    "alias": "base",
                }
            )
        elif name not in self.stages:
            raise ConfigArgumentError(
                "stage",
                f"Cannot get stage: {name!r} cause it does not exists",
            )
        return self.stages[name].model_copy()
