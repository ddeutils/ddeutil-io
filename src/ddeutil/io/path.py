# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

import fnmatch
from collections.abc import Collection
from pathlib import Path
from typing import Optional, Union

from .__type import Icon, icons


class PathSearch:
    """Path Search object that use to search path tree from an input root path.
    It allows you to adjust recursive level value and exclude dir or file paths
    on the searching process.

    :param root: An input root path that want to search.
    :param exclude: A list of exclude paths.
    """

    def __init__(
        self,
        root: Union[str, Path],
        *,
        exclude: Optional[list[str]] = None,
        max_level: int = -1,
        length: int = 4,
        icon: int = 1,
    ) -> None:
        self.root: Path = Path(root) if isinstance(root, str) else root

        if not self.root.exists():
            raise FileNotFoundError(f"Does not found {self.root.resolve()}")

        self.exclude: list[str] = exclude or []
        self.max_level: int = max_level
        self.length: int = length
        self.real_level: int = 0

        # NOTE: Define icon argument and check an input length.
        self.icon: Icon = icons(icon)

        assert (
            len(self.icon) + 1
        ) < self.length, "a `length` argument must gather than length of icon."

        self.output_buf: list = [f"[{self.root.stem}]"]
        self.files: list[Path] = []
        self.__recurse(self.root, list(self.root.glob("*")), "", 0)

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
        for i, sub_path in enumerate(file_list):

            if any(fnmatch.fnmatch(sub_path.name, exc) for exc in self.exclude):
                continue

            full_path: Path = path / sub_path
            idc: str = (
                self.icon.last if i == (len(file_list) - 1) else self.icon.next
            )

            if full_path.is_dir():
                self.output_buf.append(f"{prefix}{idc}[{sub_path}]")
                tmp_prefix: str = (
                    (
                        f"{prefix}{self.icon.normal}"
                        f'{" " * (self.length - len(self.icon))}'
                    )
                    if len(file_list) > 1 and i != len(file_list) - 1
                    else f'{prefix}{" " * self.length}'
                )
                self.__recurse(
                    full_path, list(full_path.iterdir()), tmp_prefix, level + 1
                )
            elif full_path.is_file():  # pragma: no cover
                self.output_buf.append(f"{prefix}{idc}{sub_path}")
                self.files.append(full_path)

    def pick(self, filename: Union[str, Collection[str]]) -> list[Path]:
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

    def tree(self, newline: Optional[str] = None) -> str:  # pragma: no cover
        """Return path tree of root path."""
        return (newline or "\n").join(self.output_buf)
