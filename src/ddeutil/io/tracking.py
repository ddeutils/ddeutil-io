# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

import dataclasses
import logging
from functools import wraps
from typing import (
    Any,
    Optional,
    TypeVar,
    Union,
)
from urllib.parse import urlparse

from ddeutil.core import merge_dict
from ddeutil.core.dtutils import get_date

from .config import ConfABC, ConfFl, ConfSQLite

ConfLoader = TypeVar("ConfLoader", bound="BaseConfLoader")


class BaseConfLoader:
    """Base Config Loader Object for get data from any config file or
    table with name.
    """

    conf_prefix: str = ""

    conf_file_extension: str = ""

    conf_file_initial: Any = {}

    conf_sqlite_schema: dict = {}

    def __init__(
        self,
        endpoint: Optional[str],
        name: str,
        *,
        environ: Optional[str] = None,
    ):
        """Initialization of base metadata object. The metadata can implement
        with a json file or a table in any database like SQLite.

        :param endpoint: str

        :param name: str

        :param environ: Optional[str]
        """
        _environ: str = f".{_env}" if (_env := (environ or "")) else ""
        # TODO: Case endpoint is None
        url = urlparse(endpoint)
        self._cf_loader_type = url.scheme
        self._cf_loader_endpoint = f"{url.netloc}/{url.path}"
        self._cf_name: str = name

        if self._cf_loader_type == "file":
            # Case: file : the data in file does not have schemas.
            self._cf_filename: str = (
                f"{self.conf_prefix}{_environ}.{self.conf_file_extension}"
            )
            self.loading: ConfABC = ConfFl(path=self._cf_loader_endpoint)
            self.loading.create(
                name=self._cf_filename,
                initial_data=self.conf_file_initial,
            )
        elif self._cf_loader_type == "sqlite":
            # Case: sqlite : the data must use `conf_sqlite_schema`
            # for table creation.
            self._cf_filename: str = (
                f"{self.conf_prefix}{_environ}.db/tbl_{self.conf_prefix}"
            )
            self.loading: ConfABC = ConfSQLite(self._cf_loader_endpoint)
            self.loading.create(
                name=self._cf_filename, schemas=self.conf_sqlite_schema
            )
        else:
            raise NotImplementedError(
                f"{self.__class__.__name__} does not support "
                f"type: {self._cf_loader_type!r}."
            )

    def load(self) -> dict:
        """Return data from filename."""
        return self.loading.load_stage(name=self._cf_filename).get(
            self._cf_name, {}
        )

    def save(self, data: Union[dict, list]) -> None:
        """Saving data to source from filename."""
        self.loading.save_stage(name=self._cf_filename, data=data, merge=True)

    def remove(self) -> None:
        """Remove data from filename."""
        self.loading.remove_stage(
            name=self._cf_filename,
            data_name=self._cf_name,
        )


class ConfMetadata(BaseConfLoader):
    """Config Metadata Object for get data from metadata file or table"""

    conf_prefix: str = "metadata"

    conf_file_extension: str = "json"

    conf_file_initial: dict = {}

    conf_sqlite_schema: dict = {
        "name": "varchar(256) primary key",
        "shortname": "varchar(64) not null",
        "fullname": "varchar(256) not null",
        "data": "json not null",
        "updt": "datetime not null",
        "rtdt": "datetime not null",
        "author": "varchar(512) not null",
    }

    def save(self, data: dict) -> None:
        """Saving data to source with name mapping from filename."""
        self.loading.save_stage(
            name=self._cf_filename,
            data={self._cf_name: data},
            merge=True,
        )


@dataclasses.dataclass()
class Message:
    """Message Data Object for get message string and concat with `||` when
    pull result.
    """

    _message: str
    _messages: list[str] = dataclasses.field(default_factory=list)

    @property
    def messages(self) -> str:
        return self._message

    @messages.setter
    def messages(self, msg: str):
        self._messages.append(msg)
        self._message += f"||{msg}" if self._message else f"{msg}"


Logging = TypeVar("Logging", bound="ConfLogging")


def saving(func):
    @wraps(func)
    def wraps_saving(*args, **kwargs):
        self: Logging = args[0]
        _level: str = func.__name__.split("_")[-1].upper()
        if (
            (msg := args[1])
            and (getattr(logging, _level) >= self._cf_logger.level)
            and (self._cf_auto_save or kwargs.get("force", False))
        ):
            self.save(
                data=self.setup(
                    {
                        # TODO: converter msg string before save.
                        "message": msg,
                        "status": _level,
                    }
                )
            )
        return func(*args, **kwargs)

    return wraps_saving


