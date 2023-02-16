from dataclasses import dataclass
from typing import Final, Tuple, Iterable, Any, Callable, TypeVar, Generic

from pyhandling import returnly, by, mergely, take, close, post_partial, event_as, raise_
from pyhandling.annotations import dirty, reformer_of, handler

from sculpting.annotations import attribute_getter_of, attribute_setter_of, attribute_getter, attribute_setter
from sculpting.tools import setting_of_attr


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


property_attribute_map_as: Callable[[attribute_getter], AttributeMap] = documenting_by(
    """Constructor function for an AttributeMap of a read-only attribute."""
)(
    AttributeMap |by| event_as(raise_, AttributeError("Attribute cannot be set"))
)


MappedT = TypeVar("mapped")


@_method_proxies_to_attribute("__mapped", set(_MAGIC_METHODS_NAMES) - {"__repr__", "__str__"})
class Sculpture(Generic[MappedT]):
    """
    Virtual attribute mapping class for a real object.

    Virtual attributes are given keyword arguments as keys.
    Values can be either the name of a real attribute of the original object, an
    AttributeMap, or a function to get the value of this attribute from the
    original object (in which case the attribute cannot be changed).
    """

    def __init__(
        self,
        mapped: MappedT,
        **attribute_map_by_virtual_attribute_name: str | AttributeMap[MappedT] | attribute_getter_of[MappedT]
    ):
        self.__mapped = mapped
        self.__attribute_map_by_virtual_attribute_name = _dict_value_map(
            self.__convert_attribute_map_resource_to_attribute_map,
            attribute_map_by_virtual_attribute_name
        )

    def __repr__(self) -> str:
        return f"Sculpture from {self.__mapped}"

    def __getattr__(self, attribute_name: str) -> Any:
        if attribute_name[:1] == '_':
            return object.__getattribute__(self, attribute_name)

        self.__validate_availability_for(attribute_name)

        return self.__attribute_map_by_virtual_attribute_name[attribute_name].getter(
            self.__mapped
        )

    def __setattr__(self, attribute_name: str, attribute_value: Any) -> Any:
        if attribute_name[:1] == '_':
            super().__setattr__(attribute_name, attribute_value)
            return

        self.__validate_availability_for(attribute_name)

        return self.__attribute_map_by_virtual_attribute_name[attribute_name].setter(
            self.__mapped,
            attribute_value
        )

    def __validate_availability_for(self, attribute_name: str) -> None:
        """
        Method of validation and possible subsequent error about the absence
        of such a virtual attribute.
        """

        if attribute_name not in self.__attribute_map_by_virtual_attribute_name.keys():
            raise AttributeError(
                f"Attribute \"{attribute_name}\" is not allowed in {self.__repr__()}"
            )

    @staticmethod
    def __convert_attribute_map_resource_to_attribute_map(
        attribute_map_resource: str | AttributeMap[MappedT] | attribute_getter_of[MappedT]
    ) -> AttributeMap[MappedT]:
        """
        Function to cast an unstructured virtual attribute resource into a map
        of that virtual attribute.

        Implements casting according to the rules defined in the Sculpture
        documentation.
        """

        if isinstance(attribute_map_resource, AttributeMap):
            return attribute_map_resource
        elif callable(attribute_map_resource):
            return property_attribute_map_as(attribute_map_resource)
        else:
            return attribute_map_for(attribute_map_resource)