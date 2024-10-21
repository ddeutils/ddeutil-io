# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
"""Register module provide the Register object for manage configuration file
with multiple storing stages. That mean if you have original config file with
YAML file format and want to save memory to reading in your any application
you will convert it to JSON file or some binary file and always reuse it if the
original config file does not change context data inside.

    So, this module will help you handle this scenario with Register object.
This object can dynamic stage with your params config.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, ClassVar, Literal, TypedDict

from dateutil.relativedelta import relativedelta
from ddeutil.core import base, hash, merge, splitter
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
from typing_extensions import Self

from .config import DATE_FMT, DATE_LOG_FMT, UPDATE_KEY, VERSION_KEY, Params
from .exceptions import RegisterArgumentError, StoreNotFound
from .files import rm
from .stores import Store

TupleStr = tuple[str, ...]

logger = logging.getLogger("ddeutil.io")

METADATA: dict[str, Any] = {}
REGISTER_BASE_STAGE_DEFAULT: str = "base"
REGISTER_DIFF_LEVEL: dict[int, TupleStr] = {
    1: (
        "values_changed",
        "type_changes",
    ),
    2: (
        "dictionary_item_added",
        "dictionary_item_removed",
        "iterable_item_added",
        "iterable_item_removed",
    ),
}

__all__: TupleStr = (
    "Register",
    "ArchiveRegister",
)


class StageFl(TypedDict):
    """Stage files dict typing for the mypy checker step."""

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
    """Base Register object that is not implement any features without base
    properties.

    :param name: A name of key of config data that want to register.
    :param domain: A dir path of config files that use to search a name of data.
    """

    def __init__(self, name: str, *, domain: str | None = None) -> None:
        self.name: str = name
        self.domain: str = (
            domain.replace(os.sep, "/").strip("/").lower() if domain else ""
        )
        if any(sep in self.name for sep in (",", ".")):
            raise RegisterArgumentError(
                "The register name should not contain any `,` or `.` "
                "characters."
            )

        # NOTE: generate update datetime.
        self.updt: datetime = get_date("datetime")

    @property
    def fullname(self) -> str:
        """Return a configuration fullname, which join `name` and `domain`
        together with domain partition string.

        :rtype: str
        """
        return f"{self.domain}:{self.name}" if self.domain else self.name

    @property
    def shortname(self) -> str:
        """Return a configuration shortname, which get first character of any
        split string by name partition string.

        :rtype: str
        """
        return base.concat(word[0] for word in self.name.split("_"))

    @property
    def fmt_type(self) -> FormatterGroupType:  # pragma: no cove
        """Return the generated formatter group that include constant formatters
        from ``self.name`` and ``self.domain``.

        :rtype: FormatterGroupType
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
    """Register Object that contain configuration config methods and metadata
    management. This object work with stage input argument, that set all
    properties in the `parameter.yaml` file.

    :param name: A fullname of register data that able to split domain and name
        before passing to parent base register object with ``:``.
    :param stage: A stage name that want to get data with an input name.
    :param params:
    :param store:
    """

    @classmethod
    def reset(cls, name: str, params: Params) -> Self:
        """Reset all configuration data files that exists in any stage but
        does not do anything in the base stage. This method will use when the
        config name of data was changed and does not use the old name. If the
        name was changed and that config data does not reset,
        the configuration files of this data will exist in any moved stage.

        :param name: The fullname of configuration.
        :type name: str
        :param params:
        :type params: Params

        :rtype: Self
        :return: itself object that passing the fullname to initialize step.
        """
        for stage in params.stages:
            try:
                # NOTE: Start reset (remove) on the target stage area.
                cls(name, stage=stage, params=params).remove()
            except StoreNotFound:
                continue
        return cls(name, params=params)

    def __init__(
        self,
        name: str,
        stage: str | None = None,
        *,
        params: Params | None = None,
        store: type[Store] | None = None,
    ) -> None:
        domain, name = splitter.must_rsplit(
            base.concat(name.split()),
            sep=":",
            maxsplit=1,
        )
        super().__init__(name=name, domain=domain)
        if not params:
            raise NotImplementedError(
                "This register instance can not do any actions because config "
                "param does not set."
            )
        self.params: Params | None = params
        self.stage: str = stage or REGISTER_BASE_STAGE_DEFAULT
        self.store: type[Store] | None = store

        # NOTE: Load latest version of data from data lake or data store of
        #   configuration files.
        self.__raw_data: dict[str, Any] = self.get(stage=self.stage)
        if not self.__raw_data:
            raise StoreNotFound(
                f"Register name {self.name!r} "
                f"{f'in domain {self.domain!r} ' if self.domain else ' '}"
                f"does not find data in stage: {self.stage!r}."
            )

        # NOTE: Running metadata tracking cache.
        self.__manage_metadata()

    def __manage_metadata(self):
        """Manage the latest context data for detect change by metadata
        strategy.
        """
        if self.fullname not in METADATA:
            METADATA[self.fullname] = {}

        self.meta: dict[str, Any] = METADATA.get(self.fullname)

        # NOTE: Compare data from current stage and latest version in metadata.
        self.changed: int = self.compare_data(self.meta.get(self.stage, {}))

        # NOTE:
        #   Update metadata if the configuration data does not exist, or it has
        #   any changes.
        if self.changed > 0:
            if self.changed == 99:
                logger.debug(
                    f"Data in stage: {self.stage!r} does not exists in metadata"
                )
            else:
                logger.debug(
                    f"Should update metadata because diff level is "
                    f"{self.changed}."
                )
            self.meta.update({self.stage: self.data(hashing=True)})

    def __str__(self) -> str:
        return f"({self.fullname}, {self.stage})"

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}(name={self.fullname!r}"
            f"{f'stage={self.stage!r}' if self.stage != 'base' else ''})>"
        )

    def __eq__(self, other: Self) -> bool:
        if isinstance(other, self.__class__):
            return (
                self.fullname == other.fullname
                and self.stage == other.stage
                and self.timestamp == other.timestamp
            )
        return NotImplemented

    def data(self, hashing: bool = False) -> dict[str, Any]:
        """Return the context data with the specific name of data.

        :param hashing: A hashing flag that allow use hash function on the
            context data.
        :type hashing: bool (Default=False)
        :rtype: dict[str, Any]
        """
        _data: dict[str, Any] = self.__raw_data.copy()
        meta: dict[str, Any] = self.meta.get(self.stage, {})
        if not self.stage or (self.stage == REGISTER_BASE_STAGE_DEFAULT):
            _data: dict[str, Any] = {
                k: meta[k] for k in meta if k in (UPDATE_KEY, VERSION_KEY)
            } | self.__raw_data

        return (
            hash.hash_all(_data, exclude={UPDATE_KEY, VERSION_KEY})
            if hashing
            else _data
        )

    @property
    def timestamp(self) -> datetime:
        """Return the current timestamp value of config data. If timestamp value
        does not exist. this property will return timestamp of initialize.

        :rtype: datetime
        """
        if self.changed > 0:
            return self.updt
        elif dt := self.data().get(UPDATE_KEY):
            return datetime.strptime(dt, DATE_FMT)
        return self.updt

    def version(self, force_next: bool = False) -> VerPackage:
        """Generate version value from the get method. If version value does
        not exist from configuration data, this property will return the
        default, `v0.0.1`. If the initialization process tracking some change
        from configuration data between metadata and the latest data in the
        stage, the _next will be generated.

        :param force_next: A flag to force path version to next value.
        :type force_next: bool (Default=False)

        :rtype: VerPackage
        """
        version = VerPackage.parse(self.data().get(VERSION_KEY, "v0.0.1"))
        if not force_next or self.changed == 0:
            return version
        elif self.changed >= 3:
            return version.bump_major()
        elif self.changed == 2:
            return version.bump_minor()
        return version.bump_patch()

    def fmt(self, update: dict[str, Any] | None = None) -> FormatterGroup:
        """Return FormatterGroup object that passing ``self.timestamp`` and
        ``self.version`` values.

        :param update: An update values on the formatter group object.

        :rtype: FormatterGroup
        """
        return self.fmt_type(
            {
                "timestamp": self.timestamp,
                "version": self.version(),
                **(update or {}),
            }
        )

    def compare_data(self, data: dict[str, Any]) -> Literal[0, 1, 2, 99]:
        """Return difference column from dictionary comparison method which use
        the `deepdiff` library.

        :param data: dict : The data dictionary for compare with current
            configuration data.

        :rtype: Literal[0, 1, 2, 99]
        """
        if not data:
            return 99

        rs = DeepDiff(
            self.data(hashing=True),
            data,
            ignore_order=True,
            exclude_paths={f"root[{k!r}]" for k in (UPDATE_KEY, VERSION_KEY)},
        )
        for level, diffs in REGISTER_DIFF_LEVEL.items():
            if any(_ in rs for _ in diffs):
                return level
        return 0

    def __stage_files(
        self,
        stage: str,
        store: Store,
    ) -> dict[int, StageFl]:
        """Return the mapping of StageFl data from target stage area.

        :param stage: A stage value that want to search files.
        :param store: A store object that passing path with stage path.

        :rtype: dict[int, StageFl]
        """
        rs: dict[int, StageFl] = {}
        for index, file in enumerate((_f.name for _f in store.ls()), start=1):
            try:
                rs[index]: StageFl = {
                    "parse": self.fmt_type.parse(
                        value=file,
                        fmt=rf"{self.params.get_stage(stage).format}\.json",
                    ),
                    "file": file,
                }
            except FormatterArgumentError:
                continue
        return rs

    def get(
        self,
        stage: str | None = None,
        *,
        order: int | None = 1,
        reverse: bool = False,
    ) -> dict[str, Any]:
        """Get the context data from the specific stage value (use 'base' if the
        stage do not pass on this method).

        :param stage: A stage value that want to get context data.
        :param order:
        :param reverse: A reverse flag that use to get stage file.
        """
        if (stage is None) or (stage == REGISTER_BASE_STAGE_DEFAULT):
            return Store(path=(self.params.paths.conf / self.domain)).get(
                name=self.name, order=order
            )

        store = Store(
            path=self.params.paths.data / stage,
            compress=self.params.get_stage(stage).rule.compress,
        )

        if rs := self.__stage_files(stage, store):
            max_data: list = sorted(
                rs.items(),
                key=lambda x: (x[1]["parse"],),
                reverse=reverse,
            )
            return store.load(path=(store.path / max_data[-order][1]["file"]))
        return {}

    def move(
        self,
        stage: str,
        *,
        force: bool = False,
        retention: bool = True,
    ) -> Self:
        """Move the config data file to the target stage.

        :param stage:
        :param force:
        :param retention:

        :rtype: Self
        """
        store: Store = Store(
            path=self.params.paths.data / stage,
            compress=self.params.get_stage(stage).rule.compress,
        )
        if (
            self.compare_data(
                hash.hash_all(
                    self.get(stage=stage), exclude=(UPDATE_KEY, VERSION_KEY)
                )
            )
            > 0
            or force
        ):
            _filename: str = self.fmt().format(
                f"{self.params.get_stage(name=stage).format}.json",
            )
            if (store.path / _filename).exists():
                logger.warning(
                    f"File {_filename!r} already exists in {stage!r} stage."
                )
            store.save(
                path=(store.path / _filename),
                data=merge.merge_dict(
                    self.data(),
                    {
                        UPDATE_KEY: f"{self.timestamp:{DATE_FMT}}",
                        VERSION_KEY: f"v{str(self.version())}",
                    },
                ),
            )
            # NOTE: Retention process after move data to the stage successful
            if retention:
                self.purge(stage=stage)
        else:
            logger.warning(
                f"Config {self.name!r} cannot move {self.stage!r} -> "
                f"{stage!r} cause the data does not has any change or "
                f"force moving flag does not set."
            )
        return self.switch(stage=stage)

    def switch(self, stage: str) -> Self:
        """Switch instance from old stage to new stage with input argument.

        :param stage: A stage name that want to switch.
        """
        return self.__class__(self.fullname, stage=stage, params=self.params)

    def purge(self, stage: str | None = None) -> None:
        """Purge configuration files that match with any rules in the stage
        setting.
        """
        _stage: str = stage or self.stage
        if not (_rules := self.params.get_stage(_stage).rule):
            return
        store: Store = Store(
            path=self.params.paths.data / stage,
            compress=_rules.compress,
        )
        rs: dict[int, StageFl] = self.__stage_files(_stage, store)

        upper_bound: FormatterGroup | None = None
        if _rtt_ts := _rules.timestamp:
            max_file: FormatterGroup = max(
                rs.items(),
                key=lambda x: (x[1]["parse"],),
            )[1]["parse"]

            upper_bound = max_file.adjust(
                {"timestamp": relativedelta(**_rtt_ts)}
            )

        if upper_bound is not None:
            for _, data in filter(
                lambda x: x[1]["parse"] < upper_bound,
                rs.items(),
            ):
                _file: str = data["file"]
                rm(store.path / _file)

    def deploy(self, stop: str | None = None) -> Self:
        """Deploy the config data from the current stage to the final stage or
        specific an input stop stage.

        :param stop: A stage name for stop when move store from base stage
            to final stage.
        :type stop: str

        :raise RegisterArgumentError: If an input stop value does not exists on
            the stages configuration.

        :rtype: Self
        """
        _base: Self = self
        _stop: str = stop or self.params.stage_final
        if _stop not in self.params.stages:
            raise RegisterArgumentError(
                "The `stop` argument should exists in the stages data on the "
                "Params argument."
            )

        for stage in self.params.stages:
            _base: Register = _base.move(stage)
            if stage == _stop:
                break
        return _base

    def remove(self, stage: str | None = None) -> None:
        """Remove all config files from an input stage store area.

        :param stage: a stage value that want to remove (Use current stage if it
            does not pass to this method).
        :type stage: str | None

        :raise RegisterArgumentError: If current stage be the base stage.
            Because it do not do anything on origin config files.

        :rtype: NoReturn
        """
        stage: str = stage or self.stage

        if stage == REGISTER_BASE_STAGE_DEFAULT:
            raise RegisterArgumentError(
                "The remove method can not process with the 'base' stage."
            )

        store: Store = Store(path=self.params.paths.data / stage)
        for stage_file in self.__stage_files(stage, store).values():
            rm(store.path / stage_file["file"])


