# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

import datetime
import os
from typing import (
    Any,
    Optional,
    TypedDict,
)

from dateutil.relativedelta import relativedelta
from ddeutil.core import (
    concat,
    hash_all,
    merge_dict,
)
from ddeutil.core.__base import must_rsplit
from ddeutil.core.dtutils import get_date
from deepdiff import DeepDiff
from fmtutil import (
    ConstantType,
    Datetime,
    FormatterArgumentError,
    FormatterGroup,
    FormatterGroupType,
    Naming,
    VerPackage,
    Version,
    make_const,
    make_group,
)

from .__base.pathutils import rm
from .config import ConfFile, FileSystem
from .exceptions import ConfigArgumentError, ConfigNotFound
from .models import Params

METADATA: dict[Any, Any] = {}


CompressConst: ConstantType = make_const(
    name="CompressConst",
    formatter={
        "%g": "gzip",
        "%-g": "gz",
        "%b": "bz2",
        "%r": "rar",
        "%x": "xz",
        "%z": "zip",
    },
)

FileExtensionConst: ConstantType = make_const(
    name="FileExtensionConst",
    formatter={
        "%j": "json",
        "%y": "yaml",
        "%e": "env",
        "%t": "toml",
    },
)


class BaseRegister:
    """Base Register Object"""

    def __init__(
        self,
        name: str,
        domain: Optional[str] = None,
    ):
        self.name = name
        self.domain: str = domain or ""
        self.updt: datetime.datetime = get_date("datetime")

        if domain:
            self.domain = (
                domain.replace(os.sep, "/").rstrip("/").lstrip("/").lower()
            )
        if any(sep in self.name for sep in {",", "."}):
            # Raise if name of configuration contain comma (`,`)
            # or dot (`.`) characters.
            raise ConfigArgumentError(
                "name",
                "the name of config should not contain comma or dot characters",
            )

    @property
    def fullname(self) -> str:
        """Return a configuration fullname, which join `name` and `domain`
        together with domain partition string.
        """
        return f"{self.domain}:{self.name}" if self.domain else self.name

    @property
    def shortname(self) -> str:
        """Return a configuration shortname, which get first character of any
        split string by name partition string.
        """
        return concat(word[0] for word in self.name.split("_"))

    @property
    def fmt_group(self) -> FormatterGroupType:
        """Generate the formatter group that include constant formatters from
        ``self.name`` and ``self.domain``.
        """
        return make_group(
            {
                "naming": make_const(fmt=Naming, value=self.name),
                "domain": make_const(fmt=Naming, value=self.domain),
                "compress": CompressConst,
                "extension": FileExtensionConst,
                "version": Version,
                "timestamp": Datetime,
            }
        )


class StageFiles(TypedDict):
    parse: FormatterGroup
    file: str


