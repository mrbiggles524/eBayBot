"""Validate and sanitize image URLs for eBay Inventory API."""
import re
from typing import Optional
from urllib.parse import urlparse

DEFAULT_PLACEHOLDER_IMAGE = "https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp"

# Non-image page URLs users sometimes paste (Beckett articles, checklist pages, etc.)
_NON_IMAGE_HOST_PATTERNS = (
    r'beckett\.com/news',
    r'beckett\.com/[^/]+$',
    r'cardsmithsbreaks\.com',
    r'cardboardconnection\.com',
)
_NON_IMAGE_SUFFIXES = ('.html', '.htm', '.php', '.asp', '.aspx')


def sanitize_image_url(url: Optional[str], allow_placeholder: bool = False) -> str:
    """
    Return a valid http(s) image URL or empty string.
    Rejects checklist/article URLs that cause eBay 'invalid image URL' errors.
    """
    if not url or not isinstance(url, str):
        return DEFAULT_PLACEHOLDER_IMAGE if allow_placeholder else ''

    cleaned = url.strip().replace('\n', '').replace('\r', '')
    if not cleaned:
        return DEFAULT_PLACEHOLDER_IMAGE if allow_placeholder else ''

    lower = cleaned.lower()
    if lower.startswith('data:') or lower.startswith('blob:') or lower.startswith('javascript:'):
        return DEFAULT_PLACEHOLDER_IMAGE if allow_placeholder else ''

    if not lower.startswith(('http://', 'https://')):
        return DEFAULT_PLACEHOLDER_IMAGE if allow_placeholder else ''

    for pat in _NON_IMAGE_HOST_PATTERNS:
        if re.search(pat, lower):
            return DEFAULT_PLACEHOLDER_IMAGE if allow_placeholder else ''

    if any(lower.split('?')[0].endswith(suf) for suf in _NON_IMAGE_SUFFIXES):
        return DEFAULT_PLACEHOLDER_IMAGE if allow_placeholder else ''

    try:
        parsed = urlparse(cleaned)
        if not parsed.netloc:
            return DEFAULT_PLACEHOLDER_IMAGE if allow_placeholder else ''
    except Exception:
        return DEFAULT_PLACEHOLDER_IMAGE if allow_placeholder else ''

    return cleaned


def ensure_publish_image_urls(urls: list) -> list:
    """Ensure at least one valid image URL for eBay publish (Error 25717)."""
    valid = []
    seen = set()
    for u in urls or []:
        s = sanitize_image_url(u)
        if s and s not in seen:
            seen.add(s)
            valid.append(s)
    if not valid:
        valid = [DEFAULT_PLACEHOLDER_IMAGE]
    return valid[:12]
