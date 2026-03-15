"""Auto-fetch card images from TCDB, eBay, and fallback sources."""
import requests
import re
import time
from typing import List, Dict, Optional
from bs4 import BeautifulSoup


class CardImageFetcher:
    """Fetch card images from multiple sources: TCDB, eBay search, placeholder."""
    
    def __init__(self, rate_limit_delay: float = 0.25):
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
        Caller should pass only cards to process (e.g. qty>0, max 50).
        """
        # Limit to 50 cards (increased from 25 for better coverage)
        to_process = cards[:50]
        set_name = (set_name or '').strip()
        for i, card in enumerate(to_process):
            if card.get('image_url') or card.get('imageUrl'):
                card['image_url'] = card.get('image_url') or card.get('imageUrl')
                card['imageUrl'] = card['image_url']
                continue
            name = (card.get('name') or '').strip()
            number = str(card.get('number') or '')
            
            # Try TCDB first (sports cards), then eBay
            img = self._search_tcdb_for_image(name, number, set_name)
            if not img:
                img = self._search_ebay_for_image(name, set_name)
            if img:
                card['image_url'] = img
            else:
                card['image_url'] = self.placeholder
            card['imageUrl'] = card['image_url']
            
            time.sleep(self.rate_limit_delay)
        
        return cards
    
    def _search_tcdb_for_image(self, player_name: str, card_number: str, set_name: str) -> Optional[str]:
        """Search TCDB (Trading Card Database) - search results have set links, not card images. Skip for now."""
        return None
    
    def _search_ebay_for_image(self, player_name: str, set_name: str) -> Optional[str]:
        """Search eBay for listings and extract first image URL (real card photos)."""
        if not player_name:
            return None
        # Build query - include set_name if available, else just player
        query = f"{player_name} {set_name}".strip() if set_name else player_name
        query = query.replace(' ', '+')[:100]
        url = f"https://www.ebay.com/sch/i.html?_nkw={query}&_sacat=261328"
        try:
            r = self.session.get(url, timeout=12)
            if r.status_code != 200:
                return None
            soup = BeautifulSoup(r.text, 'html.parser')
            # Multiple selectors - eBay structure varies (lazy loading, A/B tests)
            imgs = (
                soup.select('img.s-item__image-img') or
                soup.select('img[class*="s-item__image"]') or
                soup.find_all('img', src=re.compile(r'ebayimg\.com')) or
                soup.find_all('img', attrs={'src': re.compile(r'i\.ebayimg\.com')})
            )
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
        except Exception:
            pass
        return None
    
    def get_placeholder(self) -> str:
        """Return default placeholder image URL."""
        return self.placeholder
