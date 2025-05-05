# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
"""
This is the main function for open any files in local or remote space
with the best python libraries and the best practice such as build-in
``io.open``, ``mmap.mmap``, etc.

TODO: Add more compress type such as
    - h5,hdf5(h5py)
    - fits(astropy)
    - rar(...)
"""
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
import re
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
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
    Iterator,
)

try:
    import msgpack
except ImportError:  # pragma: no cov
    msgpack = None

try:
    import yaml

    try:
        from yaml import CSafeLoader as SafeLoader
        from yaml import CUnsafeLoader as UnsafeLoader
    except ImportError:  # pragma: no cov
        from yaml import SafeLoader, UnsafeLoader
except ImportError:  # pragma: no cov
    yaml = None
    SafeLoader = None
    UnsafeLoader = None

try:
    import rtoml
except ImportError:  # pragma: no cov
    rtoml = None

from .utils import search_env, search_env_replace

logger = logging.getLogger("ddeutil.io")
FileCompressType = Literal["gzip", "gz", "xz", "bz2"]
LOCK: Lock = Lock()

__all__: tuple[str, ...] = (
    "Fl",
    "EnvFlMixin",
    "EnvFl",
    "JsonFl",
    "JsonEnvFl",
    "JsonLineFl",
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


class CompressProtocol(Protocol):  # pragma: no cov
    """Compress protocol object that allow to implement and use ``decompress``
    and ``open`` methods.
    """

    def decompress(self, *args, **kwargs) -> AnyStr: ...

    def open(self, *args, **kwargs) -> IO: ...


def compress_lib(compress: Optional[FileCompressType]) -> CompressProtocol:
    """Return Compress module that use to unpack data from the compressed file.
    Now, it support for "gzip", "gz", "xz", and "bz2".

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


class FlABC(abc.ABC):  # pragma: no cov
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
    because it does not override necessary methods from FlABC abstract class.

    :param path: A path that respresent the file location.
    :type path: str | Path
    :param encoding: An open file encoding value, it will use UTF-8 by default.
    :type encoding: Optional[str] (None)
    :param compress: A compress type for this file.
    :type compress: FileCompressType | None (None)

    Examples:
        >>> with Fl(
        ...     path='./<path>/<filename>.gz.txt', compress='gzip'
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

    def after_set_attrs(self) -> None:  # pragma: no cov
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

    def __mode(self, mode: Optional[str] = None) -> dict[str, str]:
        """Convert mode property before passing to the main standard lib.

        :param mode: a reading or writing mode for the open method.
        :type mode: Optional[str] (None)

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

        if self.compress in get_args(FileCompressType):
            return (
                {"mode": mode}
                if byte_mode
                else {"mode": f"{mode}t", "encoding": self.encoding}
            )

        raise NotImplementedError(
            f"mode conversion does not support for compress type no in "
            f"{get_args(FileCompressType)}."
        )

    def open(self, *, mode: Optional[str] = None, **kwargs) -> IO:
        """Open this file object with standard libs that match with it file
        format subclass propose.

        :param mode: An opening mode that allow you to use read or write mode.
        :type mode: Optional[str] (None)
        :rtype: IO
        """
        return compress_lib(self.compress).open(
            self.path, **(self.__mode(mode) | kwargs)
        )

    @contextmanager
    def mopen(self, *, mode: Optional[str] = None) -> Iterator[IO]:
        """Open with memory mode context manager.

        :param mode: An opening mode that allow you to use read or write mode.
        :type mode: Optional[str] (None)
        :rtype: Iterator[IO]
        """
        mode: str = mode or "r"
        file: IO = self.open(mode=mode)
        _access: int = mmap.ACCESS_READ if ("r" in mode) else mmap.ACCESS_WRITE
        try:
            yield mmap.mmap(file.fileno(), length=0, access=_access)
        except ValueError:
            logger.exception("Can not open file with memory mode")
            yield file
        finally:
            file.close()

    def read(self, *args, **kwargs):  # pragma: no cov
        raise NotImplementedError(
            "This is abstract class only, so, you should implement open file "
            "object with this class and override this method."
        )

    def write(self, *args, **kwargs) -> None:  # pragma: no cov
        raise NotImplementedError(
            "This is abstract class only, so, you should implement open file "
            "object with this class and override this method."
        )


class EnvFlMixin:
    """Environment Mapping to read method of open file object mixin. This object
    already implement class variables that need to use on ``search_env_replace``
    function.
    """

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

    def search_env_replace(self, content: str) -> str:
        """Return environment variable replaced content.

        :param content: A content data that want to search and replace env var.
        """
        return search_env_replace(
            content,
            raise_if_default_not_exists=self.raise_if_not_default,
            default=self.default,
            escape=self.escape,
            caller=self.prepare,
        )


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
            rs: dict[str, str] = search_env(
                f.read(),
                keep_newline=self.keep_newline,
                default=self.default,
            )
        if update:
            os.environ.update(**rs)
        return rs

    def write(self, data: dict[str, Any]) -> None:  # pragma: no cov
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

            ```python
            import re
            from yaml.resolver import Resolver

            # NOTE: zap the Resolver class' internal dispatch table
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
        with LOCK:
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


class YamlEnvFl(YamlFl, EnvFlMixin):
    """Yaml open file object which mapping search environment variable."""

    def read(self, safe: bool = True) -> dict[str, Any]:
        """Return data context from yaml file format and mapping search
        environment variables before returning context data.

        :param safe: A flag that allow to use safe reading mode.
        :type safe: bool (True)
        :rtype: dict[str, Any]
        """
        with self.open(mode="r") as f:
            context_env_replace: str = self.search_env_replace(
                yaml.dump(yaml.load(f.read(), UnsafeLoader))
            )
        return yaml.load(
            context_env_replace,
            (SafeLoader if safe else UnsafeLoader),
        )

    def write(self, data: dict[str, Any]) -> None:  # pragma: no cov
        raise NotImplementedError(
            "Yaml open file with mapping env var does not allow to write."
        )


class CsvFl(Fl):
    """CSV open file object with comma (,) seperator charactor."""

    def read(self, pre_load: int = 0) -> list[dict[Union[str, int], Any]]:
        """Return data context from csv file format.

        :param pre_load: An input bytes number that use to preloading for
            define column structure before reading with csv.
        :type pre_load: int (0)
        :rtype: list[dict[str | int, Any]]
        """
        with self.open(mode="r") as f:
            return list(csv.DictReader(f, delimiter=",", quoting=csv.QUOTE_ALL))

    def write(
        self,
        data: Union[list[Any], dict[Any, Any]],
        *,
        mode: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Write CSV file with an input data context. This method allow to use
        append write mode.
        """
        if not data:
            raise ValueError("data that want writing to CSV file was empty")

        mode: str = mode or "w"
        assert mode in (
            "a",
            "w",
        ), "save mode in CSV must contain only value `a` nor `w`."

        if isinstance(data, dict):
            data: list = [data]

        with self.open(mode=mode, newline="") as f:
            # noinspection PyTypeChecker
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
        """Return true if the file with csv format already implement header.

        :param pre_load: An input bytes number that use to preloading for
            define header.
        :type pre_load: int (128)
        :rtype: bool
        """
        with self.open(mode="r") as f:
            try:
                return csv.Sniffer().has_header(f.read(pre_load))
            except csv.Error:
                return False


class CsvDynamicFl(CsvFl):  # pragma: no cov
    """CSV open file object with dynamic dialect reader."""

    def read(self, pre_load: int = 128) -> list[dict[Union[str, int], Any]]:
        """Return data context from csv file format with dynamic dialect reader.

        :param pre_load: An input bytes number that use to preloading for
            define column structure before reading with csv.
        :type pre_load: int (128)
        :rtype: list[dict[str | int, Any]]
        """
        with self.open(mode="r") as f:
            dialect = csv.Sniffer().sniff(f.read(pre_load))
            f.seek(0)
            return list(csv.DictReader(f, dialect=dialect))


class CsvPipeFl(CsvFl):
    """CSV open file object with pipe (|) seperator charactor."""

    def after_set_attrs(self) -> None:
        """Register csv dialect after setting attribute open file object."""
        csv.register_dialect(
            "pipe_delimiter", delimiter="|", quoting=csv.QUOTE_ALL
        )

    def read(self, pre_load: int = 0) -> list:
        """Return data context from csv file format with the pipe seperator.
        This read method do not use ``pre_load`` parameter because it is passing
        fix dialect argument.

        :param pre_load: An input bytes number that use to preloading for
            define column structure before reading with csv.
        :type pre_load: int (0)
        :rtype: list[dict[str | int, Any]]
        """
        with self.open(mode="r") as f:
            return list(csv.DictReader(f, delimiter="|", quoting=csv.QUOTE_ALL))

    def write(
        self,
        data: Union[list[Any], dict[Any, Any]],
        *,
        mode: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Write data to the CSV file format."""
        if not data:
            raise ValueError("data to write is empty")

        mode: str = mode or "w"
        assert mode in {
            "a",
            "w",
        }, "save mode must contain only value `a` nor `w`."

        if isinstance(data, dict):
            data: list = [data]

        with self.open(mode=mode, newline="") as f:
            # noinspection PyTypeChecker
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


class JSONCommentsDecoder(json.JSONDecoder):
    """Override JSON Decoder object for remove comment statement inside data
    content that not remove by default json built-in module.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def decode(self, s: str, _w=None):
        """Decode with a comment in the Json data context.

        Reference:
            - https://stackoverflow.com/questions/69021815/
                how-to-read-json-file-with-comments
        """
        # NOTE: This below regex requires the ``re.X`` flag, to ignore
        #   whitespaces inside the regex.
        #
        #   (
        #       "(?:\\"|[^"])*?" (?# First try to match balanced quotes)
        #   )
        #   | (?# If not successfully, try the following)
        #   (
        #       \/\*(?:.|\s)*?\*\/ (?# Match a block comment)
        #       |
        #       \/\/.* (?# Match a line comment)
        #   )
        #
        regex: str = r"""("(?:\\"|[^"])*?")|(\/\*(?:.|\s)*?\*\/|\/\/.*)"""
        s: str = re.sub(regex, r"\1", s)  # NOTE: , flags = re.X | re.M)
        return super().decode(s)


class JsonFl(Fl):
    """Json open file object that read data context from Json file format
    (.json).
    """

    def read(self) -> Union[dict[Any, Any], list[Any]]:
        with self.open(mode="r") as f:
            try:
                return json.loads(f.read(), cls=JSONCommentsDecoder)
            except json.decoder.JSONDecodeError as err:
                logger.exception(err)
                raise

    def write(self, data, *, indent: int = 4) -> None:
        with self.open(mode="w") as f:
            if self.compress:
                f.write(json.dumps(data, default=str))
            else:
                # noinspection PyTypeChecker
                json.dump(data, f, indent=indent, default=str)


class JsonEnvFl(JsonFl, EnvFlMixin):
    """Json open file object which mapping search environment variable before
    parsing with json package.
    """

    def read(self) -> Union[dict[Any, Any], list[Any]]:
        with self.open(mode="rt") as f:
            try:
                return json.loads(
                    self.search_env_replace(f.read()),
                    cls=JSONCommentsDecoder,
                )
            except json.decoder.JSONDecodeError as err:
                logger.exception(err)
                raise

    def write(self, data, *, indent: int = 4) -> None:  # pragma: no cov
        raise NotImplementedError(
            "Json open file with mapping env var does not allow to write."
        )


class JsonLineFl(Fl):
    """Json open file object that read data context from Json file format
    (.json) with a newline seperator.
    """

    def read(self) -> list[Any]:
        rs: list[Any] = []
        with self.open(mode="rt") as f:
            for line in f:
                try:
                    rs.append(json.loads(line, cls=JSONCommentsDecoder))
                except json.decoder.JSONDecodeError as err:
                    logger.exception(err)
                    raise
        return rs

    def write(self, data, *, mode: Optional[str] = None) -> None:
        if not data:
            raise ValueError("data to write is empty")

        mode: str = mode or "w"
        assert mode in {
            "a",
            "w",
        }, "save mode must contain only value `a` nor `w`."

        with self.open(mode=mode) as f:
            if isinstance(data, list):
                for d in data:
                    f.write(json.dumps(d, default=str) + "\n")
            else:
                f.write(json.dumps(data, default=str) + "\n")


class TomlFl(Fl):
    """TOML open file object that read data context from TOML file format
    (.toml).
    """

    def read(self):
        if rtoml is None:  # pragma: no cov
            raise ImportError(
                "writing toml file need `rtoml` package, you should to install "
                "rtoml via `pip install rtoml` first."
            )
        with self.open(mode="rt") as f:
            return rtoml.loads(f.read())

    def write(self, data: dict[str, Any]) -> None:
        if rtoml is None:  # pragma: no cov
            raise ImportError(
                "writing toml file need `rtoml` package, you should to install "
                "rtoml via `pip install rtoml` first."
            )
        with self.open(mode="wt") as f:
            # noinspection PyTypeChecker
            rtoml.dump(data, f)


class TomlEnvFl(TomlFl, EnvFlMixin):
    """TOML open file object which mapping search environment variable before
    parsing with `rtoml` package from TOML file format (.toml).
    """

    def read(self):
        if rtoml is None:  # pragma: no cov
            raise ImportError(
                "writing toml file need `rtoml` package, you should to install "
                "rtoml via `pip install rtoml` first."
            )
        with self.open(mode="rt") as f:
            return rtoml.loads(self.search_env_replace(f.read()))

    def write(self, data: dict[str, Any]) -> None:  # pragma: no cov
        raise NotImplementedError(
            "Toml open file with mapping env var does not allow to write."
        )


class PickleFl(Fl):  # pragma: no cov
    """Pickle open file object that read data context from Pickle file format
    (.pickle).
    """

    def read(self):
        with self.open(mode="rb") as f:
            return pickle.loads(f.read())

    def write(self, data):
        with self.open(mode="wb") as f:
            # noinspection PyTypeChecker
            pickle.dump(data, f)


class MarshalFl(Fl):  # pragma: no cov
    """Marshal open file object that read data context from Marshal file format.

    Note: use marshal package
    """

    def read(self):
        with self.open(mode="rb") as f:
            return marshal.loads(f.read())

    def write(self, data):
        with self.open(mode="wb") as f:
            # noinspection PyTypeChecker
            marshal.dump(data, f)


class MsgpackFl(Fl):  # pragma: no cov
    """Msgpack open file object that read data context from Msgpack file format.

    Note: use msgpack package
    """

    def read(self):
        with self.open(mode="rb") as f:
            return msgpack.loads(f.read())

    def write(self, data):
        with self.open(mode="wb") as f:
            msgpack.dump(data, f)
