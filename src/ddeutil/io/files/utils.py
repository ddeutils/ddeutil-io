# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

import os
from collections.abc import Iterator
from typing import IO, AnyStr, Callable, Optional

from ..__conf import RegexConf

__all__: tuple[str, ...] = (
    "add_newline",
    "search_env_replace",
    "search_env",
)


def add_newline(text: str, newline: Optional[str] = None) -> str:
    """Add newline to a text value.

    :param text: A text value that want to add newline.
    :param newline: A newline value that want to use.

    :rtype: str
    :returns: A newline added text.
    """
    nl: str = newline or "\n"
    return f"{text}{nl}" if not text.endswith(nl) else text


def search_env_replace(
    contents: str,
    *,
    raise_if_default_not_exists: bool = False,
    default: str = "null",
    escape: str = "ESC",
    caller: Callable[[str], str] = (lambda x: x),
) -> str:
    """Prepare content data before parse to any file parsing object.

    :param contents: A string content that want to format with env vars
    :type contents: str
    :param raise_if_default_not_exists: A flag that will allow this function
        raise the error when default of env var does not set from contents.
    :type raise_if_default_not_exists: bool(=False)
    :param default: a default value.
    :type default: str(='null')
    :param escape: a escape value that use for initial replace when found escape
        char on searching.
    :type escape: str(='ESC')
    :param caller: a prepare function that will execute before replace env var.
    :type caller: Callable[[str], str]

    :rtype: str
    :returns: A prepared content data.

    Examples:

        >>> import os
        >>> os.environ["NAME"] = 'foo'
        >>> search_env_replace("Hello ${NAME}")
        'Hello foo'
    """
    shifting: int = 0
    replaces: dict = {}
    replaces_esc: dict = {}
    for content in RegexConf.RE_ENV_SEARCH.finditer(contents):
        search: str = content.group(1)
        if not (_escaped := content.group("escaped")):
            var: str = content.group("braced")
            _braced_default: str = content.group("braced_default")
            if not _braced_default and raise_if_default_not_exists:
                raise ValueError(
                    f"Could not find default value for {var} in the contents"
                )
            elif not var:
                raise ValueError(
                    f"Value {search!r} in the contents file has something "
                    f"wrong with regular expression"
                )
            replaces[search] = caller(
                os.environ.get(var, _braced_default) or default
            )
        elif "$" in _escaped:
            span = content.span()
            search = f"${{{escape}{_escaped}}}"
            contents = (
                contents[: (span[0] + shifting)]
                + search
                + contents[(span[1] + shifting) :]
            )
            shifting += len(search) - (span[1] - span[0])
            replaces_esc[search] = "$"
    for _replace in sorted(replaces, reverse=True):
        contents = contents.replace(_replace, replaces[_replace])
    for _replace in sorted(replaces_esc, reverse=True):
        contents = contents.replace(_replace, replaces_esc[_replace])
    return contents


