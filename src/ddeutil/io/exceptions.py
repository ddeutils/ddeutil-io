# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations


class BaseError(Exception):
    """Base Error Object that use for catch any errors statement of all steps in
    this ``/src`` directory.
    """


class IOBaseError(BaseError):
    """Core Base Error object"""


class StoreNotFound(IOBaseError):
    """Error raise for a method not found the config file or data."""


class StoreArgumentError(IOBaseError):  # pragma: no cover
    """Error raise for a wrong configuration argument."""

    def __init__(self, argument: str | tuple, message: str) -> None:
        """Main Initialization that merge the argument and message input values
        with specific content message together like

            `__class__` with `argument`, `message`

        :param argument: Union[str, tuple]
        :param message: str
        """
        if isinstance(argument, tuple):
            _last_arg: str = str(argument[-1])
            _argument: str = (
                (
                    ", ".join([f"{_!r}" for _ in argument[:-1]])
                    + f", and {_last_arg!r}"
                )
                if len(argument) > 1
                else f"{_last_arg!r}"
            )
        else:
            _argument: str = f"{argument!r}"
        super().__init__(f"with {_argument}, {message}")
