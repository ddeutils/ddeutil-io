from __future__ import annotations

from typing import Union

TupleStr = tuple[str, ...]
AnyValue = Union[str, int, float, bool, None]
AnyData = Union[AnyValue, dict[str, AnyValue], list[AnyValue]]
