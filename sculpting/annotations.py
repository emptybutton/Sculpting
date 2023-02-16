from typing import Any, Callable

from pyannotating import AnnotationTemplate, input_annotation
from pyhandling.annotations import handler_of


attribute_getter_of = handler_of
attribute_setter_of = AnnotationTemplate(Callable, [[input_annotation, Any], Any])

attribute_getter = attribute_getter_of[object]
attribute_setter = attribute_setter_of[object]