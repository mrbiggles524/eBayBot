"""
Robust debugging script for eBay listing creation.
Tests multiple approaches to identify the correct API structure.
"""
import json
import time
from typing import Dict, List
from ebay_api_client import eBayAPIClient
from ebay_listing import eBayListingManager
from config import Config

class ListingDebugger:
    """Debug eBay listing creation with multiple approaches."""
    
    def __init__(self):
        self.api_client = eBayAPIClient()
        self.config = Config()
        self.policies = self.api_client.get_policy_ids()
        self.debug_log = []
    
    def log(self, message: str, data: Dict = None):
        """Log debug message with optional data."""
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "message": message,
            "data": data
        }
        self.debug_log.append(log_entry)
        print(f"[DEBUG {log_entry['timestamp']}] {message}")
        if data:
            print(f"  Data: {json.dumps(data, indent=2)[:500]}")
    
    def test_group_creation_approach_1(self, group_key: str, aspects: Dict, variant_skus: List[str], title: str):
        """Approach 1: Minimal group (only aspects and variantSKUs) - current approach"""
        self.log("Testing Approach 1: Minimal group (no title)")
        group_data = {
            "inventoryItemGroup": {
                "aspects": aspects
            },
            "variantSKUs": variant_skus
        }
        return self._test_group_creation(group_key, group_data, "Approach 1: Minimal")
    
    def test_group_creation_approach_2(self, group_key: str, aspects: Dict, variant_skus: List[str], title: str):
        """Approach 2: Group WITH title (despite docs saying not to)"""
        self.log("Testing Approach 2: Group WITH title (testing if eBay requires it)")
        # Validate title
        if not title or len(title) < 1:
            title = "Card Set Variation Listing"
        if len(title) > 80:
            title = title[:80]
        
        group_data = {
            "inventoryItemGroup": {
                "aspects": aspects,
                "title": title
            },
            "variantSKUs": variant_skus
        }
        return self._test_group_creation(group_key, group_data, "Approach 2: With Title")
    
    def test_group_creation_approach_3(self, group_key: str, aspects: Dict, variant_skus: List[str], title: str):
        """Approach 3: Group with title and description"""
        self.log("Testing Approach 3: Group with title and description")
        if not title or len(title) < 1:
            title = "Card Set Variation Listing"
        if len(title) > 80:
            title = title[:80]
        
        group_data = {
            "inventoryItemGroup": {
                "aspects": aspects,
                "title": title,
                "description": "Card set variation listing"
            },
            "variantSKUs": variant_skus
        }
        return self._test_group_creation(group_key, group_data, "Approach 3: With Title & Description")
    
    def test_group_creation_approach_4(self, group_key: str, aspects: Dict, variant_skus: List[str], title: str):
        """Approach 4: Group with only one aspect (Card Name only)"""
        self.log("Testing Approach 4: Single aspect (Card Name only)")
        single_aspect = {"Card Name": aspects.get("Card Name", [])}
        if not single_aspect["Card Name"]:
            single_aspect = {"Card Number": aspects.get("Card Number", [])}
        
        group_data = {
            "inventoryItemGroup": {
                "aspects": single_aspect
            },
            "variantSKUs": variant_skus
        }
        return self._test_group_creation(group_key, group_data, "Approach 4: Single Aspect")
    
    def test_group_creation_approach_5(self, group_key: str, aspects: Dict, variant_skus: List[str], title: str):
        """Approach 5: Group with title and single aspect"""
        self.log("Testing Approach 5: Title + Single Aspect")
        if not title or len(title) < 1:
            title = "Card Set Variation Listing"
        if len(title) > 80:
            title = title[:80]
        
        single_aspect = {"Card Name": aspects.get("Card Name", [])}
        if not single_aspect["Card Name"]:
            single_aspect = {"Card Number": aspects.get("Card Number", [])}
        
        group_data = {
            "inventoryItemGroup": {
                "aspects": single_aspect,
                "title": title
            },
            "variantSKUs": variant_skus
        }
        return self._test_group_creation(group_key, group_data, "Approach 5: Title + Single Aspect")
    
    def _test_group_creation(self, group_key: str, group_data: Dict, approach_name: str) -> Dict:
        """Test creating a group with given data."""
        self.log(f"Attempting group creation: {approach_name}")
        self.log(f"Group key: {group_key}")
        self.log(f"Group data structure", group_data)
        
        # Create clean copy
        clean_data = {}
        if 'inventoryItemGroup' in group_data:
            clean_data['inventoryItemGroup'] = {}
            for key in group_data['inventoryItemGroup']:
                clean_data['inventoryItemGroup'][key] = group_data['inventoryItemGroup'][key]
        
        if 'variantSKUs' in group_data:
            clean_data['variantSKUs'] = group_data['variantSKUs']
        
        # Log the exact payload
        json_payload = json.dumps(clean_data, indent=2)
        self.log(f"Exact JSON payload for {approach_name}")
        print(json_payload)
        
        # Try to create the group
        try:
            result = self.api_client.create_inventory_item_group(group_key, clean_data)
            
            if result.get("success"):
                self.log(f"✅ SUCCESS with {approach_name}!", {"group_key": group_key})
                return {
                    "success": True,
                    "approach": approach_name,
                    "group_key": group_key,
                    "data": result.get("data")
                }
            else:
                error = result.get("error", "Unknown error")
                raw_response = result.get("raw_response", "")
                self.log(f"❌ FAILED with {approach_name}", {
                    "error": error,
                    "raw_response": raw_response[:500] if raw_response else None
                })
                return {
                    "success": False,
                    "approach": approach_name,
                    "error": error,
                    "raw_response": raw_response
                }
        except Exception as e:
            self.log(f"❌ EXCEPTION with {approach_name}", {"exception": str(e)})
            return {
                "success": False,
                "approach": approach_name,
                "error": f"Exception: {str(e)}"
            }
    
    def test_all_approaches(self, cards: List[Dict], title: str, description: str, 
                          category_id: str, price, quantity: int = 1, condition: str = None):
        """Test all approaches to find what works."""
        self.log("=" * 80)
        self.log("STARTING COMPREHENSIVE DEBUGGING SESSION")
        self.log("=" * 80)
        
        # First, create inventory items (required for group)
        self.log("Step 1: Creating inventory items...")
        listing_manager = eBayListingManager()
        
        # Get the method that creates items (we need to access the private method)
        # Actually, let's use the listing manager's method
        try:
            # We'll need to create items first - let's call the internal method
            from ebay_listing import eBayListingManager
            manager = eBayListingManager()
            
            # Create a test listing to get the items created
            # Actually, let's extract the item creation logic
            created_items = []
            errors = []
            
            for card in cards:
                if card.get('quantity', 0) <= 0:
                    continue
                
                # Generate SKU
                card_name = card.get('name', '').replace(' ', '_').replace("'", '').upper()[:30]
                card_number = str(card.get('number', ''))[:10]
                set_name_clean = "CARDSET"
                sku = f"CARD_{set_name_clean}_{card_name}_{card_number}_{int(time.time())}"
                
                # Create inventory item
                item_data = {
                    "product": {
                        "title": f"{card.get('name', 'Card')} #{card.get('number', '')}",
                        "aspects": {
                            "Card Name": [card.get('name', '')],
                            "Card Number": [str(card.get('number', ''))]
                        }
                    },
                    "condition": condition or "NEW",
                    "conditionDescription": "Like New"
                }
                
                result = self.api_client.create_inventory_item(sku, item_data)
                if result.get("success"):
                    created_items.append({
                        "sku": sku,
                        "card": card
                    })
                else:
                    errors.append(f"Failed to create item for {card.get('name')}: {result.get('error')}")
            
            if not created_items:
                return {
                    "success": False,
                    "error": "Failed to create any inventory items",
                    "errors": errors
                }
            
            self.log(f"Created {len(created_items)} inventory items")
            
            # Build aspects
            card_names = [name for name in set(card.get('name', '') for card in cards if card.get('name')) if name and str(name).strip()]
            card_numbers = [num for num in set(card.get('number', '') for card in cards if card.get('number')) if num and str(num).strip()]
            
            aspects = {}
            if card_names:
                aspects["Card Name"] = card_names
            if card_numbers:
                aspects["Card Number"] = card_numbers
            
            variant_skus = [item["sku"] for item in created_items]
            
            # Generate unique group keys for each test
            base_time = int(time.time())
            
            # Test all approaches
            results = []
            
            # Approach 1: Minimal (current)
            group_key_1 = f"DEBUG_GROUP_1_{base_time}"
            result_1 = self.test_group_creation_approach_1(group_key_1, aspects, variant_skus, title)
            results.append(result_1)
            if result_1.get("success"):
                self.log("🎉 FOUND WORKING APPROACH: Approach 1 (Minimal)")
                return result_1
            time.sleep(2)  # Rate limiting
            
            # Approach 2: With Title
            group_key_2 = f"DEBUG_GROUP_2_{base_time}"
            result_2 = self.test_group_creation_approach_2(group_key_2, aspects, variant_skus, title)
            results.append(result_2)
            if result_2.get("success"):
                self.log("🎉 FOUND WORKING APPROACH: Approach 2 (With Title)")
                return result_2
            time.sleep(2)
            
            # Approach 4: Single Aspect (skip 3 for now)
            group_key_4 = f"DEBUG_GROUP_4_{base_time}"
            result_4 = self.test_group_creation_approach_4(group_key_4, aspects, variant_skus, title)
            results.append(result_4)
            if result_4.get("success"):
                self.log("🎉 FOUND WORKING APPROACH: Approach 4 (Single Aspect)")
                return result_4
            time.sleep(2)
            
            # Approach 5: Title + Single Aspect
            group_key_5 = f"DEBUG_GROUP_5_{base_time}"
            result_5 = self.test_group_creation_approach_5(group_key_5, aspects, variant_skus, title)
            results.append(result_5)
            if result_5.get("success"):
                self.log("🎉 FOUND WORKING APPROACH: Approach 5 (Title + Single Aspect)")
                return result_5
            time.sleep(2)
            
            # Approach 3: With Title & Description
            group_key_3 = f"DEBUG_GROUP_3_{base_time}"
            result_3 = self.test_group_creation_approach_3(group_key_3, aspects, variant_skus, title)
            results.append(result_3)
            if result_3.get("success"):
                self.log("🎉 FOUND WORKING APPROACH: Approach 3 (With Title & Description)")
                return result_3
            
            # None worked - return summary
            self.log("=" * 80)
            self.log("ALL APPROACHES FAILED")
            self.log("=" * 80)
            
            return {
                "success": False,
                "error": "All test approaches failed",
                "results": results,
                "debug_log": self.debug_log
            }
            
        except Exception as e:
            self.log(f"EXCEPTION during testing: {str(e)}")
            return {
                "success": False,
                "error": f"Exception: {str(e)}",
                "debug_log": self.debug_log
            }
    
    def save_debug_log(self, filename: str = "debug_listing_log.json"):
        """Save debug log to file."""
        with open(filename, 'w') as f:
            json.dump(self.debug_log, f, indent=2)
        print(f"Debug log saved to {filename}")


