"""
Create a fresh test listing to see if description issue persists.
"""
from ebay_listing import eBayListingManager
from config import Config
import sys

sys.stdout.reconfigure(encoding='utf-8')

def create_fresh():
    """Create a fresh test listing."""
    print("=" * 80)
    print("Creating Fresh Test Listing")
    print("=" * 80)
    print()
    
    config = Config()
    manager = eBayListingManager()
    
    # Create a simple test listing
    title = "Fresh Test Listing - Please Delete"
    description = """Fresh Test Listing - Please Delete

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
    
    cards = [
        {
            "name": "Fresh Test Card",
            "number": "1"
        }
    ]
    
    print("Creating listing...")
    print(f"Title: {title}")
    print(f"Cards: {len(cards)}")
    print(f"Description length: {len(description)}")
    print()
    
    try:
        result = manager.create_variation_listing(
            cards=cards,
            title=title,
            description=description,
            category_id="261328",  # Trading Cards
            price=1.00,
            quantity=1,
            publish=False  # Create as draft first
        )
        
        if result.get('success'):
            print("=" * 80)
            print("[SUCCESS] Fresh Listing Created!")
            print("=" * 80)
            print()
            print(f"Group Key: {result.get('group_key', 'N/A')}")
            print(f"SKUs: {result.get('skus', [])}")
            print()
            print("Next step: Try to publish this listing")
            print()
            return result
        else:
            error = result.get('error', 'Unknown error')
            print(f"[ERROR] Failed to create listing: {error}")
            return None
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    create_fresh()
