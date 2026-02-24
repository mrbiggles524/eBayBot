"""
Manage eBay listings via API - View, Update, Delete listings created via API.
Since drafts may not appear in Seller Hub, use this to manage them via API.
"""
from ebay_api_client import eBayAPIClient
import sys
import json
from typing import List, Dict, Optional

sys.stdout.reconfigure(encoding='utf-8')

class ListingManager:
    """Manage listings via eBay API."""
    
    def __init__(self):
        self.client = eBayAPIClient()
    
    def list_all_groups(self) -> List[Dict]:
        """List all inventory item groups (variation listings)."""
        print("=" * 80)
        print("Listing All Inventory Item Groups")
        print("=" * 80)
        print()
        
        # Note: eBay API doesn't have a direct "list all groups" endpoint
        # We need to track group keys or query offers to find groups
        print("[INFO] eBay API doesn't provide a direct 'list all groups' endpoint.")
        print("       You need to know the group keys or query offers.")
        print()
        print("To find groups, you can:")
        print("  1. Query offers by SKU (if you know the SKUs)")
        print("  2. Track group keys when creating listings")
        print("  3. Use the 'get_group_by_sku' function if you know a SKU")
        print()
        
        return []
    
    def get_group_by_sku(self, sku: str) -> Optional[Dict]:
        """Get group information by SKU."""
        print(f"Getting group for SKU: {sku}")
        print()
        
        # Get offer first to find group key
        offer_result = self.client.get_offer_by_sku(sku)
        if not offer_result.get('success'):
            print(f"[ERROR] Could not get offer for SKU: {sku}")
            return None
        
        offer = offer_result['offer']
        group_key = offer.get('inventoryItemGroupKey')
        
        if not group_key or group_key == 'N/A':
            print(f"[WARNING] Offer {sku} is not linked to a group")
            print(f"  Offer ID: {offer.get('offerId')}")
            print(f"  Status: {offer.get('listingStatus')}")
            return None
        
        print(f"Found group key: {group_key}")
        print()
        
        # Get group details
        group_result = self.client.get_inventory_item_group(group_key)
        if not group_result.get('success'):
            print(f"[ERROR] Could not get group: {group_result.get('error')}")
            return None
        
        return group_result.get('data')
    
    def get_offer_by_sku(self, sku: str) -> Optional[Dict]:
        """Get offer details by SKU."""
        print(f"Getting offer for SKU: {sku}")
        print()
        
        result = self.client.get_offer_by_sku(sku)
        if not result.get('success'):
            print(f"[ERROR] {result.get('error')}")
            return None
        
        return result.get('offer')
    
    def display_group_info(self, group_key: str):
        """Display detailed group information."""
        print("=" * 80)
        print(f"Group Information: {group_key}")
        print("=" * 80)
        print()
        
        # Get group
        group_result = self.client.get_inventory_item_group(group_key)
        if not group_result.get('success'):
            print(f"[ERROR] {group_result.get('error')}")
            return
        
        group_data = group_result.get('data', {})
        
        print(f"Title: {group_data.get('title', 'N/A')}")
        print(f"Variant SKUs: {group_data.get('variantSKUs', [])}")
        print()
        
        # Display variesBy
        varies_by = group_data.get('variesBy', {})
        specifications = varies_by.get('specifications', [])
        if specifications:
            print("Variation Specifications:")
            for spec in specifications:
                print(f"  - {spec.get('name', 'N/A')}: {spec.get('values', [])}")
        print()
        
        # Get offers for each SKU
        variant_skus = group_data.get('variantSKUs', [])
        if variant_skus:
            print("Variant Offers:")
            for sku in variant_skus:
                offer = self.get_offer_by_sku(sku)
                if offer:
                    print(f"  SKU: {sku}")
                    print(f"    Offer ID: {offer.get('offerId')}")
                    print(f"    Status: {offer.get('listingStatus')}")
                    print(f"    Price: ${offer.get('pricingSummary', {}).get('price', {}).get('value', 'N/A')}")
                    print(f"    Quantity: {offer.get('availableQuantity', offer.get('quantity', 'N/A'))}")
                    print()
    
    def update_group_title(self, group_key: str, new_title: str):
        """Update group title."""
        print(f"Updating group title: {group_key}")
        print(f"New title: {new_title}")
        print()
        
        # Get current group
        group_result = self.client.get_inventory_item_group(group_key)
        if not group_result.get('success'):
            print(f"[ERROR] Could not get group: {group_result.get('error')}")
            return False
        
        group_data = group_result.get('data', {})
        
        # Build update with new title
        update_data = {
            "title": new_title,
            "variesBy": group_data.get('variesBy', {}),
            "variantSKUs": group_data.get('variantSKUs', [])
        }
        
        # Include inventoryItemGroup if it exists (though GET doesn't return it)
        # We'll try to preserve it
        update_data["inventoryItemGroup"] = {
            "aspects": {}  # Will be preserved by API
        }
        
        result = self.client.create_inventory_item_group(group_key, update_data)
        if result.get('success'):
            print("[OK] Group title updated")
            return True
        else:
            print(f"[ERROR] {result.get('error')}")
            return False
    
    def update_offer_price(self, sku: str, new_price: float):
        """Update offer price."""
        print(f"Updating price for SKU: {sku}")
        print(f"New price: ${new_price}")
        print()
        
        # Get current offer
        offer_result = self.client.get_offer_by_sku(sku)
        if not offer_result.get('success'):
            print(f"[ERROR] Could not get offer: {offer_result.get('error')}")
            return False
        
        offer = offer_result['offer']
        offer_id = offer.get('offerId')
        
        # Build update
        update_data = {
            "sku": sku,
            "marketplaceId": offer.get('marketplaceId', 'EBAY_US'),
            "format": offer.get('format', 'FIXED_PRICE'),
            "categoryId": offer.get('categoryId'),
            "pricingSummary": {
                "price": {
                    "value": str(new_price),
                    "currency": "USD"
                }
            },
            "quantity": offer.get('availableQuantity', offer.get('quantity', 1)),
            "availableQuantity": offer.get('availableQuantity', offer.get('quantity', 1)),
            "listingDuration": offer.get('listingDuration', 'GTC'),
            "merchantLocationKey": offer.get('merchantLocationKey')
        }
        
        result = self.client.update_offer(offer_id, update_data)
        if result.get('success'):
            print("[OK] Offer price updated")
            return True
        else:
            print(f"[ERROR] {result.get('error')}")
            return False
    
    def update_offer_quantity(self, sku: str, new_quantity: int):
        """Update offer quantity."""
        print(f"Updating quantity for SKU: {sku}")
        print(f"New quantity: {new_quantity}")
        print()
        
        # Get current offer
        offer_result = self.client.get_offer_by_sku(sku)
        if not offer_result.get('success'):
            print(f"[ERROR] Could not get offer: {offer_result.get('error')}")
            return False
        
        offer = offer_result['offer']
        offer_id = offer.get('offerId')
        
        # Build update
        update_data = {
            "sku": sku,
            "marketplaceId": offer.get('marketplaceId', 'EBAY_US'),
            "format": offer.get('format', 'FIXED_PRICE'),
            "categoryId": offer.get('categoryId'),
            "pricingSummary": offer.get('pricingSummary', {}),
            "quantity": new_quantity,
            "availableQuantity": new_quantity,
            "listingDuration": offer.get('listingDuration', 'GTC'),
            "merchantLocationKey": offer.get('merchantLocationKey')
        }
        
        result = self.client.update_offer(offer_id, update_data)
        if result.get('success'):
            print("[OK] Offer quantity updated")
            return True
        else:
            print(f"[ERROR] {result.get('error')}")
            return False
    
    def delete_group(self, group_key: str):
        """Delete an inventory item group and its offers."""
        print(f"Deleting group: {group_key}")
        print("[WARNING] This will delete the group and all associated offers!")
        print()
        
        # Get group to find SKUs
        group_result = self.client.get_inventory_item_group(group_key)
        if not group_result.get('success'):
            print(f"[ERROR] Could not get group: {group_result.get('error')}")
            return False
        
        group_data = group_result.get('data', {})
        variant_skus = group_data.get('variantSKUs', [])
        
        # Delete offers first
        for sku in variant_skus:
            offer_result = self.client.get_offer_by_sku(sku)
            if offer_result.get('success'):
                offer = offer_result['offer']
                offer_id = offer.get('offerId')
                
                # Delete offer
                delete_result = self.client._make_request('DELETE', f'/sell/inventory/v1/offer/{offer_id}')
                if delete_result.status_code in [200, 204]:
                    print(f"[OK] Deleted offer for SKU: {sku}")
                else:
                    print(f"[WARNING] Could not delete offer for SKU: {sku} (status: {delete_result.status_code})")
        
        # Delete group
        result = self.client.delete_inventory_item_group(group_key)
        if result.get('success'):
            print(f"[OK] Group deleted: {group_key}")
            return True
        else:
            print(f"[ERROR] {result.get('error')}")
            return False
    
    def list_test_listings(self):
        """List known test listings."""
        print("=" * 80)
        print("Known Test Listings")
        print("=" * 80)
        print()
        
        test_groups = [
            ("GROUPSAHF8A3F381768715399", "CARD_DIFF_APPROACH_TEST_1_0", "Different Approach Test"),
            ("GROUPSET1768715280", "CARD_SET_NORMAL_FLOW_TEST_CAR_1_0", "Normal Flow Test"),
            ("GROUPSET1768714571", "CARD_SET_FINAL_TEST_CARD_1_0", "Final Test Listing"),
        ]
        
        for group_key, sku, name in test_groups:
            print(f"Group: {group_key}")
            print(f"  Name: {name}")
            print(f"  SKU: {sku}")
            
            # Try to get group
            group_result = self.client.get_inventory_item_group(group_key)
            if group_result.get('success'):
                group_data = group_result.get('data', {})
                print(f"  Title: {group_data.get('title', 'N/A')}")
                print(f"  Status: Exists")
            else:
                print(f"  Status: Not found or deleted")
            
            # Try to get offer
            offer_result = self.client.get_offer_by_sku(sku)
            if offer_result.get('success'):
                offer = offer_result['offer']
                print(f"  Offer Status: {offer.get('listingStatus', 'N/A')}")
                print(f"  Price: ${offer.get('pricingSummary', {}).get('price', {}).get('value', 'N/A')}")
            else:
                print(f"  Offer Status: Not found")
            
            print()