class Register(BaseRegister):
    """Register Object that contain configuration loading methods and metadata
    management. This object work with stage input argument, that set all
    properties in the `parameter.yaml` file.
    """

    @classmethod
    def reset(
        cls,
        name: str,
        config: Params,
    ) -> Register:
        """Reset all configuration data files that exists in any stage but
        does not do anything in the base stage. This method will use when the
        config name of data was changed and does not use the old name. If the
        name was changed and that config data does not reset,
        the configuration files of this data will exist in any moved stage.

        :param name: str : The fullname of configuration.
        :param config:
        :type config: Params
        """

        # Delete all config file from any stage.
        for stage in config.stages:
            try:
                cls(
                    name,
                    stage=stage,
                    config=config,
                ).remove()
            except ConfigNotFound:
                continue

        # # Delete data form metadata.
        # ConfMetadata(
        #     params.engine.path.metadata,
        #     name=_name,
        #     environ=Env(config=params).name,
        # ).remove()
        return cls(name, config=config)

    def __init__(
        self,
        name: str,
        stage: Optional[str] = None,
        *,
        config: Optional[Params] = None,
        loader: Optional[type[FileSystem]] = None,
    ):
        _domain, _name = must_rsplit(concat(name.split()), ":", maxsplit=1)
        super().__init__(name=_name, domain=_domain)
        self.stage: str = stage or "base"
        self.config = config
        self.loader = loader

        # Load latest version of data from data lake or data store of
        # configuration files
        self.__data: dict[str, Any] = self.pick(stage=self.stage)
        if not self.__data:
            _domain_stm: str = (
                f"with domain {self.domain!r}" if self.domain else ""
            )
            raise ConfigNotFound(
                f"Configuration {self.name!r} {_domain_stm} "
                f"does not found in the {self.stage!r} data lake or data store."
            )

        # TODO: Implement meta object
        self.meta = METADATA

        # Compare data from current stage and latest version in metadata.
        self.changed: int = self.compare_data(
            target=self.meta.get(self.stage, {})
        )

        # Update metadata if the configuration data does not exist, or
        # it has any changes.
        if not self.params.engine.flags.auto_update:
            print("Skip update metadata table/file ...")
        elif self.changed == 99:
            print(
                f"Configuration data with stage: {self.stage!r} does not "
                f"exists in metadata ..."
            )
        elif self.changed > 0:
            print(
                f"Should update metadata because diff level is {self.changed}."
            )
            _version_stm: str = f"v{str(self.version((self.stage != 'base')))}"

    def __hash__(self):
        return hash(
            self.fullname
            + self.stage
            + f"{self.timestamp:{self.params.engine.values.datetime_fmt}}"
        )

    def __str__(self) -> str:
        return f"({self.fullname}, {self.stage})"

    def __repr__(self) -> str:
        _params: list = [f"name={self.fullname!r}"]
        if self.stage != "base":
            _params.append(f"stage={self.stage!r}")
        return f"<{self.__class__.__name__}({', '.join(_params)})>"

    def __eq__(self, other: Register) -> bool:
        if isinstance(other, self.__class__):
            return (
                self.fullname == other.fullname
                and self.stage == other.stage
                and self.timestamp == other.timestamp
            )
        return NotImplemented

    def data(self, hashing: bool = False) -> dict[str, Any]:
        """Return the data with the configuration name."""
        _data = self.__data
        if (self.stage is None) or (self.stage == "base"):
            _data = merge_dict(
                {
                    k: v
                    for k, v in (self.meta.get(self.stage, {}).items())
                    if k in self.params.engine.values.excluded_keys
                },
                self.__data,
            )
        return (
            hash_all(
                _data,
                exclude=set(self.params.engine.values.excluded_keys),
            )
            if hashing
            else _data
        )

    @property
    def params(self) -> Params:
        if self.config is None:
            raise NotImplementedError(
                "This register instance can not do any actions because config "
                "param does not set."
            )
        return self.config

    @params.setter
    def params(self, config: Params) -> None:
        self.config = config

    @property
    def timestamp(self) -> datetime.datetime:
        """Return the current timestamp value of config data. If timestamp value
        does not exist. this property will return timestamp of initialize.

        :return: datetime
        """
        if self.changed > 0:
            return self.updt
        elif _dt := self.data().get("updt"):
            return datetime.datetime.strptime(
                _dt,
                self.params.engine.values.datetime_fmt,
            )
        return self.updt

    def version(self, _next: bool = False) -> VerPackage:
        """Generate version value from the pick method. If version value does
        not exist from configuration data, this property will return the
        default, `v0.0.1`. If the initialization process tracking some change
        from configuration data between metadata and the latest data in the
        stage, the _next will be generated.

        :return: VerPackage
        """
        _vs = VerPackage.parse(self.data().get("version", "v0.0.1"))
        if not _next or self.changed == 0:
            return _vs
        elif self.changed >= 3:
            return _vs.bump_major()
        elif self.changed == 2:
            return _vs.bump_minor()
        return _vs.bump_patch()

    def fmt(self, update: Optional[dict[str, Any]] = None):
        return self.fmt_group(
            {
                "timestamp": self.timestamp,
                "version": self.version(),
                **(update or {}),
            }
        )

    def compare_data(
        self,
        target: dict[Any, Any],
    ) -> int:
        """Return difference column from dictionary comparison method which use
        the `deepdiff` library.

        :param target: dict : The target dictionary for compare with current
                configuration data.
        """
        if not target:
            return 99

        results = DeepDiff(
            self.data(hashing=True),
            target,
            ignore_order=True,
            exclude_paths={
                f"root[{key!r}]"
                for key in self.params.engine.values.excluded_keys
            },
        )
        if any(
            _ in results
            for _ in (
                "dictionary_item_added",
                "dictionary_item_removed",
                "iterable_item_added",
                "iterable_item_removed",
            )
        ):
            return 2
        elif any(
            _ in results
            for _ in (
                "values_changed",
                "type_changes",
            )
        ):
            return 1
        return 0

    def __stage_files(
        self,
        stage: str,
        loading: ConfFile,
    ) -> dict[int, StageFiles]:
        """Return mapping of StageFiles data."""
        results: dict[int, StageFiles] = {}
        for index, file in enumerate(
            (_f.name for _f in loading.files()),
            start=1,
        ):
            try:
                results[index]: dict = {
                    "parse": self.fmt_group.parse(
                        value=file,
                        fmt=rf"{self.params.get_stage(stage).format}\.json",
                    ),
                    "file": file,
                }
            except FormatterArgumentError:
                continue
        return results

    def pick(
        self,
        stage: Optional[str] = None,
        *,
        order: Optional[int] = 1,
        reverse: bool = False,
    ):
        # Load data from source
        if (stage is None) or (stage == "base"):
            return ConfFile(
                path=(self.params.engine.paths.conf / self.domain),
                open_file=self.loader,
            ).load(name=self.name, order=order)

        loading = ConfFile(
            path=self.params.engine.paths.data / stage,
            compress=self.params.get_stage(stage).rules.compress,
            open_file=self.loader,
        )

        if results := self.__stage_files(stage, loading):
            max_data: list = sorted(
                results.items(),
                key=lambda x: (x[1]["parse"],),
                reverse=reverse,
            )
            return loading.load_stage(
                path=(loading.path / max_data[-order][1]["file"])
            )
        return {}

    def move(
        self,
        stage: str,
        *,
        force: bool = False,
        retention: bool = True,
    ) -> Register:
        """"""
        loading = ConfFile(
            path=self.params.engine.paths.data / stage,
            compress=self.params.get_stage(stage).rules.compress,
            open_file=self.loader,
        )
        if (
            self.compare_data(
                hash_all(
                    self.pick(stage=stage),
                    exclude=set(self.params.engine.values.excluded_keys),
                )
            )
            > 0
            or force
        ):
            _filename: str = self.fmt().format(
                f"{self.params.get_stage(name=stage).format}.json",
            )
            if os.path.exists(loading.path / _filename):
                # TODO: generate serial number if file exists
                print(
                    f"file {_filename!r} already exists in the "
                    f"{stage!r} stage.",
                )
            _dt_fmt: str = self.params.engine.values.datetime_fmt
            loading.save_stage(
                path=(loading.path / _filename),
                data=merge_dict(
                    self.data(),
                    {
                        "updt": f"{self.timestamp:{_dt_fmt}}",
                        "version": f"v{str(self.version())}",
                    },
                ),
            )
            # Retention process after move data to the stage successful
            if retention:
                self.purge(stage=stage)
        else:
            print(
                f"Config {self.name!r} can not move {self.stage!r} -> "
                f"{stage!r} because config data does not any change or "
                f"does not force moving."
            )
        return self.switch(stage=stage)

    def switch(self, stage: str) -> Register:
        """Switch instance from old stage to new stage with input argument."""
        return self.__class__(
            name=self.fullname,
            stage=stage,
            config=self.params,
        )

    def purge(self, stage: Optional[str] = None) -> None:
        """Purge configuration files that match with any rules in the stage
        setting.
        """
        _stage: str = stage or self.stage
        if not (_rules := self.params.get_stage(_stage).rules):
            return
        loading = ConfFile(
            path=self.params.engine.paths.data / stage,
            compress=_rules.compress,
            open_file=self.loader,
        )
        results: dict = self.__stage_files(_stage, loading)
        max_file: FormatterGroup = max(
            results.items(),
            key=lambda x: (x[1]["parse"],),
        )[1]["parse"]

        upper_bound: Optional[FormatterGroup] = None
        if _rtt_ts := _rules.timestamp:
            _metric: Optional[str] = _rules.timestamp_metric
            upper_bound = max_file.adjust(
                {"timestamp": relativedelta(**_rtt_ts)}
            )
        # elif _rtt_value := _rules.version:
        #     upper_bound = max_file.adjust(
        #         {'version': _rtt_value}
        #     )

        if upper_bound is not None:
            for _, data in filter(
                lambda x: x[1]["parse"] < upper_bound,
                results.items(),
            ):
                _file: str = data["file"]
                if self.params.engine.flags.archive:
                    _ac_path: str = (
                        f"{stage.lower()}_{self.updt:%Y%m%d%H%M%S}_{_file}"
                    )
                    loading.move(
                        _file,
                        destination=self.params.engine.paths.archive / _ac_path,
                    )
                rm(loading.path / _file)

    def deploy(self, stop: Optional[str] = None) -> Register:
        """Deploy data that move from base to final stage.

        :param stop: A stage name for stop when move config from base stage
            to final stage.
        :type stop: str
        """
        _base: Register = self
        _stop: str = stop or self.params.stage_final
        assert (
            _stop in self.params.stages
        ), "a `stop` argument should exists in stages data on Param config."
        for stage in self.params.stages:
            _base: Register = _base.move(stage)
            if _stop and (stage == _stop):
                break
        return _base

    def remove(self, stage: Optional[str] = None) -> None:
        """Remove config file from the stage storage.

        :param stage:
        :type stage: Optional[str]
        """
        _stage: str = stage or self.stage
        assert (
            _stage != "base"
        ), "The remove method can not process on the 'base' stage."
        loading = ConfFile(
            path=self.params.engine.paths.data / _stage,
            open_file=self.loader,
        )

        # Remove all files from the stage.
        for _, data in self.__stage_files(_stage, loading).items():
            _file: str = data["file"]
            if self.params.engine.flags.archive:
                _ac_path: str = (
                    f"{_stage.lower()}_{self.updt:%Y%m%d%H%M%S}_{_file}"
                )
                loading.move(
                    _file,
                    destination=self.params.engine.paths.archive / _ac_path,
                )
            rm(loading.path / _file)


__all__ = ("Register",)
