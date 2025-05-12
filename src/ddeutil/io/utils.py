# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

import os
import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import IO, AnyStr, Callable, Optional, TypeVar, Union

from ddeutil.core import convert, import_string

from .__regex import RegexConf

T = TypeVar("T")


def rm(
    path: Union[str, Path],
    is_dir: bool = False,
    force_raise: bool = True,
) -> None:  # pragma: no cov
    """Remove a file or dir from an input path.

    :param path: A path of file or dir that want to remove.
    :param is_dir: A flag that tell this input path is dir or not.
    :param force_raise: A flag that disable raise error if it not remove.
    """
    path: Path = Path(path) if isinstance(path, str) else path
    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)
    elif os.path.isdir(path) and is_dir:
        shutil.rmtree(path)
    else:
        if force_raise:
            raise ValueError(
                f"Path {path!r} is not a file{' or dir' if is_dir else ''}."
            )


def touch(path: Union[str, Path], times=None) -> None:  # pragma: no cov
    """Create an empty file with specific name and modified time of path it an
    input times was set.

    :param path: A file path that want to create.
    :param times: A time that want to adjust modified time.
    """
    file_handle = open(path, mode="a")
    try:
        os.utime(path, times)
    finally:
        file_handle.close()


def template_secret(value: T, secrets: dict[str, str]) -> T:
    """Map the secret value to an any input data.

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
    :type raise_if_default_not_exists: bool (False)
    :param default: a default value.
    :type default: str (Default is 'null')
    :param escape: An escape value that use for initial replace when found escape
        char on searching.
    :type escape: str (Default is 'ESC')
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
        >>> search_env(
        ...     "Data='demo'\\n"
        ...     "foo=bar"
        ... )
        {'Data': 'demo', 'foo': 'bar'}
        >>> search_env(
        ...     "Data='demo'\\n"
        ...     "# foo=bar\\n"
        ...     "hello=${Data}-2"
        ... )
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
) -> Iterator[AnyStr]:  # pragma: no cov
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
