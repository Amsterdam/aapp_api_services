from datetime import datetime
from typing import Literal, NamedTuple

from django.db.models import TextChoices


class QuestionType(TextChoices):
    BUTTONS = "selection_buttons"
    CHECK = "checkbox"
    DATE = "date"
    EMAIL = "email"
    NUMERIC = "numeric"
    RADIO = "radio"
    RATING = "rating"
    SELECT = "select"
    TELEPHONE = "tel"
    TEXT = "text"
    TEXTAREA = "textarea"
    TIME = "time"
    URL = "url"


class ConditionType(TextChoices):
    EQUAL = "equal"
    NOT_EQUAL = "not_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"


class Orientation(TextChoices):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class TeamCode(TextChoices):
    AAPP = "aapp"
    MAMS = "mams"


class Choice(NamedTuple):
    id: str
    text: str
    label: str
    show_textfield: bool = False


class Condition(NamedTuple):
    question_id: str
    value: str
    type: ConditionType


class ChoiceQuestion(NamedTuple):
    question_id: str
    question_text: str
    choices: list[Choice]
    required: bool
    question_type: QuestionType
    default: str | None = None
    description: str = ""
    conditions_type: Literal["and", "or"] = "and"
    conditions: list[Condition] = []
    orientation: Orientation = Orientation.HORIZONTAL.value


class TextQuestion(NamedTuple):
    question_id: str
    question_text: str
    required: bool
    min_characters: int = 10
    max_characters: int = 500
    textarea_rows: int = 4
    default: str = "open antwoord"
    description: str = ""
    question_type: QuestionType = QuestionType.TEXT.value
    conditions_type: Literal["and", "or"] = "and"
    conditions: list[Condition] = []


class Survey(NamedTuple):
    title: str
    unique_code: str
    team: TeamCode


class SurveyVersion(NamedTuple):
    survey: Survey
    version: int
    active_from: datetime
    questions: list[ChoiceQuestion | TextQuestion]
