"""Auto-fetch card images from eBay Browse API, SerpAPI, and fallback sources.

Fetch Images targets only the top N most expensive cards (TOP_N_IMAGES),
with strict single-card title matching (player + number + set).
"""
import os
import requests
import re
import time
import sys
import base64
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import cloudscraper
    _HAS_CLOUDSCRAPER = True
except ImportError:
    _HAS_CLOUDSCRAPER = False

# Only fetch images for the N highest-priced cards per request.
TOP_N_IMAGES = 10

# eBay Browse API app token cache (scope: commerce.browse.product)
_browse_token_cache = {"token": None, "expires": 0}

# Lot / multi-card listing noise in titles
_LOT_RE = re.compile(
    r"(?i)\b("
    r"lot\s+of|lots?\b|lotto|multi[\s-]?card|multi[\s-]?pack|"
    r"breaker?s?|break\b|bundle|set\s+of|collection\b|"
    r"x\s*\d+|\d+\s*x\b|\(\s*\d+\s*\)|"
    r"team\s+lot|player\s+lot|card\s+lot|wholesale|"
    r"you\s+pick|pick\s+your|random\s+lot"
    r")\b"
)

# Prefer raw / near-mint singles when present in title
_QUALITY_BONUS_RE = re.compile(r"(?i)\b(nm|near[\s-]?mint|mint|raw|ungraded|single)\b")
_GRADED_RE = re.compile(r"(?i)\b(psa|bgs|sgc|cgc)\s*\d")


