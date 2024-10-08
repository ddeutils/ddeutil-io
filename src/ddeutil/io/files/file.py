# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

import abc
import csv
import io
import json
import logging
import marshal
import mmap
import os
import pickle
from contextlib import contextmanager
from pathlib import Path
from typing import (
    IO,
    Any,
    AnyStr,
    Callable,
    ClassVar,
    Literal,
    Optional,
    Protocol,
    Union,
    get_args,
)

import msgpack
import toml
import yaml

try:
    from yaml import CSafeLoader as SafeLoader
    from yaml import CUnsafeLoader as UnsafeLoader
except ImportError:  # pragma: no cover
    from yaml import SafeLoader, UnsafeLoader

from .utils import search_env, search_env_replace

FileCompressType = Literal["gzip", "gz", "xz", "bz2"]

__all__: tuple[str, ...] = (
    "Fl",
    "EnvFl",
    "JsonFl",
    "JsonEnvFl",
    "YamlFl",
    "YamlFlResolve",
    "YamlEnvFl",
    "CsvFl",
    "CsvPipeFl",
    "TomlFl",
    "TomlEnvFl",
    "MarshalFl",
    "MsgpackFl",
    "PickleFl",
    "compress_lib",
)


def compress_lib(compress: str) -> CompressProtocol:
    """Return Compress module that use to unpack data from the compressed file.
    Now, it support for "gzip", "gz", "xz", "bz2"]

    :param compress: A compress string type value that want to get compress
        package.
    :type compress: str
    :rtype: CompressProtocol
    """
    if not compress:
        return io
    elif compress in ("gzip", "gz"):
        import gzip

        return gzip
    elif compress in ("bz2",):
        import bz2

        return bz2
    elif compress in ("xz",):
        import lzma as xz

        return xz
    raise NotImplementedError(f"Compress {compress} does not implement yet")


class CompressProtocol(Protocol):  # pragma: no cover
    """Compress protocol object that allow to implement and use ``decompress``
    and ``open`` methods.
    """

    def decompress(self, *args, **kwargs) -> AnyStr: ...

    def open(self, *args, **kwargs) -> IO: ...


class FlABC(abc.ABC):  # pragma: no cover
    """Open File abstraction object for marking abstract methods that need to
    implement on any open file subclass.
    """

    @abc.abstractmethod
    def read(self, *args, **kwargs): ...

    @abc.abstractmethod
    def write(self, *args, **kwargs): ...


