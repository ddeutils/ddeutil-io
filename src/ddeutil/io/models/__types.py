# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

from typing import Annotated
from urllib.parse import unquote_plus

from pydantic import EncodedStr, EncoderProtocol
from pydantic.networks import UrlConstraints
from pydantic_core import Url

CustomUrl = Annotated[
    Url,
    UrlConstraints(
        host_required=True,
        default_port=1234,
    ),
]

LocalUrl = Annotated[
    Url,
    UrlConstraints(
        default_host="127.0.0.1",
        default_port=None,
    ),
]


class UnquoteEncoder(EncoderProtocol):
    @classmethod
    def decode(cls, data: bytes) -> bytes:
        # NOTE:
        #   We have to use unquote rather than unquote_plus because only unquote
        #   can work with bytes objects. This may be a limitation if your URL
        #   string contains encoded spaces.
        return str.encode(unquote_plus(data))


EncodedStr = Annotated[str, EncodedStr(encoder=UnquoteEncoder)]
