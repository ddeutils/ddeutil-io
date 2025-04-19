# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

if TYPE_CHECKING:
    from typing_extensions import Self

from .__type import TupleStr
from .exceptions import ConfigArgumentError
from .files import YamlEnvFl

UPDATE_KEY: str = "__updt"
VERSION_KEY: str = "__version"
VERSION_DEFAULT: str = "1990-01-01"
DATE_FMT: str = "%Y-%m-%d %H:%M:%S"
DATE_LOG_FMT: str = "%Y%m%d%H%M%S"
FMT_NAMES: TupleStr = (
    "naming",
    "domain",
    "environ",
    "timestamp",
    "version",
    "compress",
    "extension",
)
RULE_NECESSARY_KEYS: TupleStr = (
    "timestamp",
    "compress",
)


def get_root_path() -> Path:
    """Return the root path for this package that receive env var with
    ``IO_REGISTER_ROOT_PATH`` key.

    :rtype: Path
    """
    if (root := os.getenv("IO_REGISTER_ROOT_PATH")) is not None:
        return Path(root)
    return Path()


@dataclass(frozen=True)
class Rule:
    """Rule dataclass that keep rule setting data for Register object.

    Examples:
        >>> rule = {
        ...     "timestamp": {"minutes": 15},
        ...     "excluded": [],
        ...     "compress": None,
        ... }
    """

    timestamp: dict[str, int] = field(default_factory=dict)
    excluded: list = field(default_factory=list)
    compress: Optional[str] = field(default=None)


@dataclass
class Stage:
    """Stage dataclass that keep stage data for transition data.

    Examples:
        >>> stage = {
        ...     "raw": {
        ...         "format": "",
        ...         "rule": { ... },
        ...     },
        ... }
    """

    format: str
    alias: Optional[str] = field(default=None)
    rule: Rule = field(default_factory=Rule)
    layer: int = field(default=0)

    def __post_init__(self) -> Self:
        """Post initialize method of this stage dataclass."""
        # NOTE: Nested Rule object on the rule field.
        if isinstance(self.rule, dict):
            self.rule: Rule = Rule(**self.rule)

        # VALIDATE: Check the name in format string should contain any format
        #   name.
        if not (
            _searches := re.findall(
                r"{\s?(?P<name>\w+):?(?P<format>[^{}]+)?\s?}",
                self.format,
            )
        ):
            raise ConfigArgumentError(
                f"This `{self.alias}` stage format dose not include any format "
                f"name, the stage file was duplicated."
            )

        # VALIDATE: Check the name in format string should exist in `FMT_NAMES`.
        if any((_search[0] not in FMT_NAMES) for _search in _searches):
            raise ConfigArgumentError(
                "The stage has an unsupported format name.",
            )

        # VALIDATE: Validate a format of stage that relate with rules.
        for rule_key in RULE_NECESSARY_KEYS:
            if getattr(self.rule, rule_key, None) and (
                not re.search(rf"{rule_key}", self.format)
            ):
                raise ConfigArgumentError(
                    f"This stage rule was set `{rule_key}` property but does "
                    f"not have a `{rule_key}` format name in the format."
                )
        return self


base_stage: Stage = Stage(
    **{
        "format": "{naming}_{timestamp}",
        "alias": "base",
    }
)


@dataclass
class Paths:
    """Paths dataclass that keep necessary paths for register or loading object.

    Examples:
        >>> path = {
        ...     "root": "./",
        ...     "data": "./data",
        ...     "conf": "./config",
        ... }
    """

    root: Path = field(default_factory=get_root_path)
    data: Path = field(default=None)
    conf: Path = field(default=None)

    def __post_init__(self) -> Self:
        """Post initialize for prepare paths that receive with string value."""
        if isinstance(self.root, str):
            self.root = Path(self.root)

        if self.data is None:
            self.data = self.root / "data"
        elif isinstance(self.data, str):
            self.data = Path(self.data)

        if self.conf is None:
            self.conf = self.root / "conf"
        elif isinstance(self.conf, str):
            self.conf = Path(self.conf)

        return self


@dataclass
class Params:
    """Params dataclass."""

    stages: dict[str, Stage]
    paths: Paths = field(default_factory=Paths)

    @classmethod
    def from_toml(cls, path: Union[Path]) -> Self:
        """Read params from the `.toml` file"""
        import rtoml

        with open(
            path or "./io-register.toml",
            encoding="utf-8",
        ) as f:
            data: dict[str, Any] = (
                rtoml.load(f).get("tool", {}).get("io", {}).get("register", {})
            )
        return Params(**data)

    @classmethod
    def from_yaml(cls, path: Union[Path]) -> Self:
        """Read params from the `.yaml` file"""
        return cls(
            **YamlEnvFl(path or "./io-register.yaml")
            .read()
            .get("tool", {})
            .get("io", {})
            .get("register", {})
        )

    def __post_init__(self) -> Self:
        """Post initialize for prepare params."""
        for index, k in enumerate(self.stages, start=1):
            stage: Union[dict[str, Any], Stage] = self.stages[k]
            if isinstance(stage, dict):
                layer: int = stage.get("layer") or index
                self.stages[k] = Stage(**(stage | {"alias": k, "layer": layer}))
            elif isinstance(stage, Stage):
                layer: int = stage.layer or index
                stage.alias = k
                stage.layer = layer
                self.stages[k] = stage
            else:
                raise ConfigArgumentError(f"The stage: {k} does not valid type")

        if isinstance(self.paths, dict):
            self.paths: Paths = Paths(**self.paths)
        return self

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
        """Return Stage model that match with stage name. If an input stage
        value equal 'base', it will return the default stage model.

        :param name: A stage name that want to get from this params.
        :type name: str
        """
        if name == "base":
            return base_stage
        elif name not in self.stages:
            raise ConfigArgumentError(
                f"Cannot get stage: {name!r} cause it does not exists",
            )
        return self.stages[name]

    def to_dict(self) -> dict[str, Any]:
        """Return dict of all this dataclass fields."""
        return asdict(self)
