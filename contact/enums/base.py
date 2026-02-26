from enum import Enum
from typing import NamedTuple


class ChoicesEnum(Enum):
    @classmethod
    def choices(cls):
        return [item.value._asdict() for item in cls]


class FilterClass(NamedTuple):
    label: str
    filter_key: str
    filter_value: str | bool | int


class PropertiesClass(NamedTuple):
    label: str | None
    property_key: str
    property_type: str
    icon: str | None


class ServiceClass(NamedTuple):
    id: int
    title: str
    icon: str
    dataservice: callable
