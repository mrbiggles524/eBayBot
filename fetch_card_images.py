"""
Fetch card images from checklist sites.
Note: For production use, you should take your own photos of the actual cards.
These stock images are for reference/placeholder purposes.
"""
import requests
from bs4 import BeautifulSoup
import re
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

def fetch_from_tradingcarddb(set_name: str, year: str = "2024"):
    """
    Fetch card images from Trading Card DB.
    Returns a dict of {card_number: image_url}
    """
    print(f"Searching Trading Card DB for: {set_name}")
    
    # This is a simplified example - actual implementation would need
    # to handle the site's structure and pagination
    
    # For now, return empty - we'll use a different approach
    return {}


def fetch_from_ebay_search(player_name: str, set_name: str):
    """
    Search eBay for similar listings and get their image URLs.
    This is a more reliable approach as these images are already on eBay.
    """
    print(f"Searching eBay for: {player_name} {set_name}")
    
    # Build search URL
    query = f"{player_name} {set_name}".replace(" ", "+")
    url = f"https://www.ebay.com/sch/i.html?_nkw={query}&_sacat=261328"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find listing images
            images = soup.find_all('img', class_='s-item__image-img')
            
            for img in images[:5]:  # Check first 5 results
                src = img.get('src') or img.get('data-src')
                if src and 'ebayimg.com' in src:
                    # Convert to high-res version
                    high_res = re.sub(r'/s-l\d+\.', '/s-l1600.', src)
                    return high_res
    except Exception as e:
        print(f"  Error: {e}")
    
    return None


def get_placeholder_image():
    """Return a generic trading card placeholder image."""
    # This is a generic card back image - replace with your own
    return "https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp"


def fetch_images_for_set(cards: list, set_name: str):
    """
    Fetch images for a list of cards.
    
    Args:
        cards: List of dicts with 'name' and 'number' keys
        set_name: Name of the card set
    
    Returns:
        List of cards with 'image_url' added
    """
    print("=" * 80)
    print("FETCHING CARD IMAGES")
    print("=" * 80)
    print()
    print(f"Set: {set_name}")
    print(f"Cards: {len(cards)}")
    print()
    
    results = []
    
    for i, card in enumerate(cards):
        player_name = card.get('name', '')
        card_number = card.get('number', '')
        
        print(f"[{i+1}/{len(cards)}] {card_number}. {player_name}...", end=" ")
        
        # Try to find an image
        image_url = fetch_from_ebay_search(player_name, set_name)
        
        if image_url:
            print(f"[FOUND]")
        else:
            image_url = get_placeholder_image()
            print(f"[PLACEHOLDER]")
        
        # Add image URL to card data
        card_with_image = card.copy()
        card_with_image['image_url'] = image_url
        results.append(card_with_image)
        
        # Be nice to servers
        time.sleep(0.5)
    
    print()
    print("=" * 80)
    print(f"Found images for {sum(1 for c in results if 'ebayimg' in c.get('image_url', ''))} cards")
    print("=" * 80)
    
    return results


# Example usage
if __name__ == "__main__":
    # Example cards
    test_cards = [
        {"name": "LeBron James", "number": "1", "price": 5.00},
        {"name": "Stephen Curry", "number": "2", "price": 4.00},
        {"name": "Kevin Durant", "number": "3", "price": 3.50},
    ]
    
    set_name = "2024-25 Topps Chrome Basketball"
    
    cards_with_images = fetch_images_for_set(test_cards, set_name)
    
    print()
    print("Results:")
    for card in cards_with_images:
        print(f"  {card['number']}. {card['name']}")
        print(f"     Image: {card['image_url'][:60]}...")