def main():
    """Main function to run debugging."""
    print("=" * 80)
    print("eBay Listing Creation Debugger")
    print("=" * 80)
    print()
    
    # Example test data (you can modify this)
    test_cards = [
        {"name": "Pascal Siakam", "number": "1", "quantity": 1, "team": "Indiana Pacers"},
        {"name": "Zaccharie Risacher", "number": "2", "quantity": 2, "team": "Atlanta Hawks"},
        {"name": "Tyrese Haliburton", "number": "3", "quantity": 1, "team": "Indiana Pacers"},
        {"name": "Ty Jerome", "number": "4", "quantity": 2, "team": "Cleveland Cavaliers"}
    ]
    
    test_title = "2025-26 Topps Chrome Basketball"
    test_description = "2025-26 Topps Chrome Basketball"
    test_category = "261328"  # Trading Cards
    test_price = 1.00
    
    debugger = ListingDebugger()
    
    print("\nStarting comprehensive testing...")
    print("This will test multiple API approaches to find what works.\n")
    
    result = debugger.test_all_approaches(
        cards=test_cards,
        title=test_title,
        description=test_description,
        category_id=test_category,
        price=test_price,
        quantity=1,
        condition="NEW"
    )
    
    # Save debug log
    debugger.save_debug_log()
    
    print("\n" + "=" * 80)
    print("DEBUGGING COMPLETE")
    print("=" * 80)
    print(f"\nResult: {json.dumps(result, indent=2)}")
    
    if result.get("success"):
        print(f"\n✅ SUCCESS! Working approach: {result.get('approach')}")
        print(f"Group key: {result.get('group_key')}")
    else:
        print(f"\n❌ All approaches failed. Check debug_listing_log.json for details.")


if __name__ == "__main__":
    main()