def search_env(
    contents: str,
    *,
    keep_newline: bool = False,
    default: Optional[str] = None,
) -> dict[str, str]:
    """Prepare content data from `.env` file before load to the OS environment
    variables.

    :param contents: A string content in the `.env` file
    :type contents: str
    :param keep_newline: A flag that filter out a newline
    :type keep_newline: bool(=False)
    :param default: A default value that use if it does not exists
    :type default: str | None(=None)

    :rtype: dict[str, str]
    :returns: A mapping of name and value of env variable

    Note:
        This function reference code from python-dotenv package. I will use this
    instead install this package. Because I want to enhance serialize step that
    fit with my package. (https://github.com/theskumar/python-dotenv)

    Examples:
        >>> search_env("Data='demo'\\nfoo=bar")
        {'Data': 'demo', 'foo': 'bar'}
        >>> search_env("Data='demo'\\n# foo=bar\\nhello=${Data}-2")
        {'Data': 'demo', 'hello': 'demo-2'}
    """
    _default: str = default or ""
    env: dict[str, str] = {}
    for content in RegexConf.RE_DOTENV.finditer(contents):
        name: str = content.group("name")

        # NOTE: Remove leading/trailing whitespace
        _value: str = (content.group("value") or "").strip()

        if not _value or _value in ("''", '""'):
            raise ValueError(
                f"Value {name!r} in `.env` file does not set value "
                f"of variable"
            )
        value: str = _value if keep_newline else "".join(_value.splitlines())
        quoted: Optional[str] = None

        # NOTE: Remove surrounding quotes
        if m2 := RegexConf.RE_ENV_VALUE_QUOTED.match(value):
            quoted: str = m2.group("quoted")
            value: str = m2.group("value")

        if quoted == "'":
            env[name] = value
            continue
        elif quoted == '"':
            # NOTE: Unescape all chars except $ so variables
            #   can be escaped properly
            value: str = RegexConf.RE_ENV_ESCAPE.sub(r"\1", value)

        # NOTE: Substitute variables in a value
        env[name] = __search_var(value, env, default=_default)
    return env


def __search_var(
    value: str,
    env: dict[str, str],
    *,
    default: Optional[str] = None,
) -> str:
    """Search variable on the string content.

    :param value: a string value that want to search env variable.
    :type value: str
    :param env: a pair of env values that keep in memory dict.
    :type env: dict[str, str]
    :param default: a default value if it does not found on env vars.
    :type default: str | None(=None)

    :rtype: str
    :returns: A searched value from env veriables.

    Examples:
        >>> __search_var("Test ${VAR}", {"VAR": "foo"})
        'Test foo'
        >>> __search_var("Test ${VAR2}", {"VAR": "foo"})
        'Test '
        >>> __search_var("Test ${VAR2}", {"VAR": "foo"}, default="bar")
        'Test bar'
        >>> import os
        >>> os.environ["VAR2"] = "baz"
        >>> __search_var("Test ${VAR2}", {"VAR": "foo"}, default="bar")
        'Test baz'
    """
    _default: str = default or ""
    for sub_content in RegexConf.RE_DOTENV_VAR.findall(value):
        replace: str = "".join(sub_content[1:-1])
        if sub_content[0] != "\\":
            # NOTE: Replace it with the value from the environment
            replace: str = env.get(
                sub_content[-1],
                os.environ.get(sub_content[-1], _default),
            )
        value: str = value.replace("".join(sub_content[:-1]), replace)
    return value


def reverse_readline(
    f: IO,
    buf_size: int = 8192,
) -> Iterator[AnyStr]:  # pragma: no cover
    """A generator that returns the lines of a file in reverse order

    Reference:
        - https://stackoverflow.com/questions/2301789/ -
            how-to-read-a-file-in-reverse-order
        - https://stackoverflow.com/a/23646049/8776239
    """
    segment: AnyStr | None = None
    offset: int = 0
    f.seek(0, os.SEEK_END)
    file_size = remaining_size = f.tell()

    while remaining_size > 0:
        offset = min(file_size, offset + buf_size)
        f.seek(file_size - offset)
        buffer: AnyStr = f.read(min(remaining_size, buf_size))
        remaining_size -= buf_size
        lines: list[AnyStr] = buffer.splitlines(True)

        # NOTE: the first line of the buffer is probably not a complete line so
        #   we'll save it and append it to the last line of the next buffer
        #   we read
        if segment is not None:

            # NOTE: if the previous chunk starts right from the beginning of
            #   line do not concat the segment to the last line of new chunk
            #   instead, yield the segment first
            if buffer[-1] == "\n":
                yield segment
            else:
                lines[-1] += segment
        segment: AnyStr = lines[0]
        for index in range(len(lines) - 1, 0, -1):
            if len(lines[index]):
                yield lines[index]

    # WARNING: Don't yield None if the file was empty
    if segment is not None:
        yield segment
