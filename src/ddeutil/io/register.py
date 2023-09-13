# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

import datetime
import logging
import os
import pathlib
import sys
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    TypedDict,
)

import packaging.version
from dateutil.relativedelta import relativedelta
from ddeutil.core import (
    concat,
    hash_all,
    merge_dict,
    rsplit,
)
from ddeutil.core.dtutils import get_date
from deepdiff import DeepDiff
from fmtutil import (
    ConstantType,
    Datetime,
    FormatterArgumentError,
    FormatterGroup,
    FormatterGroupType,
    Naming,
    Version,
    make_const,
    make_group,
)

from .base.pathutils import remove_file
from .config import ConfFile
from .exceptions import ConfigArgumentError, ConfigNotFound
from .models import Params

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
logger = logging.getLogger(__name__)

PCK_PATH: pathlib.Path = pathlib.Path(__file__).parent / "../../.."
EXC_KEYS: Tuple[str, ...] = (
    "version",
    "updt",
)
DT_FMT: str = "%Y-%m-%d %H:%M:%S"


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

    # @classmethod
    # def reset(
    #         cls,
    #         name: str,
    #         *,
    #         author: Optional[str] = None,
    # ) -> "Register":
    #     """Reset all configuration data files that exists in any stage but
    #     does not do anything in the base stage. This method will use when the
    #     config name of data was changed and does not use the old name. If the
    #     name was changed and that config data does not reset,
    #     the configuration files of this data will exist in any moved stage.
    #
    #     :param name: str : The fullname of configuration.
    #
    #     :param author: Optional[str] : ...
    #     """
    #     _name: str = concat(name.split())
    #     if cls.DOM_PTT in _name:
    #         _, _name = _name.rsplit(cls.DOM_PTT, maxsplit=1)
    #
    #     # Delete all config file from any stage.
    #     for stage in params.stages:
    #         cls(
    #             name,
    #             stage=stage,
    #             config={
    #                 "author": author,
    #                 "auto_update": False,
    #                 "force_exists": True,
    #             },
    #         ).remove()
    #
    #     # Delete data form metadata.
    #     ConfMetadata(
    #         params.engine.path.metadata,
    #         name=_name,
    #         environ=Env(config=params).name,
    #     ).remove()
    #     return cls(name, config={"author": author})

    def __init__(
        self,
        name: str,
        stage: Optional[str] = None,
        *,
        config: Optional[Params] = None,
    ):
        _domain, _name = rsplit(concat(name.split()), ":", maxsplit=1)
        super().__init__(
            name=_name,
            domain=_domain,
        )
        self.config = config

        self.stage = stage or "base"

        # Load latest version of data from data lake or data store of
        # configuration files
        self.__data: Dict[str, Any] = self.pick(stage=self.stage)
        if not self.__data:
            _domain_stm: str = (
                f"with domain {self.domain!r}" if self.domain else ""
            )
            raise ConfigNotFound(
                f"Configuration {self.name!r} {_domain_stm} "
                f"does not found in the {self.stage!r} data lake or data store."
            )

        # TODO: Implement meta object
        self.meta = {}
        # # Generate data for all conditions of the Register object
        # self.updt: dt.datetime = get_date("datetime")
        # self.__meta: ConfLoader = ConfMetadata(
        #     params.engine.path.metadata,
        #     name=self.name,
        #     environ=self.env.name,
        # )
        # self.__log: ConfLoader = ConfLogging(
        #     params.engine.path.logging,
        #     name=self.name,
        #     _logger=logger,
        #     environ=self.env.name,
        # )

        # Compare data from current stage and latest version in metadata.
        self.changed: int = self.compare_data(
            target=self.meta.get(self.stage, {})
        )

        # if params.engine.path.stage_archive:
        #     self._cf_archive: bool = True
        #
        # # Update metadata if the configuration data does not exist, or
        # # it has any changes.
        # if not self.config.auto_update:
        #     self.__log.p_debug("Skip update metadata table/file ...")
        # elif self.changed == 99:
        #     self.__log.p_debug(
        #         f"Configuration data with stage: {self.stage!r} does not "
        #         f"exists in metadata ..."
        #     )
        #     self.__log.p_debug(
        #         "The Process will automate update this data to metadata ..."
        #     )
        #     self.meta_update(
        #         config_data={
        #             self.stage: merge_dict(
        #                 {
        #                     "updt": f"{self.updt:{self.DT_FMT}}",
        #                     "version": f"v{str(self.version())}",
        #                 },
        #                 self.data_hash,
        #             )
        #         }
        #     )
        # elif self.changed > 0:
        #     self.__log.p_debug(
        #         f"Should update metadata because difference level is "
        #         f"{self.changed}"
        #     )
        #     _version_stm: str = f"v{str(self.version((self.stage != 'base')))}"
        #     self.meta_update(
        #         config_data={
        #             self.stage: merge_dict(
        #                 self.data_hash,
        #                 {
        #                     "updt": f"{self.timestamp:{self.DT_FMT}}",
        #                     "version": _version_stm,
        #                 },
        #             )
        #         }
        #     )
        #
        # # Save logging.
        # self.__log.save_logging()

    def __hash__(self):
        return hash(self.fullname + self.stage + f"{self.timestamp:{DT_FMT}}")

    def __str__(self) -> str:
        return f"({self.fullname}, {self.stage})"

    # def __repr__(self) -> str:
    #     _params: list = [f"name={self.fullname!r}"]
    #     if self.stage != "base":
    #         _params.append(f"stage={self.stage!r}")
    #     if self.config.author != "unknown":
    #         _params.append(f"author={self.config.author!r}")
    #     return f"<{self.__class__.__name__}({', '.join(_params)})>"
    #
    # def __eq__(self, other) -> bool:
    #     if isinstance(other, self.__class__):
    #         return (
    #             self.name == other.name
    #             and self.domain == other.domain
    #             and self.stage == other.stage
    #             and self.config.author == other.config.author
    #         )
    #     return False

    def data(self, hashing: bool = False) -> Dict[str, Any]:
        """Return the data with the configuration name."""
        _data = self.__data
        if (self.stage is None) or (self.stage == "base"):
            _data = merge_dict(
                {
                    k: v
                    for k, v in (self.meta.get(self.stage, {}).items())
                    if k in EXC_KEYS
                },
                self.__data,
            )
        return hash_all(_data, exclude=set(EXC_KEYS)) if hashing else _data

    # @property
    # def meta(self) -> RegisterMetaData:
    #     _meta: Dict[str, Any] = self.__meta.load()
    #     if not _meta:
    #         self.__log.p_debug(
    #             (
    #                 f"Metadata does not exists for {self.fullname!r} in stage: "
    #                 f"{self.stage!r}, so the process will return default data."
    #             ),
    #             force=True,
    #         )
    #     _data: dict = _meta.pop("data", {})
    #     return RegisterMetaData.model_validate(
    #         merge_dict(
    #             {
    #                 "name": self.name,
    #                 "shortname": self.shortname,
    #                 "fullname": self.fullname,
    #                 "data": _data,
    #                 "updt": f"{self.updt:{self.DT_FMT}}",
    #                 "rtdt": f"{self.updt:{self.DT_FMT}}",
    #                 "author": self.config.author,
    #             },
    #             _meta,
    #         )
    #     )
    #
    # def meta_update(
    #         self,
    #         data: Optional[dict] = None,
    #         config_data: Optional[dict] = None,
    # ) -> None:
    #     """Update data to metadata table or file with optional new data and new
    #     config data.
    #
    #     :param data: Optional[dict]
    #
    #     :param config_data: Optional[dict]
    #     """
    #     _meta: RegisterMetaData = self.meta
    #     data: dict = merge_dict(
    #         {
    #             "updt": f"{self.updt:{self.DT_FMT}}",
    #             "author": self.config.author,
    #         },
    #         (data or {}),
    #     )
    #     if config_data:
    #         data: dict = merge_dict(
    #             data,
    #             {
    #                 "data": merge_dict(
    #                     _meta.data,
    #                     config_data,
    #                 ),
    #             },
    #         )
    #     return self.__meta.save(
    #         data=merge_dict(
    #             _meta.model_dump(),
    #             data,
    #         ),
    #     )

    @property
    def params(self):
        if self.config is None:
            raise NotImplementedError
        return self.config

    @property
    def timestamp(self) -> datetime.datetime:
        """Return the current timestamp value of config data. If timestamp value
        does not exist. this property will return timestamp of initialize.

        :return: datetime
        """
        if self.changed > 0:
            return self.updt
        elif _dt := self.data().get("updt"):
            return datetime.datetime.strptime(_dt, DT_FMT)
        return self.updt

    def version(self, _next: bool = False) -> packaging.version.Version:
        """Generate version value from the pick method. If version value does
        not exist from configuration data, this property will return the
        default, `v0.0.1`. If the initialization process tracking some change
        from configuration data between metadata and the latest data in the
        stage, the _next will be generated.

        :return: packaging.version.Version
        """
        _vs = packaging.version.parse(self.data().get("version", "v0.0.1"))
        if not _next or _vs == 0:
            return packaging.version.parse(self.data().get("version", "v0.0.1"))
        elif self.changed >= 3:
            return packaging.version.parse(f"v{str(_vs.major + 1)}.0.0")
        elif self.changed == 2:
            return packaging.version.parse(
                f"v{_vs.major}.{str(_vs.minor + 1)}.0"
            )
        return packaging.version.parse(
            f"v{_vs.major}.{_vs.minor}.{str(_vs.micro + 1)}"
        )

    def fmt(self, update: Optional[Dict[str, Any]] = None):
        return self.fmt_group(
            {
                "timestamp": self.timestamp,
                "version": self.version(),
                **(update or {}),
            }
        )

    def compare_data(
        self,
        target: Dict[Any, Any],
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
            exclude_paths={f"root[{key!r}]" for key in EXC_KEYS},
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
    ) -> Dict[int, StageFiles]:
        """Return mapping of StageFiles data."""
        results: Dict[int, StageFiles] = {}
        for index, file in enumerate(
            (_f.rsplit("/", maxsplit=1)[-1] for _f in loading.files()),
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
                path=PCK_PATH / "tests/examples/conf" / self.domain
            ).load(name=self.name, order=order)

        loading = ConfFile(
            path=PCK_PATH / "data/.archive" / stage,
            compress=self.params.get_stage(stage).rules.compress,
        )

        if results := self.__stage_files(stage, loading):
            max_data: List = sorted(
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
            path=PCK_PATH / "data/.archive" / stage,
            compress=self.params.get_stage(stage).rules.compress,
        )
        if (
            self.compare_data(
                hash_all(
                    self.pick(stage=stage),
                    exclude=set(EXC_KEYS),
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
            loading.save_stage(
                path=(loading.path / _filename),
                data=merge_dict(
                    self.data(),
                    {
                        "updt": f"{self.timestamp:{DT_FMT}}",
                        "version": f"v{str(self.version())}",
                    },
                ),
            )
            # TODO: Implement retention
            # Retention process after move data to the stage successful
            # if retention:
            #     self.purge(stage=stage)
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
            path=PCK_PATH / "data/.archive" / stage,
            compress=_rules.compress,
        )
        results: dict = self.__stage_files(_stage, loading)
        max_file: FormatterGroup = max(
            results.items(),
            key=lambda x: (x[1]["parse"],),
        )[1]["parse"]

        if (_rtt_value := _rules.timestamp) > 0:
            _metric: Optional[str] = _rules.timestamp_metric
            max_file.adjust(
                {"timestamp": relativedelta(**{_metric: _rtt_value})}
            )
        # elif _rtt_value := _rules.version:
        #     upper_bound = max_file.adjust(
        #         {'version': _rtt_value}
        #     )

        # if upper_bound:
        #     for _, data in filter(
        #         lambda x: x[1]["parse"] < upper_bound,
        #         results.items(),
        #     ):
        #         _file: str = data["file"]
        #         if self.params.engine.path.is_archived:
        #             _ac_path: str = (
        #                 f"{stage.lower()}_{self.updt:%Y%m%d%H%M%S}_{_file}"
        #             )
        #             loading.move(
        #                 _file,
        #                 join_root_with(
        #                     join_path(env.ARCHIVE_PATH, _ac_path, abs=False)
        #                 ),
        #             )
        #         loading.remove(_file)

    def deploy(self, stop: Optional[str] = None) -> Register:
        """Deploy data that move from base to final stage.

        :param stop: A stage name for stop when move config from base stage
            to final stage.
        :type stop: str
        """
        _base: Register = self
        assert (
            stop in self.params.stages
        ), "a `stop` argument should exists in `parameter.yaml` file."
        for stage in self.params.stages:
            _base: Register = _base.move(stage)
            if stop and (stage == stop):
                break
        return _base

    def remove(self, stage: Optional[str] = None) -> None:
        """Remove config file from the stage storage."""
        _stage: str = stage or self.stage
        assert (
            _stage != "base"
        ), "The remove method should not process on the 'base' stage"
        loading = ConfFile(path=PCK_PATH / "data/.archive" / stage)
        results: dict = self.__stage_files(_stage, loading)

        # Remove all files from the stage.
        for _, data in results.items():
            _file: str = data["file"]
            if self.params.engine.path.is_archived:
                _ac_path: str = (
                    f"{stage.lower()}_{self.updt:%Y%m%d%H%M%S}_{_file}"
                )
                loading.move(_file, PCK_PATH / "data/.archive" / stage)
            remove_file(loading.path / _file)


__all__ = ("Register",)
