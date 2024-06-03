# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

import logging
from collections.abc import Container
from typing import (
    AbstractSet,
    Any,
    Callable,
    TypeVar,
    Union,
)

from pydantic import BaseModel, ConfigDict, ValidationError
from typing_extensions import Self

T = TypeVar("T")
TModel = TypeVar("TModel", bound=BaseModel)

AbstractSetOrDict = Union[
    AbstractSet[Union[int, str]],
    dict[Union[int, str], Any],
]


class __BaseModel(BaseModel):
    # NOTE:
    #   This config allow to validate before assign new data to any field
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        populate_by_name=True,
    )


class BaseUpdatableModel(__BaseModel):
    """Base Model that was implemented updatable method and properties."""

    @classmethod
    def get_field_names(cls, alias=False):
        return list(cls.model_json_schema(alias).get("properties").keys())

    @classmethod
    def get_properties(cls) -> list:
        """Return list of properties of this model"""
        return [
            prop
            for prop in cls.__dict__
            if isinstance(cls.__dict__[prop], property)
        ]

    def dict(
        self,
        *,
        include: AbstractSetOrDict = None,
        exclude: AbstractSetOrDict = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """Override the dict function to include our properties
        docs: https://github.com/pydantic/pydantic/issues/935
        """
        attribs = super().model_dump(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            **kwargs,
        )
        props: list = self.get_properties()

        # Include and exclude properties
        if include:
            props: list = [prop for prop in props if prop in include]
        if exclude:
            props: list = [prop for prop in props if prop not in exclude]

        # Update the attribute dict with the properties
        if props:
            attribs.update({prop: getattr(self, prop) for prop in props})
        return attribs

    def update(self, data: dict) -> Self:
        """Updatable method for update data to existing model data.
        docs: https://github.com/pydantic/pydantic/discussions/3139
        """
        update = self.dict()
        update.update(data)
        for k, v in (
            self.model_validate(update).dict(exclude_defaults=True).items()
        ):
            logging.debug(
                f"Updating value '{k}' from '{getattr(self, k, None)}' to '{v}'"
            )
            setattr(self, k, v)
        return self


def invalid_to_none(v: Any, handler: Callable[[Any], Any]) -> Any:
    """Invalid to None value function.

    Examples:
        >>> from typing import Annotated, Optional
        >>> from pydantic import WrapValidator
        >>> class Foo(BaseModel):
        ...     age: Annotated[Optional[int], WrapValidator(invalid_to_none)]
        ...     name: Optional[str]
        >>> Foo(age="invalid", name="Jim").model_dump()
        {'age': None, 'name': 'Jim'}

    Examples:
        We able to implement this to all fields on any sub-classes.
        >>> from typing import get_args, get_origin
        >>> class CustomBaseModel(BaseModel):
        ...     def __init_subclass__(cls, **kwargs: Any) -> None:
        ...         for name, annotation in cls.__annotations__.items():
        ...             # exclude protected/private attributes
        ...             if name.startswith("_"):
        ...                 continue
        ...             validator = WrapValidator(invalid_to_none)
        ...             if get_origin(annotation) is Annotated:
        ...                 cls.__annotations__[name] = Annotated[
        ...                     (*get_args(annotation), ),
        ...                     validator,
        ...                 ]
        ...             else:
        ...                 cls.__annotations__[name] = Annotated[
        ...                     annotation, validator
        ...                 ]
        >>> class Foo(CustomBaseModel):
        ...     age: Optional[int]
        ...     name: Optional[str]
        >>> Foo(age="invalid", name="Jim").model_dump()
        {'age': None, 'name': 'Jim'}

    Reference:
        *   https://stackoverflow.com/questions/76669927/ -
            pydantic-how-to-ignore-invalid-values-when-creating-model-instance
    """
    try:
        return handler(v)
    except ValidationError:
        return None


def _remove_validators(validators: T, names: Container[str]) -> T:
    return [v for v in validators if v.__name__ not in names]


def remove_validators(*names: str) -> Callable[[type[TModel]], type[TModel]]:
    def decorator(model: type[TModel]) -> type[TModel]:
        for name in names:
            if not getattr(model, name):
                raise ValueError(
                    f"{model.__name__} does not implement {name} validator"
                )
            model.__pydantic_decorators__.field_validators.pop(name)
        model.model_rebuild()
        return model

    return decorator
