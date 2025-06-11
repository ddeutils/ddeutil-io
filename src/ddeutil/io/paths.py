# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

import fnmatch
from collections.abc import Collection, Iterator
from pathlib import Path
from typing import Optional, Union

from .__type import Icon, icons


def replace_sep(value: str) -> str:
    return value.replace("\\", "/")


def glob_files(path: Path) -> Iterator[Path]:  # pragma: no cov
    yield from (file for file in path.rglob("*") if file.is_file())


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
            elif full_path.is_file():  # pragma: no cov
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

    def tree(self, newline: Optional[str] = None) -> str:  # pragma: no cov
        """Return path tree of root path."""
        return (newline or "\n").join(self.output_buf)


def read_ignore(file: Union[str, Path]) -> list[str]:
    """Read ignore file content to list of ignore pattern."""
    ignores: list[str] = [file.name]
    if file.exists():
        ignores.extend(
            [
                line.strip()
                for line in file.read_text().splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
        )
    return ignores


def is_ignored(file: Path, ignores: list[str]) -> bool:
    """Check if a path should be ignored based on patterns.

    :params file: (Path): a file path to check against ignore patterns
    :params ignores:

    :returns: True if path should be ignored, False otherwise
    """
    return any(
        (
            file.resolve().match(f"**/{pattern.removesuffix('/')}/*")
            or file.resolve().match(f"**/{pattern.removesuffix('/')}*")
        )
        for pattern in ignores
    )


def ls(path: Union[str, Path], ignore_file: Optional[str] = None) -> list[Path]:
    """List files in a directory, applying ignore-style filtering.

    :params base_dir: (str | Path) Base directory to search for files.
    :params ignore_file: (str) Name of the ignore file.

    :return: (list[Path]) Paths of file that are not ignored.
    """
    path: Path = Path(path).resolve()
    ignores: list[str] = read_ignore(path / ignore_file) if ignore_file else []
    return [
        file
        for file in glob_files(path)
        if not is_ignored(file, ignores=ignores)
    ]
