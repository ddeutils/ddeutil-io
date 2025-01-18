from __future__ import annotations

from dataclasses import dataclass
from typing import Union

TupleStr = tuple[str, ...]
AnyValue = Union[str, int, float, bool, None]
AnyData = Union[AnyValue, dict[str, AnyValue], list[AnyValue]]


@dataclass(frozen=True)  # pragma: no cover
class Icon:
    normal: str
    next: str
    last: str

    def __len__(self) -> int:
        return max(len(self.normal), len(self.next), len(self.last))


def icons(theme: int) -> Icon:
    return {
        1: Icon(normal="│", next="├─", last="└─"),
        2: Icon(normal="┃", next="┣━", last="┗━"),
        3: Icon(normal="│", next="├─", last="╰─"),
    }[theme]
