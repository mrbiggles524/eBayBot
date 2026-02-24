"""
Example: Update a listing's price and quantity via API.
"""
from manage_listings_api import ListingManager
import sys

sys.stdout.reconfigure(encoding='utf-8')

def update_example():
    """Example of updating a listing."""
    manager = ListingManager()
    
    # Example SKU and group
    sku = "CARD_DIFF_APPROACH_TEST_1_0"
    group_key = "GROUPSAHF8A3F381768715399"
    
    print("=" * 80)
    print("Example: Updating a Listing")
    print("=" * 80)
    print()
    
    # Step 1: View current listing
    print("Step 1: Viewing current listing...")
    print()
    manager.display_group_info(group_key)
    
    print()
    print("=" * 80)
    print()
    
    # Step 2: Update price
    print("Step 2: Updating price to $2.50...")
    print()
    manager.update_offer_price(sku, 2.50)
    
    print()
    print("=" * 80)
    print()
    
    # Step 3: Update quantity
    print("Step 3: Updating quantity to 3...")
    print()
    manager.update_offer_quantity(sku, 3)
    
    print()
    print("=" * 80)
    print()
    
    # Step 4: View updated listing
    print("Step 4: Viewing updated listing...")
    print()
    manager.display_group_info(group_key)
    
    print()
    print("=" * 80)
    print("[SUCCESS] Listing updated via API!")
    print("=" * 80)
    print()

if __name__ == "__main__":
    # Uncomment to run the example:
    # update_example()
    
    print("=" * 80)
    print("Update Listing Example")
    print("=" * 80)
    print()
    print("This script shows how to update listings via API.")
    print()
    print("To run the example, uncomment 'update_example()' in the code.")
    print()
    print("Or use the ListingManager directly:")
    print()
    print("  from manage_listings_api import ListingManager")
    print("  manager = ListingManager()")
    print("  manager.update_offer_price('CARD_DIFF_APPROACH_TEST_1_0', 2.50)")
    print("  manager.update_offer_quantity('CARD_DIFF_APPROACH_TEST_1_0', 3)")
    print()
