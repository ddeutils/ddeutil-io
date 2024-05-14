from __future__ import annotations

import fnmatch
import os
import shutil
from pathlib import Path
from typing import (
    Optional,
)

from .__regex import RegexConf
from .files import (
    CsvFl,
    CsvPipeFl,
    EnvFl,
    Fl,
    JsonEnvFl,
    JsonFl,
    MarshalFl,
    PickleFl,
    YamlEnvFl,
    YamlFl,
)
from .utils import (
    add_newline,
    search_env_replace,
)


def rm(path: str, is_dir: bool = False) -> None:
    """Remove file or dir from a input path."""
    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)
    elif os.path.isdir(path) and is_dir:
        shutil.rmtree(path)
    else:
        raise ValueError(
            f"file {path!r} is not a file{' or dir' if is_dir else ''}."
        )


def touch(filename: str, times=None) -> None:
    """Touch file"""
    file_handle = open(filename, mode="a")
    try:
        os.utime(filename, times)
    finally:
        file_handle.close()


class PathSearch:
    """Path Search object"""

    def __init__(
        self,
        root: Path,
        *,
        exclude: Optional[list] = None,
        exclude_dir: Optional[list] = None,
        max_level: int = -1,
        length: int = 4,
        icon: int = 1,
    ):
        self.root: Path = root
        self.exclude_dir: list = exclude_dir or []
        self.exclude: list = exclude or []
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
        try:
            self.__recurse(self.root, list(self.root.iterdir()), "", 0)
        except FileNotFoundError:
            pass

    @property
    def level(self) -> int:
        """Return level of sub path from the root path."""
        return self.real_level + 1 if self.max_level == -1 else self.max_level

    def __recurse(
        self,
        path: Path,
        file_list: list,
        prefix: str,
        level: int,
    ):
        """Path recursive method for generate buffer of tree and files."""
        if not file_list or (self.max_level != -1 and self.max_level <= level):
            return

        self.real_level: int = max(level, self.real_level)
        file_list.sort(key=lambda f: (path / f).is_file())
        for idx, sub_path in enumerate(file_list):
            if any(exc == sub_path for exc in self.exclude):
                continue

            full_path: Path = path / sub_path
            idc: str = self.__switch_icon(idx, len(file_list))

            if full_path.is_dir() and sub_path not in self.exclude_dir:
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
            elif full_path.is_file():
                self.output_buf.append(f"{prefix}{idc}{sub_path}")
                self.files.append(full_path)

    def pick(self, filename: str) -> list[Path]:
        """Return filename with match with input argument."""
        return list(
            filter(
                lambda file: fnmatch.fnmatch(file, f"*/{filename}"),
                self.files,
            )
        )

    def tree(self, newline: Optional[str] = None) -> str:
        """Return path tree of root path."""
        return (newline or "\n").join(self.output_buf)

    def __switch_icon(self, number_now: int, number_all: int):
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
