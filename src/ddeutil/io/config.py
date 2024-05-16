# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

import abc
import contextlib
import inspect
import json
import logging
import os
import shutil
import sqlite3
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import (
    Any,
    Optional,
    Union,
)

from .__base import (
    Fl,
    JsonFl,
    PathSearch,
    YamlEnvFl,
    rm,
)
from .exceptions import ConfigArgumentError


class ConfABC(abc.ABC):
    """Config Adapter abstract object."""

    @abc.abstractmethod
    def load_stage(self, name: str) -> dict:
        raise NotImplementedError

    @abc.abstractmethod
    def save_stage(self, name: str, data: dict, merge: bool = False) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def remove_stage(self, name: str, data_name: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def create(self, name: str, **kwargs) -> None:
        raise NotImplementedError


class BaseConfFl:
    """Base Config File object for getting data with `.yaml` format and mapping
    environment variables to the content data.
    """

    def __init__(
        self,
        path: Union[str, Path],
        *,
        compress: Optional[str] = None,
        open_file: Optional[type[Fl]] = None,
        excluded_fmt: Optional[tuple[str]] = None,
    ):
        self.path: Path = Path(path) if isinstance(path, str) else path
        self.compress: Optional[str] = compress
        self.open_file: type[Fl] = open_file or YamlEnvFl
        self.excluded_fmt: tuple[str] = excluded_fmt or (".json", ".toml")
        if not self.path.exists():
            self.path.mkdir(parents=True)

    def load(
        self,
        name: str,
        *,
        order: int = 1,
    ) -> dict[str, Any]:
        """Return configuration data from name of the config.

        :param name: A name of config key that want to search in the path.
        :type name: str
        :param order: An order number that want to get from ordered list
            of duplicate data.
        :type order: int (Default 1)
        """
        rs: list[dict[Any, Any]]
        if rs := [
            {"alias": name} | data
            for file in self.files(excluded=self.excluded_fmt)
            if (
                data := self.open_file(path=file, compress=self.compress)
                .read()
                .get(name)
            )
        ]:
            try:
                if order > len(rs):
                    raise IndexError
                return sorted(
                    rs,
                    key=lambda x: (
                        datetime.fromisoformat(x.get("version", "1990-01-01")),
                        len(x),
                    ),
                    reverse=False,
                )[-order]
            except IndexError:
                logging.warning(
                    f"Does not load config {name!r} with order: -{order}"
                )
        return {}

    def files(
        self,
        path: Optional[str] = None,
        name: Optional[str] = None,
        *,
        excluded: Optional[list] = None,
    ) -> Iterator[Path]:
        """Return all files that exists in the loading path."""
        yield from filter(
            lambda x: x.is_file(),
            (
                PathSearch(root=(path or self.path), exclude=excluded).pick(
                    filename=(name or "*")
                )
            ),
        )

    def move(
        self,
        path: Path,
        destination: Path,
        *,
        auto_create: bool = True,
    ) -> None:
        """Copy filename to destination path."""
        if auto_create:
            destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.path / path, destination)


class ConfFl(BaseConfFl, ConfABC):
    """Config File Loading Object for get data from configuration and stage."""

    def __init__(
        self,
        path: Union[str, Path],
        *,
        compress: Optional[str] = None,
        open_file: Optional[type[Fl]] = None,
        excluded_fmt: Optional[list[str]] = None,
        open_file_stg: Optional[type[Fl]] = None,
    ):
        """Main initialize of config file loading object.

        :param path: A path of files to action.
        :type path: Union[str, Path]
        :param compress: Optional[str] : A compress type of action file.
        """
        super().__init__(
            path,
            compress=compress,
            open_file=open_file,
            excluded_fmt=excluded_fmt,
        )
        self.open_file_stg: type[Fl] = open_file_stg or JsonFl

    def load_stage(
        self,
        path: Union[str, Path],
        *,
        default: Optional[Any] = None,
    ) -> Union[dict[Any, Any], list[Any]]:
        """Return content data from file with filename, default empty dict."""
        try:
            return self.open_file_stg(
                path=path,
                compress=self.compress,
            ).read()
        except FileNotFoundError:
            return default if (default is not None) else {}

    def save_stage(
        self,
        path: Union[str, Path],
        data: Union[dict[Any, Any], list[Any]],
        *,
        merge: bool = False,
    ) -> None:
        """Write content data to file with filename. If merge is true, it will
        load current data from file and merge the data content together
        before write.
        """
        if not merge:
            self.open_file_stg(path, compress=self.compress).write(data)
            print(f"Start writing data to {path}")
            return
        elif merge and (
            "mode"
            in inspect.getfullargspec(self.open_file_stg.write).annotations
        ):
            self.open_file_stg(path, compress=self.compress).write(
                **{
                    "data": data,
                    "mode": "a",
                }
            )
            return

        all_data: Union[dict, list] = self.load_stage(path=path)
        try:
            if isinstance(all_data, list):
                _merge_data: Union[dict, list] = all_data
                if isinstance(data, dict):
                    _merge_data.append(data)
                else:
                    _merge_data.extend(data)
            else:
                _merge_data: dict = all_data | data
            self.open_file_stg(path, compress=self.compress).write(_merge_data)
        except TypeError as err:
            rm(path=path)
            if all_data:
                self.open_file_stg(path, compress=self.compress).write(
                    all_data,
                )
            raise err

    def remove_stage(self, path: str, name: str) -> None:
        """Remove data by name insided the staging file with filename."""
        if all_data := self.load_stage(path=path):
            all_data.pop(name, None)
            self.open_file_stg(path, compress=self.compress).write(
                all_data,
            )

    def create(
        self,
        path: Path,
        *,
        initial_data: Optional[Any] = None,
    ) -> None:
        """Create filename in path."""
        if not path.exists():
            self.save_stage(
                path=path,
                data=({} if initial_data is None else initial_data),
                merge=False,
            )


