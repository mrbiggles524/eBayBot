"""
Quick test script to verify the listing fix works.
Run this to test listing creation with your actual data.
"""
import json
from ebay_listing import eBayListingManager
from config import Config

def test_listing_creation():
    """Test listing creation with sample data."""
    print("=" * 80)
    print("Testing eBay Listing Creation Fix")
    print("=" * 80)
    print()
    
    # Sample data matching your use case
    test_cards = [
        {
            "name": "Pascal Siakam",
            "number": "1",
            "quantity": 1,
            "team": "Indiana Pacers",
            "set_name": "https://cardsmithsbreaks.com/full-checklist/2025-26-topps-chrome-basketball-hobby/"
        },
        {
            "name": "Zaccharie Risacher",
            "number": "2",
            "quantity": 2,
            "team": "Atlanta Hawks",
            "set_name": "https://cardsmithsbreaks.com/full-checklist/2025-26-topps-chrome-basketball-hobby/"
        },
        {
            "name": "Tyrese Haliburton",
            "number": "3",
            "quantity": 1,
            "team": "Indiana Pacers",
            "set_name": "https://cardsmithsbreaks.com/full-checklist/2025-26-topps-chrome-basketball-hobby/"
        },
        {
            "name": "Ty Jerome",
            "number": "4",
            "quantity": 2,
            "team": "Cleveland Cavaliers",
            "set_name": "https://cardsmithsbreaks.com/full-checklist/2025-26-topps-chrome-basketball-hobby/"
        }
    ]
    
    # Filter to only cards with quantity > 0
    listing_cards = [card for card in test_cards if card.get('quantity', 0) > 0]
    
    print(f"Testing with {len(listing_cards)} cards:")
    for card in listing_cards:
        print(f"  - {card['name']} #{card['number']} (Qty: {card['quantity']})")
    print()
    
    # Create listing manager
    try:
        manager = eBayListingManager()
        print("✓ Listing manager created")
    except Exception as e:
        print(f"❌ Failed to create listing manager: {e}")
        return
    
    # Test listing creation
    print("\nCreating listing...")
    print("-" * 80)
    
    try:
        result = manager.create_variation_listing(
            cards=listing_cards,
            title="2025-26 Topps Chrome Basketball",
            description="2025-26 Topps Chrome Basketball",
            category_id="261328",  # Trading Cards
            price=1.00,
            quantity=1,
            condition="NEW",
            publish=False  # Create as draft first
        )
        
        print("\n" + "=" * 80)
        print("RESULT:")
        print("=" * 80)
        print(json.dumps(result, indent=2))
        print()
        
        if result.get("success"):
            print("✅ SUCCESS! Listing created successfully!")
            print(f"   Group Key: {result.get('groupKey')}")
            print(f"   Offer ID: {result.get('offerId')}")
            if result.get('listingId'):
                print(f"   Listing ID: {result.get('listingId')}")
        else:
            print("❌ FAILED!")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            
            # Show debug info if available
            if result.get('debug_info'):
                print("\nDebug Info:")
                debug_info = result.get('debug_info')
                if debug_info.get('raw_response'):
                    print(f"   Raw Response: {debug_info['raw_response'][:500]}")
        
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_listing_creation()
