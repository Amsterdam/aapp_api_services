from enum import Enum
from typing import Callable, Literal, NamedTuple, Optional
from rest_framework import serializers

property_types = Literal["address", "boolean",  "image", "price","string"]


class ChoicesEnum(Enum):
    @classmethod
    def choices(cls):
        return [item.value._asdict() for item in cls]
    

class ServiceClass(NamedTuple):
    id: int
    title: str
    icon: str
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


class ListPropertyClass(NamedTuple):
    key: str
    type: property_types

class SerializerMapping(NamedTuple):
    type: str
    serializer: serializers.Serializer

