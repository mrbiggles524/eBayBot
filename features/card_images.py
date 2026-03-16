"""Auto-fetch card images from eBay Browse API, SerpAPI, and fallback sources."""
import os
import requests
import re
import time
import sys
import base64
from typing import List, Dict, Optional
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

# eBay Browse API app token cache (scope: commerce.browse.product)
_browse_token_cache = {"token": None, "expires": 0}

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


def _set_keywords(set_name: str) -> list:
    """Extract searchable keywords from set name for title matching."""
    if not set_name:
        return []
    # "2024-25 Topps Chrome Basketball" -> ["2024", "25", "topps", "chrome", "basketball"]
    words = re.findall(r'\b[\w\-]+\b', (set_name or '').lower())
    return [w for w in words if len(w) > 1 and w not in ('the', 'and', 'or')]


def _title_matches_set(title: str, set_keywords: list) -> bool:
    """True if title contains at least 2 set keywords (e.g. Topps Chrome)."""
    if not title or not set_keywords or len(set_keywords) < 2:
        return True  # No filter when few keywords
    t = title.lower()
    hits = sum(1 for k in set_keywords if len(k) > 2 and k in t)
    return hits >= 2


def _build_search_query(player_name: str, set_name: str, card_number: str) -> str:
    """Build optimized query: set first (more specific) + player + #number."""
    parts = []
    if set_name:
        parts.append(set_name.strip())
    parts.append(player_name)
    if card_number and str(card_number).strip():
        parts.append(f"#{card_number.strip()}")
    return ' '.join(parts).strip()[:120]


def _log(msg: str):
    import os
    debug = os.environ.get('IMAGE_FETCH_DEBUG') or os.environ.get('LOCAL_DEV')
    if debug:
        print(f"[IMAGE-FETCH] {msg}", flush=True)
    elif any(x in msg.lower() for x in ('error', 'fail', 'exception', 'timeout')):
        print(f"[IMAGE-FETCH] {msg}", flush=True)


