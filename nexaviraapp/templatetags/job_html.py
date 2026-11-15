import html
import re

import nh3
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

_ALLOWED_TAGS = {
    'a',
    'blockquote',
    'br',
    'em',
    'h2',
    'h3',
    'li',
    'ol',
    'p',
    'strong',
    'ul',
}
_ALLOWED_ATTRIBUTES = {'a': {'href', 'title'}}
_BLOCK_END_TAG = re.compile(r'</(?:p|li|h[1-6]|blockquote|div)\s*>', re.IGNORECASE)


@register.filter
def sanitize_job_html(value):
    cleaned = nh3.clean(
        str(value or ''),
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        url_schemes={'http', 'https', 'mailto'},
    )
    return mark_safe(cleaned)


@register.filter
def job_plain_text(value):
    prepared = _BLOCK_END_TAG.sub(' ', str(value or ''))
    cleaned = nh3.clean(prepared, tags=set(), attributes={})
    return html.unescape(re.sub(r'\s+', ' ', cleaned)).strip()
