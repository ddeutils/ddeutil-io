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


class ConfigArgumentError(IOBaseError):
    """Error raise for arguments that passing to config object not valid."""


class StoreNotFound(IOBaseError):
    """Error raise for a method not found the config file or data."""


class StoreArgumentError(IOBaseError):
    """Error raise for arguments that passing to store object not valid."""


class RegisterArgumentError(IOBaseError):
    """Error raise for arguments that passing to register object not valid."""
