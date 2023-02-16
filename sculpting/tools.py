from typing import Any

from pyhandling import return_
from pyhandling.annotations import handler

from sculpting.annotations import attribute_setter


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