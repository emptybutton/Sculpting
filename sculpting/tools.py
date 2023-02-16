from typing import Any

from pyhandling import return_
from pyhandling.annotations import handler

from sculpting.annotations import attribute_setter


def setting_of_attr(attribute_name: str, *, value_transformer: handler = return_) -> attribute_setter:
    def wrapper(object_: object, value: Any) -> Any:
        return setattr(object_, attribute_name, value_transformer(value))
    return wrapper