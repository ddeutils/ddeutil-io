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
import pathlib
import shutil
import sqlite3
import sys
from datetime import datetime
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    NoReturn,
    Optional,
    Type,
    Union,
)

from ddeutil.core import merge_dict, str2args
from ddeutil.core.base import (
    import_string,
)

from .base import (
    CSVPipeDim,
    Json,
    OpenFile,
    Pickle,
    YamlEnv,
)
from .base.pathutils import PathSearch, remove_file
from .base.settings import SettingRegex
from .exceptions import ConfigArgumentError

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
logger = logging.getLogger(__name__)


FILE_EXTENSION: Dict[str, Type[OpenFile]] = {
    "json": Json,
    "yaml": YamlEnv,
    "csv": CSVPipeDim,
    "pickle": Pickle,
}


def map_secret(value: Any) -> Union[Union[dict, str], Any]:
    """Map the secret value to configuration data."""
    if isinstance(value, dict):
        return {k: map_secret(value[k]) for k in value}
    elif isinstance(value, (list, tuple)):
        return type(value)([map_secret(i) for i in value])
    elif not isinstance(value, str):
        return value
    for search in SettingRegex.RE_SECRETS.finditer(value):
        searches: dict = search.groupdict()
        if "." in (br := searches["braced"]):
            raise ConfigArgumentError(
                "secrets",
                f", value {br!r},  should not contain dot ('.') in get value.",
            )
        # TODO: Implement this secrets data
        secrets = {}
        value: str = value.replace(
            searches["search"],
            secrets.get(br.strip(), searches["braced_default"]),
        )
    return value


def map_function(value: Any) -> Union[Union[dict, str], Any]:
    """Map the function result to configuration data."""
    if isinstance(value, dict):
        return {k: map_secret(value[k]) for k in value}
    elif isinstance(value, (list, tuple)):
        return type(value)([map_secret(i) for i in value])
    elif not isinstance(value, str):
        return value
    for search in SettingRegex.RE_FUNCTION.finditer(value):
        searches: dict = search.groupdict()
        if not callable(_fn := import_string(searches["function"])):
            raise ConfigArgumentError(
                "@function",
                f'from function {searches["function"]!r} is not callable.',
            )
        args, kwargs = str2args(searches["arguments"])
        value: str = value.replace(searches["search"], _fn(*args, **kwargs))
    return value


def map_func_to_str(value: Any, fn: Callable[[str], str]) -> Any:
    """Map any function from input argument to configuration data."""
    if isinstance(value, dict):
        return {k: map_func_to_str(value[k], fn) for k in value}
    elif isinstance(value, (list, tuple)):
        return type(value)([map_func_to_str(i, fn) for i in value])
    elif not isinstance(value, str):
        return value
    return fn(value)


