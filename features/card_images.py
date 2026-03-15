"""Auto-fetch card images from TCDB, eBay, and fallback sources."""
import requests
import re
import time
import sys
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        self.rate_limit_delay = rate_limit_delay
        self.placeholder = "https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp"
    
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
                
                img = self._search_tcdb_for_image(name, number, set_name)
                if not img:
                    img = self._search_ebay_for_image(name, set_name)
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
    
    def _search_tcdb_for_image(self, player_name: str, card_number: str, set_name: str) -> Optional[str]:
        return None
    
    def _search_ebay_for_image(self, player_name: str, set_name: str) -> Optional[str]:
        """Search eBay for listings and extract first image URL."""
        if not player_name:
            _log("  eBay search: no player_name, skip")
            return None
        query = f"{player_name} {set_name}".strip() if set_name else player_name
        query = query.replace(' ', '+')[:100]
        url = f"https://www.ebay.com/sch/i.html?_nkw={query}&_sacat=261328"
        try:
            _log(f"  eBay GET: {url[:80]}...")
            r = self.session.get(url, timeout=10)
            if r.status_code != 200:
                _log(f"  eBay: status {r.status_code}")
                return None
            soup = BeautifulSoup(r.text, 'html.parser')
            imgs = (
                soup.select('img.s-item__image-img') or
                soup.select('img[class*="s-item__image"]') or
                soup.find_all('img', src=re.compile(r'ebayimg\.com')) or
                soup.find_all('img', attrs={'src': re.compile(r'i\.ebayimg\.com')})
            )
            _log(f"  eBay: found {len(imgs)} img tags")
            for img in imgs[:8]:
                src = (
                    img.get('src') or
                    img.get('data-src') or
                    img.get('data-lazy-src') or
                    img.get('data-zoom-image')
                )
                if src and 'ebayimg.com' in str(src) and 'lazy' not in str(src).lower():
                    hi = re.sub(r'/s-l\d+\.', '/s-l1600.', str(src))
                    if hi and hi.startswith('http'):
                        return hi
        except requests.exceptions.Timeout:
            _log(f"  eBay: TIMEOUT for {player_name}")
            return None
        except requests.exceptions.RequestException as e:
            _log(f"  eBay: RequestException: {e}")
            return None
        except Exception as e:
            _log(f"  eBay: Exception: {type(e).__name__}: {e}")
            return None
        return None
    
    def get_placeholder(self) -> str:
        return self.placeholder
