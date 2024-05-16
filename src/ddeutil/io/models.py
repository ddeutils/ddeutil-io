# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

import re
from pathlib import Path
from typing import (
    Any,
    Optional,
    Union,
)

from pydantic import (
    BaseModel,
    Field,
    ValidationInfo,
)
from pydantic.functional_validators import field_validator

from .__base import YamlEnvFl
from .exceptions import ConfigArgumentError

FMT_NAMES: tuple[str, ...] = (
    "naming",
    "domain",
    "environ",
    "timestamp",
    "version",
    "compress",
    "extension",
)

RULE_FIX: tuple[str, ...] = (
    "timestamp",
    "version",
    "compress",
)


class RuleData(BaseModel):
    """Rule Data Model
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
    version: Optional[str] = Field(default=None)
    excluded: Optional[list[str]] = Field(default_factory=list)
    compress: Optional[str] = Field(default=None)


class StageData(BaseModel):
    """
    .. example::
        {
            "raw": {
                "format": "",
                rules: {},
            },
        }
    """

    alias: str
    rules: RuleData = Field(default_factory=RuleData)
    format: str
    layer: int = Field(default=0)

    @field_validator("format", mode="before")
    def validate_format(cls, value, info: ValidationInfo):
        # Validate the name in format string should contain any format name.
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

        # Validate the name in format string should exist in `FMT_NAMES`.
        if any((_search[0] not in FMT_NAMES) for _search in _searches):
            raise ConfigArgumentError(
                "format",
                "This stage have an unsupported format name.",
            )
        return value

    @field_validator("format", mode="after")
    def validate_rule_relate_with_format(cls, value, info: ValidationInfo):
        # Validate a format of stage that relate with rules.
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
    def prepare_path_from_str(cls, v, info: ValidationInfo) -> Path:
        if v is not None:
            return Path(v) if isinstance(v, str) else v
        if info.field_name == "archive":
            return info.data["root"] / ".archive"
        return info.data["root"] / info.field_name


class FlagData(BaseModel):
    archive: bool = Field(default=False)
    auto_update: bool = Field(default=False)


class ValueData(BaseModel):
    dt_fmt: str = Field(default="%Y-%m-%d %H:%M:%S")
    excluded: tuple[str, ...] = Field(
        default=(
            "version",
            "updt",
        )
    )


class EngineData(BaseModel):
    paths: PathData = Field(default_factory=PathData)
    flags: FlagData = Field(default_factory=FlagData)
    values: ValueData = Field(default_factory=ValueData)


class Params(BaseModel, validate_assignment=True):
    stages: dict[str, StageData] = Field(default_factory=dict)
    engine: EngineData = Field(default_factory=EngineData)

    @classmethod
    def from_file(cls, path: Union[str, Path]):
        cls._origin_path = path
        return cls.model_validate(YamlEnvFl(path).read())

    @field_validator("stages", mode="before")
    def order_layer(cls, value: dict[str, dict[Any, Any]]):
        for i, k in enumerate(value, start=1):
            value[k] = value[k].copy() | {"layer": i, "alias": k}
        return value

    @property
    def stage_final(self) -> str:
        return max(self.stages.items(), key=lambda i: i[1].layer)[0]

    @property
    def stage_first(self) -> str:
        return min(self.stages.items(), key=lambda i: i[1].layer)[0]

    def get_stage(self, name: str) -> StageData:
        if name == "base":
            return StageData.model_validate(
                {
                    "format": "{naming}_{timestamp}",
                    "layer": 0,
                    "alias": "base",
                }
            )
        elif name not in self.stages:
            raise ConfigArgumentError(
                "stage",
                (
                    f"Cannot get stage: {name!r} because it does not set "
                    f"in `parameters.yaml`"
                ),
            )
        return self.stages[name].model_copy()

    def refresh(self, path: Optional[str] = None) -> Params:
        _origin_path = path or self._origin_path
        self.__dict__.update(self.from_file(path=_origin_path).__dict__)
        return self
