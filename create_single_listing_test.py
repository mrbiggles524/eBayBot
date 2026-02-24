"""
Create a SINGLE listing (not variation) to test if it appears in drafts.
Variation listings may not show in Seller Hub drafts.
"""
from ebay_listing import eBayListingManager
from config import Config
import sys

sys.stdout.reconfigure(encoding='utf-8')

def create_single_listing():
    """Create a single listing (not variation) to test."""
    print("=" * 80)
    print("Creating Single Listing (Not Variation) - Test")
    print("=" * 80)
    print()
    
    config = Config()
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    print("Creating a SINGLE listing (not a variation)...")
    print("Single listings should appear in Seller Hub drafts.")
    print()
    
    listing_manager = eBayListingManager()
    
    # Create a single card listing (not variation)
    # We'll create just one card, which should create a single listing
    
    test_cards = [{
        'name': 'Single Test Card',
        'number': '999',
        'quantity': 1,
        'team': 'Test',
        'price': 1.0,
        'set_name': 'Single Test Set'
    }]
    
    try:
        result = listing_manager.create_variation_listing(
            cards=test_cards,
            title="SINGLE TEST - Please Delete",
            description="This is a single listing test (not a variation). Please delete after testing.",
            category_id="261328",
            price=1.0,
            quantity=1,
            condition="Near Mint",
            publish=False  # Create as draft
        )
        
        if result.get('success'):
            print()
            print("=" * 80)
            print("[SUCCESS] Single Listing Created!")
            print("=" * 80)
            print()
            print("This should appear in Seller Hub drafts.")
            print()
            print("Check:")
            print("  1. Refresh Seller Hub drafts page")
            print("  2. Look for 'SINGLE TEST - Please Delete'")
            print("  3. Single listings show up better than variation listings")
            print()
        else:
            error = result.get('error', 'Unknown error')
            print(f"[ERROR] Failed to create listing: {error}")
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_single_listing()
