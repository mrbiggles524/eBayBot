"""
Try creating a test draft listing in production.
Sometimes Inventory API works even when Account API shows 403.
"""
from ebay_listing import eBayListingManager
from config import Config

def try_create_draft():
    """Try creating a simple test draft."""
    print("=" * 80)
    print("Trying to Create Production Draft (Test)")
    print("=" * 80)
    print()
    
    config = Config()
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Create a simple test listing
    listing_manager = eBayListingManager()
    
    # Simple test card
    test_cards = [{
        'name': 'Test Card',
        'number': '1',
        'quantity': 1,
        'team': 'Test',
        'price': 1.0,
        'set_name': 'Test Set'
    }]
    
    print("Creating test draft listing...")
    print("This will test if Inventory API is working.")
    print()
    
    try:
        result = listing_manager.create_variation_listing(
            cards=test_cards,
            title="Test Listing - Please Delete",
            description="This is a test listing. Please delete after testing.",
            category_id="261328",
            price=1.0,
            quantity=1,
            condition="Near Mint",
            publish=False  # Create as draft
        )
        
        if result.get('success'):
            print()
            print("=" * 80)
            print("[SUCCESS] Draft Created!")
            print("=" * 80)
            print()
            print("Your keyset IS working!")
            print("You can now create production drafts.")
            print()
            print("Next steps:")
            print("  1. Go to: https://www.ebay.com/sh/landing")
            print("  2. Navigate to: Selling -> Drafts")
            print("  3. You should see your test listing")
            print("  4. Delete the test listing")
            print("  5. Create real listings via Streamlit UI")
            print()
        else:
            error = result.get('error', 'Unknown error')
            print()
            print("=" * 80)
            print("[INFO] Could not create draft")
            print("=" * 80)
            print(f"Error: {error}")
            print()
            print("This might mean:")
            print("  1. Keyset activation still propagating (wait 10-30 more minutes)")
            print("  2. Need a fresh token (get new one from Developer Console)")
            print("  3. Try again later")
            print()
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try_create_draft()
