# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

from typing import Callable, TypeVar

from ddeutil.core import import_string, str2args

try:
    from .__base import RegexConf
    from .exceptions import ConfigArgumentError
except ImportError:
    from __base import RegexConf
    from exceptions import ConfigArgumentError


T = TypeVar("T")


def map_secret(value: T, secrets: dict[str, str]) -> T:
    """Map the secret value to a any input data.

    :param value: A data that want to map secrets
    :param secrets: A mapping of secrets
    :type secrets: dict[str, str]

    Examples:
        >>> map_secret(
        ...     "Value include secrets: s3://@secrets{foo}",
        ...     secrets={"foo": "bar"},
        ... )
        'Value include secrets: s3://bar'
    """
    if isinstance(value, dict):
        return {k: map_secret(value[k], secrets) for k in value}
    elif isinstance(value, (list, tuple)):
        return type(value)([map_secret(i, secrets) for i in value])
    elif not isinstance(value, str):
        return value
    for search in RegexConf.RE_SECRETS.finditer(value):
        searches: dict = search.groupdict()
        if "." in (br := searches["braced"]):
            raise ConfigArgumentError(
                "@secrets",
                f", value {br!r},  should not contain dot ('.') in get value.",
            )
        value: str = value.replace(
            searches["search"],
            secrets.get(br.strip(), searches["braced_default"]),
        )
    return value


def map_importer(value: T) -> T:
    """Map the function result to configuration data.

    :param value: A data that want to map imported function with arguments.

    Examples:
        >>> map_importer(
        ...     "Test @function{ddeutil.io.__base.add_newline:'a',newline='|'}"
        ... )
        'Test a|'
    """
    if isinstance(value, dict):
        return {k: map_importer(value[k]) for k in value}
    elif isinstance(value, (list, tuple)):
        return type(value)([map_importer(i) for i in value])
    elif not isinstance(value, str):
        return value
    for search in RegexConf.RE_FUNCTION.finditer(value):
        searches: dict = search.groupdict()
        if not callable(_fn := import_string(searches["function"])):
            raise ConfigArgumentError(
                "@function",
                f'from function {searches["function"]!r} is not callable.',
            )
        args, kwargs = str2args(searches["arguments"])
        value: str = value.replace(searches["search"], _fn(*args, **kwargs))
    return value


def map_func(value: T, fn: Callable[[str], str]) -> T:
    """Map any function from input argument to configuration data.

    Examples:
        >>> map_func({"foo": "bar"}, lambda x: x + "!")
        {'foo': 'bar!'}
    """
    if isinstance(value, dict):
        return {k: map_func(value[k], fn) for k in value}
    elif isinstance(value, (list, tuple)):
        return type(value)([map_func(i, fn) for i in value])
    elif not isinstance(value, str):
        return value
    return fn(value)
