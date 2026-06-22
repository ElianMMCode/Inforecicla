import re
from urllib.parse import urlparse, parse_qs

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


_YOUTUBE_ALLOWED_PARAMS = {
    "autoplay", "cc_load_policy", "color", "controls", "end",
    "hl", "iv_load_policy", "loop", "modestbranding", "mute",
    "playlist", "playsinline", "rel", "si", "start",
}


def _youtube_embed_url(parsed):
    if parsed.netloc == "youtu.be":
        video_id = parsed.path.strip("/")
    else:
        qs = parse_qs(parsed.query)
        video_id = qs.get("v", [None])[0]
        if not video_id:
            path = parsed.path.strip("/")
            if path.startswith(("embed/", "v/")):
                video_id = path.split("/")[-1]
    if video_id:
        embed = f"https://www.youtube.com/embed/{video_id}"
        params = parse_qs(parsed.query)
        keep = sorted(
            f"{k}={v[0]}"
            for k, v in params.items()
            if k in _YOUTUBE_ALLOWED_PARAMS
        )
        if keep:
            embed += "?" + "&".join(keep)
        return embed
    return None


def _vimeo_embed_url(parsed):
    video_id = parsed.path.strip("/").split("/")[-1]
    if video_id and video_id.isdigit():
        return f"https://player.vimeo.com/video/{video_id}"
    return None


@register.filter
def video_embed_url(value):
    """Convierte URL de YouTube/Vimeo a URL de embed."""
    if not value:
        return ""
    parsed = urlparse(value)
    if "youtube" in parsed.netloc or "youtu.be" in parsed.netloc:
        result = _youtube_embed_url(parsed)
        if result:
            return result
    if "vimeo" in parsed.netloc:
        result = _vimeo_embed_url(parsed)
        if result:
            return result
    return value