class Fl(FlABC):
    """Open File object that use to open any normal or compression file from
    current local file system (I do not have plan to implement remote object
    storage like AWS S3, GCS, or ADLS).

        Note that, this object should to implement it with subclass again
    because it do not override necessary methods from FlABC abstract class.

    :param path: A path that respresent the file location.
    :param encoding: An open file encoding value, it will use UTF-8 by default.
    :param compress: A compress type for this file.

    Examples:
        >>> with Fl(
        ...     path='./<path>/<filename>.gz.txt',
        ...     compress='gzip',
        ... ).open() as f:
        ...     data = f.readline()
    """

    def __init__(
        self,
        path: Union[str, Path],
        *,
        encoding: Optional[str] = None,
        compress: Optional[FileCompressType] = None,
    ) -> None:
        self.path: Path = Path(path) if isinstance(path, str) else path
        self.encoding: str = encoding or "utf-8"
        self.compress: Optional[FileCompressType] = compress

        # NOTE: Action anything after set up attributes.
        self.after_set_attrs()

    def after_set_attrs(self) -> None:  # pragma: no cover
        """Do any action after the object initialize step."""

    def __call__(self, *args, **kwargs) -> IO:
        """Return IO of this object."""
        return self.open(*args, **kwargs)

    @property
    def decompress(self) -> Callable[[...], AnyStr]:
        """Return decompress method that getting from its compression type.

        :rtype: Callable[[...], AnyStr]
        """
        if self.compress is not None and self.compress in get_args(
            FileCompressType
        ):
            return compress_lib(self.compress).decompress
        raise NotImplementedError(
            "Does not implement decompress method for None compress value."
        )

    def __mode(self, mode: str | None = None) -> dict[str, str]:
        """Convert mode property before passing to the main standard lib.

        :param mode: a reading or writing mode for the open method.
        :type mode: str | None (None)

        :rtype: dict[str, str]
        :returns: A mapping of mode and other input parameters for standard
            libs.
        """
        if not mode:
            return {"mode": "r"}
        byte_mode: bool = "b" in mode
        if self.compress is None:
            _mode: dict[str, str] = {"mode": mode}
            return _mode if byte_mode else {"encoding": self.encoding, **_mode}
        elif not byte_mode and self.compress in ("gzip", "gz", "xz", "bz2"):
            # NOTE:
            #   Add `t` in open file mode for force with text mode.
            return {"mode": f"{mode}t", "encoding": self.encoding}
        elif byte_mode and self.compress in ("gzip", "gz", "xz", "bz2"):
            return {"mode": mode}
        return {"mode": mode}

    def open(self, *, mode: Optional[str] = None, **kwargs) -> IO:
        """Open this file object with standard libs that match with it file
        format subclass propose.

        :rtype: IO
        """
        return compress_lib(self.compress).open(
            self.path, **(self.__mode(mode) | kwargs)
        )

    @contextmanager
    def mopen(self, *, mode: Optional[str] = None) -> IO:
        mode: str = mode or "r"
        file: IO = self.open(mode=mode)
        _access = mmap.ACCESS_READ if ("r" in mode) else mmap.ACCESS_WRITE
        try:
            yield mmap.mmap(file.fileno(), length=0, access=_access)
        except ValueError as err:
            if str(err) != "cannot mmap an empty file":
                raise err
            yield file
            logging.error("Does not open file with memory mode")
        finally:
            file.close()

    def read(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError()

    def write(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError()


class EnvFl(Fl):
    """Dot env open file object which mapping search engine to data context that
    reading from dot env file format (.env).
    """

    keep_newline: ClassVar[bool] = False
    default: ClassVar[str] = ""

    def read(self, *, update: bool = True) -> dict[str, str]:
        """Return data context from dot env file format.

        :param update: A update environment variable to interpreter flag.
        :type update: bool (True)
        :rtype: dict[str, str]
        """
        with self.open(mode="r") as f:
            f.seek(0)
            _result: dict = search_env(
                f.read(),
                keep_newline=self.keep_newline,
                default=self.default,
            )
        if update:
            os.environ.update(**_result)
        return _result

    def write(self, data: dict[str, Any]) -> None:  # pragma: no cover
        raise NotImplementedError(
            "Dot env open file object does not allow to write."
        )


class YamlFl(Fl):
    """Yaml open file object that read data context from Yaml file format (.yml,
    or .yaml).

        Note that, the boolean values on the data context in the yaml file will
    convert to the Python object;
        * true:     y, Y, true, Yes, on, ON
        * false:    n, N, false, No, off, OFF
    """

    def read(self, safe: bool = True) -> dict[str, Any]:
        """Return data context from yaml file format.

        :param safe: A flag that allow to use safe reading mode.
        :type safe: bool (True)
        :rtype: dict[str, Any]
        """
        with self.open(mode="r") as f:
            return yaml.load(f.read(), (SafeLoader if safe else UnsafeLoader))

    def write(self, data: dict[str, Any]) -> None:
        with self.open(mode="w") as f:
            yaml.dump(data, f, default_flow_style=False)


class YamlFlResolve(YamlFl):
    """Yaml open file object with resolve boolean convert value problem such as
    convert 'on' value to true instead a string of 'on' value. This object also
    read data context from Yaml file format (.yml, or .yaml).
    """

    def read(self, safe: bool = True) -> dict[str, Any]:
        """Reading Yaml data with does not convert boolean value.

        :param safe: A flag that allow to use safe reading mode.
        :type safe: bool (True)
        :rtype: dict[str, Any]

        Note that:
            Handle top level yaml property ``on``
            docs: https://github.com/yaml/pyyaml/issues/696

            ```
            import re
            from yaml.resolver import Resolver

            # zap the Resolver class' internal dispatch table
            Resolver.yaml_implicit_resolvers = {}

            # NOTE: Current Resolver
            Resolver.add_implicit_resolver(
                    'tag:yaml.org,2002:bool',
                    re.compile(r'''^(?:yes|Yes|YES|no|No|NO
                                |true|True|TRUE|false|False|FALSE
                                |on|On|ON|off|Off|OFF)$''', re.X),
                    list('yYnNtTfFoO'))

            # NOTE: The 1.2 bool impl Resolver:
            Resolver.add_implicit_resolver(
                    'tag:yaml.org,2002:bool',
                    re.compile(r'^(?:true|false)$', re.X),
                    list('tf'))
            ```
        """
        from yaml.resolver import Resolver

        revert = Resolver.yaml_implicit_resolvers.copy()

        for ch in "OoYyNn":
            if len(Resolver.yaml_implicit_resolvers[ch]) == 1:
                del Resolver.yaml_implicit_resolvers[ch]
            else:
                Resolver.yaml_implicit_resolvers[ch] = [
                    x
                    for x in Resolver.yaml_implicit_resolvers[ch]
                    if x[0] != "tag:yaml.org,2002:bool"
                ]

        with self.open(mode="r") as f:
            rs: dict[str, Any] = yaml.load(
                f.read(), (SafeLoader if safe else UnsafeLoader)
            )
            # NOTE: Override revert resolver when want to use safe load.
            Resolver.yaml_implicit_resolvers = revert
            return rs


class YamlEnvFl(YamlFl):
    """Yaml open file object which mapping search environment variable."""

    raise_if_not_default: ClassVar[bool] = False
    default: ClassVar[str] = "null"
    escape: ClassVar[str] = "<ESCAPE>"

    @staticmethod
    def prepare(value: str) -> str:
        """Prepare function it use on searching environment variable process
        that passing string value to this function before keeping to the final
        context data.

        :param value: A string value that passing from searching process
        :type value: str
        :rtype: str
        """
        return value

    def read(self, safe: bool = True) -> dict[str, Any]:
        """Return data context from yaml file format and mapping search
        environment variables before returning context data.

        :param safe: A flag that allow to use safe reading mode.
        :type safe: bool (True)
        :rtype: dict[str, Any]
        """
        with self.open(mode="r") as f:
            _env_replace: str = search_env_replace(
                yaml.dump(yaml.load(f.read(), UnsafeLoader)),
                raise_if_default_not_exists=self.raise_if_not_default,
                default=self.default,
                escape=self.escape,
                caller=self.prepare,
            )
            if _result := yaml.load(
                _env_replace,
                (SafeLoader if safe else UnsafeLoader),
            ):
                return _result
            return {}

    def write(self, data: dict[str, Any]) -> None:  # pragma: no cover
        raise NotImplementedError(
            "Yaml open file with mapping env var does not allow to write."
        )


class CsvFl(Fl):
    """CSV open file object with comma (,) seperator charactor."""

    def read(self, pre_load: int = 128) -> list[dict[str | int, Any]]:
        """Return data context from csv file format.

        :param pre_load: An input bytes number that use to pre-loading for
            define column structure before reading with csv.
        :type pre_load: int (128)
        :rtype: list[dict[str | int, Any]]
        """
        with self.open(mode="r") as f:
            try:
                dialect = csv.Sniffer().sniff(f.read(pre_load))
                f.seek(0)
                return list(csv.DictReader(f, dialect=dialect))
            except csv.Error:
                return []

    def write(
        self,
        data: list[Any] | dict[Any, Any],
        *,
        mode: str | None = None,
        **kwargs,
    ) -> None:
        """Write CSV file with an input data context. This method allow to use
        append write mode.
        """
        if not data:
            return

        mode: str = mode or "w"
        assert mode in (
            "a",
            "w",
        ), "save mode must contain only value `a` nor `w`."

        if isinstance(data, dict):
            data: list = [data]

        with self.open(mode=mode, newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=list(data[0].keys()),
                lineterminator="\n",
                **kwargs,
            )
            if mode == "w" or not self.has_header:
                writer.writeheader()
            writer.writerows(data)

    @property
    def has_header(self, pre_load: int = 128) -> bool:
        with self.open(mode="r") as f:
            try:
                return csv.Sniffer().has_header(f.read(pre_load))
            except csv.Error:
                return False


class CsvPipeFl(CsvFl):
    def after_set_attrs(self) -> None:
        csv.register_dialect(
            "pipe_delimiter", delimiter="|", quoting=csv.QUOTE_ALL
        )

    def read(self, pre_load: int = 0) -> list:
        with self.open(mode="r") as f:
            try:
                return list(
                    csv.DictReader(f, delimiter="|", quoting=csv.QUOTE_ALL)
                )
            except csv.Error:
                return []

    def write(
        self,
        data: Union[list[Any], dict[Any, Any]],
        *,
        mode: Optional[str] = None,
        **kwargs,
    ) -> None:
        mode = mode or "w"
        assert mode in {
            "a",
            "w",
        }, "save mode must contain only value `a` nor `w`."
        with self.open(mode=mode, newline="") as f:
            _has_data: bool = True
            if isinstance(data, dict):
                data: list = [data]
            elif not data:
                data: list = [{}]
                _has_data: bool = False
            if _has_data:
                writer = csv.DictWriter(
                    f,
                    fieldnames=list(data[0].keys()),
                    lineterminator="\n",
                    delimiter="|",
                    quoting=csv.QUOTE_ALL,
                    **kwargs,
                )
                if mode == "w" or not self.has_header:
                    writer.writeheader()
                writer.writerows(data)


class JsonFl(Fl):
    """Json open file object that read data context from Json file format
    (.json).
    """

    def read(self) -> Union[dict[Any, Any], list[Any]]:
        with self.open(mode="r") as f:
            try:
                return json.loads(f.read())
            except json.decoder.JSONDecodeError:
                return {}

    def write(self, data, *, indent: int = 4) -> None:
        with self.open(mode="w") as f:
            if self.compress:
                f.write(json.dumps(data))
            else:
                json.dump(data, f, indent=indent)


class JsonEnvFl(JsonFl):
    """Json open file object which mapping search environment variable before
    parsing with json package.
    """

    raise_if_not_default: ClassVar[bool] = False
    default: ClassVar[str] = "null"
    escape: ClassVar[str] = "<ESCAPE>"

    @staticmethod
    def prepare(value: str) -> str:
        return value

    def read(self) -> Union[dict[Any, Any], list[Any]]:
        with self.open(mode="rt") as f:
            return json.loads(
                search_env_replace(
                    f.read(),
                    raise_if_default_not_exists=self.raise_if_not_default,
                    default=self.default,
                    escape=self.escape,
                    caller=self.prepare,
                )
            )

    def write(self, data, *, indent: int = 4) -> None:  # pragma: no cover
        raise NotImplementedError(
            "Json open file with mapping env var does not allow to write."
        )


class TomlFl(Fl):
    def read(self):
        with self.open(mode="rt") as f:
            return toml.loads(f.read())

    def write(self, data: Any) -> None:
        with self.open(mode="wt") as f:
            toml.dump(data, f)


class TomlEnvFl(TomlFl):
    raise_if_not_default: ClassVar[bool] = False
    default: ClassVar[str] = "null"
    escape: ClassVar[str] = "<ESCAPE>"

    @staticmethod
    def prepare(x: str) -> str:
        return x

    def read(self):
        with self.open(mode="rt") as f:
            return toml.loads(
                search_env_replace(
                    f.read(),
                    raise_if_default_not_exists=self.raise_if_not_default,
                    default=self.default,
                    escape=self.escape,
                    caller=self.prepare,
                )
            )


class PickleFl(Fl):
    def read(self):
        with self.open(mode="rb") as f:
            return pickle.loads(f.read())

    def write(self, data):
        with self.open(mode="wb") as f:
            pickle.dump(data, f)


class MarshalFl(Fl):
    def read(self):
        with self.open(mode="rb") as f:
            return marshal.loads(f.read())

    def write(self, data):
        with self.open(mode="wb") as f:
            marshal.dump(data, f)


class MsgpackFl(Fl):
    def read(self):
        with self.open(mode="rb") as f:
            return msgpack.loads(f.read())

    def write(self, data):
        with self.open(mode="wb") as f:
            msgpack.dump(data, f)
