import re
from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

_URL_RE = re.compile(r'(https?://[^\s<>"{}|\\^`\[\]]+)', re.IGNORECASE)


@register.filter(is_safe=True)
def urlize_blank(value):
    """Convierte URLs en el texto en enlaces clicables que abren en pestaña nueva."""
    parts = _URL_RE.split(str(value))
    result = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            result.append(escape(part))
        else:
            safe_href = escape(part)
            result.append(
                f'<a href="{safe_href}" target="_blank" rel="noopener noreferrer">{safe_href}</a>'
            )
    return mark_safe(''.join(result))