class ArchiveRegister(Register):
    """Cycle Register object that implement archiving management on the Register
    object such as ``self.purge``, and ``self.remove`` methods.
    """

    archiving: ClassVar[str] = ".archive"

    def purge(self, stage: str | None = None) -> None:
        """Purge configuration files that match with any rules in the stage
        setting and move it to archiving area.

        :param stage: a stage value that want to purge.
        :type stage: str | None
        """
        _stage: str = stage or self.stage
        if not (_rules := self.params.get_stage(_stage).rule):
            return
        store: Store = Store(
            path=self.params.paths.data / stage,
            compress=_rules.compress,
        )
        rs: dict[int, StageFl] = self.__stage_files(_stage, store)

        upper_bound: FormatterGroup | None = None
        if _rtt_ts := _rules.timestamp:
            max_file: FormatterGroup = max(
                rs.items(),
                key=lambda x: (x[1]["parse"],),
            )[1]["parse"]
            upper_bound = max_file.adjust(
                {"timestamp": relativedelta(**_rtt_ts)}
            )

        if upper_bound is not None:
            for _, data in filter(
                lambda x: x[1]["parse"] < upper_bound,
                rs.items(),
            ):
                _file: str = data["file"]
                # NOTE: Archive step
                _ac_path: str = (
                    f"{stage.lower()}_{self.updt:{DATE_LOG_FMT}}_{_file}"
                )
                store.move(
                    _file,
                    dest=self.params.paths.data / self.archiving / _ac_path,
                )
                rm(store.path / _file)

    def remove(self, stage: str | None = None) -> None:
        """Remove all config files from an input stage store area and move it to
        archiving area.

        :param stage: a stage value that want to remove (Use current stage if it
            does not pass to this method).
        :type stage: str | None

        :raise RegisterArgumentError: If current stage be the base stage.
            Because it do not do anything on origin config files.

        :rtype: NoReturn
        """
        _stage: str = stage or self.stage

        if _stage == REGISTER_BASE_STAGE_DEFAULT:
            raise RegisterArgumentError(
                "The remove method can not process with the 'base' stage."
            )

        store: Store = Store(path=self.params.paths.data / _stage)

        for stage_file in self.__stage_files(_stage, store).values():
            file: str = stage_file["file"]
            store.move(
                file,
                dest=(
                    self.params.paths.data
                    / self.archiving
                    / f"{_stage.lower()}_{self.updt:{DATE_LOG_FMT}}_{file}"
                ),
            )
            rm(store.path / file)
