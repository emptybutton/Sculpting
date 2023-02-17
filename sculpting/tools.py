from typing import Any, Callable

from pyhandling import return_, nothing
from pyhandling.annotations import handler

from sculpting.annotations import attribute_setter


__all__ = ("setting_of", "once")


def setting_of_attr(attribute_name: str, *, value_transformer: handler = return_) -> attribute_setter:
    """
    Function to get a function to change an attribute of a given name.
    Delegates a possible transformation of the new value of the attribute to value_transformer.
    """

    def wrapper(object_: object, value: Any) -> Any:
        """
        Function created as a result of calling setting_of_attr.
        See setting_of_attr for more info.
        """

        return setattr(object_, attribute_name, value_transformer(value))

    return wrapper


class once:
    """
    Decorator for a function that causes it to execute only once, after which it
    always returns its result.
    """

    __result = nothing

    def __init__(self, func: Callable):
        self._func = func

    def __call__(self, *args, **kwargs) -> Any:
        if self.__result is nothing:
            self.__result = self._func(*args, **kwargs)

        return self.__result