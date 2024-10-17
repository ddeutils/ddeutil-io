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

import fnmatch
import os
import shutil
from collections.abc import Collection
from pathlib import Path

from .conf import RegexConf
from .dir import (
    Dir,
)
from .file import (
    CsvFl,
    CsvPipeFl,
    EnvFl,
    Fl,
    JsonEnvFl,
    JsonFl,
    MarshalFl,
    MsgpackFl,
    PickleFl,
    TomlEnvFl,
    TomlFl,
    YamlEnvFl,
    YamlFl,
    YamlFlResolve,
)
from .utils import (
    add_newline,
    search_env_replace,
)


def rm(path: str, is_dir: bool = False) -> None:  # no cove
    """Remove a file or dir from a input path.

    :param path: A path of file or dir that want to remove.
    :param is_dir: A flag that tell this input path is dir or not.
    """
    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)
    elif os.path.isdir(path) and is_dir:
        shutil.rmtree(path)
    else:
        raise ValueError(
            f"file {path!r} is not a file{' or dir' if is_dir else ''}."
        )


def touch(filename: str, times=None) -> None:  # no cove
    """Create an empty file with specific name and modified time of path it an
    input times was set.
    """
    file_handle = open(filename, mode="a")
    try:
        os.utime(filename, times)
    finally:
        file_handle.close()


class PathSearch:
    """Path Search object that use to search path tree from an input root path.
    It allow you to adjust recursive level value and exclude dir or file paths
    on the searching process.

    :param root: A input root path that want to search.
    :param exclude: A list of exclude paths.
    """

    def __init__(
        self,
        root: Path,
        *,
        exclude: list[str] | None = None,
        max_level: int = -1,
        length: int = 4,
        icon: int = 1,
    ) -> None:
        self.root: Path = root
        self.exclude: list[str] = exclude or []
        self.max_level: int = max_level
        self.length: int = length
        self.real_level: int = 0

        # Declare icon arguments
        self._icon_last: str = self.icons()[icon]["last"]
        self._icon_next: str = self.icons()[icon]["next"]
        self._icon: str = self.icons()[icon]["normal"]
        self._icon_length: int = len(self._icon)

        assert (
            self._icon_length + 1
        ) < self.length, "a `length` argument must gather than length of icon."

        self.output_buf: list = [f"[{self.root.stem}]"]
        self.files: list[Path] = []
        self.__recurse(self.root, list(self.root.iterdir()), "", 0)

    @property
    def level(self) -> int:
        """Return level of sub path from the root path."""
        return self.real_level + 1 if self.max_level == -1 else self.max_level

    def __recurse(
        self,
        path: Path,
        file_list: list[Path],
        prefix: str,
        level: int,
    ):
        """Path recursive method for generate buffer of tree and files."""
        if not file_list or (self.max_level != -1 and self.max_level <= level):
            return

        self.real_level: int = max(level, self.real_level)
        file_list.sort(key=lambda f: (path / f).is_file())
        for idx, sub_path in enumerate(file_list):

            if any(fnmatch.fnmatch(sub_path.name, exc) for exc in self.exclude):
                continue

            full_path: Path = path / sub_path
            idc: str = self.__switch_icon(idx, len(file_list))
            if full_path.is_dir():
                self.output_buf.append(f"{prefix}{idc}[{sub_path}]")
                tmp_prefix: str = (
                    (
                        f"{prefix}{self._icon}"
                        f'{" " * (self.length - self._icon_length)}'
                    )
                    if len(file_list) > 1 and idx != len(file_list) - 1
                    else f'{prefix}{" " * self.length}'
                )
                self.__recurse(
                    full_path, list(full_path.iterdir()), tmp_prefix, level + 1
                )
            elif full_path.is_file():  # no cove
                self.output_buf.append(f"{prefix}{idc}{sub_path}")
                self.files.append(full_path)

    def pick(self, filename: str | Collection[str]) -> list[Path]:
        """Return filename with match with input argument."""
        patterns = (filename,) if isinstance(filename, str) else filename
        return list(
            filter(
                (
                    lambda f: any(
                        fnmatch.fnmatch(f, f"*/{pattern}")
                        for pattern in patterns
                    )
                ),
                self.files,
            )
        )

    def tree(self, newline: str | None = None) -> str:  # no cove
        """Return path tree of root path."""
        return (newline or "\n").join(self.output_buf)

    def __switch_icon(self, number_now: int, number_all: int):
        """Private method that use to switch icon mapping."""
        return (
            self._icon_last
            if number_now == (number_all - 1)
            else self._icon_next
        )

    @staticmethod
    def icons() -> dict[int, dict[str, str]]:
        return {
            1: {"normal": "│", "next": "├─", "last": "└─"},
            2: {"normal": "┃", "next": "┣━", "last": "┗━"},
            3: {"normal": "│", "next": "├─", "last": "╰─"},
        }
