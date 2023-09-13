import os
from typing import Dict, Optional

from .settings import SettingRegex


def add_newline(text: str, newline: Optional[str] = None) -> str:
    nl: str = newline or "\n"
    return f"{text}{nl}" if not text.endswith(nl) else text


def search_env_replace(
    contents: str,
    *,
    raise_if_default_not_exists: bool = False,
    default_value: str = "N/A",
    escape_replaced: str = "ESC",
) -> str:
    """Prepare content data before parse to any file loading method"""
    shifting: int = 0
    replaces: dict = {}
    replaces_esc: dict = {}
    for content in SettingRegex.RE_ENV_SEARCH.finditer(contents):
        search: str = content.group(1)
        if not (escaped := content.group("escaped")):
            variable: str = content.group("braced")
            default: str = content.group("braced_default")
            if not default and raise_if_default_not_exists:
                raise ValueError(
                    f"Could not find default value for {variable} "
                    f"in `.yaml` file"
                )
            elif not variable:
                raise ValueError(
                    f"Value {search!r} in `.yaml` file has something wrong "
                    f"with regular expression"
                )
            replaces[search] = (
                os.environ.get(variable, default) or default_value
            )
        elif "$" in escaped:
            span = content.span()
            search = f"${{{escape_replaced}{escaped}}}"
            contents = (
                contents[: span[0] + shifting]
                + search
                + contents[span[1] + shifting :]
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
) -> Dict[str, str]:
    """Prepare content data from .env string format before load
    to the OS environment.

    :ref:
        - python-dotenv
            ref: https://github.com/theskumar/python-dotenv
    """
    _default: str = default or ""
    env: Dict[str, str] = {}
    for content in SettingRegex.RE_DOTENV.finditer(contents):
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
        if m2 := SettingRegex.RE_ENV_VALUE_QUOTED.match(value):
            quoted: str = m2.group("quoted")
            value: str = m2.group("value")

        if quoted == "'":
            env[name] = value
            continue
        elif quoted == '"':
            # Unescape all chars except $ so variables
            # can be escaped properly
            value: str = SettingRegex.RE_ENV_ESCAPE.sub(r"\1", value)

        # Substitute variables in a value
        for sub_content in SettingRegex.RE_DOTENV_VAR.findall(value):
            replace: str = "".join(sub_content[1:-1])
            if sub_content[0] != "\\":
                # Replace it with the value from the environment
                replace: str = env.get(
                    sub_content[-1],
                    os.environ.get(sub_content[-1], _default),
                )
            value: str = value.replace("".join(sub_content[:-1]), replace)
        env[name] = value
    return env
