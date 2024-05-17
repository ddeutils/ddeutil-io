from __future__ import annotations

import os
from typing import (
    Callable,
    Optional,
)

try:
    from .__regex import RegexConf
except ImportError:
    from __regex import RegexConf


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
                    f"Could not find default value for {var} "
                    f"in `.yaml` file"
                )
            elif not var:
                raise ValueError(
                    f"Value {search!r} in `.yaml` file has something wrong "
                    f"with regular expression"
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
    default: str | None = None,
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

        # Remove leading/trailing whitespace
        _value: str = (content.group("value") or "").strip()

        if not _value:
            raise ValueError(
                f"Value {name:!r} in `.env` file does not set value "
                f"of variable"
            )
        value: str = _value if keep_newline else "".join(_value.splitlines())
        quoted: Optional[str] = None

        # Remove surrounding quotes
        if m2 := RegexConf.RE_ENV_VALUE_QUOTED.match(value):
            quoted: str = m2.group("quoted")
            value: str = m2.group("value")

        if quoted == "'":
            env[name] = value
            continue
        elif quoted == '"':
            # Unescape all chars except $ so variables
            # can be escaped properly
            value: str = RegexConf.RE_ENV_ESCAPE.sub(r"\1", value)

        # Substitute variables in a value
        env[name] = __search_var(value, env, default=_default)
    return env


def __search_var(
    value: str,
    env: dict[str, str],
    *,
    default: str | None = None,
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
            # Replace it with the value from the environment
            replace: str = env.get(
                sub_content[-1],
                os.environ.get(sub_content[-1], _default),
            )
        value: str = value.replace("".join(sub_content[:-1]), replace)
    return value
