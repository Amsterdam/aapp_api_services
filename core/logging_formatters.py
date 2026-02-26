import logging
import pprint

# Standard LogRecord attributes
_RESERVED = set(
    logging.LogRecord(
        name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None
    ).__dict__.keys()
)
_RESERVED |= {"message", "asctime", "stack_info"}
SILENCES_LOGGERS = ["django.server", "django.request"]


class PrettyExtraFormatter(logging.Formatter):
    INDENT = "    "

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        extras = {
            k: v
            for k, v in record.__dict__.items()
            if k not in _RESERVED and not k.startswith("_")
        }
        if not extras or record.name in SILENCES_LOGGERS:
            return base

        lines = [base]
        items = sorted(extras.items())
        for key, value in items:
            # Pretty-print complex values (dicts, lists, etc.)
            if isinstance(value, (dict, list, tuple, set)):
                formatted_value = pprint.pformat(value, compact=True)
            else:
                formatted_value = repr(value)
            lines.append(f"{self.INDENT}-> {key} = {formatted_value}")

        return "\n".join(lines)
