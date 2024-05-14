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
    """Core Configuration Model"""

    # Normal regular expression for the secret value.
    # ---
    # [\"\']?                             # single or double quoted value
    # (?P<search>@secrets{                # search string for replacement
    #     (?P<braced>.*?)                 # value if use braced {}
    #     (?::(?P<braced_default>.*?))?   # value default with sep :
    # })                                  # end with }
    # [\"\']?                             # single or double-quoted value
    #
    # Note: For secrets grouping level.
    # ---
    # [\"\']?                             # single or double quoted value
    # (?P<search>@secrets                 # search string for replacement
    # (?P<group>(\.\w+)*)?{               # search groups
    #     (?P<braced>.*?)                 # value if use braced {}
    #     (:(?P<braced_default>.*?))?     # value default with sep :
    # })                                  # end with }
    # [\"\']?                             # single or double-quoted value
    RE_SECRETS: Pattern = re.compile(
        r"""
        [\"\']?                             # single or double quoted value
        (?P<search>@secrets{                # search string for replacement
            (?P<braced>.*?)                 # value if use braced {}
            (?::(?P<braced_default>.*?))?   # value default with sep :
        })                                  # end with }
        [\"\']?                             # single or double-quoted value
    """,
        MULTILINE | UNICODE | IGNORECASE | VERBOSE,
    )

    # Normal regular expression for the function value.
    # ---
    # [\"\']?                             # single or double quoted value
    # (?P<search>@function{               # search string for replacement
    #     (?P<function>[\w.].*?)          # called function
    #     (?::(?P<arguments>.*?))?        # arguments for calling function
    # })                                  # end with }
    # [\"\']?                             # single or double-quoted value
    RE_FUNCTION: Pattern = re.compile(
        r"""
        [\"\']?                             # single or double quoted value
        (?P<search>@function{               # search string for replacement
            (?P<function>[\w.].*?)          # called function
            (?::(?P<arguments>.*?))?        # arguments for calling function
        })                                  # end with }
        [\"\']?                             # single or double-quoted value
    """,
        MULTILINE | UNICODE | IGNORECASE | VERBOSE,
    )

    # Normal regular expression for dotenv variable
    # ---
    # (\\)?(\$)({?([A-Z0-9_]+)}?)
    RE_DOTENV_VAR: Pattern = re.compile(
        r"""
        (\\)?               # is it escaped with a backslash?
        (\$)                # literal $
        (                   # collect braces with var for sub
            {?              # allow brace wrapping
            ([A-Z0-9_]+)    # match the variable
            }?              # closing brace
        )                   # braces end
    """,
        IGNORECASE | VERBOSE,
    )

    # Normal regular expression for dotenv
    # ---
    # ^\s*(?:export\s+)?(?P<name>[\w.-]+)(?:\s*=\s*?|:\s+?)(?P<value>\s*\'(?:\\'|[^'])*\'|\s*\"(?:\\"|[^"])*\"
    # |\s*`(?:\\`|[^`])*`|[^#\r\n]+)?\s*$
    RE_DOTENV: Pattern = re.compile(
        r"""
        ^\s*(?:export\s+)?      # optional export
        (?P<name>[\w.-]+)       # name of key
        (?:\s*=\s*?|:\s+?)      # separator `=` or `:`
        (?P<value>
            \s*\'(?:\\'|[^'])*\'    # single quoted value
            |
            \s*\"(?:\\"|[^"])*\"    # double quoted value
            |
            \s*`(?:\\`|[^`])*`      # backticks value
            |
            [^#\r\n]+           # unquoted value
        )?\s*                   # optional space
        (?:[^\S\r\n]*\#[^\r\n]*)?
        $
    """,
        MULTILINE | VERBOSE,
    )

    # Note
    # ---
    # (\s|^)#.*
    RE_YAML_COMMENT: Pattern = re.compile(
        r"(\s|^)#.*",
        MULTILINE | UNICODE | IGNORECASE,
    )

    # Note
    # ---
    # [\"\']?(\$(?:(?P<escaped>\$|\d+)|({(?P<braced>.*?)(:(?P<braced_default>.*?))?})))[\"\']?
    RE_ENV_SEARCH: Pattern = re.compile(
        r"""
        [\"\']?                             # single or double quoted value
        (\$(?:                              # start with non-capturing group
            (?P<escaped>\$|\d+)             # escape $ or number like $1
            |
            (\{
                (?P<braced>.*?)             # value if use braced {}
                (:(?P<braced_default>.*?))? # value default with sep :
            })
        ))
        [\"\']?                             # single or double quoted value
    """,
        MULTILINE | UNICODE | IGNORECASE | VERBOSE,
    )

    RE_ENV_VALUE_QUOTED: Pattern = re.compile(
        r"""
        ^
            (?P<quoted>[\'\"`])
            (?P<value>.*)\1
        $
    """,
        MULTILINE | VERBOSE,
    )

    RE_ENV_ESCAPE: Pattern = re.compile(r"\\([^$])")
