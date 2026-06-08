from enum import Enum
from typing import NamedTuple, Optional


class ChoicesEnum(Enum):
    @classmethod
    def choices_as_list(cls):
        return [item.value._asdict() for item in cls]

    @classmethod
    def choices_as_dict(cls):
        return {item.value._asdict()["index"]: item.value._asdict() for item in cls}


class NewsArticleExtract(NamedTuple):
    index: str  # indexAlias in IPROX
    boolean_column: str  # the name of the boolean column to set to True for articles retrieved from this source, e.g. "is_highlight", "is_liveblog", "is_district"
    district: Optional[
        str
    ]  # only for type "district", e.g. "noord", "west", "zuid", "oost", "centrum", "nieuw-west", "zuidoost", "weesp"
