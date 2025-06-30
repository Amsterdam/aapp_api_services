from django.utils.html import format_html
from django.utils.safestring import mark_safe

from modules.icons import ModuleIconPath


class ModuleAdminMixin:
    def icon_svg(self, obj):
        svg_path = ModuleIconPath.get(obj.icon)
        if not svg_path:
            return ""
        svg_html = f'<svg viewBox="0 0 32 32" width="24" height="24" fill-rule="evenodd"><path d="{svg_path}"></path></svg>'
        return mark_safe(svg_html)

    def module_status(self, obj):
        status_text = obj.get_status_display()
        if obj.status == 0:  # or status_text == "Inactive"
            return format_html(
                '<div style="color:white; background-color:red; padding:0.5em; '
                'border:2px solid orange; font-weight:bold;">{}</div>',
                status_text,
            )
        if not self.latest_version(obj):
            return format_html(
                '<div style="background-color:yellow; padding:0.5em; '
                'border:2px solid orange; font-weight:bold;">no versions</div>',
                status_text,
            )
        return status_text
