from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Final, Tuple, Iterable, Any, Callable, TypeVar, Generic, Optional, Union

from pyannotating import AnnotationTemplate, input_annotation
from pyhandling import returnly, by, documenting_by, mergely, take, close, post_partial, event_as, raise_, then, to, next_action_decorator_of
from pyhandling.annotations import dirty, reformer_of, handler

from sculpting.annotations import attribute_getter_of, attribute_setter_of, attribute_getter
from sculpting.tools import setting_of_attr


__all__ = (
    "Sculpture",
    "AttributeMap",
    "attribute_map_for",
    "read_only_attribute_map_as",
    "read_only_attribute_map_for",
    "changing_attribute_map_for"
)


_MAGIC_METHODS_NAMES: Final[Tuple[str]] = (
    "__pos__", "__neg__", "__abs__", "__invert__", "__round__", "__floor__",
    "__ceil__", "__iadd__", "__isub__", "__imul__", "__ifloordiv__", "__idiv__",
    "__itruediv__", "__imod__", "__ipow__", "__ilshift__", "__irshift__",
    "__iand__", "__ior__", "__ixor__", "__int__", "__float__", "__complex__",
    "__oct__", "__hex__", "__index__", "__trunc__", "__str__", "__repr__",
    "__unicode__", "__format__", "__hash__", "__nonzero__", "__add__", "__sub__",
    "__mul__", "__floordiv__", "__truediv__", "__mod__", "__pow__", "__lt__",
    "__le__", "__eq__", "__ne__", "__ge__"
)


def _method_proxies_to_attribute(attribute_name: str, method_names: Iterable[str]) -> dirty[reformer_of[type]]:
    """
    Function that creates a class decorator for which methods will be created by
    proxy, the call of which is delegated to an attribute of an instance of the
    input class.
    """

    @returnly
    def decorator(type_: type, attribute_name: str) -> type:
        """
        Class decorator created as a result of calling
        _method_proxies_to_attribute.

        See _method_proxies_to_attribute for more info.
        """

        if attribute_name[:2] == '__':
            attribute_name = f"_{type_.__name__}{attribute_name}"

        for method_name in method_names:
            setattr(
                type_,
                method_name,
                _proxy_method_to_attribute(attribute_name, method_name, type_)
            )

    return decorator |by| attribute_name


def _proxy_method_to_attribute(attribute_name: str, method_name: str, type_: type) -> Callable[[object, ...], Any]:
    """Function to create a proxy method whose call is delegated to an attribute."""

    def method_wrapper(instance: object, *args, **kwargs) -> Any:
        """
        Method created as a result of calling _proxy_method_to_attribute.
        See _proxy_method_to_attribute for more info.
        """

        return getattr(getattr(instance, attribute_name), method_name)(*args, **kwargs)

    return method_wrapper


def _dict_value_map(value_transformer: handler, dict_: dict) -> dict:
    """
    Map function to create a similarity to the input dictionary, but with
    transformed values.
    """

    return {
        _: value_transformer(value)
        for _, value in dict_.items()
    }


AttributeOwnerT = TypeVar("AttributeOwnerT")


@dataclass(frozen=True)
class AttributeMap(Generic[AttributeOwnerT]):
    """
    Dataclass that represents some real or virtual attribute.
    Contains functions to interact with it.
    """

    getter: attribute_getter_of[AttributeOwnerT]
    setter: attribute_setter_of[AttributeOwnerT]


attribute_map_for: Callable[[str], AttributeMap] = documenting_by(
    """Constructor function for an AttributeMap of a real attribute."""
)(
    mergely(
        take(AttributeMap),
        close(getattr, closer=post_partial),
        setting_of_attr
    )
)


read_only_attribute_map_as: Callable[[attribute_getter], AttributeMap] = documenting_by(
    """Constructor function for an AttributeMap of a read-only attribute."""
)(
    AttributeMap |by| event_as(raise_, AttributeError("Attribute cannot be set"))
)


read_only_attribute_map_for: Callable[[str], AttributeMap] = documenting_by(
    """Constructor function for an AttributeMap of a read-only real attribute."""
)(
    close(getattr, closer=post_partial) |then>> read_only_attribute_map_as
)


def changing_attribute_map_for(attribute_name: str, changer: reformer_of[Any]) -> AttributeMap:
    """Function to create a map for an attribute whose value will change when set."""

    return AttributeMap(
        getattr |by| attribute_name,
        setting_of_attr(attribute_name, value_transformer=changer)
    )