def main():
    """Main function with examples."""
    manager = ListingManager()
    
    print("=" * 80)
    print("eBay Listing Manager - API-Based Management")
    print("=" * 80)
    print()
    print("Since drafts may not appear in Seller Hub, use this tool to:")
    print("  - View listing details")
    print("  - Update prices, quantities, titles")
    print("  - Delete listings")
    print("  - Check listing status")
    print()
    print("Examples:")
    print()
    print("1. View a group:")
    print("   manager.display_group_info('GROUPSAHF8A3F381768715399')")
    print()
    print("2. Get offer by SKU:")
    print("   manager.get_offer_by_sku('CARD_DIFF_APPROACH_TEST_1_0')")
    print()
    print("3. Update price:")
    print("   manager.update_offer_price('CARD_DIFF_APPROACH_TEST_1_0', 2.50)")
    print()
    print("4. Update quantity:")
    print("   manager.update_offer_quantity('CARD_DIFF_APPROACH_TEST_1_0', 5)")
    print()
    print("5. Update group title:")
    print("   manager.update_group_title('GROUPSAHF8A3F381768715399', 'New Title')")
    print()
    print("6. Delete a group:")
    print("   manager.delete_group('GROUPSAHF8A3F381768715399')")
    print()
    print("7. List test listings:")
    print("   manager.list_test_listings()")
    print()
    print("=" * 80)
    print()
    
    # Show test listings
    manager.list_test_listings()
    
    print()
    print("=" * 80)
    print("Interactive Usage")
    print("=" * 80)
    print()
    print("You can use this script interactively:")
    print("  python -i manage_listings_api.py")
    print()
    print("Then call methods like:")
    print("  >>> manager.display_group_info('GROUPSAHF8A3F381768715399')")
    print()


if __name__ == "__main__":
    main()
