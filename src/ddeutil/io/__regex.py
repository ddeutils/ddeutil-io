# -------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# --------------------------------------------------------------------------
import re
from re import (
    IGNORECASE,
    MULTILINE,
    UNICODE,
    VERBOSE,
    Pattern,
)


class RegexConf:
    """Regular expression configuration object for this package."""

    # NOTE: Normal regular expression for the secret value.
    # ---
    # [\"\']?                             # single or double-quoted value
    # (?P<search>@secrets{                # search string for replacement
    #     (?P<braced>.*?)                 # value if use braced {}
    #     (?::(?P<braced_default>.*?))?   # value default with sep :
    # })                                  # end with }
    # [\"\']?                             # single or double-quoted value
    #
    # NOTE: For secrets grouping level.
    # ---
    # [\"\']?                             # single or double-quoted value
    # (?P<search>@secrets                 # search string for replacement
    # (?P<group>(\.\w+)*)?{               # search groups
    #     (?P<braced>.*?)                 # value if use braced {}
    #     (:(?P<braced_default>.*?))?     # value default with sep :
    # })                                  # end with }
    # [\"\']?                             # single or double-quoted value
    __re_secrets: str = r"""
        [\"\']?                             # single or double quoted value
        (?P<search>@secrets{                # search string for replacement
            (?P<braced>.*?)                 # value if use braced {}
            (?::(?P<braced_default>.*?))?   # value default with sep :
        })                                  # end with }
        [\"\']?                             # single or double-quoted value
    """
    RE_SECRETS: Pattern = re.compile(
        __re_secrets, MULTILINE | UNICODE | IGNORECASE | VERBOSE
    )

    # NOTE: Normal regular expression for the function value.
    # ---
    # [\"\']?                             # single or double quoted value
    # (?P<search>@function{               # search string for replacement
    #     (?P<function>[\w.].*?)          # called function
    #     (?::(?P<arguments>.*?))?        # arguments for calling function
    # })                                  # end with }
    # [\"\']?                             # single or double-quoted value
    __re_function: str = r"""
        [\"\']?                             # single or double quoted value
        (?P<search>@function{               # search string for replacement
            (?P<function>[\w.].*?)          # called function
            (?::(?P<arguments>.*?))?        # arguments for calling function
        })                                  # end with }
        [\"\']?                             # single or double-quoted value
    """
    RE_FUNCTION: Pattern = re.compile(
        __re_function, MULTILINE | UNICODE | IGNORECASE | VERBOSE
    )

    # NOTE: Normal regular expression for dotenv variable
    # ---
    # (\\)?(\$)({?([A-Z0-9_]+)}?)
    __re_dotenv_var: str = r"""
        (\\)?               # is it escaped with a backslash?
        (\$)                # literal $
        (                   # collect braces with var for sub
            {?              # allow brace wrapping
            ([A-Z0-9_]+)    # match the variable
            }?              # closing brace
        )                   # braces end
    """
    RE_DOTENV_VAR: Pattern = re.compile(__re_dotenv_var, IGNORECASE | VERBOSE)

    # NOTE: Normal regular expression for dotenv
    # ---
    # ^\s*(?:export\s+)?(?P<name>[\w.-]+)(?:\s*=\s*?|:\s+?)(?P<value>\s*\'(?:\\'|[^'])*\'|\s*\"(?:\\"|[^"])*\"
    # |\s*`(?:\\`|[^`])*`|[^#\r\n]+)?\s*$
    __re_dotenv: str = r"""
        ^\s*(?:export\s+)?          # optional export
        (?P<name>[\w.-]+)           # name of key
        (?:\s*=\s*?|:\s+?)          # separator `=` or `:`
        (?P<value>
            \s*\'(?:\\'|[^'])*\'    # single quoted value
            |
            \s*\"(?:\\"|[^"])*\"    # double quoted value
            |
            \s*`(?:\\`|[^`])*`      # backticks value
            |
            [^#\r\n]+               # unquoted value
        )?\s*                       # optional space
        (?:[^\S\r\n]*\#[^\r\n]*)?
        $
    """
    RE_DOTENV: Pattern = re.compile(__re_dotenv, MULTILINE | VERBOSE)

    # NOTE:
    # ---
    # (\s|^)#.*
    __re_yaml_comment: str = r"(\s|^)#.*"
    RE_YAML_COMMENT: Pattern = re.compile(
        __re_yaml_comment, MULTILINE | UNICODE | IGNORECASE
    )

    # NOTE:
    # ---
    # [\"\']?(\$(?:(?P<escaped>\$|\d+)|({(?P<braced>.*?)(:(?P<braced_default>.*?))?})))[\"\']?
    #
    # NOTE: If you want to catch only string not number:
    #   ... `([a-zA-Z0-9_.\s'\"\[\]\(\)]+?)`
    __re_env_search: str = r"""
        [\"\']?                             # single or double quoted value
        (\$(?:                              # start with non-capturing group
            (?P<escaped>\$|\d+)             # escape $ or number like $1
            |
            (\{
                \s?
                (?P<braced>([^{}]*?))       # value in braced {} not contain {}
                (:                          # : seperator for default
                    (?P<braced_default>[^{}]*?) # value default with sep :
                )?
                \s?
            })
        ))
        [\"\']?                             # single or double quoted value
    """
    RE_ENV_SEARCH: Pattern = re.compile(
        __re_env_search, MULTILINE | UNICODE | IGNORECASE | VERBOSE
    )

    __re_env_value_quoted: str = r"""
        ^
            (?P<quoted>[\'\"`])     # single or double quoted value
            (?P<value>.*)\1
        $
    """
    RE_ENV_VALUE_QUOTED: Pattern = re.compile(
        __re_env_value_quoted,
        MULTILINE | UNICODE | VERBOSE,
    )

    # NOTE:
    __re_env_escape: str = r"\\([^$])"
    RE_ENV_ESCAPE: Pattern = re.compile(__re_env_escape, MULTILINE | UNICODE)
