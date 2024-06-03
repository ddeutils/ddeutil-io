# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

import re
from typing import (
    Optional,
    Union,
)
from urllib.parse import unquote_plus


def unquote_str(value: str):
    """
    :param value:
    :return:

    Examples:
        >>> unquote_str('P%40ssw0rd')
        'P@ssw0rd'
        >>> unquote_str(None)

    """
    return unquote_plus(value) if value else value


def catch_str(
    value: str,
    key: str,
    *,
    replace: Optional[str] = None,
    flag: bool = True,
) -> tuple[str, Optional[Union[bool, str]]]:
    """Catch keyword from string value and return True if it exits.

    :param value: a string value that want to catch with the key.
    :param key: a key that use to catch.
    :param replace: a string value that want to replace if catch found
    :param flag: if it true, it will return boolean instead catched string

    :rtype: tuple[str, Optional[Union[bool, str]]]
    :return: a pair or prepared value and catched string or boolean if flag wan
        setted.

    Examples:
        >>> catch_str("varchar( 100 ) unique", "unique")
        ('varchar( 100 )', True)
        >>> catch_str("integer primary keys", "primary key")
        ('integer s', True)
        >>> catch_str("timestamp( 6 ) not null", "not null", replace="null")
        ('timestamp( 6 ) null', True)
        >>> catch_str("integer primary keys", "primary key", flag=False)
        ('integer s', 'primary key')
    """
    if key in value:
        return (
            " ".join(value.replace(key, (replace or "")).split()),
            (True if flag else key),
        )
    return value, (False if flag else None)


def split_dtype(dtype: str) -> tuple[str, str]:
    """Split the datatype value from long string by null string

    :param dtype: a data type string value that want to split
    :type dtype: str

    :rtype: tuple[str, str]
    :return: a pair of full data type value and null/not null string value.

    Examples:
        >>> split_dtype("string null")
        ('string', 'null')
        >>> split_dtype("numeric(10, 2) Null")
        ('numeric(10, 2)', 'null')
        >>> split_dtype("timestamp(6) NULL")
        ('timestamp(6)', 'null')
        >>> split_dtype("string not null")
        ('string', 'not null')
        >>> split_dtype("varchar( 20 ) not null null")
        ('varchar( 20 )', 'null')
        >>> split_dtype("string null null")
        ('string', 'null')
    """
    _nullable: str = "null"
    for null_str in (
        "not null",
        "Not Null",
        "NOT NULL",
        "null",
        "Null",
        "NULL",
    ):
        if re.search(null_str, dtype):
            _nullable = null_str
            dtype = dtype.replace(null_str, "")
    return " ".join(dtype.strip().split()), _nullable.lower()


def extract_dtype(dtype: str) -> dict[str, str]:
    """Extract Data Type from an input string.

    Examples:
        >>> extract_dtype("varchar( 255 )")
        {'type': 'varchar', 'max_length': '255'}
        >>> extract_dtype("varchar[10]")
        {'type': 'varchar', 'max_length': '10'}
        >>> extract_dtype("numeric(19, 2)")
        {'type': 'numeric', 'precision': '19', 'scale': '2'}
    """
    if m := re.search(
        r"(?P<type>\w+)"
        r"(?:\s?[(\[]\s?(?P<max_length>\d+)(?:,\s?(?P<scale>\d+))?\s?[])])?",
        dtype.strip(),
    ):
        extract = m.groupdict()
        if (t := extract["type"]) in ("numeric", "decimal"):
            extract["precision"] = extract.pop("max_length")
            extract["scale"] = extract.pop("scale", None) or -1
            return extract

        extract.pop("scale")
        if t in ("timestamp", "time"):
            extract["precision"] = extract.pop("max_length")
            return extract
        return extract
    return {"type": dtype}
