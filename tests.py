from typing import Any, Type

from pyhandling import times, by, then, operation_by, execute_operation, to, ArgumentPack
from pytest import mark, raises

from sculpting.annotations import attribute_getter, attribute_setter
from sculpting.core import *
from sculpting.tools import setting_of_attr, once


class AttributeKeeper:
    def __init__(self, **attributes):
        self.__dict__ = attributes


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


def test_once():
    runner = times(1)
    once_runner = once(runner)

    assert tuple(once_runner() for _ in range(8)) == (True, ) * 8
    assert tuple(runner() for _ in range(8)) == (False, True) * 4


@mark.parametrize(
    "obj, attribute_getter, result",
    [
        (AttributeKeeper(id=42), attribute_map_for('id').getter, 42),
        (
            AttributeKeeper(name="undefined"),
            read_only_attribute_map_as(getattr |by| 'name').getter,
            "undefined"
        ),
        (Sculpture(AttributeKeeper(next_node=None), next="next_node"), getattr |by| 'next', None),
        (Sculpture(AttributeKeeper(_protected=64), public="_protected"), getattr |by| "public", 64),
        (
            Sculpture(
                AttributeKeeper(value=4),
                modified_value=(getattr |by| "value") |then>> operation_by('**', 4)
            ),
            getattr |by| "modified_value",
            256
        ),
        (
            Sculpture(
                AttributeKeeper(username="Mario"),
                name=AttributeMap(
                    (getattr |by| "username") |then>> (execute_operation |to* ("Not ", '+')),
                    setting_of_attr("username")
                )
            ),
            getattr |by| "name",
            "Not Mario"
        ),
    ]
)
def test_attribute_getter(obj: object, attribute_getter: attribute_getter, result: Any):
    assert attribute_getter(obj) == result


@mark.parametrize(
    "obj, attribute_setter, input_attribute_value, result_attribute_name, result_attribute_value",
    [
        (AttributeKeeper(id=42), attribute_map_for('id').setter, 256, 'id', 256),
        (AttributeKeeper(), attribute_map_for('name').setter, "undefined", 'name', "undefined"),
        (AttributeKeeper(other=None), attribute_map_for("other").setter, None, "other", None),
        (
            Sculpture(AttributeKeeper(value=4), modified_value="value"),
            setting_of_attr("modified_value"),
            256,
            "modified_value",
            256,
        ),
        (
            Sculpture(
                AttributeKeeper(id=0),
                hash=AttributeMap(
                    getattr |by| 'id',
                    setting_of_attr('id', value_transformer=operation_by('*', 2))
                )
            ),
            setting_of_attr('hash'),
            32,
            'hash',
            64,
        )
    ]
)
def test_attribute_setter(
    obj: object,
    attribute_setter: attribute_setter,
    input_attribute_value: Any,
    result_attribute_name: str,
    result_attribute_value: Any
):
    attribute_setter(obj, input_attribute_value)

    assert getattr(obj, result_attribute_name) == result_attribute_value


@mark.parametrize(
    "obj, attribute_setter, input_attribute_value, raising_error_type",
    [
        (
            AttributeKeeper(),
            read_only_attribute_map_as(getattr |by| "non_existent_attribute").setter,
            "_",
            AttributeError
        ),
        (
            Sculpture(AttributeKeeper(user_id=4), id="user_id"),
            setting_of_attr("non_existent_attribute"),
            "_",
            AttributeError
        ),
        (
            Sculpture(AttributeKeeper(value=4), only_read_value=read_only_attribute_map_for("value")),
            setting_of_attr("only_read_value"),
            "_",
            AttributeError
        ),
    ]
)
def test_attribute_setter_error_raising(
    obj: object,
    attribute_setter: attribute_setter,
    input_attribute_value: Any,
    raising_error_type: Type[Exception],
):
    with raises(raising_error_type):
        attribute_setter(obj, input_attribute_value)


@mark.parametrize(
    "mapped, original_attribute_name, sculpture_argument_pack, virtual_attribute_name, new_attribute_value",
    [(AttributeKeeper(value=0), "value", ArgumentPack.of(modified_value="value"), "modified_value", 256)]
)
def test_sculpture_attribute_mapping(
    mapped: object,
    original_attribute_name: str,
    sculpture_argument_pack: ArgumentPack,
    virtual_attribute_name: str,
    new_attribute_value: Any
):
    sculpture = sculpture_argument_pack.call(Sculpture |to| mapped)

    setattr(sculpture, virtual_attribute_name, new_attribute_value)

    assert getattr(sculpture, virtual_attribute_name) == getattr(mapped, original_attribute_name)