def _get_ebay_browse_token() -> Optional[str]:
    """Get application access token for eBay Browse API (no user login needed)."""
    app_id = (os.environ.get('EBAY_APP_ID') or '').strip()
    cert_id = (os.environ.get('EBAY_CERT_ID') or '').strip()
    if not app_id or not cert_id:
        return None
    now = time.time()
    if _browse_token_cache["token"] and _browse_token_cache["expires"] > now + 60:
        return _browse_token_cache["token"]
    try:
        creds = base64.b64encode(f"{app_id}:{cert_id}".encode()).decode()
        r = requests.post(
            "https://api.ebay.com/identity/v1/oauth2/token",
            headers={"Content-Type": "application/x-www-form-urlencoded", "Authorization": f"Basic {creds}"},
            data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope/commerce.browse.product"},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            _browse_token_cache["token"] = data.get("access_token")
            _browse_token_cache["expires"] = now + (data.get("expires_in") or 7200)
            return _browse_token_cache["token"]
    except Exception as e:
        _log(f"eBay Browse token: {e}")
    return None

def _get_serpapi_key() -> str:
    """Read SERPAPI_KEY at call time (env may load after import on some hosts)."""
    return (os.environ.get('SERPAPI_KEY') or os.environ.get('SERP_API_KEY') or '').strip()

def _normalize_player_name(name: str) -> str:
    """Fix common checklist typos so search finds the correct card."""
    if not name or not name.strip():
        return name
    n = name.strip()
    fixes = [
        (r"\brisac\b", "Risacher"),
        (r"haliburt(?!on)", "Haliburton"),
    ]
    for pat, repl in fixes:
        n = re.sub(pat, repl, n, flags=re.I)
    return n


def _player_tokens(name: str) -> List[str]:
    """Significant name tokens for matching (skip initials/short words)."""
    if not name:
        return []
    parts = re.findall(r"[A-Za-z']+", name)
    return [p.lower() for p in parts if len(p) > 1]


def _title_has_player(title: str, player_name: str) -> bool:
    """True if title contains the player (full name or last name + another token)."""
    if not title or not player_name:
        return False
    t = title.lower()
    full = player_name.strip().lower()
    if full and full in t:
        return True
    tokens = _player_tokens(player_name)
    if not tokens:
        return False
    last = tokens[-1]
    if last not in t:
        return False
    if len(tokens) == 1:
        return True
    return any(tok in t for tok in tokens[:-1])


def _card_number_variants(card_number: str) -> List[str]:
    """Variants of a card number for title matching: BP-64, BP64, #BP-64, etc."""
    raw = (card_number or "").strip()
    if not raw:
        return []
    raw = raw.lstrip("#").strip()
    variants = {raw.lower(), raw.upper(), raw}
    no_hyphen = re.sub(r"[-_\s]+", "", raw)
    if no_hyphen:
        variants.add(no_hyphen.lower())
        variants.add(no_hyphen.upper())
    m = re.match(r"^([A-Za-z]+)(\d+[A-Za-z]?)$", no_hyphen)
    if m:
        hyphenated = f"{m.group(1)}-{m.group(2)}"
        variants.add(hyphenated.lower())
        variants.add(hyphenated.upper())
        variants.add(hyphenated)
    m2 = re.search(r"(\d+[A-Za-z]?)$", no_hyphen)
    if m2 and m:
        variants.add(f"#{m2.group(1)}")
        variants.add(f"#{hyphenated}")
    variants.add(f"#{raw}")
    variants.add(f"#{no_hyphen}")
    out = []
    seen = set()
    for v in variants:
        key = v.lower()
        if key and key not in seen:
            seen.add(key)
            out.append(v)
    return out


def _title_has_card_number(title: str, card_number: str) -> bool:
    """True if title contains the card number in a recognizable form."""
    if not title or not (card_number or "").strip():
        return False
    t = title.lower()
    for v in _card_number_variants(card_number):
        vl = v.lower()
        if len(vl) < 2:
            continue
        if re.search(rf"(?<![a-z0-9]){re.escape(vl)}(?![a-z0-9])", t, re.I):
            return True
    return False


def _is_lot_title(title: str) -> bool:
    """Reject multi-card / lot / break listings."""
    if not title:
        return False
    return bool(_LOT_RE.search(title))


def _set_keywords(set_name: str) -> list:
    """Extract searchable keywords from set name for title matching."""
    if not set_name:
        return []
    words = re.findall(r'\b[\w\-]+\b', (set_name or '').lower())
    return [w for w in words if len(w) > 1 and w not in ('the', 'and', 'or')]


def _title_matches_set(title: str, set_keywords: list) -> bool:
    """True if title contains enough set keywords (e.g. Bowman + 2026)."""
    if not title or not set_keywords or len(set_keywords) < 1:
        return True
    t = title.lower()
    meaningful = [k for k in set_keywords if len(k) > 2]
    if not meaningful:
        return True
    hits = sum(1 for k in meaningful if k in t)
    years = [k for k in meaningful if re.fullmatch(r"20\d{2}", k)]
    brands = [k for k in meaningful if not re.fullmatch(r"20\d{2}", k)]
    if years and any(y in t for y in years) and any(b in t for b in brands):
        return True
    need = 2 if len(meaningful) >= 2 else 1
    return hits >= need


def _score_listing(title: str, player_name: str, set_name: str, card_number: str) -> int:
    """
    Score a listing title for this card. Higher is better.
    Returns -1 to reject (wrong player, lot, etc.).
    """
    if not title:
        return -1
    if _is_lot_title(title):
        return -1
    if not _title_has_player(title, player_name):
        return -1

    score = 40  # base: correct player, not a lot
    if _title_has_card_number(title, card_number):
        score += 50
    set_kw = _set_keywords(set_name)
    if set_kw and _title_matches_set(title, set_kw):
        score += 25
    elif set_kw:
        t = title.lower()
        if any(k in t for k in set_kw if len(k) > 2):
            score += 8
    if _QUALITY_BONUS_RE.search(title):
        score += 8
    if _GRADED_RE.search(title):
        score -= 3
    if (card_number or "").strip() and not _title_has_card_number(title, card_number):
        if set_kw and _title_matches_set(title, set_kw):
            score -= 20
        else:
            return -1
    return score


def _pick_best_image(
    items: List[dict],
    player_name: str,
    set_name: str,
    card_number: str,
    extract_img,
    title_key: str = "title",
) -> Optional[str]:
    """Rank listing candidates; return best matching image URL or None."""
    scored: List[Tuple[int, str]] = []
    for it in items:
        title = it.get(title_key) or it.get("title") or ""
        sc = _score_listing(title, player_name, set_name, card_number)
        if sc < 0:
            continue
        url = extract_img(it)
        if url:
            scored.append((sc, url))
    if not scored:
        return None
    scored.sort(key=lambda x: -x[0])
    best_score, best_url = scored[0]
    if (card_number or "").strip() and best_score < 70:
        _log(f"  Best score {best_score} too weak for numbered card — skip")
        return None
    return best_url


def _build_search_query(player_name: str, set_name: str, card_number: str) -> str:
    """Build query: player + card number + set keywords (Bowman 2026 etc.)."""
    parts = []
    if player_name:
        parts.append(player_name.strip())
    num = (card_number or "").strip().lstrip("#")
    if num:
        no_hyphen = re.sub(r"[-_\s]+", "", num)
        m = re.match(r"^([A-Za-z]+)(\d+[A-Za-z]?)$", no_hyphen)
        if m:
            parts.append(f"{m.group(1)}-{m.group(2)}")
        else:
            parts.append(num if "-" in num or not num.isdigit() else f"#{num}")
    if set_name:
        sn = re.sub(r"(?i)\b(hobby|blaster|retail|checklist)\b", "", set_name).strip()
        sn = re.sub(r"\s+", " ", sn).strip()
        if sn:
            parts.append(sn)
    return " ".join(parts).strip()[:120]


def _log(msg: str):
    import os
    debug = os.environ.get('IMAGE_FETCH_DEBUG') or os.environ.get('LOCAL_DEV')
    if debug:
        print(f"[IMAGE-FETCH] {msg}", flush=True)
    elif any(x in msg.lower() for x in ('error', 'fail', 'exception', 'timeout')):
        print(f"[IMAGE-FETCH] {msg}", flush=True)


def select_top_cards_by_price(cards: List[Dict], top_n: int = TOP_N_IMAGES) -> List[Dict]:
    """Return the top_n cards sorted by price descending (stable for ties)."""
    def _card_price(c):
        try:
            return float(c.get('price') if c.get('price') is not None else 0)
        except (TypeError, ValueError):
            return 0.0

    n = max(1, int(top_n or TOP_N_IMAGES))
    indexed = list(enumerate(cards))
    indexed.sort(key=lambda pair: (-_card_price(pair[1]), pair[0]))
    return [c for _, c in indexed[:n]]


class CardImageFetcher:
    """Fetch card images from multiple sources: eBay Browse, SerpAPI, HTML scrape."""
    
    def __init__(self, rate_limit_delay: float = 0.2):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.ebay.com/',
        })
        self.rate_limit_delay = rate_limit_delay
        from features.image_utils import resolve_default_image_url
        self.placeholder = resolve_default_image_url()
        self._cloud = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}) if _HAS_CLOUDSCRAPER else None
        self.last_targets: List[Dict] = []
    
    def fetch_images_for_cards(
        self,
        cards: List[Dict],
        set_name: str,
        source_url: Optional[str] = None,
        max_per_card: int = 1,
        progress_callback=None,
        default_price: float = 1.0,
        max_cards: int = TOP_N_IMAGES,
    ) -> List[Dict]:
        """
        Fetch images only for the top max_cards (default TOP_N_IMAGES) by price.
        Does not modify image_url on cards outside that top set.
        Returns the full cards list; only top-N entries may gain new image URLs.
        """
        top_n = max(1, min(int(max_cards or TOP_N_IMAGES), TOP_N_IMAGES))

        to_process = select_top_cards_by_price(cards, top_n)
        self.last_targets = [
            {
                "name": c.get("name"),
                "number": c.get("number"),
                "price": c.get("price"),
                "_idx": c.get("_idx"),
            }
            for c in to_process
        ]
        set_name = (set_name or '').strip()
        _log(
            f"Starting fetch for top {len(to_process)}/{len(cards)} by price, "
            f"set_name='{set_name}' (TOP_N={TOP_N_IMAGES})"
        )

        def _progress(done, total, message=None):
            if not progress_callback:
                return
            try:
                progress_callback(done, total, message)
            except Exception:
                pass

        names_preview = ", ".join(
            (c.get("name") or c.get("number") or "?") for c in to_process[:5]
        )
        more = f" (+{len(to_process) - 5} more)" if len(to_process) > 5 else ""
        _progress(0, len(to_process), f'Top {len(to_process)} by price: {names_preview}{more}')

        for i, card in enumerate(to_process):
            label = (card.get('name') or card.get('number') or '?')
            num = str(card.get('number') or '')
            _progress(
                i,
                len(to_process),
                f'Top {len(to_process)} by price — {i + 1}/{len(to_process)}: {label}'
                + (f' #{num}' if num else ''),
            )
            try:
                existing = (card.get('image_url') or card.get('imageUrl') or '').strip()
                if existing and existing != self.placeholder:
                    card['image_url'] = existing
                    card['imageUrl'] = existing
                    _log(f"  [{i+1}/{len(to_process)}] {card.get('name','?')} - already has image, skip")
                    continue
                name = (card.get('name') or '').strip()
                number = str(card.get('number') or '')
                name = _normalize_player_name(name)
                
                img = self._search_ebay_browse_api(name, set_name, number)
                if not img:
                    img = self._search_serpapi_ebay(name, set_name, number)
                if not img:
                    img = self._search_serpapi_google_images(name, set_name, number)
                if not img:
                    img = self._search_ebay_for_image(name, set_name, number)
                if img:
                    card['image_url'] = img
                    card['imageUrl'] = img
                    _log(f"  [{i+1}/{len(to_process)}] {name} - FOUND: {img[:60]}...")
                else:
                    card['image_url'] = ''
                    card['imageUrl'] = ''
                    _log(f"  [{i+1}/{len(to_process)}] {name} - no confident match")
                
                time.sleep(self.rate_limit_delay)
            except Exception as e:
                _log(f"  [{i+1}/{len(to_process)}] EXCEPTION: {e}")

        _progress(len(to_process), len(to_process), f'Done — top {len(to_process)} by price')
        found = sum(
            1 for c in to_process
            if (c.get('image_url') or '').startswith('http')
            and (c.get('image_url') or '') != self.placeholder
        )
        _log(f"Done: {found}/{len(to_process)} matched images (only top {top_n} attempted)")
        return cards

    def _search_ebay_browse_api(self, player_name: str, set_name: str, card_number: str = '') -> Optional[str]:
        """eBay Browse API - official, no SerpAPI needed. Uses APP_ID+CERT_ID."""
        token = _get_ebay_browse_token()
        if not token or not player_name:
            return None
        q = _build_search_query(player_name, set_name, card_number)
        try:
            r = self.session.get(
                "https://api.ebay.com/buy/browse/v1/item_summary/search",
                headers={"Authorization": f"Bearer {token}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"},
                params={"q": q, "category_ids": "261328", "limit": 20, "sort": "bestMatch"},
                timeout=12
            )
            if r.status_code != 200:
                return None
            data = r.json() or {}
            items = data.get("itemSummaries") or []
            url = _pick_best_image(items, player_name, set_name, card_number, self._extract_img_url)
            if url:
                _log(f"  eBay Browse API: matched for {player_name} {card_number}")
            return url
        except Exception as e:
            _log(f"  eBay Browse: {type(e).__name__}: {e}")
        return None

    def _extract_img_url(self, item: dict) -> Optional[str]:
        """Extract high-res eBay image URL from item (Browse API or SerpAPI format)."""
        img = item.get("image") or item.get("thumbnail") or item.get("original_image") or {}
        if isinstance(img, str) and "ebayimg" in img:
            url = img
        elif isinstance(img, dict):
            url = img.get("imageUrl") or img.get("url") or img.get("src") or img.get("link")
        else:
            url = None
        if url and "ebayimg" in str(url):
            hi = re.sub(r"/s-l\d+\.", "/s-l1600.", str(url))
            if hi.startswith("http"):
                return hi
        return None

    def _search_serpapi_ebay(self, player_name: str, set_name: str, card_number: str = '') -> Optional[str]:
        """Use SerpAPI eBay search - returns structured JSON with image URLs, no blocking."""
        api_key = _get_serpapi_key()
        if not api_key or not player_name:
            if not api_key:
                _log("SerpAPI skip: no SERPAPI_KEY in env")
            return None
        query = _build_search_query(player_name, set_name, card_number)
        try:
            r = self.session.get('https://serpapi.com/search.json', params={
                'engine': 'ebay', '_nkw': query, 'ebay_domain': 'ebay.com', 'api_key': api_key,
                '_sop': 15
            }, timeout=15)
            try:
                data = r.json() if r.text else {}
            except ValueError:
                data = {}
                _log("SerpAPI: invalid JSON response")
            if r.status_code != 200:
                err = data.get('error') or data.get('message') or r.text[:200]
                _log(f"SerpAPI status {r.status_code}: {err}")
                return None
            if data.get('error'):
                _log(f"SerpAPI error: {data.get('error')}")
                return None
            results = data.get('organic_results') or []
            if not results:
                _log(f"  SerpAPI eBay: 0 results for '{query[:50]}'")
            url = _pick_best_image(results, player_name, set_name, card_number, self._extract_img_url)
            if url:
                _log(f"  SerpAPI eBay: matched for {player_name} {card_number}")
            return url
        except Exception as e:
            _log(f"SerpAPI exception: {type(e).__name__}: {e}")
        return None

    def _search_serpapi_google_images(self, player_name: str, set_name: str, card_number: str = '') -> Optional[str]:
        """Fallback: SerpAPI Google Images — only accept results whose title/source match card."""
        api_key = _get_serpapi_key()
        if not api_key or not player_name:
            return None
        query = _build_search_query(player_name, set_name, card_number) + ' trading card'
        try:
            r = self.session.get('https://serpapi.com/search.json', params={
                'engine': 'google_images', 'q': query, 'api_key': api_key
            }, timeout=15)
            try:
                data = r.json() if r.text else {}
            except ValueError:
                return None
            if r.status_code != 200 or data.get('error'):
                return None
            images = data.get('images_results') or []
            candidates = []
            for img in images[:16]:
                title = (img.get('title') or img.get('source') or '') + ' ' + (img.get('link') or '')
                sc = _score_listing(title, player_name, set_name, card_number)
                if sc < 0:
                    continue
                url = img.get('original') or img.get('thumbnail') or img.get('image')
                if not (isinstance(url, str) and url.startswith('http')):
                    continue
                if 'ebayimg.com' in url:
                    url = re.sub(r'/s-l\d+\.', '/s-l1600.', url)
                    sc += 5
                elif not any(d in url.lower() for d in ('ebayimg', 'tcdb', 'tradingcard', 'comc', 'sportscard')):
                    continue
                candidates.append((sc, url))
            if not candidates:
                return None
            candidates.sort(key=lambda x: -x[0])
            if (card_number or "").strip() and candidates[0][0] < 70:
                return None
            _log(f"  SerpAPI Google: matched for {player_name}")
            return candidates[0][1]
        except Exception as e:
            _log(f"  SerpAPI Google: {type(e).__name__}: {e}")
        return None

    def _search_ebay_for_image(self, player_name: str, set_name: str, card_number: str = '') -> Optional[str]:
        """Search eBay HTML; reject lots and wrong players."""
        if not player_name:
            _log("  eBay search: no player_name, skip")
            return None
        query = _build_search_query(player_name, set_name, card_number)
        from urllib.parse import quote_plus
        url = f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(query)}&_sacat=261328&_sop=15"
        sess = self.session
        for attempt in range(2):
            try:
                if attempt == 1 and _HAS_CLOUDSCRAPER and self._cloud:
                    sess = self._cloud
                    _log(f"  eBay GET (attempt 2, cloudscraper): {url[:80]}...")
                else:
                    _log(f"  eBay GET (attempt {attempt+1}): {url[:90]}...")
                r = sess.get(url, timeout=20)
                if r.status_code != 200:
                    _log(f"  eBay: status {r.status_code}")
                    continue
                img_url = self._extract_ebay_image_from_html(r.text, player_name, set_name, card_number)
                if img_url:
                    return img_url
            except requests.exceptions.Timeout:
                _log(f"  eBay: TIMEOUT (attempt {attempt+1}) for {player_name}")
            except requests.exceptions.RequestException as e:
                _log(f"  eBay: RequestException: {e}")
            except Exception as e:
                _log(f"  eBay: Exception: {type(e).__name__}: {e}")
            time.sleep(1.0)
        return None

    def _extract_ebay_image_from_html(
        self,
        html: str,
        player_name: str,
        set_name: str = '',
        card_number: str = '',
    ) -> Optional[str]:
        """Extract image from eBay HTML using scored title matching."""
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.select('li.s-item') or soup.select('div.s-item') or soup.select('[class*="s-item"]')
        candidates = []
        for item in items[:24]:
            title_el = item.select_one('.s-item__title') or item.select_one('[class*="title"]')
            title = (title_el.get_text(strip=True) if title_el else '')[:240]
            if not title or title.lower().startswith('shop on ebay'):
                continue
            sc = _score_listing(title, player_name, set_name, card_number)
            if sc < 0:
                continue
            img = (
                item.select_one('img.s-item__image-img')
                or item.select_one('img[class*="s-item__image"]')
                or item.find('img', src=re.compile(r'ebayimg\.com'))
            )
            if not img:
                continue
            src = (
                img.get('src') or img.get('data-src') or img.get('data-lazy-src') or img.get('data-zoom-image')
            )
            if not src or 'ebayimg.com' not in str(src) or 'lazy' in str(src).lower():
                continue
            hi = re.sub(r'/s-l\d+\.', '/s-l1600.', str(src))
            if hi.startswith('http'):
                candidates.append((sc, hi))
        if not candidates:
            _log(f"  eBay HTML: no scored matches for {player_name}")
            return None
        candidates.sort(key=lambda x: -x[0])
        if (card_number or "").strip() and candidates[0][0] < 70:
            _log(f"  eBay HTML: best score {candidates[0][0]} too weak")
            return None
        return candidates[0][1]
    
    def get_placeholder(self) -> str:
        return self.placeholder
