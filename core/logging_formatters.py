import logging

# LogRecord attributes that are NOT "extra"
_RESERVED = set(
    logging.LogRecord(
        name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None
    ).__dict__.keys()
)

# A few common fields that sometimes appear depending on integrations
_RESERVED |= {
    "message",
    "asctime",
    "stack_info",
}


class PrettyExtraFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)

        extras = {
            k: v
            for k, v in record.__dict__.items()
            if k not in _RESERVED and not k.startswith("_")
        }

        if not extras:
            return base

        # Human-friendly: key=value key=value (colored via Rich markup)
        parts = []
        for k, v in sorted(extras.items()):
            # keep it readable; repr helps for strings/objects
            parts.append(f"[bold cyan]{k}[/]=[cyan]{v!r}[/]")

        return f"{base}  [dim]│[/] " + "  ".join(parts)