class BaseConfFile:
    """Base Config File object for getting data with `.yaml` format and mapping
    environment variables to the content data.
    """

    CONF_OPEN_FIL: Type[OpenFile] = YamlEnv

    CONF_FMT_EXC: List[str] = [".json", ".toml"]

    def __init__(
        self,
        path: Union[str, pathlib.Path],
        *,
        compress: Optional[str] = None,
        auto_create: bool = True,
    ):
        self.path: pathlib.Path = (
            pathlib.Path(path) if isinstance(path, str) else path
        )
        self.compress = compress
        if not os.path.exists(self.path):
            if not auto_create:
                raise FileNotFoundError(f"Path {path} does not exists.")
            os.makedirs(self.path)

    def load(
        self,
        name: str,
        *,
        order: int = 1,
    ) -> Dict[Any, Any]:
        """Return configuration data from name of the config.

        :param name: A name of config key that want to search in the path.
        :type name: str
        :param order: An order number that want to get from ordered list
            of duplicate data.
        :type order: int (Default 1)
        """
        rs: List[Dict[Any, Any]]
        if rs := [
            merge_dict({"alias": name}, data)
            for file in self.files(excluded=self.CONF_FMT_EXC)
            if (
                data := self.CONF_OPEN_FIL(path=file, compress=self.compress)
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
                    f"Does not load config data with order: -{order} "
                    f"and name: {name!r}."
                )
        return {}

    def files(
        self,
        path: Optional[str] = None,
        name: Optional[str] = None,
        *,
        excluded: Optional[list] = None,
    ) -> Iterator:
        """Return all files that exists in the loading path."""
        return filter(
            lambda x: os.path.isfile(x),
            PathSearch.from_dict(
                {
                    "root": (path or str(self.path.resolve())),
                    "exclude_name": excluded,
                }
            ).pick(filename=(name or "*")),
        )

    def move(
        self,
        path: Union[str, pathlib.Path],
        destination: Union[str, pathlib.Path],
        *,
        auto_create: bool = True,
    ):
        """Copy filename to destination path."""
        if auto_create:
            os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copy(self.path / path, destination)


class ConfAdapter(abc.ABC):
    """Config Adapter abstract object."""

    @abc.abstractmethod
    def load_stage(self, name: str) -> dict:
        raise NotImplementedError

    @abc.abstractmethod
    def save_stage(
        self,
        name: str,
        data: dict,
        merge: bool = False,
    ) -> NoReturn:
        raise NotImplementedError

    @abc.abstractmethod
    def remove_stage(
        self,
        name: str,
        data_name: str,
    ) -> NoReturn:
        raise NotImplementedError

    @abc.abstractmethod
    def create(self, name: str, **kwargs) -> NoReturn:
        raise NotImplementedError


class ConfFile(BaseConfFile, ConfAdapter):
    """Config File Loading Object for get data from configuration and stage."""

    CONF_OPEN_FIL_STG: Type[OpenFile] = Json

    def __init__(
        self,
        path: Union[str, pathlib.Path],
        *,
        compress: Optional[str] = None,
        auto_create: bool = True,
    ):
        """Main initialize of config file loading object.

        :param path: A path of files to action.
        :type path: Union[str, pathlib.Path]
        :param compress: Optional[str] : A compress type of action file.
        """
        super().__init__(
            path,
            compress=compress,
            auto_create=auto_create,
        )

    def load_stage(
        self,
        path: Union[str, pathlib.Path],
        default: Optional[Any] = None,
    ) -> Union[Dict[Any, Any], List[Any]]:
        """Return content data from file with filename, default empty dict."""
        try:
            return self.CONF_OPEN_FIL_STG(
                path=path,
                compress=self.compress,
            ).read()
        except FileNotFoundError:
            return default if (default is not None) else {}

    def save_stage(
        self,
        path: Union[str, pathlib.Path],
        data: Union[Dict[Any, Any], List[Any]],
        *,
        merge: bool = False,
    ) -> NoReturn:
        """Write content data to file with filename. If merge is true, it will
        load current data from file and merge the data content together
        before write.
        """
        if not merge:
            self.CONF_OPEN_FIL_STG(path, compress=self.compress).write(data)
            return
        elif merge and (
            "mode"
            in inspect.getfullargspec(self.CONF_OPEN_FIL_STG.write).annotations
        ):
            self.CONF_OPEN_FIL_STG(path, compress=self.compress).write(
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
                _merge_data: Union[dict, list] = merge_dict(all_data, data)
            self.CONF_OPEN_FIL_STG(path, compress=self.compress).write(
                _merge_data
            )
        except TypeError as err:
            remove_file(path=path)
            if all_data:
                self.CONF_OPEN_FIL_STG(path, compress=self.compress).write(
                    all_data,
                )
            raise err

    def remove_stage(self, path: str, name: str) -> NoReturn:
        """Remove data by name from file with filename."""
        if all_data := self.load_stage(path=path):
            all_data.pop(name, None)
            self.CONF_OPEN_FIL_STG(path, compress=self.compress).write(
                all_data,
            )

    def create(
        self,
        path: Union[str, pathlib.Path],
        *,
        initial_data: Optional[Any] = None,
    ) -> NoReturn:
        """Create filename in path."""
        if not os.path.exists(path):
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
        path: Union[str, pathlib.Path],
        *,
        auto_create: bool = True,
    ):
        self.path: pathlib.Path = (
            pathlib.Path(path) if isinstance(path, str) else path
        )
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
            logger.error(err)
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


class ConfSQLite(BaseConfSQLite, ConfAdapter):
    def load_stage(
        self,
        table: str,
        default: Optional[Dict[Any, Any]] = None,
    ) -> Dict[Any, Any]:
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
    ) -> NoReturn:
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
    ) -> NoReturn:
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
    ) -> NoReturn:
        """Create table in database."""
        if not schemas:
            raise ConfigArgumentError(
                "schemas",
                (
                    f"in `create` method of {self.__class__.__name__} "
                    f"should have value."
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
    ) -> Dict[str, Union[str, int, float]]:
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
    "map_secret",
    "map_function",
    "map_func_to_str",
    "ConfAdapter",
    "ConfFile",
    "ConfSQLite",
)
