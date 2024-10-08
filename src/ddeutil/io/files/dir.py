# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from tarfile import TarFile
from typing import (
    Any,
    Literal,
    Protocol,
    Union,
)

from ddeutil.core import splitter

DirCompressType = Literal["zip", "rar", "tar", "h5", "hdf5", "fits"]


class OpenDirProtocol(Protocol):  # pragma: no cover
    """Open Directory Protocol object."""

    def write(self, name, arcname): ...

    def safe_extract(self, path: str | Path, members=None): ...


class CustomZipFl(zipfile.ZipFile):
    """Override ZipFile object."""

    def safe_extract(self, path=str, members=None):
        self.extractall(path, members)


class CustomTarFl(TarFile):
    """Override TarFile object."""

    def write(self, name, arcname=None):
        """Clone ``self.add`` method to the new name."""
        return self.add(name, arcname)

    def safe_extract(self, path: str | Path = ".", members=None):
        path: Path = path if isinstance(path, Path) else Path(path)
        # NOTE: For Python version >= 3.12
        if sys.version_info >= (3, 12):
            self.extractall(path, members, filter="data")
            return
        self.extractall(path, members)


class Dir:
    """Open File Object"""

    def __init__(
        self,
        path: Union[str, Path],
        *,
        compress: str,
    ) -> None:
        self.path: Path = Path(path) if isinstance(path, str) else path
        _compress, sub = splitter.must_split(compress, ":", maxsplit=1)
        self.compress: DirCompressType = _compress
        self.sub_compress: str = sub or "_"

        # NOTE: Action anything after set up attributes.
        self.after_set_attrs()

    def after_set_attrs(self) -> None: ...

    def open(self, *, mode: str, **kwargs) -> OpenDirProtocol:
        """Open dir"""
        if self.compress in ("zip",):
            ZIP_COMPRESS: dict[str, Any] = {
                "_": zipfile.ZIP_DEFLATED,
                "bz2": zipfile.ZIP_BZIP2,
            }

            return CustomZipFl(
                self.path,
                mode=mode,
                compression=ZIP_COMPRESS[self.sub_compress],
                **kwargs,
            )
        elif self.compress in ("tar",):
            TAR_COMPRESS: dict[str, str] = {
                "_": "gz",
                "gz": "gz",
                "bz2": "bz2",
                "xz": "xz",
            }

            return CustomTarFl.open(
                self.path,
                mode=f"{mode}:{TAR_COMPRESS[self.sub_compress]}",
            )
        raise NotImplementedError
