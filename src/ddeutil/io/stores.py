# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
"""Store objects that use to keep context configuration data with different
versions. This module will provide standard and abstraction objects for your
customize usage.

    *   StoreFl     : Store with open file object like json, yaml etc.

    Store will keep data with 2 stages, that mean data have data layer and stage
layer.
"""
from __future__ import annotations

import abc
import inspect
import logging
import shutil
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any, Union

from .config import VERSION_DEFAULT
from .files import (
    Fl,
    JsonFl,
    PathSearch,
    YamlEnvFl,
    rm,
)

TupleStr = tuple[str, ...]
AnyData = Union[str, int, float, bool, None]
DictData = dict[str, Union[AnyData, dict[str, AnyData], list[AnyData]]]

DEFAULT_OPEN_FILE: type[Fl] = YamlEnvFl
DEFAULT_OPEN_FILE_STG: type[Fl] = JsonFl
DEFAULT_INCLUDED_FMT: TupleStr = ("*.yml", "*.yaml")
DEFAULT_EXCLUDED_FMT: TupleStr = ("*.json", "*.toml")

__all__: TupleStr = (
    "BaseStore",
    "Store",
)


class BaseStore(abc.ABC):
    """Base Store File object for getting data with `.yaml` format (default
    format for a config file) and mapping environment variables to the content
    data.

        This object implement only source file without stage open file.

        Base Store Adapter abstract class for any config sub-class that should
    implement necessary methods for unity usage and dynamic config backend
    changing scenario.

    :param path:
    :param compress:
    :param open_file:
    :param excluded_file_fmt:
    """

    def __init__(
        self,
        path: str | Path,
        *,
        compress: str | None = None,
        open_file: type[Fl] | None = None,
        included_file_fmt: TupleStr | None = None,
        excluded_file_fmt: TupleStr | None = None,
    ) -> None:
        self.path: Path = Path(path) if isinstance(path, str) else path
        self.compress: str | None = compress
        self.open_file: type[Fl] = open_file or DEFAULT_OPEN_FILE
        self.included_fmt: TupleStr = included_file_fmt or DEFAULT_INCLUDED_FMT
        self.excluded_fmt: TupleStr = excluded_file_fmt or DEFAULT_EXCLUDED_FMT

        # NOTE: Create parent dir and skip if it already exist
        if not self.path.exists():
            self.path.mkdir(parents=True)

    def get(self, name: str, *, order: int = 1) -> DictData:
        """Return configuration data from name of the config that already adding
        `alias` key with this input name.

        :param name: A name of config key that want to search in the path.
        :type name: str
        :param order: An order number that want to get from ordered list
            of duplicate data.
        :type order: int (Default=1)

        :rtype: DictData
        :returns: The loaded context data from the open file read method.
        """
        rs: list[dict[Any, Any]]
        if not (
            rs := [
                {"alias": name} | data
                for file in self.ls(excluded=self.excluded_fmt)
                if (
                    data := (
                        self.open_file(path=file, compress=self.compress)
                        .read()
                        .get(name)
                    )
                )
            ]
        ):
            return {}

        try:
            if order > len(rs):
                raise IndexError(
                    "Order argument should be less or equal than len of "
                    "data that exist in the store path."
                )
            return sorted(
                rs,
                key=lambda x: (
                    datetime.fromisoformat(x.get("version", VERSION_DEFAULT)),
                    len(x),
                ),
                reverse=False,
            )[-order]
        except IndexError:
            logging.warning(
                f"Does not get config data {name!r} with passing order: "
                f"-{order}"
            )
            return {}

    def ls(
        self,
        path: str | None = None,
        name: str | None = None,
        *,
        excluded: list[str] | None = None,
    ) -> Iterator[Path]:
        """Return all files that already exist in the store path.

        :param path: A specific root path that want to list.
        :param name: A filename pattern that want to list.
        :param excluded: A list of excluded filenames.
        :rtype: Iterator[Path]
        """
        yield from filter(
            lambda x: x.is_file(),
            (
                PathSearch(
                    root=(path or self.path),
                    exclude=excluded,
                ).pick(filename=(name or "*"))
            ),
        )

    def move(self, path: Path, dest: Path) -> None:
        """Copy filename inside this config path to the destination path.

        :param path: A child path that exists in this store path.
        :param dest: A destination path.
        """
        if not dest.parent.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.path / path, dest)

    @abc.abstractmethod
    def load(self, name: str) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError()

    @abc.abstractmethod
    def save(
        self, name: str, data: dict, *, merge: bool = False
    ) -> None:  # pragma: no cover
        raise NotImplementedError()

    @abc.abstractmethod
    def remove(self, name: str, data_name: str) -> None:  # pragma: no cover
        raise NotImplementedError()

    @abc.abstractmethod
    def create(self, name: str, **kwargs) -> None:  # pragma: no cover
        raise NotImplementedError()


