from enum import Enum
from typing import Callable, Literal, NamedTuple, Optional

from rest_framework import serializers

property_types = Literal[
    "address", "boolean", "image", "price", "string", "malfunction"
]


class ChoicesEnum(Enum):
    @classmethod
    def choices_as_list(cls):
        return [item.value._asdict() for item in cls]

    @classmethod
    def choices_as_dict(cls):
        return {item.value._asdict()["label"]: item.value._asdict() for item in cls}


class ModuleSourceChoices(Enum):
    HANDIG_IN_DE_STAD = "handig-in-de-stad"
    KONINGSDAG = "koningsdag"


class ServiceClass(NamedTuple):
    id: int
    title: str
    icon: str
    input_module: str
    dataservice: Optional[Callable] = None


class FilterClass(NamedTuple):
    label: str
    filter_key: str
    filter_value: str | bool | int


class PropertiesClass(NamedTuple):
    label: str | None
    property_key: str
    property_type: property_types
    icon: str | None


class IconClass(NamedTuple):
    label: str
    path: str
    path_color: str | None
    circle_color: str | None


class ListPropertyClass(NamedTuple):
    key: str
    type: property_types


class SerializerMapping(NamedTuple):
    type: str
    serializer: serializers.Serializer