class BaseConfSQLite:
    """Base Config SQLite object for getting data with SQLite database from
    file storage."""

    def __init__(
        self,
        path: Union[str, Path],
        *,
        auto_create: bool = True,
    ):
        self.path: Path = Path(path) if isinstance(path, str) else path
        if not os.path.exists(self.path):
            if not auto_create:
                raise FileNotFoundError(f"Path {path} does not exists.")
            os.makedirs(self.path, exist_ok=True)

    @contextlib.contextmanager
    def connect(self, database: str):
        """Return SQLite Connection context."""
        _conn = sqlite3.connect(self.path / database, timeout=3)
        _conn.row_factory = self.dict_factory
        try:
            yield _conn
        except sqlite3.Error as err:
            logging.error(err)
            raise ConfigArgumentError(
                "syntax", f"SQLite syntax error {err}"
            ) from err
        _conn.commit()
        _conn.close()

    @staticmethod
    def dict_factory(cursor, row):
        """Result of dictionary factory.

        :note:
            Another logic of dict factory.

            - dict(
                [
                    (col[0], row[idx])
                    for idx, col in enumerate(cursor.description)
                ]
            )

            - dict(zip([col[0] for col in cursor.description], row))
        """
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


class ConfSQLite(BaseConfSQLite, ConfABC):
    def load_stage(
        self,
        table: str,
        default: Optional[dict[Any, Any]] = None,
    ) -> dict[Any, Any]:
        """Return content data from database with table name, default empty
        dict."""
        _db, _table = table.rsplit("/", maxsplit=1)
        with self.connect(_db) as conn:
            cur = conn.cursor()
            cur.execute(f"select * from {_table};")
            if result := cur.fetchall():
                return {_["name"]: self.convert_type(_) for _ in result}
            return default if (default is not None) else {}

    def save_stage(
        self,
        table: str,
        data: dict,
        merge: bool = False,
    ) -> None:
        """Write content data to database with table name. If merge is true, it
        will update or insert the data content.
        """
        _db, _table = table.rsplit("/", maxsplit=1)
        _data: dict = self.prepare_values(data.get(list(data.keys())[0]))
        with self.connect(_db) as conn:
            cur = conn.cursor()
            doing: str = "nothing"
            if merge:
                _doing_list = [
                    f"{_} = excluded.{_}" for _ in _data if _ != "name"
                ]
                doing: str = f'update set {", ".join(_doing_list)}'
            query: str = (
                f'insert into {_table} ({", ".join(_data.keys())}) values '
                f'({":" + ", :".join(_data.keys())}) '
                f"on conflict ( name ) do {doing};"
            )
            cur.execute(query, _data)

    def remove_stage(
        self,
        table: str,
        data_name: str,
    ) -> None:
        """Remove data by name from table in database with table name."""
        _db, _table = table.rsplit("/", maxsplit=1)
        with self.connect(_db) as conn:
            cur = conn.cursor()
            query: str = f"delete from {_table} where name = '{data_name}';"
            cur.execute(query)

    def create(
        self,
        table: str,
        schemas: Optional[dict] = None,
    ) -> None:
        """Create table in database."""
        if not schemas:
            raise ConfigArgumentError(
                "schemas",
                (
                    f"in `create` method of {self.__class__.__name__} "
                    f"was required"
                ),
            )
        _schemas: str = ", ".join([f"{k} {v}" for k, v in schemas.items()])
        _db, _table = table.rsplit("/", maxsplit=1)
        with self.connect(_db) as conn:
            cur = conn.cursor()
            cur.execute(f"create table if not exists {_table} ({_schemas})")

    @staticmethod
    def prepare_values(
        values: dict,
    ) -> dict[str, Union[str, int, float]]:
        """Return prepare value with dictionary type to string
        to source system.
        """
        results: dict = values.copy()
        for _ in values:
            if isinstance(values[_], dict):
                results[_] = json.dumps(values[_])
        return results

    @staticmethod
    def convert_type(
        data: dict,
        key: Optional[str] = None,
    ) -> dict:
        """Return converted value from string to dictionary
        from source system.
        """
        _key: str = key or "data"
        _results: dict = data.copy()
        _results[_key] = json.loads(data[_key])
        return _results


__all__ = (
    "ConfABC",
    "ConfFl",
    "ConfSQLite",
    "Fl",
)