class Store(BaseStore):
    """Store File Loading Object for get data from configuration and stage.

    :param path: A path of files to action.
    :param compress: A compress type of action file.
    :param open_file:
    :param included_file_fmt:
    :param excluded_file_fmt:
    :param open_file_stg:
    """

    def __init__(
        self,
        path: str | Path,
        *,
        compress: str | None = None,
        included_file_fmt: TupleStr | None = None,
        excluded_file_fmt: TupleStr | None = None,
        open_file: type[Fl] | None = None,
        open_file_stg: type[Fl] | None = None,
    ) -> None:
        """Main initialize of config file loading object."""
        super().__init__(
            path,
            compress=compress,
            open_file=open_file,
            included_file_fmt=included_file_fmt,
            excluded_file_fmt=excluded_file_fmt,
        )
        self.open_file_stg: type[Fl] = open_file_stg or DEFAULT_OPEN_FILE_STG

    def load(
        self,
        path: str | Path,
        *,
        default: Any = None,
    ) -> Union[dict[Any, Any], list[Any]]:
        """Return content data from file with filename, default empty dict."""
        try:
            return self.open_file_stg(
                path=path,
                compress=self.compress,
            ).read()
        except FileNotFoundError:
            return default if (default is not None) else {}

    def save(
        self,
        path: str | Path,
        data: Union[dict[Any, Any], list[Any]],
        *,
        merge: bool = False,
    ) -> None:
        """Write content data to file with filename. If merge is true, it will
        load the current data from saving file and merge the incoming data
        together before re-write the file.
        """
        if not merge:
            self.open_file_stg(path, compress=self.compress).write(data)
            logging.debug(f"Start writing data to {path}")
            return
        elif merge and (
            "mode"
            in inspect.getfullargspec(self.open_file_stg.write).annotations
        ):
            self.open_file_stg(path, compress=self.compress).write(
                **{"data": data, "mode": "a"}
            )
            return

        all_data: Union[dict, list] = self.load(path=path)
        try:
            if isinstance(all_data, list):
                _merge_data: Union[dict, list] = all_data
                (
                    _merge_data.append(data)
                    if isinstance(data, dict)
                    else _merge_data.extend(data)
                )
            else:
                _merge_data: dict = all_data | data

            # NOTE: Writing data to the stage layer
            self.open_file_stg(path, compress=self.compress).write(_merge_data)
        except TypeError as err:
            # NOTE: Remove the previous saving file path for rollback.
            rm(path=path)
            if all_data:
                self.open_file_stg(path, compress=self.compress).write(
                    all_data,
                )
            raise err

    def remove(self, path: str, name: str) -> None:
        """Remove data by name insided the staging file with filename.

        :param path:
        :param name:
        """
        if all_data := self.load(path=path):
            # NOTE: Remove data with the input name key.
            all_data.pop(name, None)
            (self.open_file_stg(path, compress=self.compress).write(all_data))

    def create(self, path: Path, *, initial_data: Any = None) -> None:
        """Create file with an input filename to the store path. This method
        allow to create with initial data.

        :param path:
        :param initial_data:
        """
        if not path.exists():
            self.save(
                path=path,
                data=(initial_data or {}),
                merge=False,
            )
