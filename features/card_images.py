"""Auto-fetch card images from Beckett, Cardsmiths, and eBay."""
import requests
import re
import time
from typing import List, Dict, Optional
from bs4 import BeautifulSoup


class CardImageFetcher:
    """Fetch card images from multiple sources."""
    
    def __init__(self, rate_limit_delay: float = 0.3):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml',
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
        Attempt to fetch images for cards. Tries: eBay search -> placeholder.
        Modifies cards in place with image_url, returns updated list.
        Caller should pass only cards to process (e.g. qty>0, max 25).
        """
        # Limit to 25 cards to avoid timeout/freeze
        to_process = cards[:25]
        for i, card in enumerate(to_process):
            if card.get('image_url'):
                card['imageUrl'] = card['image_url']  # Sync both keys
                continue
            name = card.get('name', '')
            number = str(card.get('number', ''))
            
            # Try eBay search for similar listings
            img = self._search_ebay_for_image(name, set_name)
            if img:
                card['image_url'] = img
            else:
                card['image_url'] = self.placeholder
            # Set both keys so frontend/backend can use either
            card['imageUrl'] = card['image_url']
            
            time.sleep(self.rate_limit_delay)
        
        return cards
    
    def _search_ebay_for_image(self, player_name: str, set_name: str) -> Optional[str]:
        """Search eBay for listings and extract first image URL."""
        if not player_name or not set_name:
            return None
        query = f"{player_name} {set_name}".replace(' ', '+')
        url = f"https://www.ebay.com/sch/i.html?_nkw={query}&_sacat=261328"
        try:
            r = self.session.get(url, timeout=12)
            if r.status_code != 200:
                return None
            soup = BeautifulSoup(r.text, 'html.parser')
            if not soup:
                return None
            # Try multiple selectors - eBay structure can vary
            imgs = soup.select('img.s-item__image-img')
            if not imgs:
                imgs = soup.find_all('img', src=re.compile(r'ebayimg\.com'))
            for img in imgs[:5]:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if src and 'ebayimg.com' in str(src):
                    hi = re.sub(r'/s-l\d+\.', '/s-l1600.', str(src))
                    if hi and hi.startswith('http'):
                        return hi
        except Exception:
            pass
        return None
    
    def get_placeholder(self) -> str:
        """Return default placeholder image URL."""
        return self.placeholder