class CardImageFetcher:
    """Fetch card images from multiple sources: TCDB, eBay search, placeholder."""
    
    def __init__(self, rate_limit_delay: float = 0.2):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.ebay.com/',
        })
        self.rate_limit_delay = rate_limit_delay
        self.placeholder = "https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp"
        self._cloud = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}) if _HAS_CLOUDSCRAPER else None
    
    def fetch_images_for_cards(
        self,
        cards: List[Dict],
        set_name: str,
        source_url: Optional[str] = None,
        max_per_card: int = 1
    ) -> List[Dict]:
        """
        Attempt to fetch images for cards. Tries: TCDB -> eBay search -> placeholder.
        Modifies cards in place with image_url, returns updated list.
        """
        to_process = cards[:50]
        set_name = (set_name or '').strip()
        _log(f"Starting fetch for {len(to_process)} cards, set_name='{set_name}' (enable IMAGE_FETCH_DEBUG=1 for per-card logs)")
        
        for i, card in enumerate(to_process):
            try:
                if card.get('image_url') or card.get('imageUrl'):
                    card['image_url'] = card.get('image_url') or card.get('imageUrl')
                    card['imageUrl'] = card['image_url']
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
                    card['image_url'] = self.placeholder
                    card['imageUrl'] = self.placeholder
                    _log(f"  [{i+1}/{len(to_process)}] {name} - placeholder (no result)")
                
                time.sleep(self.rate_limit_delay)
            except Exception as e:
                _log(f"  [{i+1}/{len(to_process)}] EXCEPTION: {e}")
                card['image_url'] = self.placeholder
                card['imageUrl'] = self.placeholder
        
        ph = self.placeholder
        found = sum(1 for c in to_process if (c.get('image_url') or '').startswith('http') and (c.get('image_url') or '') != ph)
        _log(f"Done: {found} from eBay, {len(to_process)-found} placeholders")
        return cards

    def _search_ebay_browse_api(self, player_name: str, set_name: str, card_number: str = '') -> Optional[str]:
        """eBay Browse API - official, no SerpAPI needed. Uses APP_ID+CERT_ID."""
        token = _get_ebay_browse_token()
        if not token or not player_name:
            return None
        q = _build_search_query(player_name, set_name, card_number)
        set_kw = _set_keywords(set_name)
        try:
            r = self.session.get(
                "https://api.ebay.com/buy/browse/v1/item_summary/search",
                headers={"Authorization": f"Bearer {token}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"},
                params={"q": q, "category_ids": "261328", "limit": 12},
                timeout=12
            )
            if r.status_code != 200:
                return None
            data = r.json() or {}
            items = data.get("itemSummaries") or []
            player_lower = (player_name or "").lower()
            # Prefer: player in title AND set keywords in title
            for it in items:
                title = (it.get("title") or "")
                if player_lower and title.lower() and player_lower not in title.lower():
                    continue
                if set_kw and not _title_matches_set(title, set_kw):
                    continue
                url = self._extract_img_url(it)
                if url:
                    _log(f"  eBay Browse API: found for {player_name}")
                    return url
            # Fallback: player in title only
            for it in items:
                title = (it.get("title") or "").lower()
                if player_lower and title and player_lower not in title:
                    continue
                url = self._extract_img_url(it)
                if url:
                    _log(f"  eBay Browse API: found (loose) for {player_name}")
                    return url
            # Last: any item with image
            for it in items[:6]:
                url = self._extract_img_url(it)
                if url:
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
        set_kw = _set_keywords(set_name)
        try:
            r = self.session.get('https://serpapi.com/search.json', params={
                'engine': 'ebay', '_nkw': query, 'ebay_domain': 'ebay.com', 'api_key': api_key
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
            player_lower = (player_name or '').lower()
            # Prefer: player + set in title
            for item in results[:12]:
                title = (item.get('title') or '')
                if player_lower and title.lower() and player_lower not in title.lower():
                    continue
                if set_kw and not _title_matches_set(title, set_kw):
                    continue
                url = self._extract_img_url(item)
                if url:
                    _log(f"  SerpAPI eBay: found for {player_name}")
                    return url
            # Fallback: player in title only
            for item in results[:10]:
                title = (item.get('title') or '').lower()
                if player_lower and title and player_lower not in title:
                    continue
                url = self._extract_img_url(item)
                if url:
                    _log(f"  SerpAPI eBay: found (loose) for {player_name}")
                    return url
            # Last: any item with image
            for item in results[:8]:
                url = self._extract_img_url(item)
                if url:
                    return url
        except Exception as e:
            _log(f"SerpAPI exception: {type(e).__name__}: {e}")
        return None

    def _search_serpapi_google_images(self, player_name: str, set_name: str, card_number: str = '') -> Optional[str]:
        """Fallback: SerpAPI Google Images - returns image URLs from various sources (eBay, TCDB, etc)."""
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
            for img in images[:12]:
                url = img.get('original') or img.get('thumbnail') or img.get('image')
                if isinstance(url, str) and url.startswith('http'):
                    if 'ebayimg.com' in url:
                        hi = re.sub(r'/s-l\d+\.', '/s-l1600.', url)
                        _log(f"  SerpAPI Google: found eBay img for {player_name}")
                        return hi
            for img in images[:8]:
                url = img.get('original') or img.get('thumbnail') or img.get('image')
                if isinstance(url, str) and url.startswith('http'):
                    if any(d in url.lower() for d in ('ebayimg', 'tcdb', 'tradingcard', 'comc', 'sportscard')):
                        _log(f"  SerpAPI Google: found card img for {player_name}")
                        return url
        except Exception as e:
            _log(f"  SerpAPI Google: {type(e).__name__}: {e}")
        return None

    def _search_ebay_for_image(self, player_name: str, set_name: str, card_number: str = '') -> Optional[str]:
        """
        Search eBay for listings and extract image URL.
        Uses player + set + card number in query for better matching.
        Tries listing blocks first (img + title) to prefer listings where title contains player name.
        """
        if not player_name:
            _log("  eBay search: no player_name, skip")
            return None
        query = _build_search_query(player_name, set_name, card_number)
        from urllib.parse import quote_plus
        url = f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(query)}&_sacat=261328"
        # Prefer Base Set when we have a card number (reduces refractors/inserts)
        if card_number:
            url += "&Features=Base%2520Set"
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
                html = r.text
                # 1) Try structured extraction (listing blocks with title verification)
                img_url = self._extract_ebay_image_from_html(html, player_name)
                if img_url:
                    return img_url
                # 2) Regex fallback: find any i.ebayimg.com URL in raw HTML
                m = re.search(r'https?://i\.ebayimg\.com/images/[^\s"\'<>]+', html)
                if m:
                    src = m.group(0).split('"')[0].split("'")[0].strip()
                    hi = re.sub(r'/s-l\d+\.', '/s-l1600.', src)
                    if hi and hi.startswith('http'):
                        _log(f"  eBay: regex fallback found image")
                        return hi
            except requests.exceptions.Timeout:
                _log(f"  eBay: TIMEOUT (attempt {attempt+1}) for {player_name}")
            except requests.exceptions.RequestException as e:
                _log(f"  eBay: RequestException: {e}")
            except Exception as e:
                _log(f"  eBay: Exception: {type(e).__name__}: {e}")
            time.sleep(1.0)  # Brief pause before retry
        return None

    def _extract_ebay_image_from_html(self, html: str, player_name: str) -> Optional[str]:
        """Extract image from eBay HTML, preferring listings where title contains player name."""
        soup = BeautifulSoup(html, 'html.parser')
        player_lower = (player_name or '').lower()
        imgs = (
            soup.select('img.s-item__image-img') or
            soup.select('img[class*="s-item__image"]') or
            soup.find_all('img', src=re.compile(r'ebayimg\.com')) or
            soup.find_all('img', attrs={'src': re.compile(r'i\.ebayimg\.com')})
        )
        _log(f"  eBay: found {len(imgs)} img tags")
        for img in imgs[:12]:
            src = (
                img.get('src') or
                img.get('data-src') or
                img.get('data-lazy-src') or
                img.get('data-zoom-image')
            )
            if not src or 'ebayimg.com' not in str(src) or 'lazy' in str(src).lower():
                continue
            # Verify: try to find parent listing and check title contains player
            parent = img.find_parent('div', class_=re.compile(r's-item'))
            if parent and player_lower:
                title_el = parent.select_one('.s-item__title')
                title = (title_el.get_text(strip=True) if title_el else '')[:200]
                if title and player_lower not in title.lower():
                    continue  # Skip if title doesn't contain player
            hi = re.sub(r'/s-l\d+\.', '/s-l1600.', str(src))
            if hi and hi.startswith('http'):
                return hi
        # No verified match - return first valid image anyway
        for img in imgs[:8]:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or img.get('data-zoom-image')
            if src and 'ebayimg.com' in str(src) and 'lazy' not in str(src).lower():
                hi = re.sub(r'/s-l\d+\.', '/s-l1600.', str(src))
                if hi and hi.startswith('http'):
                    return hi
        return None
    
    def get_placeholder(self) -> str:
        return self.placeholder
