# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
"""Store objects that use to keep context configuration data with different
versions. This module will provide standard and abstraction objects for your
customize usage.

    *   Store           : Store with Yaml open file and use stage with Json.
    *   StoreJsonToCsv  : Store with Json open file and use stage with Yaml.

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
from typing import Any, ClassVar, Optional, Union

from .__type import AnyData, TupleStr
from .config import VERSION_DEFAULT
from .files import (
    CsvPipeFl,
    Fl,
    JsonEnvFl,
    JsonFl,
    JsonLineFl,
    YamlEnvFl,
)
from .paths import PathSearch
from .utils import rm

__all__: TupleStr = (
    "BaseStore",
    "Store",
    "StoreJsonToCsv",
    "StoreToJsonLine",
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
    """

    open_file: ClassVar[type[Fl]] = YamlEnvFl
    included_file_fmt: ClassVar[TupleStr] = ("*.yml", "*.yaml")
    excluded_file_fmt: ClassVar[TupleStr] = ("*.json", "*.toml", "*.csv")

    def __init__(
        self,
        path: Union[str, Path],
        *,
        compress: Optional[str] = None,
    ) -> None:
        self.path: Path = Path(path) if isinstance(path, str) else path
        self.compress: Optional[str] = compress

        # NOTE: Create parent dir and skip if it already exists
        if not self.path.exists():
            self.path.mkdir(parents=True)

    def get(self, name: str, *, order: int = 1) -> AnyData:
        """Return configuration data from name of the config that already adding
        `alias` key with this input name.

        :param name: A name of config key that want to search in the path.
        :type name: str
        :param order: An order number that want to get from ordered list
            of duplicate data.
        :type order: int (Default=1)

        :rtype: AnyData
        :returns: The loaded context data from the open file read method.
        """
        rs: list[dict[Any, Any]]
        if not (
            rs := [
                {"alias": name} | data
                for file in self.ls(excluded=self.excluded_file_fmt)
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
        path: Optional[str] = None,
        name: Optional[str] = None,
        *,
        excluded: Optional[Union[list[str], tuple[str, ...]]] = None,
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

    def move(self, path: Union[str, Path], dest: Path) -> None:
        """Copy filename inside this config path to the destination path.

        :param path: A child path that exists in this store path.
        :param dest: A destination path.
        """
        if not dest.parent.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.path / path, dest)

    @abc.abstractmethod
    def load(self, name: str) -> dict[str, Any]:  # pragma: no cov
        raise NotImplementedError()

    @abc.abstractmethod
    def save(
        self, name: str, data: dict, *, merge: bool = False
    ) -> None:  # pragma: no cov
        raise NotImplementedError()

    @abc.abstractmethod
    def delete(self, path: str, name: str) -> None:  # pragma: no cov
        raise NotImplementedError()

    @abc.abstractmethod
    def create(self, name: str, **kwargs) -> None:  # pragma: no cov
        raise NotImplementedError()


class Store(BaseStore):
    """Store File Loading Object for get data from configuration and stage.

    :param path: A path of files to action.
    :param compress: A compress type of action file.
    """

    open_file: ClassVar[type[Fl]] = YamlEnvFl
    open_file_stg: ClassVar[type[Fl]] = JsonFl

    def __init__(
        self,
        path: Union[str, Path],
        *,
        compress: Optional[str] = None,
    ) -> None:
        """Main initialize of config file loading object."""
        super().__init__(path, compress=compress)

    def load(
        self, path: Union[str, Path], *, default: AnyData = None
    ) -> AnyData:
        """Return content data from file with filename, default empty dict.

        :rtype: AnyData
        """
        try:
            return self.open_file_stg(path=path, compress=self.compress).read()
        except FileNotFoundError:
            return default if (default is not None) else {}

    def save(
        self,
        path: Union[str, Path],
        data: AnyData,
        *,
        merge: bool = False,
    ) -> None:
        """Write content data to file with filename. If merge is true, it will
        load the current data from saving file and merge the incoming data
        together before re-write the file.

        :param path:
        :param data:
        :param merge:
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

        all_data: AnyData = self.load(path=path)
        try:
            if isinstance(all_data, list):
                rs: list[AnyData] = all_data
                (rs.append(data) if isinstance(data, dict) else rs.extend(data))
            else:
                rs: dict = all_data | data

            # NOTE: Writing data to the stage layer
            self.open_file_stg(path, compress=self.compress).write(rs)
        except TypeError:
            # NOTE: Remove the previous saving file path for rollback.
            rm(path=path, force_raise=False)
            if all_data:
                self.open_file_stg(path, compress=self.compress).write(
                    all_data,
                )
            raise

    def delete(self, path: Union[str, Path], name: str) -> None:
        """Remove data by name insided the staging file with filename.

        :param path:
        :param name:
        """
        # NOTE: Remove data with the input name key if it exists.
        if all_data := self.load(path=path):
            all_data.pop(name, None)
            (self.open_file_stg(path, compress=self.compress).write(all_data))

    def create(
        self, path: Union[str, Path], *, initial_data: AnyData = None
    ) -> None:
        """Create file with an input filename to the store path. This method
        allow to create with initial data.

        :param path:
        :param initial_data:
        :type initial_data: AnyData
        :rtype: None
        """
        if not path.exists():
            self.save(
                path=path,
                data=(initial_data or {}),
                merge=False,
            )


class StoreJsonToCsv(Store):
    """Store object that getting the Json context data and save it to stage with
    CSV file format.
    """

    open_file: ClassVar[type[Fl]] = JsonEnvFl
    open_file_stg: ClassVar[type[Fl]] = CsvPipeFl
    included_file_fmt: ClassVar[TupleStr] = ("*.json",)
    excluded_file_fmt: ClassVar[TupleStr] = (
        "*.yml",
        "*.yaml",
        "*.toml",
        "*.csv",
    )


class StoreToJsonLine(Store):
    """Store object that getting the YAML context data and save it to stage with
    Json line file format.
    """

    open_file_stg: ClassVar[type[Fl]] = JsonLineFl
