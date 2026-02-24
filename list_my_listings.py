"""
Simple script to list and view your listings via API.
"""
from manage_listings_api import ListingManager
import sys

sys.stdout.reconfigure(encoding='utf-8')

def main():
    manager = ListingManager()
    
    print("=" * 80)
    print("Your eBay Listings (via API)")
    print("=" * 80)
    print()
    
    # Show test listings
    manager.list_test_listings()
    
    print()
    print("=" * 80)
    print("To view details of a specific listing:")
    print("=" * 80)
    print()
    print("Example:")
    print("  manager.display_group_info('GROUPSAHF8A3F381768715399')")
    print()
    print("To update a listing:")
    print("  manager.update_offer_price('CARD_DIFF_APPROACH_TEST_1_0', 2.50)")
    print("  manager.update_offer_quantity('CARD_DIFF_APPROACH_TEST_1_0', 5)")
    print()
    print("To delete a listing:")
    print("  manager.delete_group('GROUPSAHF8A3F381768715399')")
    print()

if __name__ == "__main__":
    main()