_attribute_resource_for = (AnnotationTemplate |to| Union)([
    str,
    AnnotationTemplate(AttributeMap, [input_annotation]),
    AnnotationTemplate(attribute_getter_of, [input_annotation])
])


def _attribute_map_from(
    attribute_resource: _attribute_resource_for[AttributeOwnerT]
) -> AttributeMap[AttributeOwnerT]:
    """
    Function to cast an unstructured attribute resource into a map of that
    attribute.
    """

    if isinstance(attribute_resource, AttributeMap):
        return attribute_resource
    elif callable(attribute_resource):
        return read_only_attribute_map_as(attribute_resource)
    else:
        return attribute_map_for(attribute_resource)


class _DynamicAttributeKepper(Generic[AttributeOwnerT], ABC):
    def __init__(
        self,
        *,
        _default_attribute_resource_factory: Optional[Callable[[str], _attribute_resource_for[AttributeOwnerT]]] = None,
        **attribute_resource_by_attribute_name: _attribute_resource_for[AttributeOwnerT],
    ):
        self._attribute_map_by_attribute_name = _dict_value_map(
            _attribute_map_from,
            attribute_resource_by_attribute_name
        )

        self._default_attribute_map_for = (
            _default_attribute_resource_factory |then>> _attribute_map_from
            if _default_attribute_resource_factory is not None
            else "Attribute \"{}\" is not allowed in {{}}".format |then>> mergely(
                take(AttributeMap),
                (getattr |by| "format") |then>> next_action_decorator_of(AttributeError |then>> raise_),
                close(lambda template, obj, _: raise_(AttributeError(template.format(obj.__repr__()))))
            )
        )

    def __getattr__(self, attribute_name: str) -> Any:
        return (
            object.__getattribute__(self, attribute_name)
            if attribute_name[:1] == '_'
            else self._attribute_value_for(
                attribute_name,
                self.__attribute_map_for(attribute_name)
            )
        )

    def __setattr__(self, attribute_name: str, attribute_value: Any) -> Any:
        return (
            super().__setattr__(attribute_name, attribute_value)
            if attribute_name[:1] == '_'
            else self._set_attribute_value_for(
                attribute_name,
                attribute_value,
                self.__attribute_map_for(attribute_name)
            )
        )

    @abstractmethod
    def _attribute_value_for(self, attribute_name: str, attribute_map: AttributeMap[AttributeOwnerT]) -> Any:
        pass

    @abstractmethod
    def _set_attribute_value_for(self, attribute_name: str, attribute_value: Any, attribute_map: AttributeMap[AttributeOwnerT]) -> Any:
        pass

    def __attribute_map_for(self, attribute_name: str) -> AttributeMap[AttributeOwnerT]:
        return (
            self._attribute_map_by_attribute_name[attribute_name]
            if attribute_name in self._attribute_map_by_attribute_name.keys()
            else self._default_attribute_map_for(attribute_name)
        )


OriginalT = TypeVar("OriginalT")


@_method_proxies_to_attribute("__original", set(_MAGIC_METHODS_NAMES) - {"__repr__", "__str__"})
class Sculpture(_DynamicAttributeKepper, Generic[OriginalT]):
    """
    Virtual attribute mapping class for a real object.

    Virtual attribute names are given keyword arguments as keys.
    Values can be either the name of a real attribute of the original object, an
    AttributeMap, or a function to get the value of this attribute from the
    original object (in which case the attribute cannot be changed).
    """

    def __init__(
        self,
        original: OriginalT,
        *,
        default_attribute_resource_factory: Optional[_attribute_resource_for[OriginalT]] = None,
        **attribute_resource_by_attribute_name: _attribute_resource_for[OriginalT],
    ):
        super().__init__(
            default_attribute_resource_factory=default_attribute_resource_factory,
            **attribute_resource_by_attribute_name
        )

        self.__original = original

    def __repr__(self) -> str:
        return f"Sculpture from {self.__original}"

    def _attribute_value_for(self, attribute_name: str, attribute_map: AttributeMap[OriginalT]) -> Any:
        return attribute_map.getter(self.__original)

    def _set_attribute_value_for(self, attribute_name: str, attribute_value: Any, attribute_map: AttributeMap[OriginalT]) -> Any:
        return attribute_map.setter(self.__original, attribute_value)