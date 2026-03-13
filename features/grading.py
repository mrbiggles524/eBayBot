"""Grading integration - PSA, BGS, SGC item specifics for eBay."""
from typing import Dict, List, Optional


# eBay item specifics for graded cards
GRADING_SPECIFICS = {
    'PSA': {
        'Grader': 'PSA',
        'Grade': '10',  # User would override
        'Certification_Number': '',
        'Card_Condition': 'Certified - Graded',
    },
    'BGS': {
        'Grader': 'BGS',
        'Grade': '10',
        'Certification_Number': '',
        'Card_Condition': 'Certified - Graded',
    },
    'SGC': {
        'Grader': 'SGC',
        'Grade': '10',
        'Certification_Number': '',
        'Card_Condition': 'Certified - Graded',
    },
}


class GradingHelper:
    """Build eBay item specifics for graded sports cards."""
    
    def __init__(self):
        self.graders = list(GRADING_SPECIFICS.keys())
    
    def get_aspects_for_graded(
        self,
        grader: str,
        grade: str,
        cert_number: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Return eBay aspect key-value pairs for a graded card.
        grader: PSA, BGS, SGC
        grade: e.g. 10, 9.5, 9
        """
        base = GRADING_SPECIFICS.get(grader.upper(), GRADING_SPECIFICS['PSA']).copy()
        base['Grade'] = str(grade)
        if cert_number:
            base['Certification_Number'] = str(cert_number)
        return base
    
    def augment_listing_for_graded(
        self,
        listing_data: Dict,
        grader: str = 'PSA',
        grade: str = '10',
        cert_number: Optional[str] = None
    ) -> Dict:
        """Add grading aspects to listing offer/inventory data."""
        aspects = self.get_aspects_for_graded(grader, grade, cert_number)
        if 'aspects' not in listing_data:
            listing_data['aspects'] = {}
        listing_data['aspects'].update(aspects)
        return listing_data
    
    def suggest_title_suffix(self, grader: str, grade: str) -> str:
        """e.g. 'PSA 10' for title."""
        return f"{grader.upper()} {grade}"
