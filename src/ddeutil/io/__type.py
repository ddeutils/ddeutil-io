# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

from dataclasses import dataclass
from typing import Union

TupleStr = tuple[str, ...]
AnyValue = Union[str, int, float, bool, None]
AnyData = Union[
    AnyValue, dict[str, AnyValue], list[AnyValue], list[dict[str, AnyValue]]
]


@dataclass(frozen=True)  # pragma: no cov
class Icon:
    """Icon dataclass object that keep necessary element for making tree."""

    normal: str
    next: str
    last: str

    def __len__(self) -> int:
        """Return the maximum length of element characters."""
        return max(len(self.normal), len(self.next), len(self.last))


def icons(theme: int) -> Icon:
    """Get the Icon object from a theme value."""
    return {
        1: Icon(normal="│", next="├─", last="└─"),
        2: Icon(normal="┃", next="┣━", last="┗━"),
        3: Icon(normal="│", next="├─", last="╰─"),
    }[theme]
