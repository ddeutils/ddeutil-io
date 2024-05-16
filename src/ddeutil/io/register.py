# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

import logging
import os
from datetime import datetime
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

from .__base import Fl, rm
from .config import ConfFl
from .exceptions import ConfigArgumentError, ConfigNotFound
from .models import Params

METADATA: dict[str, Any] = {}


class StageFiles(TypedDict):
    parse: FormatterGroup
    file: str


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
        *,
        domain: Optional[str] = None,
    ) -> None:
        self.name: str = name
        self.updt: datetime = get_date("datetime")
        self.domain: str = (
            domain.replace(os.sep, "/").strip("/").lower() if domain else ""
        )
        if any(sep in self.name for sep in (",", ".")):
            raise ConfigArgumentError(
                "name",
                "Config name should not contain `,` or `.` char",
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


class Register(BaseRegister):
    """Register Object that contain configuration loading methods and metadata
    management. This object work with stage input argument, that set all
    properties in the `parameter.yaml` file.
    """

    @classmethod
    def reset(
        cls,
        name: str,
        params: Params,
    ) -> Register:
        """Reset all configuration data files that exists in any stage but
        does not do anything in the base stage. This method will use when the
        config name of data was changed and does not use the old name. If the
        name was changed and that config data does not reset,
        the configuration files of this data will exist in any moved stage.

        :param name: The fullname of configuration.
        :type name: str
        :param params:
        :type params: Params
        """
        for stage in params.stages:
            try:
                cls(name, stage=stage, params=params).remove()
            except ConfigNotFound:
                continue
        return cls(name, params=params)

    def __init__(
        self,
        name: str,
        stage: Optional[str] = None,
        *,
        params: Optional[Params] = None,
        loader: Optional[type[Fl]] = None,
        loader_stg: Optional[type[Fl]] = None,
    ):
        _domain, _name = must_rsplit(concat(name.split()), ":", maxsplit=1)
        super().__init__(name=_name, domain=_domain)
        if not params:
            raise NotImplementedError(
                "This register instance can not do any actions because config "
                "param does not set."
            )
        self.stage: str = stage or "base"
        self.loader: Optional[type[Fl]] = loader
        self.loader_stg: Optional[type[Fl]] = loader_stg
        self.params: Optional[Params] = params

        # Load latest version of data from data lake or data store of
        # configuration files
        self.__data: dict[str, Any] = self.pick(stage=self.stage)
        if not self.__data:
            raise ConfigNotFound(
                f"Config {self.name!r} "
                f"{f'in domain {self.domain!r} ' if self.domain else ' '}"
                f"does not exist in stage {self.stage!r}."
            )

        self.meta: dict[str, Any] = METADATA.get(self.fullname, {})

        # NOTE:
        #   Compare data from current stage and latest version in metadata.
        self.changed: int = self.compare_data(
            target=self.meta.get(self.stage, {})
        )

        # NOTE:
        #   Update metadata if the configuration data does not exist, or
        #   it has any changes.
        if not self.params.engine.flags.auto_update:
            logging.info("Skip update metadata ...")
        elif self.changed == 99:
            logging.info(
                f"Configuration data with stage: {self.stage!r} does not "
                f"exists in metadata ..."
            )
            # TODO: Create metadata for caching value before compare data next
            #   time. (It can be table on database or sqlite file.
            # METADATA.update({"self.fullname": self.__data})
        elif self.changed > 0:
            logging.info(
                f"Should update metadata because diff level is {self.changed}."
            )

        # TODO: Remove this line when develop metadata feature in the next
        #   release.
        METADATA.pop(self.fullname, None)

    def __hash__(self) -> int:
        return hash(
            self.fullname
            + self.stage
            + f"{self.timestamp:{self.params.engine.values.dt_fmt}}"
        )

    def __str__(self) -> str:
        return f"({self.fullname}, {self.stage})"

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}(name={self.fullname!r}"
            f"{f'stage={self.stage!r}' if self.stage != 'base' else ''})>"
        )

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
        if not self.stage or (self.stage == "base"):
            _data = {
                k: v
                for k, v in (self.meta.get(self.stage, {}).items())
                if k in self.params.engine.values.excluded
            } | self.__data
        return (
            hash_all(_data, exclude=set(self.params.engine.values.excluded))
            if hashing
            else _data
        )

    @property
    def timestamp(self) -> datetime:
        """Return the current timestamp value of config data. If timestamp value
        does not exist. this property will return timestamp of initialize.

        :return: datetime
        """
        if self.changed > 0:
            return self.updt
        elif _dt := self.data().get("updt"):
            return datetime.strptime(
                _dt,
                self.params.engine.values.dt_fmt,
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

    def fmt(self, update: Optional[dict[str, Any]] = None) -> FormatterGroup:
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
                f"root[{key!r}]" for key in self.params.engine.values.excluded
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
        loading: ConfFl,
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
    ) -> dict[str, Any]:
        if (stage is None) or (stage == "base"):
            return ConfFl(
                path=(self.params.engine.paths.conf / self.domain),
                open_file=self.loader,
                open_file_stg=self.loader_stg,
            ).load(name=self.name, order=order)

        loading = ConfFl(
            path=self.params.engine.paths.data / stage,
            compress=self.params.get_stage(stage).rules.compress,
            open_file=self.loader,
            open_file_stg=self.loader_stg,
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
        """Move file to the target stage."""
        loading: ConfFl = ConfFl(
            path=self.params.engine.paths.data / stage,
            compress=self.params.get_stage(stage).rules.compress,
            open_file=self.loader,
            open_file_stg=self.loader_stg,
        )
        if (
            self.compare_data(
                hash_all(
                    self.pick(stage=stage),
                    exclude=set(self.params.engine.values.excluded),
                )
            )
            > 0
            or force
        ):
            _filename: str = self.fmt().format(
                f"{self.params.get_stage(name=stage).format}.json",
            )
            if (loading.path / _filename).exists():
                # TODO: generate serial number if file exists
                logging.warning(
                    f"File {_filename!r} already exists in {stage!r} stage."
                )
            _dt_fmt: str = self.params.engine.values.dt_fmt
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
            # NOTE:
            #   Retention process after move data to the stage successful
            if retention:
                self.purge(stage=stage)
        else:
            logging.warning(
                f"Config {self.name!r} cannot move {self.stage!r} -> "
                f"{stage!r} cause the data does not has any change or "
                f"force moving flag does not set."
            )
        return self.switch(stage=stage)

    def switch(self, stage: str) -> Register:
        """Switch instance from old stage to new stage with input argument."""
        return self.__class__(
            name=self.fullname,
            stage=stage,
            params=self.params,
        )

    def purge(self, stage: Optional[str] = None) -> None:
        """Purge configuration files that match with any rules in the stage
        setting.
        """
        _stage: str = stage or self.stage
        if not (_rules := self.params.get_stage(_stage).rules):
            return
        loading: ConfFl = ConfFl(
            path=self.params.engine.paths.data / stage,
            compress=_rules.compress,
            open_file=self.loader,
            open_file_stg=self.loader_stg,
        )
        rs: dict[int, StageFiles] = self.__stage_files(_stage, loading)
        max_file: FormatterGroup = max(
            rs.items(),
            key=lambda x: (x[1]["parse"],),
        )[1]["parse"]

        upper_bound: Optional[FormatterGroup] = None
        if _rtt_ts := _rules.timestamp:
            upper_bound = max_file.adjust(
                {"timestamp": relativedelta(**_rtt_ts)}
            )

        if upper_bound is not None:
            for _, data in filter(
                lambda x: x[1]["parse"] < upper_bound,
                rs.items(),
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

        :param stage: a stage value that want to remove.
        :type stage: Optional[str]
        """
        _stage: str = stage or self.stage
        assert (
            _stage != "base"
        ), "The remove method can not process on the 'base' stage."
        loading: ConfFl = ConfFl(
            path=self.params.engine.paths.data / _stage,
            open_file=self.loader,
            open_file_stg=self.loader_stg,
        )

        # Remove all files from the stage.
        data: StageFiles
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
