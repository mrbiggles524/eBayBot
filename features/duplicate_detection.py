"""Duplicate listing detection - warn before creating similar listings."""
from typing import Dict, List, Optional, Tuple
import re


class DuplicateDetector:
    """Check for potentially duplicate/similar existing listings."""
    
    def __init__(self, api_client=None):
        self.api_client = api_client
    
    def normalize_title_for_match(self, title: str) -> str:
        """Normalize listing title for fuzzy comparison."""
        t = title.lower()
        t = re.sub(r'[^\w\s]', '', t)
        t = re.sub(r'\s+', ' ', t)
        return t.strip()
    
    def extract_set_keywords(self, title: str) -> set:
        """Extract likely set/year keywords from title."""
        words = self.normalize_title_for_match(title).split()
        # Filter numeric years and set-like terms
        keywords = set()
        for w in words:
            if len(w) >= 3 and (w.isdigit() or w.isalpha()):
                keywords.add(w)
        return keywords
    
    def similarity_score(self, title_a: str, title_b: str) -> float:
        """
        Return similarity 0-1. High = likely duplicate.
        """
        a = self.extract_set_keywords(title_a)
        b = self.extract_set_keywords(title_b)
        if not a or not b:
            return 0
        overlap = len(a & b) / max(len(a), len(b))
        # Also check if one contains the other
        na, nb = self.normalize_title_for_match(title_a), self.normalize_title_for_match(title_b)
        if na in nb or nb in na:
            overlap = max(overlap, 0.8)
        return min(1.0, overlap + 0.2 if overlap > 0.3 else overlap)
    
    def check_duplicates(
        self,
        proposed_title: str,
        existing_listings: List[Dict],
        threshold: float = 0.6
    ) -> List[Tuple[Dict, float]]:
        """
        Return list of (listing, score) that may be duplicates.
        existing_listings: [{title, listing_id, ...}, ...]
        """
        matches = []
        for li in existing_listings:
            t = li.get('title') or li.get('name') or ''
            if not t:
                continue
            score = self.similarity_score(proposed_title, t)
            if score >= threshold:
                matches.append((li, score))
        matches.sort(key=lambda x: -x[1])
        return matches
    
    def get_existing_listings_for_user(self, token: str) -> List[Dict]:
        """Fetch user's active/draft listings from eBay API."""
        if not self.api_client:
            return []
        try:
            from ebay_api_client import eBayAPIClient
            client = eBayAPIClient(token_override=token)
            # Use sell inventory API to list offers
            # Simplified: we'd need actual endpoint - stub for now
            return []
        except Exception:
            return []