class ConfLogging(BaseConfLoader):
    """Config Logging Object for log message from any change from register
    or loader process.
    """

    conf_prefix: str = "logging"

    conf_file_extension: str = "csv"

    conf_file_initial: list = []

    conf_sqlite_schema: dict = {
        "parent_hash_id": "varchar(64) not null",
        "hash_id": "varchar(64) primary key not null",
        "conf_name": "varchar(256) not null",
        "message": "text",
        "updt": "datetime not null",
        "status": "varchar(64) not null",
        "author": "varchar(512) not null",
    }

    def __init__(
        self,
        endpoint: str,
        name: str,
        _logger: logging.Logger,
        *,
        environ: Optional[str] = None,
        setup: Optional[dict] = None,
        auto_save: bool = False,
    ):
        super().__init__(endpoint, name, environ=environ)
        self._cf_logger: logging.Logger = _logger
        self._cf_msgs: list[Optional[dict]] = []
        self._cf_parent_hash: str = str(int(get_date("datetime").timestamp()))
        self._cf_setup: dict = merge_dict(
            {"conf_name": self._cf_name}, (setup or {})
        )
        self._cf_auto_save: bool = auto_save

    def setup(self, data) -> dict:
        _now = get_date("datetime")
        return merge_dict(
            self._cf_setup,
            {
                "parent_hash_id": self._cf_parent_hash,
                "hash_id": str(int(_now.timestamp())),
                "updt": _now.strftime("%Y-%m-%d %H:%M:%S"),
            },
            data,
        )

    def save_logging(self):
        if self.is_pulled:
            self.save(data=self._cf_msgs)
            self._cf_msgs: list[Optional[dict]] = []

    def debug(self, msg):
        self._cf_logger.debug(msg)

    def info(self, msg):
        self._cf_logger.info(msg)

    def warning(self, msg):
        self._cf_logger.warning(msg)

    def critical(self, msg):
        self._cf_logger.critical(msg)

    @saving
    def p_debug(self, msg, force: bool = False):
        if (
            (logging.DEBUG >= self.level)
            and (not self._cf_auto_save)
            and (not force)
        ):
            self._cf_msgs.append(
                self.setup({"message": msg, "status": "DEBUG"}),
            )
        self._cf_logger.debug(msg)

    @saving
    def p_info(self, msg, force: bool = False):
        if (
            logging.INFO >= self.level
            and (not self._cf_auto_save)
            and (not force)
        ):
            self._cf_msgs.append(self.setup({"message": msg, "status": "INFO"}))
        self._cf_logger.info(msg)

    @saving
    def p_warning(self, msg, force: bool = False):
        if (
            logging.WARNING >= self.level
            and (not self._cf_auto_save)
            and (not force)
        ):
            self._cf_msgs.append(
                self.setup({"message": msg, "status": "WARNING"}),
            )
        self._cf_logger.warning(msg)

    @saving
    def p_critical(self, msg, force: bool = False):
        if (
            logging.CRITICAL >= self.level
            and (not self._cf_auto_save)
            and (not force)
        ):
            self._cf_msgs.append(
                self.setup({"message": msg, "status": "CRITICAL"}),
            )
        self._cf_logger.critical(msg)

    @property
    def is_pulled(self) -> bool:
        return len(self._cf_msgs) > 0

    @property
    def level(self) -> int:
        return self._cf_logger.level


def test_meta_sqlite():
    _meta = ConfMetadata(
        "sqlite://D:/korawica/Work/dev02_miniproj/GITHUB/dde-object-defined/data",
        # 'file://D:/korawica/Work/dev02_miniproj/GITHUB/dde-object-defined/data',
        "conn_local_file2",
    )
    _meta.save(
        data={
            "name": "conn_local_file2",
            "shortname": "t3",
            "fullname": "super_test",
            "data": {"data": "ASFGSDFE13123"},
            "updt": "2022-01-02 00:00:00",
            "rtdt": "2022-01-01 00:00:00",
            "author": "unknown",
        }
    )
    print(_meta.load())


def test_logging_file():
    _log = ConfLogging(
        "file://D:/korawica/Work/dev02_miniproj/GITHUB/dde-object-defined/data/logs",
        "conn_local_file",
        _logger=logging,
        auto_save=False,
    )
    _log.p_info("test log data from info level", force=True)
    _log.p_debug("test log data from debug level1")
    _log.p_debug("test log data from debug level2")
    print(_log.is_pulled)


if __name__ == "__main__":
    test_meta_sqlite()
    # test_logging_file()
