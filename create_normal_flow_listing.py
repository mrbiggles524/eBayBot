"""
Create a listing using the normal flow to see if it appears in drafts.
"""
from ebay_listing import eBayListingManager
from config import Config
import sys

sys.stdout.reconfigure(encoding='utf-8')

def create_normal():
    """Create listing using normal flow."""
    print("=" * 80)
    print("Creating Listing via Normal Flow")
    print("=" * 80)
    print()
    
    config = Config()
    manager = eBayListingManager()
    
    # Create a simple test listing using the normal flow
    title = "Normal Flow Test Listing - Please Delete"
    description = """Normal Flow Test Listing - Please Delete

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
    
    cards = [
        {
            "name": "Normal Flow Test Card",
            "number": "1"
        }
    ]
    
    print("Creating listing via normal flow...")
    print(f"Title: {title}")
    print(f"Cards: {len(cards)}")
    print(f"Description length: {len(description)}")
    print()
    print("This will use the standard create_variation_listing function.")
    print()
    
    try:
        result = manager.create_variation_listing(
            cards=cards,
            title=title,
            description=description,
            category_id="261328",  # Trading Cards
            price=1.00,
            quantity=1,
            publish=False  # Create as draft
        )
        
        if result.get('success'):
            group_key = result.get('group_key')
            skus = result.get('skus', [])
            offer_ids = result.get('offer_ids', [])
            
            print()
            print("=" * 80)
            print("[SUCCESS] Listing Created via Normal Flow!")
            print("=" * 80)
            print()
            print(f"Group Key: {group_key}")
            print(f"SKUs: {skus}")
            if offer_ids:
                print(f"Offer IDs: {offer_ids}")
            print()
            print("Check Seller Hub:")
            print("  1. Go to: https://www.ebay.com/sh/landing")
            print("  2. Navigate to: Listings -> Drafts")
            print("  3. Look for: 'Normal Flow Test Listing - Please Delete'")
            print()
            print("Wait 1-2 minutes for eBay to process, then refresh Seller Hub.")
            print()
            
            return result
        else:
            error = result.get('error', 'Unknown error')
            print()
            print("=" * 80)
            print("[ERROR] Failed to Create Listing")
            print("=" * 80)
            print(f"Error: {error}")
            print()
            return None
    except Exception as e:
        print()
        print("=" * 80)
        print("[ERROR] Exception Occurred")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    create_normal()
