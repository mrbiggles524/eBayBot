"""Smart tiered pricing - different markups by card type (rookie, insert, base)."""
import re
from typing import Dict, List, Optional


# Common rookie keywords (partial match on card name/notes)
ROOKIE_KEYWORDS = [
    'rookie', 'rc', '1st year', 'first year', 'debut',
    'prized prospects', 'pp-', 'final draft', 'fd-',
    'spotlights', 'bs-', 'dream draft', '79d-'
]


class TieredPricingEngine:
    """Apply tiered pricing rules to cards."""
    
    def __init__(
        self,
        base_price: float = 1.00,
        rookie_markup_pct: float = 50,
        insert_markup_pct: float = 30,
        parallel_markup_pct: float = 25,
        auto_price: float = 1.00
    ):
        self.base_price = base_price
        self.rookie_markup_pct = rookie_markup_pct
        self.insert_markup_pct = insert_markup_pct
        self.parallel_markup_pct = parallel_markup_pct
        self.auto_price = auto_price
    
    def classify_card(self, card: Dict) -> str:
        """Return: 'rookie', 'insert', 'parallel', 'autograph', 'base'"""
        num = str(card.get('number', '')).lower()
        name = str(card.get('name', '')).lower()
        notes = str(card.get('notes', '') or card.get('team', '')).lower()
        text = f"{num} {name} {notes}"
        card_type = str(card.get('type', '')).lower()
        
        if 'auto' in card_type or 'autograph' in text:
            return 'autograph'
        for kw in ROOKIE_KEYWORDS:
            if kw in text:
                return 'rookie'
        if '-' in num and num.split('-')[0].isalpha():
            return 'insert'
        if 'parallel' in card_type or 'parallel' in text:
            return 'parallel'
        return 'base'
    
    def apply_tiered_pricing(
        self,
        cards: List[Dict],
        base: Optional[float] = None,
        rookie_pct: Optional[float] = None,
        insert_pct: Optional[float] = None,
        parallel_pct: Optional[float] = None,
        auto_price: Optional[float] = None
    ) -> List[Dict]:
        """
        Apply tiered pricing to cards. Modifies cards in place.
        """
        base = base or self.base_price
        rookie_pct = rookie_pct if rookie_pct is not None else self.rookie_markup_pct
        insert_pct = insert_pct if insert_pct is not None else self.insert_markup_pct
        parallel_pct = parallel_pct if parallel_pct is not None else self.parallel_markup_pct
        autograph_price = auto_price if auto_price is not None else self.auto_price
        
        for card in cards:
            ctype = self.classify_card(card)
            if ctype == 'autograph':
                card['price'] = autograph_price
            elif ctype == 'rookie':
                card['price'] = round(base * (1 + rookie_pct / 100), 2)
            elif ctype == 'insert':
                card['price'] = round(base * (1 + insert_pct / 100), 2)
            elif ctype == 'parallel':
                card['price'] = round(base * (1 + parallel_pct / 100), 2)
            else:
                card['price'] = base
        
        return cards
