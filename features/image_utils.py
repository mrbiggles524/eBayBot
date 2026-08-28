"""Validate and sanitize image URLs for eBay Inventory API."""
import os
import re
from typing import Optional
from urllib.parse import urlparse

DEFAULT_EBAY_CDN_PLACEHOLDER = "https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp"
DEFAULT_PLACEHOLDER_IMAGE = DEFAULT_EBAY_CDN_PLACEHOLDER
DEFAULT_IMAGE_FILENAME = "s-l1600.webp"

# Non-image page URLs users sometimes paste (Beckett articles, checklist pages, etc.)
_NON_IMAGE_HOST_PATTERNS = (
    r'beckett\.com/news',
    r'beckett\.com/[^/]+$',
    r'cardsmithsbreaks\.com',
    r'cardboardconnection\.com',
)
_NON_IMAGE_SUFFIXES = ('.html', '.htm', '.php', '.asp', '.aspx')


def resolve_default_image_url(base_url: Optional[str] = None) -> str:
    """Return HTTPS URL for default listing image (self-hosted when possible)."""
    if base_url:
        base = base_url.strip().rstrip('/')
        if base.startswith('http'):
            return f"{base}/pictures/{DEFAULT_IMAGE_FILENAME}"
    for env_key in ('PUBLIC_BASE_URL', 'RENDER_EXTERNAL_URL', 'APP_URL'):
        val = (os.environ.get(env_key) or '').strip().rstrip('/')
        if val.startswith('http'):
            return f"{val}/pictures/{DEFAULT_IMAGE_FILENAME}"
    return DEFAULT_EBAY_CDN_PLACEHOLDER


def sanitize_image_url(
    url: Optional[str],
    allow_placeholder: bool = False,
    placeholder_url: Optional[str] = None,
) -> str:
    """
    Return a valid http(s) image URL or empty string.
    Rejects checklist/article URLs that cause eBay 'invalid image URL' errors.
    """
    fallback = placeholder_url or resolve_default_image_url()

    if not url or not isinstance(url, str):
        return fallback if allow_placeholder else ''

    cleaned = url.strip().replace('\n', '').replace('\r', '')
    if not cleaned:
        return fallback if allow_placeholder else ''

    lower = cleaned.lower()
    if lower.startswith('data:') or lower.startswith('blob:') or lower.startswith('javascript:'):
        return fallback if allow_placeholder else ''

    if not lower.startswith(('http://', 'https://')):
        return fallback if allow_placeholder else ''

    for pat in _NON_IMAGE_HOST_PATTERNS:
        if re.search(pat, lower):
            return fallback if allow_placeholder else ''

    if any(lower.split('?')[0].endswith(suf) for suf in _NON_IMAGE_SUFFIXES):
        return fallback if allow_placeholder else ''

    try:
        parsed = urlparse(cleaned)
        if not parsed.netloc:
            return fallback if allow_placeholder else ''
    except Exception:
        return fallback if allow_placeholder else ''

    return cleaned


def ensure_publish_image_urls(urls: list, default_url: Optional[str] = None) -> list:
    """Ensure at least one valid image URL for eBay publish (Error 25717)."""
    fallback = default_url or resolve_default_image_url()
    valid = []
    seen = set()
    for u in urls or []:
        s = sanitize_image_url(u)
        if s and s not in seen:
            seen.add(s)
            valid.append(s)
    if not valid:
        valid = [fallback]
    return valid[:12]
