"""
Test listing creation directly with the same code path as the UI.
This will help identify if the issue is in the data format or something else.
"""
from ebay_listing import eBayListingManager
import json

def main():
    print("=" * 80)
    print("Test Listing Creation (Direct)")
    print("=" * 80)
    print()
    
    # Create test cards (similar to what the UI would send)
    test_cards = [
        {
            "name": "Test Card 1",
            "number": "1",
            "set_name": "TEST_SET",
            "quantity": 1,
            "weight": 0.1
        },
        {
            "name": "Test Card 2", 
            "number": "2",
            "set_name": "TEST_SET",
            "quantity": 1,
            "weight": 0.1
        }
    ]
    
    print("Creating test listing with 2 cards...")
    print()
    
    manager = eBayListingManager()
    
    try:
        result = manager.create_variation_listing(
            cards=test_cards,
            title="Test Listing - Write Permission Check",
            description="Testing if listing creation works after opt-in",
            category_id="261328",  # Trading Cards category
            price=1.00,
            quantity=1,
            condition="New",
            publish=False  # Don't publish, just create draft
        )
        
        if result.get('success'):
            print("[OK] Listing creation SUCCESSFUL!")
            print()
            print("Result:")
            print(json.dumps(result, indent=2))
            print()
            print("This confirms:")
            print("1. Token has all required scopes")
            print("2. Account has write permissions")
            print("3. Listing creation code works")
            print()
            print("If the UI still fails, the issue might be:")
            print("- Different token in UI")
            print("- Data format from UI")
            print("- SKU conflicts")
            
        else:
            error = result.get('error', 'Unknown error')
            errors = result.get('errors', [])
            
            print("[ERROR] Listing creation FAILED!")
            print()
            print(f"Error: {error}")
            print()
            
            if errors:
                print("Detailed errors:")
                for err in errors[:5]:
                    print(f"  - {err}")
            
            print()
            print("This will help identify the exact issue.")
            
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
