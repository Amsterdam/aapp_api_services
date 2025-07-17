from django.forms.widgets import Widget
from django.utils.html import mark_safe
from django.utils.safestring import SafeString


def bump_patch(vers):
    major, minor, patch = map(int, vers.split("."))
    return f"{major}.{minor}.{patch + 1}"


def bump_minor(vers):
    major, minor, patch = map(int, vers.split("."))
    return f"{major}.{minor + 1}.0"


def bump_major(vers):
    major, minor, patch = map(int, vers.split("."))
    return f"{major + 1}.0.0"


class SVGSelectWidget(Widget):
    template = (
        '<input type="radio" name="{name}" value="{value}" id="{id}" {checked} hidden>'
        '<label for="{id}" class="icon-option">{svg}</label>'
    )

    def __init__(self, choices, attrs=None):
        super().__init__(attrs)
        self.choices = choices  # [(key, svg_path), ...]

    def render(self, name, value, attrs=None, renderer=None) -> SafeString:
        rendered = []
        for idx, (key, svg_path) in enumerate(self.choices):
            rendered.append(
                self.template.format(
                    name=name,
                    value=key,
                    id=f"{attrs['id']}_{idx}",
                    checked="checked" if str(value) == str(key) else "",
                    svg=f'<svg viewBox="0 0 32 32" width="32" height="32">'
                    f'<path d="{svg_path}"/></svg>',
                )
            )
        return mark_safe('<div class="icon-select">' + "".join(rendered) + "</div>")
