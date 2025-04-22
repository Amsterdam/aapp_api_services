from django.core.validators import RegexValidator


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
