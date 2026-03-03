from enum import Enum
from typing import Callable, Literal, NamedTuple, Optional

property_types = Literal["string", "price", "address", "image"]


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
