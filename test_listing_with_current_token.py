"""
Test if listing creation works with current token despite 403 on reads.
"""
from ebay_listing import eBayListingManager
from config import Config

def main():
    print("=" * 80)
    print("Test Listing Creation with Current Token")
    print("=" * 80)
    print()
    
    config = Config()
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print(f"Token exists: {bool(config.ebay_token)}")
    print()
    
    print("The 403 errors might only affect READ operations.")
    print("Let's test if WRITE operations (creating listings) work.")
    print()
    
    # Create a simple test listing
    print("Creating a test listing with 2 cards...")
    print()
    
    try:
        listing_manager = eBayListingManager()
        
        # Simple test cards
        test_cards = [
            {
                'name': 'Test Player 1',
                'number': '1',
                'quantity': 1,
                'team': 'Test Team',
                'price': 1.00,
                'set_name': 'Test Set'
            },
            {
                'name': 'Test Player 2',
                'number': '2',
                'quantity': 1,
                'team': 'Test Team',
                'price': 1.00,
                'set_name': 'Test Set'
            }
        ]
        
        category_id = listing_manager.get_category_id("Trading Cards")
        
        result = listing_manager.create_variation_listing(
            cards=test_cards,
            title="Test Listing - Please Delete",
            description="This is a test listing. Please delete it.",
            category_id=category_id,
            price=1.00,
            quantity=1,
            condition="Like New",
            publish=False  # Create as draft
        )
        
        if result.get('success'):
            print("\n[SUCCESS] Listing creation works!")
            print("The token HAS the required permissions for WRITE operations.")
            print()
            print("The 403 errors on READ operations are likely normal for sandbox.")
            print("What matters is that listing creation (WRITE) works, which it does!")
            print()
            if result.get('offerId'):
                print(f"Offer ID: {result['offerId']}")
        else:
            error = result.get('error', 'Unknown error')
            print(f"\n[ERROR] Failed: {error}")
            print()
            if '403' in str(error) or '1100' in str(error):
                print("The token still doesn't have Inventory API permissions.")
                print("You need to get a new token with proper scopes.")
            else:
                print("This might be a different issue. Check the error above.")
                
    except Exception as e:
        print(f"\n[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
