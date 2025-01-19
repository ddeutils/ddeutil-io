# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

from typing import Callable, TypeVar

from ddeutil.core import convert, import_string

from .__conf import RegexConf

T = TypeVar("T")


def template_secret(value: T, secrets: dict[str, str]) -> T:
    """Map the secret value to a any input data.

    :param value: An input value that want to map secrets
    :param secrets: A mapping of value secrets that use to replace.
    :type secrets: dict[str, str]

    Examples:
        >>> template_secret("s3://@secrets{foo}", secrets={"foo": "bar"})
        's3://bar'
    """
    if isinstance(value, dict):
        return {k: template_secret(value[k], secrets) for k in value}
    elif isinstance(value, (list, tuple)):
        return type(value)([template_secret(i, secrets) for i in value])
    elif not isinstance(value, str):
        return value
    for search in RegexConf.RE_SECRETS.finditer(value):
        searches: dict = search.groupdict()
        if "." in (br := searches["braced"]):
            raise ValueError(
                f"The @secrets: {br!r}, should not contain dot ('.') char"
            )
        value: str = value.replace(
            searches["search"],
            secrets.get(br.strip(), searches["braced_default"]),
        )
    return value


def template_func(value: T) -> T:
    """Map the function result to configuration data.

    :param value: A data that want to map imported function with arguments.

    Examples:
        >>> template_func(
        ...     "Test @function{ddeutil.io.files.add_newline:'a',newline='|'}"
        ... )
        'Test a|'
    """
    if isinstance(value, dict):
        return {k: template_func(value[k]) for k in value}
    elif isinstance(value, (list, tuple)):
        return type(value)([template_func(i) for i in value])
    elif not isinstance(value, str):
        return value
    for search in RegexConf.RE_FUNCTION.finditer(value):
        searches: dict = search.groupdict()
        if not callable(_fn := import_string(searches["function"])):
            raise ValueError(
                f'The @function: {searches["function"]!r} is not callable.',
            )
        args, kwargs = convert.str2args(searches["arguments"])
        value: str = value.replace(searches["search"], _fn(*args, **kwargs))
    return value


def map_func(value: T, func: Callable[[str], str]) -> T:
    """Map any function from input argument to configuration data.

    Examples:
        >>> map_func({"foo": "bar"}, lambda x: x + "!")
        {'foo': 'bar!'}
        >>> map_func(("foo", "bar"), lambda x: x + "!")
        ('foo!', 'bar!')
    """
    if isinstance(value, dict):
        return {k: map_func(value[k], func) for k in value}
    elif isinstance(value, (list, tuple)):
        return type(value)([map_func(i, func) for i in value])
    elif not isinstance(value, str):
        return value
    return func(value)
