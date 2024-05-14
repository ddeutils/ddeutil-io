# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

from typing import (
    Any,
    Callable,
    Union,
)

from ddeutil.core import import_string, str2args

from .__base import RegexConf
from .exceptions import ConfigArgumentError


def map_secret(
    value: Any,
    secrets: dict[str, Any],
) -> Union[dict, str, Any]:
    """Map the secret value to configuration data.

    :param value:
    :param secrets:
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
                "secrets",
                f", value {br!r},  should not contain dot ('.') in get value.",
            )
        value: str = value.replace(
            searches["search"],
            secrets.get(br.strip(), searches["braced_default"]),
        )
    return value


def map_function(value: Any) -> Union[dict, str, Any]:
    """Map the function result to configuration data."""
    if isinstance(value, dict):
        return {k: map_function(value[k]) for k in value}
    elif isinstance(value, (list, tuple)):
        return type(value)([map_function(i) for i in value])
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


def map_func_to_str(value: Any, fn: Callable[[str], str]) -> Any:
    """Map any function from input argument to configuration data."""
    if isinstance(value, dict):
        return {k: map_func_to_str(value[k], fn) for k in value}
    elif isinstance(value, (list, tuple)):
        return type(value)([map_func_to_str(i, fn) for i in value])
    elif not isinstance(value, str):
        return value
    return fn(value)
