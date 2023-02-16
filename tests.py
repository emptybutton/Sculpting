from typing import Any, Type

from pytest import mark, raises

from sculpting.tools import setting_of_attr


class AttributeKeeper:
    def __init__(self, **attributes):
        self.__dict__ = dict(**attributes)


@mark.parametrize(
    "attribute_name, attribute_value",
    [
        ("name", "undefined"),
        ("id", 42),
        ("", None),
    ]
)
def test_setting_of_attr(attribute_name: str, attribute_value: Any):
    obj = AttributeKeeper()

    setting_of_attr(attribute_name)(obj, attribute_value)

    assert getattr(obj, attribute_name) == attribute_value


