from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from jsonschema import ValidationError as SchemaError
from jsonschema import validate

CONTEXT_SCHEMA = {
    "type": "object",
    "required": ["type", "module_slug"],
    "properties": {
        "linkSourceid": {"type": "string"},
        "type": {"type": "string"},
        "module_slug": {"type": "string"},
        "url": {"type": "string"},
        "deeplink": {"type": "string"},
    },
    "not": {
        "required": ["url", "deeplink"],
    },
    "additionalProperties": False,
}


class AappDeeplinkValidator(RegexValidator):
    """Validates amsterdam:// deeplinks.

    Accepts formats, e.g.:
    - "amsterdam://anything"
    - "amsterdam://anything?foo=bar"
    - "amsterdam://anything/something"
    - "amsterdam://anything/something?foo=bar"
    - "amsterdam://anything/something?foo=bar&fizz=buzz"
    """

    regex = r"^amsterdam://[\w-]+(?:/[\w-]+)*/?(?:\?[\w-]+=[\w-]+(?:&[\w-]+=[\w-]+)*)?$"
    message = "Invalid deeplink. Must at least start with 'amsterdam://'."


def context_validator(value):
    try:
        validate(value, CONTEXT_SCHEMA)
    except SchemaError as e:
        raise ValidationError(f"Invalid context: {e.message}")
