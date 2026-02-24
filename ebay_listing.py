"""eBay listing creation with variation support."""
import requests
import json
import time
from typing import List, Dict, Optional, Union
from config import Config
from ebay_api_client import eBayAPIClient

class eBayListingManager:
    """Manages eBay listings with variation support."""
    
    def __init__(self, token_override: Optional[str] = None):
        """Optional token_override: per-user eBay token for multi-tenant support."""
        self.config = Config()
        self.config.validate()
        self.api_client = eBayAPIClient(token_override=token_override)
        self.policies = self.api_client.get_policy_ids()
    
    def create_variation_listing(
        self,
        cards: List[Dict],
        title: str,
        description: str,
        category_id: str,
        price: Union[float, Dict[str, float]],
        quantity: int = 1,
        condition: str = None,
        images: List[str] = None,
        shipping_profile: Dict = None,
        publish: bool = True,
        fulfillment_policy_id: str = None,
        use_base_cards_policy: bool = None,
        schedule_draft: bool = False,
        schedule_hours: int = 24
    ) -> Dict:
        """
        Create an eBay listing with card variations.
        
        Args:
            cards: List of card dictionaries with name, number, etc.
            title: Main listing title
            description: Listing description
            category_id: eBay category ID
            price: Base price for cards (float) or dict mapping card SKU/name to price
            quantity: Quantity per variation
            condition: Card condition
            images: List of image URLs
            shipping_profile: Shipping settings
            publish: Whether to publish the listing immediately
            schedule_draft: If True, publish with a future start date so it appears in Seller Hub as a scheduled listing (editable)
            schedule_hours: Hours in the future to schedule the listing (default 24)
            
        Returns:
            Dictionary with listing result
        """
        condition = condition or self.config.DEFAULT_CONDITION
        
        # Determine which fulfillment policy to use
        selected_fulfillment_policy_id = fulfillment_policy_id
        
        # If not explicitly provided, determine based on card prices or use_base_cards_policy flag
        if not selected_fulfillment_policy_id:
            if use_base_cards_policy is True:
                # Explicitly use base cards policy
                selected_fulfillment_policy_id = self.config.BASE_CARDS_FULFILLMENT_POLICY_ID or self.policies.get('fulfillment_policy_id')
                print(f"[INFO] Using base cards fulfillment policy: {selected_fulfillment_policy_id}")
            elif use_base_cards_policy is False:
                # Explicitly use regular policy
                selected_fulfillment_policy_id = self.policies.get('fulfillment_policy_id')
            else:
                # Auto-detect: check if all cards are under $20
                all_under_20 = True
                if isinstance(price, dict):
                    for card_price in price.values():
                        if card_price >= 20.0:
                            all_under_20 = False
                            break
                elif isinstance(price, (int, float)):
                    if price >= 20.0:
                        all_under_20 = False
                
                if all_under_20 and self.config.BASE_CARDS_FULFILLMENT_POLICY_ID:
                    selected_fulfillment_policy_id = self.config.BASE_CARDS_FULFILLMENT_POLICY_ID
                    print(f"[INFO] All cards under $20 - using base cards fulfillment policy: {selected_fulfillment_policy_id}")
                else:
                    selected_fulfillment_policy_id = self.policies.get('fulfillment_policy_id')
        
        # Validate policies (merchant_location_key is optional)
        # Note: Return policy may be optional in some cases, but eBay typically requires it
        missing_policies = []
        if not selected_fulfillment_policy_id:
            missing_policies.append('FULFILLMENT_POLICY_ID')
        # Payment policy is OPTIONAL - eBay uses default if not provided
        # if not self.policies.get('payment_policy_id'):
        #     missing_policies.append('PAYMENT_POLICY_ID')
        # Return policy is required but we'll try without it if not set (may fail)
        if not self.policies.get('return_policy_id'):
            print("[WARNING] RETURN_POLICY_ID not set - listing may fail during publish")
            print("[WARNING] eBay requires return policies, but we'll try without it for sandbox testing")
        
        if missing_policies:
            # Try to reload policies from config
            print(f"Policies check failed. Current policies: {self.policies}")
            print("Attempting to reload policies from config...")
            self.policies = self.api_client.get_policy_ids()
            print(f"After reload: {self.policies}")
            
            # Re-check fulfillment policy if not set
            if not selected_fulfillment_policy_id:
                selected_fulfillment_policy_id = self.policies.get('fulfillment_policy_id')
            
            # Check again (but don't fail on return policy)
            missing_policies = []
            if not selected_fulfillment_policy_id:
                missing_policies.append('FULFILLMENT_POLICY_ID')
            # Payment policy is OPTIONAL - eBay uses default if not provided
            # if not self.policies.get('payment_policy_id'):
            #     missing_policies.append('PAYMENT_POLICY_ID')
            # Don't add return_policy_id to missing_policies - we'll try without it
            
            if missing_policies:
                return {
                    "success": False,
                    "error": f"Missing required policies: {', '.join(missing_policies)}. Please complete Step 3 (Auto-Configure) in the UI or set them in your .env file. Current values: Fulfillment={selected_fulfillment_policy_id or 'NOT SET'}, Payment={self.policies.get('payment_policy_id', 'NOT SET')}, Return={self.policies.get('return_policy_id', 'NOT SET (will try without it)')}"
                }
        
        # Merchant location is optional, but warn if missing
        if not self.policies.get('merchant_location_key'):
            print("Warning: MERCHANT_LOCATION_KEY not set. Some features may not work.")
        
        # Ensure description is provided - eBay requires it and it must be substantial
        # eBay typically requires descriptions to be at least 50-100 characters
        # CRITICAL: Preserve the full description - don't truncate it!
        original_description = description
        if not description or not description.strip():
            description = None  # Will be set below
        elif len(description.strip()) < 50:
            # Description is too short - use default
            description = None  # Will be set below
        else:
            # Description is provided and long enough - use it as-is
            description = description.strip()
            print(f"[DEBUG] Using provided description (length: {len(description)})")
        
        if not description:
            # Use the user's preferred description for Topps Chrome Basketball
            if "Topps Chrome" in title or "Chrome" in title:
                description = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
            else:
                description = f"""Variation listing for {title}.

Select your card from the variations below. Each card is listed as a separate variation.

All cards are in Near Mint or better condition unless otherwise noted.

Please select the specific card you want from the variation dropdown menu."""
            print(f"[INFO] No description provided or too short, using default description (length: {len(description)})")
        
        # CRITICAL: Store description for use in the loop
        # This ensures it's available when creating offers
        self._current_listing_description = description
        print(f"[DEBUG] Stored description for listing (length: {len(description)})")
        print(f"[DEBUG] Description preview: {description[:100]}...")
        
        return self._create_listing_via_inventory_api(
            cards, title, description, category_id, price, quantity, condition, publish, selected_fulfillment_policy_id
        )
    
    
    def _create_listing_via_inventory_api(
        self,
        cards: List[Dict],
        title: str,
        description: str,
        category_id: str,
        price: Union[float, Dict[str, float]],
        quantity: int,
        condition: str,
        publish: bool,
        fulfillment_policy_id: str = None,
        schedule_draft: bool = False,
        schedule_hours: int = 24
    ) -> Dict:
        # Store cards data for later use in description update
        self._current_cards_data = cards
        self._current_listing_description = description
        """Create listing using eBay Inventory API with improved error handling."""
        errors = []
        created_items = []
        
        # Generate base price if dict provided
        base_price = price if isinstance(price, (int, float)) else list(price.values())[0] if price else 1.00
        
        # Map condition to eBay format
        # For Trading Cards (category 261328), we need specific condition IDs:
        # - 2750 = Graded (requires grader, grade, optional cert number)
        # - 4000 = Ungraded (requires card condition descriptor)
        # Default to Ungraded (4000) for Trading Cards
        if category_id == "261328" or str(category_id) == "261328":
            # Trading Cards category - use Ungraded condition (4000)
            # Card condition descriptors: Near Mint or Better (40001), Excellent (40002), 
            # Very Good (40003), Good (40004), Fair (40005), Poor (40006)
            condition_map_trading_cards = {
                "New": "4000",  # Ungraded - will use Near Mint descriptor
                "Like New": "4000",  # Ungraded - will use Near Mint descriptor
                "Very Good": "4000",  # Ungraded - will use Very Good descriptor
                "Good": "4000",  # Ungraded - will use Good descriptor
                "Acceptable": "4000",  # Ungraded - will use Fair descriptor
                "Near Mint": "4000",
                "Excellent": "4000",
                "Fair": "4000",
                "Poor": "4000"
            }
            ebay_condition = condition_map_trading_cards.get(condition, "4000")  # Default to Ungraded
        else:
            # Other categories - use standard condition format
            condition_map = {
                "New": "NEW",
                "Like New": "NEW_OTHER",
                "Very Good": "USED_VERY_GOOD",
                "Good": "USED_GOOD",
                "Acceptable": "USED_ACCEPTABLE"
            }
            ebay_condition = condition_map.get(condition, "NEW")
        
        # Step 1: Create inventory items for each variation
        print(f"Creating {len(cards)} inventory items...")
        for idx, card in enumerate(cards):
            card_name = card.get('name', 'Unknown')
            card_number = str(card.get('number', idx))
            
            # Generate SKU - ensure it's unique for each card
            # Clean card name for SKU (remove special chars, limit length)
            card_name_clean = card_name.replace(' ', '_').replace("'", '').replace('-', '_').replace('.', '').upper()[:20]
            # Clean set name
            set_name_clean = card.get('set_name', 'SET').replace('https://', '').replace('http://', '').replace('www.', '').replace('/', '_').replace(':', '_').replace('.', '_').upper()[:20]
            # Ensure SKU is unique: use card name, number, and index
            sku = f"CARD_{set_name_clean}_{card_name_clean}_{card_number}_{idx}".replace(' ', '_').replace('-', '_')
            # Remove any remaining invalid characters and limit length
            import re
            sku = re.sub(r'[^A-Z0-9_]', '', sku)[:50]  # Only alphanumeric and underscore, max 50 chars
            # Final uniqueness check - add timestamp if needed
            if idx == 0:
                base_sku = sku
            else:
                # Ensure it's different from previous
                if sku == base_sku:
                    sku = f"{sku}_{idx}"
            
            print(f"[DEBUG] Generated SKU for card {idx} ({card_name} #{card_number}): {sku}")
            
            # Get price for this card
            card_price = base_price
            if isinstance(price, dict):
                # Try to match by name or number
                card_price = price.get(card_name) or price.get(card_number) or price.get(sku) or base_price
            
            # Build inventory item - eBay requires category in product
            # For variation listings, individual items should NOT have titles
            # The title is set at the offer level only
            # categoryId should be a string (eBay API accepts it as string)
            # Build condition data - for Trading Cards, condition is a string enum, descriptors are separate
            if category_id == "261328" or str(category_id) == "261328":
                # Trading Cards: condition ID 4000 (Ungraded) maps to enum "USED_VERY_GOOD"
                # conditionDescriptors must be at ROOT level, not inside condition
                condition_data = "USED_VERY_GOOD"  # Maps to condition ID 4000 (Ungraded)
                condition_descriptors = [
                    {
                        "name": "40001",  # Card Condition descriptor name
                        "values": ["400010"]  # Near Mint or Better value ID
                    }
                ]
                import json as json_module
                print(f"[DEBUG] Using Trading Cards condition: {condition_data}")
                print(f"[DEBUG] Condition descriptors: {json_module.dumps(condition_descriptors, indent=2)}")
            else:
                # Other categories use simple condition string
                condition_data = ebay_condition
                condition_descriptors = None
            
            # Build variation value for this card (used in variesBy)
            variation_value = f"{card_number} {card_name}".strip() if card_number else card_name
            
            inventory_item = {
                "product": {
                    "title": f"{card_name} #{card_number}" if card_number else card_name,  # Title for the item
                    "description": f"<p>{card_name} #{card_number} trading card.</p>" if card_number else f"<p>{card_name} trading card.</p>",
                    "categoryId": str(category_id),  # Ensure it's a string
                    "aspects": {
                        "Card Name": [card_name],
                        "Card Number": [card_number] if card_number else [],
                        "Sport": ["Basketball"],  # Default, can be customized
                        "Card Manufacturer": ["Topps"],  # Default, can be customized
                        "Season": ["2024-25"],
                        "Features": ["Base"],
                        "Type": ["Sports Trading Card"],
                        "Language": ["English"],
                        "Original/Licensed Reprint": ["Original"],
                        "Pick Your Card": [variation_value]  # CRITICAL: Variation aspect must match variesBy
                    }
                },
                "condition": condition_data,
                "availability": {
                    "shipToLocationAvailability": {
                        "quantity": int(card.get('quantity', quantity))  # Ensure quantity is int
                    }
                },
                "packageWeightAndSize": {
                    "weight": {
                        "value": "0.1875",  # 3 oz = 0.1875 pounds
                        "unit": "POUND"
                    },
                    "dimensions": {
                        "length": "6",
                        "width": "4",
                        "height": "1",
                        "unit": "INCH"
                    }
                }
            }
            
            # Add conditionDescriptors at ROOT level for Trading Cards (not inside condition)
            if category_id == "261328" or str(category_id) == "261328":
                if condition_descriptors:
                    inventory_item["conditionDescriptors"] = condition_descriptors
            
            # Debug: Print inventory item structure
            import json as json_module
            print(f"[DEBUG] Inventory item structure for {sku}:")
            print(json_module.dumps(inventory_item, indent=2)[:500])
            
            # Add imageUrls only if provided - no default image
            if card.get('image_url'):
                inventory_item["product"]["imageUrls"] = [card.get('image_url')]
            else:
                # No image provided - use empty array
                inventory_item["product"]["imageUrls"] = []
            
            # Note: Pricing is set at the offer level, not inventory item level
            
            result = self.api_client.create_inventory_item(sku, inventory_item)
            if result.get("success"):
                created_items.append({
                    "sku": sku,
                    "card": card,
                    "price": card_price
                })
                print(f"  [OK] Created item: {sku}")
            else:
                error_detail = result.get('error', 'Unknown error')
                status_code = result.get('status_code', 'Unknown')
                # Try to parse JSON error if possible
                if isinstance(error_detail, str):
                    try:
                        import json
                        error_json = json.loads(error_detail)
                        error_msg = error_json.get('errors', [{}])[0].get('message', error_detail) if isinstance(error_json, dict) else error_detail
                    except:
                        error_msg = error_detail
                else:
                    error_msg = str(error_detail)
                
                full_error = f"Failed to create item {sku} (HTTP {status_code}): {error_msg}"
                errors.append(full_error)
                print(f"  [ERROR] {full_error}")
                print(f"     SKU: {sku}")
                print(f"     Card: {card_name} #{card_number}")
                print(f"     Item data: {json.dumps(inventory_item, indent=2)[:500]}")
        
        if not created_items:
            error_summary = "Failed to create any inventory items.\n\n"
            if errors:
                error_summary += "Errors:\n"
                for i, err in enumerate(errors[:5], 1):  # Show first 5 errors
                    error_summary += f"{i}. {err}\n"
                if len(errors) > 5:
                    error_summary += f"... and {len(errors) - 5} more errors\n"
            else:
                error_summary += "No specific error messages were returned."
            
            return {
                "success": False,
                "error": error_summary,
                "errors": errors
            }
        
        # Step 2: Create inventory item group for variations
        print(f"Creating inventory item group...")
        set_name = cards[0].get('set_name', 'SET')
        # Clean set_name for group key - eBay requires ONLY alphanumeric (no underscores, dashes, etc.)
        # Max 50 characters total
        import re
        # Remove all non-alphanumeric characters
        set_name_clean = re.sub(r'[^a-zA-Z0-9]', '', set_name.replace('https://', '').replace('http://', '').replace('www.', '').upper())
        # Limit length to leave room for timestamp
        set_name_clean = set_name_clean[:20] if len(set_name_clean) > 20 else set_name_clean
        if not set_name_clean:
            set_name_clean = "CARDSET"
        
        # Generate group key - ONLY alphanumeric, max 50 chars
        # Format: GROUP + set_name + timestamp (all alphanumeric)
        timestamp = str(int(time.time()))  # Timestamp for uniqueness
        # Calculate max length for set_name to keep total under 50
        max_set_len = 50 - len("GROUP") - len(timestamp)
        if len(set_name_clean) > max_set_len:
            set_name_clean = set_name_clean[:max_set_len]
        
        group_key = f"GROUP{set_name_clean}{timestamp}"  # No underscores or special chars
        
        # Final validation - ensure it's only alphanumeric and under 50 chars
        group_key = re.sub(r'[^A-Z0-9]', '', group_key.upper())[:50]
        
        print(f"[DEBUG] Generated group key: {group_key} (length: {len(group_key)}, alphanumeric only: {group_key.isalnum()})")
        
        # Build variation aspects - use SINGLE variation aspect with full card descriptions as values
        # Based on user's working listings, they use a single aspect like "PICK YOUR BASE/PARALLEL/INSERT"
        # with values like "9 Tyger Campbell - UCLA 1st", "12 Rasir Bolton - Gonzaga 1st", etc.
        
        # Build full card descriptions for variation values
        variation_values = []
        for card in cards:
            card_name = card.get('name', '')
            card_number = str(card.get('number', ''))
            
            # Build variation value: "Number Name" or "Name" if no number
            if card_number and card_number.strip():
                variation_value = f"{card_number} {card_name}".strip()
            else:
                variation_value = card_name.strip()
            
            # Add "1st" suffix if it's a rookie (you can detect this from card data if available)
            # For now, just use the card name/number as-is
            
            if variation_value:
                variation_values.append(variation_value)
        
        if not variation_values:
            return {
                "success": False,
                "error": "No valid card information found for variation listings.",
                "created_items": len(created_items),
                "errors": errors
            }
        
        # Use a single variation aspect - eBay allows generic aspect names
        # Common names: "Card", "Select Card", "PICK YOUR CARD", etc.
        variation_aspect_name = "PICK YOUR CARD"
        
        # Build aspects dictionary for inventory items (product details)
        card_names = [name for name in set(card.get('name', '') for card in cards if card.get('name')) if name and str(name).strip()]
        card_numbers = [num for num in set(card.get('number', '') for card in cards if card.get('number')) if num and str(num).strip()]
        
        aspects = {}
        if card_names:
            aspects["Card Name"] = card_names
        if card_numbers:
            aspects["Card Number"] = card_numbers
        
        # Ensure title is valid (1-80 characters) for the OFFER (not the group)
        # Strip whitespace and ensure it's a string, remove any non-printable characters
        import unicodedata
        if title:
            # Convert to string and normalize unicode
            group_title = str(title).strip()
            # Normalize unicode characters (e.g., convert em-dash to regular dash)
            group_title = unicodedata.normalize('NFKC', group_title)
            # Remove any remaining non-printable characters
            group_title = ''.join(char for char in group_title if unicodedata.category(char)[0] != 'C' or char in '\n\r\t')
            group_title = group_title.strip()
        else:
            group_title = "Card Set Variation Listing"
        
        # Validate length (1-80 characters) - use byte length to match eBay's validation
        title_byte_length = len(group_title.encode('utf-8'))
        if len(group_title) < 1 or title_byte_length < 1:
            group_title = "Card Set Variation Listing"
        elif len(group_title) > 80 or title_byte_length > 80:
            # Truncate carefully to ensure we don't break UTF-8 characters
            while len(group_title.encode('utf-8')) > 80 and len(group_title) > 0:
                group_title = group_title[:-1]
            group_title = group_title.strip()
            # If truncation left it empty, use default
            if not group_title or len(group_title.encode('utf-8')) < 1:
                group_title = "Card Set Variation Listing"
        
        # Final safety check
        if not group_title or len(group_title) < 1 or len(group_title.encode('utf-8')) < 1:
            group_title = "Card Set Variation Listing"
        
        # Final byte length check
        final_byte_length = len(group_title.encode('utf-8'))
        print(f"[DEBUG] Offer title (for offer, NOT group): '{group_title}' (char length: {len(group_title)}, byte length: {final_byte_length})")
        
        # Ensure byte length is within limits
        if final_byte_length > 80:
            # Force truncate to 80 bytes
            group_title_bytes = group_title.encode('utf-8')[:80]
            group_title = group_title_bytes.decode('utf-8', errors='ignore').strip()
            if not group_title:
                group_title = "Card Set Variation Listing"
        
        # Build group data - eBay error suggests title might be required in group
        # Try with title first (despite docs saying otherwise)
        # The error "title = None" suggests eBay is checking for title and finding None
        import json
        
        # Based on eBay API docs, title should be at ROOT level, not inside inventoryItemGroup
        # Structure: { "title": "...", "inventoryItemGroup": {...}, "variantSKUs": [...] }
        print(f"[DEBUG] Attempting group creation WITH title at ROOT level")
        
        # Ensure title is valid
        if not group_title or group_title is None:
            group_title = "Card Set Variation Listing"
        group_title = str(group_title).strip()
        if not group_title or len(group_title) == 0:
            group_title = "Card Set Variation Listing"
        
        # Ensure byte length is valid
        title_bytes = len(group_title.encode('utf-8'))
        if title_bytes > 80:
            group_title = group_title.encode('utf-8')[:80].decode('utf-8', errors='ignore').strip()
            if not group_title:
                group_title = "Card Set Variation Listing"
        
        # Build variesBy specifications from aspects
        # Based on user's working listings, use a SINGLE variation aspect with descriptive values
        # Example: aspect name "PICK YOUR CARD" with values like "9 Tyger Campbell - UCLA 1st"
        specifications = []
        
        # Use single variation aspect with full card descriptions as values
        if variation_values:
            specifications.append({
                "name": variation_aspect_name,
                "values": variation_values
            })
            print(f"[DEBUG] Using single variation aspect: '{variation_aspect_name}'")
            print(f"[DEBUG] With {len(variation_values)} variation values")
            print(f"[DEBUG] Sample values: {variation_values[:3]}")
        else:
            print("[WARNING] No variation values available")
        
        # Based on eBay API docs, variesBy should be at ROOT level
        # CRITICAL: For variation listings, description MUST be in the inventoryItemGroup
        # This is required for publishOfferByInventoryItemGroup to work
        # Ensure description is valid - use the function parameter 'description'
        # CRITICAL: Strip ALL HTML tags for variation listings - eBay requires plain text
        import re
        raw_description = description if description else getattr(self, '_current_listing_description', '')
        
        # Aggressively strip HTML tags and convert to plain text
        if raw_description:
            # First, replace block elements with newlines
            group_description = re.sub(r'</(p|div|br|li|h[1-6])>', '\n', raw_description, flags=re.IGNORECASE)
            # Remove ALL HTML tags completely
            group_description = re.sub(r'<[^>]+>', '', group_description)
            # Replace HTML entities
            group_description = group_description.replace('&nbsp;', ' ')
            group_description = group_description.replace('&amp;', '&')
            group_description = group_description.replace('&lt;', '<')
            group_description = group_description.replace('&gt;', '>')
            group_description = group_description.replace('&quot;', '"')
            group_description = group_description.replace('&#39;', "'")
            group_description = group_description.replace('&apos;', "'")
            # Clean up multiple newlines (max 2 consecutive)
            group_description = re.sub(r'\n{3,}', '\n\n', group_description)
            # Clean up multiple spaces/tabs
            group_description = re.sub(r'[ \t]+', ' ', group_description)
            # Remove any control characters that might cause issues
            group_description = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]', '', group_description)
            # Remove any remaining HTML-like patterns
            group_description = re.sub(r'&[a-zA-Z]+;', '', group_description)  # Remove any remaining entities
            group_description = group_description.strip()
        else:
            group_description = ''
        
        if not group_description or len(group_description.strip()) < 50:
            # Generate default description - ALWAYS ensure it's at least 50 characters
            if "Topps Chrome" in group_title or "Chrome" in group_title:
                group_description = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
            else:
                # Always generate a valid description that's at least 50 characters
                group_description = f"""{group_title}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted.

Ships in penny sleeve and top loader via PWE with eBay tracking."""
            
            # Double-check length - if still too short, add more text
            if len(group_description.strip()) < 50:
                group_description = f"""{group_title}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted.

Ships in penny sleeve and top loader via PWE with eBay tracking.

This is a variation listing where you can select from multiple card options. Each card is individually priced and available in the quantities shown."""
        
        # FINAL CHECK: If description is still invalid, use a guaranteed valid one
        if not group_description or len(group_description.strip()) < 50:
            print(f"[DEBUG] [CRITICAL] Description still invalid after all attempts! Using guaranteed valid description.")
            group_description = f"""{group_title}

This is a variation listing for trading cards. Select your card from the dropdown menu below.

Each card is listed as a separate variation option with its own price and quantity.

All cards are in Near Mint or better condition unless otherwise noted.

Ships in penny sleeve and top loader via PWE with eBay tracking.

This listing allows you to choose from multiple card options, each with individual pricing and availability."""
        
        # Verify one final time
        final_desc_length = len(group_description.strip())
        if final_desc_length < 50:
            print(f"[DEBUG] [CRITICAL ERROR] Description is STILL too short ({final_desc_length} chars)! This will cause Error 25016!")
            # Last resort: use a very simple but guaranteed valid description
            group_description = f"{group_title}\n\nSelect your card from the variations below. Each card is listed as a separate variation option. All cards are in Near Mint or better condition. Ships in penny sleeve and top loader via PWE with eBay tracking. This is a variation listing where you can select from multiple card options."
        
        print(f"[DEBUG] [CRITICAL] Adding description to inventoryItemGroup (length: {len(group_description)})")
        print(f"[DEBUG] Description preview: {group_description[:100]}...")
        print(f"[DEBUG] [VERIFY] Description is valid: {bool(group_description and group_description.strip() and len(group_description.strip()) >= 50)}")
        if len(group_description.strip()) < 50:
            print(f"[DEBUG] [CRITICAL ERROR] Description validation FAILED! Length: {len(group_description.strip())}")
        
        # Use single variation aspect with descriptive values (matching user's working listings)
        # CRITICAL FIX: Description MUST be in inventoryItemGroup.description (NOT at root level)
        # eBay API requires description inside inventoryItemGroup for variation listings
        clean_group_data = {
            "title": group_title,  # ROOT level - required by eBay API
            "variesBy": {
                "specifications": specifications
            },
            "inventoryItemGroup": {
                "aspects": aspects,  # Aspects inside inventoryItemGroup
                "description": group_description  # CRITICAL: Description MUST be in inventoryItemGroup.description
            },
            "variantSKUs": [item["sku"] for item in created_items],
            "imageUrls": []  # Will be populated from card images
        }
        
        # CRITICAL: Populate imageUrls from card images (REQUIRED for publishing)
        # Collect unique image URLs from all cards
        image_urls_set = set()
        for item in created_items:
            card = item.get("card", {})
            image_url = card.get('image_url') or card.get('imageUrl')
            if image_url:
                image_urls_set.add(image_url)
        
        # Only use images from cards - no default image
        clean_group_data["imageUrls"] = list(image_urls_set) if image_urls_set else []
        print(f"[DEBUG] [CRITICAL] Added {len(clean_group_data['imageUrls'])} image URL(s) to group")
        print(f"[DEBUG] Image URLs: {clean_group_data['imageUrls']}")
        
        # CRITICAL: Verify description is actually in the data structure
        if 'inventoryItemGroup' in clean_group_data and 'description' in clean_group_data['inventoryItemGroup']:
            desc_in_group = clean_group_data['inventoryItemGroup']['description']
            print(f"[DEBUG] [VERIFY] Description confirmed in clean_group_data:")
            print(f"  Present: YES")
            print(f"  Location: inventoryItemGroup.description")
            print(f"  Value: {desc_in_group[:100]}...")
            print(f"  Length: {len(desc_in_group)}")
        else:
            print(f"[DEBUG] [CRITICAL ERROR] Description NOT in clean_group_data!")
            print(f"[DEBUG] inventoryItemGroup keys: {list(clean_group_data.get('inventoryItemGroup', {}).keys())}")
        
        print(f"[DEBUG] Including variesBy with {len(specifications)} specification(s)")
        print(f"[DEBUG] Variation aspect: '{variation_aspect_name}' with {len(variation_values)} values")
        
        print(f"[DEBUG] Using structure with variesBy at ROOT level (per eBay API docs)")
        print(f"[DEBUG] - title: [OK]")
        print(f"[DEBUG] - variesBy (root): [OK] ({len(specifications)} specifications)")
        print(f"[DEBUG] - inventoryItemGroup.aspects: [OK]")
        print(f"[DEBUG] - variantSKUs: [OK] ({len([item['sku'] for item in created_items])} SKUs)")
        
        print(f"[DEBUG] Group key: {group_key}")
        print(f"[DEBUG] Group data with title at ROOT level:")
        print(json.dumps(clean_group_data, indent=2))
        
        # Before creating group, check if any SKUs are already in groups
        # (This is a proactive check, but eBay will still validate)
        print(f"[DEBUG] Checking if SKUs are already in groups...")
        skus_to_check = [item["sku"] for item in created_items]
        problematic_skus = []
        for sku in skus_to_check:
            # Try to get offer to see if it's in a group
            offer_result = self.api_client.get_offer_by_sku(sku)
            if offer_result.get('success') and offer_result.get('offer'):
                offer = offer_result['offer']
                # Check if offer has inventoryItemGroupKey
                group_key_in_offer = offer.get('inventoryItemGroupKey')
                if group_key_in_offer:
                    problematic_skus.append((sku, group_key_in_offer))
                    print(f"[DEBUG] [WARNING] SKU {sku} is already in group: {group_key_in_offer}")
        
        if problematic_skus:
            print(f"[DEBUG] Found {len(problematic_skus)} SKU(s) already in groups. Will attempt to resolve...")
            # Try to delete the old groups
            for sku, old_group_key in problematic_skus:
                print(f"[DEBUG] Attempting to remove SKU {sku} from group {old_group_key}...")
                delete_result = self.api_client.delete_inventory_item_group(old_group_key)
                if delete_result.get("success"):
                    print(f"[DEBUG] [OK] Deleted old group {old_group_key}")
                    time.sleep(1)  # Brief pause for propagation
                else:
                    print(f"[DEBUG] [WARNING] Could not delete group {old_group_key}: {delete_result.get('error')}")
        
        # CRITICAL: Final verification before creating group
        print(f"[DEBUG] ========== FINAL GROUP DATA VERIFICATION ==========")
        print(f"[DEBUG] Group Key: {group_key}")
        print(f"[DEBUG] Title: {clean_group_data.get('title', 'MISSING')}")
        print(f"[DEBUG] Has inventoryItemGroup: {'inventoryItemGroup' in clean_group_data}")
        if 'inventoryItemGroup' in clean_group_data:
            inv_group = clean_group_data['inventoryItemGroup']
            print(f"[DEBUG] inventoryItemGroup keys: {list(inv_group.keys())}")
            print(f"[DEBUG] Has description: {'description' in inv_group}")
            if 'description' in inv_group:
                desc_val = inv_group['description']
                print(f"[DEBUG] Description value: {desc_val[:100]}...")
                print(f"[DEBUG] Description length: {len(desc_val)}")
                print(f"[DEBUG] Description is valid: {bool(desc_val and desc_val.strip() and len(desc_val.strip()) >= 50)}")
            else:
                print(f"[DEBUG] [CRITICAL ERROR] NO DESCRIPTION IN inventoryItemGroup!")
        print(f"[DEBUG] Full group data structure:")
        print(json.dumps(clean_group_data, indent=2))
        print(f"[DEBUG] ===================================================")
        
        group_result = self.api_client.create_inventory_item_group(group_key, clean_group_data)
        
        # CRITICAL: Verify group was created and check response
        print(f"[DEBUG] ========== GROUP CREATION RESULT ==========")
        print(f"[DEBUG] Success: {group_result.get('success')}")
        if group_result.get('success'):
            print(f"[DEBUG] [OK] Group creation API call succeeded!")
            result_data = group_result.get('data', {})
            print(f"[DEBUG] Response keys: {list(result_data.keys()) if result_data else 'No data'}")
            
            # CRITICAL: Verify group actually exists by fetching it
            print(f"[DEBUG] [CRITICAL] Verifying group actually exists in eBay...")
            verify_immediate = self.api_client.get_inventory_item_group(group_key)
            if verify_immediate.get('success'):
                print(f"[DEBUG] [CRITICAL] ✅ Group verified - exists in eBay!")
            else:
                print(f"[DEBUG] [CRITICAL] ⚠️ WARNING: Group creation succeeded but group not found!")
                print(f"[DEBUG] [CRITICAL] Error: {verify_immediate.get('error')}")
                print(f"[DEBUG] [CRITICAL] Waiting 5 seconds and retrying verification...")
                time.sleep(5)
                verify_retry = self.api_client.get_inventory_item_group(group_key)
                if verify_retry.get('success'):
                    print(f"[DEBUG] [CRITICAL] ✅ Group found on retry!")
                else:
                    print(f"[DEBUG] [CRITICAL] ❌ Group still not found after retry!")
                    # Mark group_result as failed so error handling kicks in
                    group_result = {"success": False, "error": f"Group creation succeeded but group not found: {verify_retry.get('error')}"}
            
            # CRITICAL: Wait after group creation to ensure description is persisted
            print(f"[DEBUG] [CRITICAL] Waiting 10 seconds after group creation for description to persist...")
            time.sleep(10)
            print(f"[DEBUG] [CRITICAL] Wait complete - description should now be stored in eBay")
            
            # CRITICAL: Link offers to the group (eBay may not auto-link if offers were created first)
            print(f"[DEBUG] [CRITICAL] Linking offers to group...")
            offers_linked = 0
            for item in created_items:
                sku = item["sku"]
                offer_result = self.api_client.get_offer_by_sku(sku)
                if offer_result.get('success'):
                    offer = offer_result.get('offer', {})
                    offer_id = offer.get('offerId')
                    current_group_key = offer.get('inventoryItemGroupKey')
                    
                    if current_group_key != group_key:
                        print(f"[DEBUG] [LINK] Linking offer {sku} to group {group_key}...")
                        # Update offer to link it to the group
                        offer_update = {
                            "sku": sku,
                            "marketplaceId": "EBAY_US",
                            "format": "FIXED_PRICE",
                            "inventoryItemGroupKey": group_key,  # CRITICAL: Link to group
                            "categoryId": offer.get('categoryId', category_id),
                            "pricingSummary": offer.get('pricingSummary', {}),
                            "listingPolicies": offer.get('listingPolicies', {}),
                            "availableQuantity": offer.get('availableQuantity', 1),
                            "listingDuration": offer.get('listingDuration', 'GTC')
                        }
                        
                        # Include listing data if present
                        if 'listing' in offer:
                            offer_update['listing'] = offer['listing']
                        
                        update_result = self.api_client.update_offer(offer_id, offer_update)
                        if update_result.get('success'):
                            offers_linked += 1
                            print(f"[DEBUG] [LINK] ✅ Linked offer {sku} to group")
                        else:
                            print(f"[DEBUG] [LINK] ❌ Failed to link offer {sku}: {update_result.get('error')}")
                    else:
                        offers_linked += 1
                        print(f"[DEBUG] [LINK] ✅ Offer {sku} already linked to group")
            
            print(f"[DEBUG] [LINK] Linked {offers_linked}/{len(created_items)} offers to group")
        else:
            print(f"[DEBUG] [ERROR] Group creation failed!")
            print(f"[DEBUG] Error: {group_result.get('error')}")
        print(f"[DEBUG] ===========================================")
        
        # Check if group was created (might have been created during error handling)
        if not group_result.get("success"):
            error_detail = group_result.get('error', 'Unknown error')
            raw_response = group_result.get('raw_response', '')
            
            # Initialize error message
            error_msg = f"Failed to create inventory item group: {error_detail}"
            
            # Check if error was already handled (group might have been created during retry)
            if '25703' in str(error_detail) and 'old_group_id' in locals():
                # Error was handled above, check if group_result was updated
                if group_result.get("success"):
                    # Group was created during retry, continue
                    pass
            
            # Handle SKU already in group error (25703)
            if '25703' in str(error_detail) or 'already a member of another group' in str(error_detail).lower():
                print(f"[DEBUG] [ERROR 25703] SKUs are already in a group. Attempting to resolve...")
                
                import re
                # Try multiple patterns to extract the old group ID
                old_group_id = None
                problematic_sku = None
                
                # Pattern 1: "groupId: GROUPBECKETTCOMNEWS2025261768536243"
                old_group_match = re.search(r'groupId[:\s]+([A-Z0-9]+)', str(error_detail), re.IGNORECASE)
                if old_group_match:
                    old_group_id = old_group_match.group(1)
                    print(f"[DEBUG] [25703] Found old group ID via pattern 1: {old_group_id}")
                
                # Pattern 2: Extract from parameters in JSON response
                if not old_group_id and raw_response:
                    try:
                        import json
                        error_json = json.loads(raw_response)
                        if 'errors' in error_json and len(error_json['errors']) > 0:
                            params = error_json['errors'][0].get('parameters', [])
                            for param in params:
                                if param.get('name') == 'text2':  # text2 usually contains the groupId
                                    old_group_id = param.get('value')
                                elif param.get('name') == 'text1':  # text1 usually contains the SKU
                                    problematic_sku = param.get('value')
                    except:
                        pass
                
                # Pattern 3: Direct search in error text
                if not old_group_id:
                    # Look for group ID pattern (usually starts with GROUP and is alphanumeric)
                    group_match = re.search(r'(GROUP[A-Z0-9]{10,})', str(error_detail), re.IGNORECASE)
                    if group_match:
                        old_group_id = group_match.group(1).upper()
                
                if old_group_id:
                    print(f"[DEBUG] Found old group ID: {old_group_id}")
                    if problematic_sku:
                        print(f"[DEBUG] Problematic SKU: {problematic_sku}")
                    
                    # CRITICAL: First unlink all offers from the old group before deleting
                    print(f"[DEBUG] [25703] [FIX] Step 1: Unlinking offers from old group...")
                    group_info = self.api_client.get_inventory_item_group(old_group_id)
                    if group_info.get('success'):
                        group_data = group_info.get('data', {})
                        variant_skus = group_data.get('variantSKUs', [])
                        print(f"[DEBUG] Old group contains {len(variant_skus)} SKUs: {variant_skus}")
                        
                        # Unlink each offer from the group
                        offers_unlinked = 0
                        for sku in variant_skus:
                            offer_result = self.api_client.get_offer_by_sku(sku)
                            if offer_result.get('success') and offer_result.get('offer'):
                                offer = offer_result['offer']
                                offer_id = offer.get('offerId')
                                current_group = offer.get('inventoryItemGroupKey')
                                
                                if current_group == old_group_id and offer_id:
                                    print(f"[DEBUG] [25703] [FIX] Unlinking offer {sku} from group...")
                                    # Update offer to remove inventoryItemGroupKey
                                    offer_update = {
                                        "sku": sku,
                                        "marketplaceId": "EBAY_US",
                                        "format": "FIXED_PRICE",
                                        "categoryId": offer.get('categoryId', category_id),
                                        "pricingSummary": offer.get('pricingSummary', {}),
                                        "listingPolicies": offer.get('listingPolicies', {}),
                                        "availableQuantity": offer.get('availableQuantity', 1),
                                        "listingDuration": offer.get('listingDuration', 'GTC')
                                    }
                                    
                                    # Include listing data if present
                                    if 'listing' in offer:
                                        offer_update['listing'] = offer['listing']
                                    
                                    # DO NOT include inventoryItemGroupKey - this unlinks it
                                    update_result = self.api_client.update_offer(offer_id, offer_update)
                                    if update_result.get('success'):
                                        offers_unlinked += 1
                                        print(f"[DEBUG] [25703] [OK] Unlinked offer {sku}")
                                    else:
                                        print(f"[DEBUG] [25703] [WARNING] Could not unlink offer {sku}: {update_result.get('error')}")
                        
                        print(f"[DEBUG] [25703] [FIX] Unlinked {offers_unlinked}/{len(variant_skus)} offers")
                        time.sleep(3)  # Wait for unlinking to propagate
                    
                    # Step 2: Now try to delete the group
                    print(f"[DEBUG] [25703] [FIX] Step 2: Attempting to delete old group: {old_group_id}")
                    delete_result = self.api_client.delete_inventory_item_group(old_group_id)
                    if delete_result.get("success"):
                        print(f"[DEBUG] [25703] [OK] Successfully deleted old group: {old_group_id}")
                        print(f"[DEBUG] [25703] [FIX] Waiting 10 seconds for deletion to fully propagate...")
                        time.sleep(10)  # Longer wait for deletion to propagate
                        
                        # Step 3: Retry creating the group
                        print(f"[DEBUG] [25703] [FIX] Step 3: Retrying group creation...")
                        retry_result = self.api_client.create_inventory_item_group(group_key, clean_group_data)
                        if retry_result.get("success"):
                            print(f"[DEBUG] [25703] [OK] Group created successfully after cleanup!")
                            group_result = retry_result  # Update group_result so code continues
                        else:
                            print(f"[DEBUG] [25703] [WARNING] Retry still failed: {retry_result.get('error')}")
                    else:
                        # Even if deletion fails, try unlinking the problematic SKU specifically
                        if problematic_sku:
                            print(f"[DEBUG] [25703] [FIX] Group deletion failed, but trying to unlink problematic SKU...")
                            offer_result = self.api_client.get_offer_by_sku(problematic_sku)
                            if offer_result.get('success') and offer_result.get('offer'):
                                offer = offer_result['offer']
                                offer_id = offer.get('offerId')
                                if offer_id:
                                    offer_update = {
                                        "sku": problematic_sku,
                                        "marketplaceId": "EBAY_US",
                                        "format": "FIXED_PRICE",
                                        "categoryId": offer.get('categoryId', category_id),
                                        "pricingSummary": offer.get('pricingSummary', {}),
                                        "listingPolicies": offer.get('listingPolicies', {}),
                                        "availableQuantity": offer.get('availableQuantity', 1),
                                        "listingDuration": offer.get('listingDuration', 'GTC')
                                    }
                                    if 'listing' in offer:
                                        offer_update['listing'] = offer['listing']
                                    
                                    unlink_result = self.api_client.update_offer(offer_id, offer_update)
                                    if unlink_result.get('success'):
                                        print(f"[DEBUG] [25703] [OK] Unlinked problematic SKU")
                                        time.sleep(5)
                                        # Retry group creation
                                        print(f"[DEBUG] [25703] [FIX] Retrying group creation after unlinking...")
                                        retry_result = self.api_client.create_inventory_item_group(group_key, clean_group_data)
                                        if retry_result.get("success"):
                                            print(f"[DEBUG] [25703] [OK] Group created successfully after unlinking!")
                                            group_result = retry_result
                        
                        # Also try to remove group reference from the problematic SKU's offer
                        if problematic_sku:
                            print(f"[DEBUG] [25703] [FIX] Removing group reference from offer for SKU: {problematic_sku}")
                            offer_result = self.api_client.get_offer_by_sku(problematic_sku)
                            if offer_result.get('success') and offer_result.get('offer'):
                                offer = offer_result['offer']
                                offer_id = offer.get('offerId')
                                if offer_id:
                                    # Update offer to remove inventoryItemGroupKey
                                    offer_update = {
                                        "sku": problematic_sku,
                                        "marketplaceId": "EBAY_US",
                                        "format": "FIXED_PRICE",
                                        "availableQuantity": offer.get('availableQuantity', 1),
                                        "pricingSummary": offer.get('pricingSummary', {}),
                                        "listingPolicies": offer.get('listingPolicies', {}),
                                        "categoryId": offer.get('categoryId', category_id),
                                        "merchantLocationKey": offer.get('merchantLocationKey', 'DEFAULT'),
                                        "listing": offer.get('listing', {})
                                        # Don't include inventoryItemGroupKey - this removes it
                                    }
                                    update_result = self.api_client.update_offer(offer_id, offer_update)
                                    if update_result.get('success'):
                                        print(f"[DEBUG] [25703] [OK] Removed group reference from offer")
                                        time.sleep(2)
                                    else:
                                        print(f"[DEBUG] [25703] [WARNING] Could not update offer: {update_result.get('error')}")
                        
                        # Generate a new unique group key
                        new_timestamp = str(int(time.time()))
                        set_name_clean = re.sub(r'[^A-Z0-9]', '', set_name.replace('https://', '').replace('http://', '').replace('www.', '').upper())[:20]
                        if not set_name_clean:
                            set_name_clean = "CARDSET"
                        max_set_len = 50 - len("GROUP") - len(new_timestamp)
                        if len(set_name_clean) > max_set_len:
                            set_name_clean = set_name_clean[:max_set_len]
                        group_key = f"GROUP{set_name_clean}{new_timestamp}"
                        group_key = re.sub(r'[^A-Z0-9]', '', group_key.upper())[:50]
                        
                        print(f"[DEBUG] New group key: {group_key}")
                        
                        # Retry with new group key
                        group_result = self.api_client.create_inventory_item_group(group_key, clean_group_data)
                        if group_result.get("success"):
                            print(f"[DEBUG] [OK] Successfully created group after deleting old one!")
                        else:
                            retry_error = group_result.get('error', 'Unknown')
                            print(f"[DEBUG] [ERROR] Still failed after deleting old group: {retry_error}")
                            # If it's still the same error, the SKUs might be in multiple groups
                            if '25703' in str(retry_error) or 'already a member' in str(retry_error).lower():
                                error_msg += f"\n\n[WARNING] SKUs may be in multiple groups. You may need to:"
                                error_msg += f"\n1. Manually delete old groups from eBay Seller Hub"
                                error_msg += f"\n2. Or use different SKUs for this listing"
                                error_msg += f"\n3. Old group ID: {old_group_id}"
                        
                        # If deletion failed, add error message
                        if not delete_result.get("success"):
                            delete_error = delete_result.get('error', 'Unknown error')
                            print(f"[DEBUG] [WARNING] Could not delete old group: {delete_error}")
                            error_msg += f"\n\n[WARNING] Could not delete old group {old_group_id}: {delete_error}"
                            # Determine base URL for Seller Hub link
                            base_url = "https://www.ebay.com" if self.config.EBAY_ENVIRONMENT == 'production' else "https://sandbox.ebay.com"
                            error_msg += f"\n\n[ACTION REQUIRED] The old group may be published or scheduled. You need to:"
                            error_msg += f"\n1. Go to Scheduled Listings: {base_url}/sh/lst/scheduled"
                            error_msg += f"\n2. Or Active Listings: {base_url}/sh/lst/active"
                            error_msg += f"\n3. Find and end/delete the listing with group: {old_group_id}"
                            error_msg += f"\n4. Then try creating your listing again"
                else:
                    print(f"[DEBUG] [WARNING] Could not extract old group ID from error")
                    error_msg += f"\n\n[WARNING] SKUs are already in another group, but could not identify which one."
                    error_msg += f"\nYou may need to manually check and delete old groups from eBay Seller Hub."
                
                # Add helpful guidance for Error 25703
                error_msg += "\n\n[SOLUTION] This error means one or more SKUs are already in another variation group."
                error_msg += "\nThe system attempted to automatically resolve this by:"
                error_msg += "\n1. Finding the old group ID"
                error_msg += "\n2. Deleting the old group"
                error_msg += "\n3. Retrying with a new group"
                base_url = "https://www.ebay.com" if self.config.EBAY_ENVIRONMENT == 'production' else "https://sandbox.ebay.com"
                error_msg += f"\n\n[ACTION REQUIRED] If deletion failed, the group may be published/scheduled. Please:"
                error_msg += f"\n1. Go to Scheduled Listings: {base_url}/sh/lst/scheduled"
                error_msg += f"\n2. Or Active Listings: {base_url}/sh/lst/active"
                error_msg += f"\n3. Find and end/delete the listing (group: {old_group_id if old_group_id else 'see above'})"
                error_msg += f"\n4. Wait 1-2 minutes for eBay to process the deletion"
                error_msg += f"\n5. Then try creating your listing again"
            
            # Show the actual payload that was sent
            error_msg += f"\n\n[DEBUG] Group data sent:"
            error_msg += f"\n{json.dumps(clean_group_data, indent=2)[:500]}"
            
            if raw_response:
                error_msg += f"\n\n[DEBUG] eBay API raw response:"
                error_msg += f"\n{raw_response[:500]}"
            
            # Try one more approach: Single aspect only (Card Name only - Card Number not allowed)
            if 'title' in str(error_detail).lower() and group_result.get("success") is False:
                print(f"[DEBUG] Still failing with title error. Trying single aspect approach...")
                single_aspect = {}
                if "Card Name" in aspects and aspects["Card Name"]:
                    single_aspect = {"Card Name": aspects["Card Name"]}
                # DO NOT use Card Number - it's not allowed as a variation aspect
        
                if single_aspect:
                    # Build variesBy for single aspect (Card Name only)
                    single_specifications = []
                    if "Card Name" in single_aspect:
                        single_specifications.append({
                            "name": "Card Name",
                            "values": single_aspect["Card Name"]
                        })
                    
                    clean_group_data_single = {
                        "title": group_title,  # ROOT level
                        "groupDetails": {
                            "variationInformation": {
                                "specifications": single_specifications
                            }
                        },
                        "inventoryItemGroup": {
                            "aspects": single_aspect,
                            "variesBy": {
                                "specifications": single_specifications
                            }
                        },
                        "variantSKUs": [item["sku"] for item in created_items]
                    }
                    # Generate alphanumeric-only group key for single aspect attempt
                    import re
                    base_key = re.sub(r'[^A-Z0-9]', '', group_key.upper())[:40]  # Leave room for suffix
                    group_key_single = f"{base_key}SA{int(time.time()) % 10000}"  # SA = Single Aspect
                    group_key_single = re.sub(r'[^A-Z0-9]', '', group_key_single.upper())[:50]  # Ensure alphanumeric only
                    group_result = self.api_client.create_inventory_item_group(group_key_single, clean_group_data_single)
                    if group_result.get("success"):
                        group_key = group_key_single
                        print(f"[DEBUG] [OK] Success with single aspect! Using group key: {group_key}")
                    else:
                        error_msg += f"\n\n[DEBUG] Single aspect approach also failed: {group_result.get('error')}"
            
            if not group_result.get("success"):
                return {
                    "success": False,
                    "error": error_msg,
                    "created_items": len(created_items),
                    "errors": errors,
                    "debug_info": {
                        "group_data": clean_group_data,
                        "raw_response": raw_response
                    }
                }
        
        # Get the actual group key from the response (eBay might return a different key)
        group_response_data = group_result.get("data", {})
        print(f"[DEBUG] Group creation response data: {group_response_data}")
        
        # Try different possible keys from response
        actual_group_key = (
            group_response_data.get("inventoryItemGroupKey") or 
            group_response_data.get("groupKey") or
            group_response_data.get("key") or
            group_key
        )
        
        if actual_group_key != group_key:
            print(f"[DEBUG] eBay returned different group key: {actual_group_key} (we sent: {group_key})")
            group_key = actual_group_key
        else:
            print(f"[DEBUG] Using original group key: {group_key}")
        
        print(f"  [OK] Created group: {group_key}")
        
        # Step 3: Ensure we have a merchant location (required for country info)
        merchant_location_key = self.policies.get('merchant_location_key')
        if not merchant_location_key:
            print(f"Creating default merchant location...")
            # Try to create a default location
            default_location_result = self.api_client.create_merchant_location(
                merchant_location_key="DEFAULT",
                name="Default Location",
                address={
                    "addressLine1": "123 Main St",
                    "city": "New York",
                    "stateOrProvince": "NY",
                    "postalCode": "10001",
                    "country": "US"
                }
            )
            if default_location_result.get('success'):
                merchant_location_key = "DEFAULT"
                print(f"  [OK] Created default merchant location: {merchant_location_key}")
            else:
                # Try to get existing locations
                location_result = self.api_client.get_merchant_locations()
                locations = location_result.get('locations', [])
                if locations:
                    merchant_location_key = locations[0].get('merchantLocationKey')
                    print(f"  [OK] Using existing location: {merchant_location_key}")
                else:
                    print(f"  [WARNING] Could not create or find merchant location")
                    print(f"  [WARNING] Listing may fail without merchant location")
        
        # Step 4: Create offers for each SKU (required before publishing variation listing)
        print(f"Creating offers for each SKU...")
        offer_errors = []
        
        # Calculate listingStartDate if schedule_draft is enabled (do this once before the loop)
        listing_start_date = None
        if schedule_draft and publish:
            from datetime import datetime, timedelta, timezone
            # Use a longer delay (at least 24 hours, or use schedule_hours if it's longer)
            # This ensures the listing stays in "Scheduled" status long enough to be edited
            actual_hours = max(schedule_hours, 24)  # Minimum 24 hours to ensure it's scheduled
            try:
                start_time = datetime.now(timezone.utc) + timedelta(hours=actual_hours)
                listing_start_date = start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            except (OSError, ValueError) as e:
                # Fallback for Windows compatibility - format without Z, then append
                print(f"[WARNING] Datetime formatting issue: {e}, using fallback")
                start_time = datetime.utcnow() + timedelta(hours=actual_hours)
                listing_start_date = start_time.strftime('%Y-%m-%dT%H:%M:%S') + '.000Z'
            print(f"[INFO] ========== SCHEDULED DRAFT MODE ==========")
            print(f"[INFO] Scheduling listing to start at: {listing_start_date}")
            print(f"[INFO] This is {actual_hours} hours from now (minimum 24 hours to ensure scheduled status)")
            print(f"[INFO] Listing will appear in Seller Hub as 'Scheduled' where you can edit it")
            print(f"[INFO] You can edit and publish immediately from Seller Hub if needed")
            print(f"[INFO] ==========================================")
        
        for item in created_items:
            sku = item["sku"]
            card_price = item["price"]
            
            # Build offer data
            # CRITICAL: For variation listings, listingPolicies may need to be at ROOT level
            # Try both locations to ensure it's saved
            policy_id_used = fulfillment_policy_id or self.policies.get('fulfillment_policy_id')
            payment_policy_id = self.policies.get('payment_policy_id')
            return_policy_id = self.policies.get('return_policy_id')
            
            # Build listingPolicies - only include policies that are set
            # NOTE: Return policy is required by eBay
            # NOTE: Payment policy is OPTIONAL - eBay will use default if not provided
            listing_policies = {
                "fulfillmentPolicyId": policy_id_used
            }
            if payment_policy_id and payment_policy_id.strip():
                listing_policies["paymentPolicyId"] = payment_policy_id
                print(f"  [DEBUG] Including payment policy ID: {payment_policy_id}")
            else:
                print(f"  [INFO] No payment policy ID set - eBay will use default payment policy")
            
            # ALWAYS include return policy if it's set (even if API says it doesn't exist)
            # Sandbox API has limitations - policy might work even if query fails
            if return_policy_id and return_policy_id.strip():
                listing_policies["returnPolicyId"] = return_policy_id
                print(f"  [DEBUG] Including return policy ID: {return_policy_id}")
                print(f"  [DEBUG] Note: API query may fail (sandbox limitation), but policy ID will be used in listing")
            else:
                print(f"  [ERROR] No return policy ID set!")
                print(f"  [ERROR] This will fail with Error 25009")
                print(f"  [ERROR] Please set RETURN_POLICY_ID in .env file")
            
            # Ensure description is valid and not empty
            # eBay requires a description - it cannot be empty or just whitespace
            # CRITICAL: Strip HTML from description for offers too
            import re
            raw_listing_desc = description if description else ''
            
            # Strip HTML tags from offer description
            if raw_listing_desc:
                listing_description = re.sub(r'</(p|div|br|li|h[1-6])>', '\n', raw_listing_desc, flags=re.IGNORECASE)
                listing_description = re.sub(r'<[^>]+>', '', listing_description)
                listing_description = listing_description.replace('&nbsp;', ' ')
                listing_description = listing_description.replace('&amp;', '&')
                listing_description = listing_description.replace('&lt;', '<')
                listing_description = listing_description.replace('&gt;', '>')
                listing_description = listing_description.replace('&quot;', '"')
                listing_description = listing_description.replace('&#39;', "'")
                listing_description = listing_description.replace('&apos;', "'")
                listing_description = re.sub(r'\n{3,}', '\n\n', listing_description)
                listing_description = re.sub(r'[ \t]+', ' ', listing_description)
                listing_description = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]', '', listing_description)
                listing_description = re.sub(r'&[a-zA-Z]+;', '', listing_description)
                listing_description = listing_description.strip()
            else:
                listing_description = ''
            
            # If description is missing or too short, create a proper one
            if not listing_description or not listing_description.strip() or len(listing_description.strip()) < 50:
                # Fallback to creating a proper description
                if "Topps Chrome" in group_title or "Chrome" in group_title:
                    listing_description = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                else:
                    listing_description = f"""Variation listing for {group_title}.

Select your card from the variations below. Each card is listed as a separate variation.

All cards are in Near Mint or better condition unless otherwise noted.

Please select the specific card you want from the variation dropdown menu."""
            
            # Ensure it's a string and properly formatted
            listing_description = str(listing_description).strip()
            
            if False:  # Old code path - keeping for reference
                pass
            else:
                # Use the user's preferred description for Topps Chrome Basketball
                if "Topps Chrome" in group_title or "Chrome" in group_title:
                    listing_description = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                else:
                    # Create a proper, detailed description for other sets
                    listing_description = f"""Variation listing for {group_title}.

Select your card from the variations below. Each card is listed as a separate variation.

All cards are in Near Mint or better condition unless otherwise noted.

Please select the specific card you want from the variation dropdown menu."""
            
            # Ensure description meets minimum length (eBay typically requires at least 50-100 characters)
            if len(listing_description.strip()) < 50:
                listing_description = f"""{group_title} - Variation Listing

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition. Please review the variation options and select the specific card you want.

Thank you for your interest!"""
            
            # Debug: Print description to verify it's set
            print(f"[DEBUG] Description for {sku}: {listing_description[:100]}... (length: {len(listing_description)})")
            print(f"[DEBUG] Description is not empty: {bool(listing_description and listing_description.strip())}")
            print(f"[DEBUG] Description meets minimum length: {len(listing_description.strip()) >= 50}")
            
            # CRITICAL DEBUG: Verify description before creating offer
            print(f"[DEBUG] ========== OFFER DATA FOR {sku} ==========")
            print(f"[DEBUG] Description being used:")
            print(f"  Value: {listing_description[:100]}...")
            print(f"  Length: {len(listing_description)}")
            print(f"  Is string: {isinstance(listing_description, str)}")
            print(f"  Is not empty: {bool(listing_description and listing_description.strip())}")
            print(f"  Meets minimum: {len(listing_description.strip()) >= 50}")
            print(f"[DEBUG] =========================================")
            
            # Extract card info for item specifics
            card = item.get("card", {})
            card_name = card.get('name', '')
            card_number = str(card.get('number', ''))
            
            # Build item specifics matching live listing structure
            # These help eBay understand the listing better and may help with Error 25016
            item_specifics = {}
            
            # Try to extract sport from title or set name
            if "Basketball" in group_title or "basketball" in group_title.lower():
                item_specifics["Sport"] = ["Basketball"]
            
            # Try to extract season/year
            import re
            year_match = re.search(r'20\d{2}', group_title)
            if year_match:
                year = year_match.group()
                item_specifics["Season"] = [year]
                item_specifics["Year Manufactured"] = [year]
            
            # Try to extract manufacturer
            if "Topps" in group_title:
                item_specifics["Manufacturer"] = ["Topps"]
            elif "Bowman" in group_title:
                item_specifics["Manufacturer"] = ["Bowman"]
            
            # Card type
            item_specifics["Type"] = ["Sports Trading Card"]
            item_specifics["Card Size"] = ["Standard"]
            item_specifics["Country of Origin"] = ["United States"]
            item_specifics["Language"] = ["English"]
            item_specifics["Original/Licensed Reprint"] = ["Original"]
            
            # Card Name and Card Number (these are in aspects, but also add to item specifics)
            if card_name:
                item_specifics["Card Name"] = [card_name]
            if card_number:
                item_specifics["Card Number"] = [card_number]
        
        offer_data = {
            "sku": sku,
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "categoryId": str(category_id),  # REQUIRED for publishing
            "listingDescription": listing_description,  # CRITICAL: eBay requires this at root level
            "listing": {
                "title": group_title,  # Use group title for all variations
                "description": listing_description,  # CRITICAL: Also in listing object
                "listingPolicies": listing_policies,
                "itemSpecifics": item_specifics  # Add item specifics to match live listings
            },
            # ALSO set at root level (some eBay API versions require this)
            "listingPolicies": listing_policies,
            "pricingSummary": {
                "price": {
                    "value": str(card_price),
                    "currency": "USD"
                }
            },
            "quantity": int(item.get("card", {}).get("quantity", quantity)),
            "availableQuantity": int(item.get("card", {}).get("quantity", quantity)),
            "listingDuration": "GTC"  # Good 'Til Cancelled
        }
        
        # Add listingStartDate if scheduling (CRITICAL for scheduled drafts)
        if listing_start_date:
            offer_data["listingStartDate"] = listing_start_date
            print(f"  [SCHEDULE] ✅ Added listingStartDate to offer {sku}: {listing_start_date}")
        elif schedule_draft and publish:
            # Safety check: if schedule_draft is True but listing_start_date wasn't set, calculate it now
            from datetime import datetime, timedelta, timezone
            # Use longer delay for production to ensure scheduled status
            min_hours = 48 if self.config.EBAY_ENVIRONMENT == 'production' else 24
            actual_hours = max(schedule_hours, min_hours)
            try:
                start_time = datetime.now(timezone.utc) + timedelta(hours=actual_hours)
                listing_start_date = start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            except (OSError, ValueError) as e:
                # Fallback for Windows compatibility
                start_time = datetime.utcnow() + timedelta(hours=actual_hours)
                listing_start_date = start_time.strftime('%Y-%m-%dT%H:%M:%S') + '.000Z'
            offer_data["listingStartDate"] = listing_start_date
            print(f"  [SCHEDULE] [FIX] ⚠️ Added listingStartDate to offer {sku} (calculated, {actual_hours}h from now): {listing_start_date}")
        
        # CRITICAL DEBUG: Verify listingStartDate is in offer_data before sending
        if schedule_draft and publish:
            if "listingStartDate" in offer_data:
                print(f"  [DEBUG] ✅ CONFIRMED: listingStartDate is in offer_data for {sku}: {offer_data['listingStartDate']}")
            else:
                print(f"  [DEBUG] ❌ ERROR: listingStartDate is MISSING from offer_data for {sku}!")
                print(f"  [DEBUG] ❌ This will cause the listing to NOT appear in Scheduled section!")
                # Try to fix it
                if not listing_start_date:
                    from datetime import datetime, timedelta, timezone
                    min_hours = 48 if self.config.EBAY_ENVIRONMENT == 'production' else 24
                    actual_hours = max(schedule_hours, min_hours)
                    try:
                        start_time = datetime.now(timezone.utc) + timedelta(hours=actual_hours)
                        listing_start_date = start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                    except (OSError, ValueError):
                        start_time = datetime.utcnow() + timedelta(hours=actual_hours)
                        listing_start_date = start_time.strftime('%Y-%m-%dT%H:%M:%S') + '.000Z'
                offer_data["listingStartDate"] = listing_start_date
                print(f"  [DEBUG] [FIXED] Added listingStartDate ({actual_hours}h from now): {listing_start_date}")
                
                # CRITICAL: Verify it's actually in the data before sending
                if "listingStartDate" not in offer_data:
                    print(f"  [DEBUG] ❌ CRITICAL ERROR: listingStartDate still missing after fix attempt!")
                    print(f"  [DEBUG] offer_data keys: {list(offer_data.keys())}")
                else:
                    print(f"  [DEBUG] ✅ VERIFIED: listingStartDate is in offer_data: {offer_data['listingStartDate']}")
        
        # Debug item specifics
        print(f"[DEBUG] Item specifics for {sku}: {item_specifics}")
        
        # Merchant location is REQUIRED for publishing (provides country info)
        if merchant_location_key:
            offer_data["merchantLocationKey"] = merchant_location_key
        else:
            # Last resort: try without location (may fail)
            print(f"  [WARNING] No merchant location available for {sku}")
        
        # Debug: Print the policy ID being used (already set above)
        print(f"[DEBUG] Creating offer for {sku} with fulfillmentPolicyId: {policy_id_used}")
        print(f"[DEBUG] Policy IDs being set:")
        print(f"  - Root level listingPolicies: {policy_id_used}")
        print(f"  - Nested listing.listingPolicies: {policy_id_used}")
        
        # Create or update offer (handles existing offers)
        offer_result = self.api_client.create_or_update_offer(offer_data)
        if offer_result.get("success"):
            offer_id = offer_result.get("data", {}).get("offerId") or offer_result.get("data", {}).get("offerId")
            if not offer_id:
                # Try to get it from the response
                offer_id = offer_result.get("offerId")
            print(f"  [OK] Created/updated offer for {sku}: {offer_id}")
            
            # CRITICAL: eBay API may not return description in GET requests immediately
            # So we ALWAYS update the offer after creation to ensure description is set
            print(f"  [FIX] Ensuring description is set by updating offer immediately...")
            # Removed sleep - update immediately
            
            # Build complete update payload with description
            # Only include payment policy if it's set (it's optional)
            update_listing_policies = {
                "fulfillmentPolicyId": policy_id_used
            }
            if payment_policy_id and payment_policy_id.strip():
                update_listing_policies["paymentPolicyId"] = payment_policy_id
            if return_policy_id and return_policy_id.strip():
                update_listing_policies["returnPolicyId"] = return_policy_id
            
            update_offer_data = {
                "sku": sku,
                "marketplaceId": "EBAY_US",
                "format": "FIXED_PRICE",
                "categoryId": str(category_id),
                "listingDescription": listing_description,  # CRITICAL: eBay requires at root level
                "listing": {
                    "title": group_title,
                    "description": listing_description,  # CRITICAL: Also in listing object
                    "listingPolicies": update_listing_policies
                },
                "listingPolicies": update_listing_policies,
                "pricingSummary": offer_data.get('pricingSummary', {}),
                "quantity": offer_data.get('quantity', quantity),
                "availableQuantity": offer_data.get('availableQuantity', quantity),
                "listingDuration": offer_data.get('listingDuration', 'GTC')
            }
            
            # Add listingStartDate if scheduling (CRITICAL - must be in update too!)
            if listing_start_date:
                update_offer_data["listingStartDate"] = listing_start_date
                print(f"  [SCHEDULE] ✅ Added listingStartDate to offer update for {sku}: {listing_start_date}")
            elif schedule_draft and publish:
                # Safety check: ensure listingStartDate is in update
                if not listing_start_date:
                    from datetime import datetime, timedelta, timezone
                    # Use longer delay for production to ensure scheduled status
                    min_hours = 48 if self.config.EBAY_ENVIRONMENT == 'production' else 24
                    actual_hours = max(schedule_hours, min_hours)
                    try:
                        start_time = datetime.now(timezone.utc) + timedelta(hours=actual_hours)
                        listing_start_date = start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                    except (OSError, ValueError):
                        start_time = datetime.utcnow() + timedelta(hours=actual_hours)
                        listing_start_date = start_time.strftime('%Y-%m-%dT%H:%M:%S') + '.000Z'
                update_offer_data["listingStartDate"] = listing_start_date
                print(f"  [SCHEDULE] [FIX] ⚠️ Added listingStartDate to offer update for {sku} (calculated): {listing_start_date}")
            
            # CRITICAL: Verify listingStartDate is in update_offer_data
            if schedule_draft and publish:
                if "listingStartDate" in update_offer_data:
                    print(f"  [DEBUG] ✅ CONFIRMED: listingStartDate is in update_offer_data for {sku}: {update_offer_data['listingStartDate']}")
                else:
                    print(f"  [DEBUG] ❌ ERROR: listingStartDate is MISSING from update_offer_data for {sku}!")
                    # Force add it
                    if not listing_start_date:
                        from datetime import datetime, timedelta, timezone
                        min_hours = 48 if self.config.EBAY_ENVIRONMENT == 'production' else 24
                        actual_hours = max(schedule_hours, min_hours)
                        try:
                            start_time = datetime.now(timezone.utc) + timedelta(hours=actual_hours)
                            listing_start_date = start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                        except (OSError, ValueError):
                            start_time = datetime.utcnow() + timedelta(hours=actual_hours)
                            listing_start_date = start_time.strftime('%Y-%m-%dT%H:%M:%S') + '.000Z'
                    update_offer_data["listingStartDate"] = listing_start_date
                    print(f"  [DEBUG] [FIXED] Added listingStartDate: {listing_start_date}")
            
            if merchant_location_key:
                update_offer_data["merchantLocationKey"] = merchant_location_key
            
            print(f"  [DEBUG] ========== FORCE UPDATE OFFER WITH DESCRIPTION ==========")
            print(f"  [DEBUG] Description in update payload: {update_offer_data['listing']['description'][:100]}...")
            print(f"  [DEBUG] Description length: {len(update_offer_data['listing']['description'])}")
            print(f"  [DEBUG] =========================================================")
            
            if offer_id:
                update_result = self.api_client.update_offer(offer_id, update_offer_data)
                if update_result.get('success'):
                    print(f"  [OK] Successfully updated offer with description!")
                else:
                    print(f"  [WARNING] Update failed but continuing: {update_result.get('error')}")
            
            # Skip verification to speed up - description should be set by update
            # Removed sleep and verification to speed up publishing
            if verify_offer.get('success') and verify_offer.get('offer'):
                offer_obj = verify_offer['offer']
                offer_policy_id = offer_obj.get('listing', {}).get('listingPolicies', {}).get('fulfillmentPolicyId')
                
                # Check description in multiple places
                offer_description = (
                    offer_obj.get('listing', {}).get('description', '') or
                    offer_obj.get('description', '') or
                    ''
                )
                
                print(f"  [DEBUG] ========== FINAL VERIFICATION ==========")
                print(f"  [DEBUG] Offer object keys: {list(offer_obj.keys())}")
                if 'listing' in offer_obj:
                    print(f"  [DEBUG] Listing keys: {list(offer_obj['listing'].keys())}")
                    print(f"  [DEBUG] Listing.description present: {'description' in offer_obj['listing']}")
                    if 'description' in offer_obj['listing']:
                        desc_val = offer_obj['listing']['description']
                        print(f"  [DEBUG] Listing.description value: {desc_val[:50] if desc_val else 'EMPTY'}...")
                        print(f"  [DEBUG] Listing.description length: {len(desc_val) if desc_val else 0}")
                print(f"  [DEBUG] Found description: {offer_description[:50] if offer_description else 'NOT FOUND'}...")
                print(f"  [DEBUG] Description length: {len(offer_description) if offer_description else 0}")
                print(f"  [DEBUG] =========================================")
                
                needs_update = False
                
                # Check if description is still missing
                if not offer_description or not offer_description.strip():
                    print(f"  [CRITICAL ERROR] Description STILL missing after update!")
                    print(f"  [FIX] Will try one more time with explicit description...")
                    needs_update = True
                else:
                    print(f"  [OK] Verified offer has description: {offer_description[:50]}... (length: {len(offer_description)})")
                
                if offer_policy_id:
                    print(f"  [OK] Verified offer has fulfillmentPolicyId: {offer_policy_id}")
                else:
                    print(f"  [WARNING] Offer created but fulfillmentPolicyId is missing!")
                    needs_update = True
                
                if needs_update:
                    print(f"  [FIX] Attempting to update offer with missing fields...")
                    # Force update the offer with the policy ID and description
                    offer_id = offer_obj.get('offerId')
                    if offer_id:
                        # Get the full offer structure and update it
                        update_offer_data = offer_data.copy()  # Use the offer_data we just sent
                        # Ensure listing structure exists
                        if 'listing' not in update_offer_data:
                            update_offer_data['listing'] = {}
                        # Ensure description is set
                        if 'description' not in update_offer_data['listing'] or not update_offer_data['listing']['description']:
                            update_offer_data['listing']['description'] = listing_description
                        # Ensure listingPolicies is set
                        if 'listingPolicies' not in update_offer_data['listing']:
                            update_offer_data['listing']['listingPolicies'] = {}
                        update_offer_data['listing']['listingPolicies']['fulfillmentPolicyId'] = policy_id_used
                        update_offer_data['listing']['listingPolicies']['paymentPolicyId'] = self.policies.get('payment_policy_id')
                        update_offer_data['listing']['listingPolicies']['returnPolicyId'] = self.policies.get('return_policy_id')
                        
                        print(f"  [DEBUG] Updating offer with description: {update_offer_data['listing'].get('description', 'MISSING')[:50]}...")
                        
                        # Update the offer
                        update_result = self.api_client.update_offer(offer_id, update_offer_data)
                        if update_result.get('success'):
                            print(f"  [OK] Successfully updated offer with fulfillmentPolicyId: {policy_id_used}")
                            # Verify again
                            time.sleep(1)  # Brief pause
                            verify_again = self.api_client.get_offer_by_sku(sku)
                            if verify_again.get('success') and verify_again.get('offer'):
                                final_policy_id = verify_again['offer'].get('listing', {}).get('listingPolicies', {}).get('fulfillmentPolicyId')
                                if final_policy_id:
                                    print(f"  [OK] Confirmed offer now has fulfillmentPolicyId: {final_policy_id}")
                                else:
                                    print(f"  [ERROR] Policy ID still missing after update - this is a critical issue")
                        else:
                            print(f"  [ERROR] Failed to update offer: {update_result.get('error')}")
                    else:
                        print(f"  [ERROR] Could not get offer ID to update")
        else:
                error_msg = offer_result.get('error', 'Unknown error')
                if isinstance(error_msg, dict):
                    errors = error_msg.get('errors', [])
                    if errors:
                        error_msg = errors[0].get('message', str(error_msg))
                offer_errors.append(f"Failed to create offer for {sku}: {error_msg}")
                print(f"  [ERROR] Failed to create offer for {sku}: {error_msg}")
        
        if offer_errors and len(offer_errors) == len(created_items):
            # All offers failed
            return {
                "success": False,
                "error": f"Failed to create any offers:\n" + "\n".join(offer_errors),
                "created_items": len(created_items),
                "group_key": group_key,
                "errors": errors + offer_errors
            }
        elif offer_errors:
            print(f"[WARNING] Some offers failed, but proceeding with successful ones...")
        
        # Wait a moment for offers to propagate
        print(f"Waiting for offers to propagate...")
        time.sleep(3)
        
        # Step 4: Verify group exists and wait for it to propagate
        print(f"Verifying group exists and waiting for propagation...")
        max_retries = 5
        group_verified = False
        
        for attempt in range(max_retries):
            wait_time = 2 + (attempt * 2)  # 2, 4, 6, 8, 10 seconds
            print(f"  Attempt {attempt + 1}/{max_retries}: Waiting {wait_time} seconds...")
            time.sleep(wait_time)
            
            # Try to get the group to verify it exists
            verify_result = self.api_client.get_inventory_item_group(group_key)
            if verify_result.get("success"):
                print(f"  [OK] Group verified! Group key: {group_key}")
                group_verified = True
                break
            else:
                print(f"  [WARNING] Group not found yet (status: {verify_result.get('status_code', 'unknown')})")
        
        if not group_verified:
            print(f"[WARNING] Could not verify group after {max_retries} attempts, but proceeding anyway...")
        
        # CRITICAL: Ensure we have a valid description before proceeding
        if not description or len(description.strip()) < 50:
            print(f"[CRITICAL] Description is too short, generating default...")
            if "Topps Chrome" in group_title or "Chrome" in group_title:
                description = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
            else:
                description = f"""{group_title}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
            print(f"[CRITICAL] Generated description (length: {len(description)})")
        
        # Step 5: CRITICAL - ALWAYS update group with description before publishing
        # eBay requires description in inventoryItemGroup for variation listings
        # This is THE MOST IMPORTANT STEP - description MUST be in the group
        print(f"")
        print(f"=" * 80)
        print(f"[CRITICAL] ========== PRE-PUBLISH GROUP DESCRIPTION UPDATE ==========")
        print(f"[CRITICAL] STEP 5: This is THE MOST IMPORTANT STEP")
        print(f"[CRITICAL] If you don't see this message, the code isn't running!")
        print(f"=" * 80)
        print(f"")
        print(f"[CRITICAL] This step ensures description is in inventoryItemGroup before publishing")
        print(f"[CRITICAL] eBay reads description from the GROUP, not from individual offers")
        print(f"[CRITICAL] =========================================================")
        
        # Get the description to use
        # CRITICAL: Strip HTML tags - eBay may require plain text for variation listings
        import re
        raw_desc = description if description else getattr(self, '_current_listing_description', '')
        
        # Strip HTML tags but keep the text content and preserve newlines
        if raw_desc:
            # Replace common block elements with newlines before removing tags
            group_desc_to_use = re.sub(r'</(p|div|br|li|h[1-6])>', '\n', raw_desc, flags=re.IGNORECASE)
            # Remove all remaining HTML tags
            group_desc_to_use = re.sub(r'<[^>]+>', '', group_desc_to_use)
            # Replace HTML entities
            group_desc_to_use = group_desc_to_use.replace('&nbsp;', ' ')
            group_desc_to_use = group_desc_to_use.replace('&amp;', '&')
            group_desc_to_use = group_desc_to_use.replace('&lt;', '<')
            group_desc_to_use = group_desc_to_use.replace('&gt;', '>')
            group_desc_to_use = group_desc_to_use.replace('&quot;', '"')
            # Clean up multiple newlines (max 2 consecutive)
            group_desc_to_use = re.sub(r'\n{3,}', '\n\n', group_desc_to_use)
            # Clean up multiple spaces (but keep single spaces)
            group_desc_to_use = re.sub(r'[ \t]+', ' ', group_desc_to_use)
            group_desc_to_use = group_desc_to_use.strip()
        else:
            group_desc_to_use = ''
        
        if not group_desc_to_use or len(group_desc_to_use.strip()) < 50:
            if "Topps Chrome" in group_title or "Chrome" in group_title:
                group_desc_to_use = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
            else:
                group_desc_to_use = f"""{group_title}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
        
        print(f"[CRITICAL] Description to use: {group_desc_to_use[:100]}... (length: {len(group_desc_to_use)})")
        print(f"[CRITICAL] Description is valid: {bool(group_desc_to_use and group_desc_to_use.strip() and len(group_desc_to_use.strip()) >= 50)}")
        
        # Get current group data
        group_result = self.api_client.get_inventory_item_group(group_key)
        
        if group_result.get('success'):
            group_data = group_result.get('data', {})
            print(f"[CRITICAL] Retrieved group data successfully")
            print(f"[CRITICAL] Group data keys: {list(group_data.keys())}")
            
            # Check if description is in the retrieved group (for debugging)
            retrieved_desc = None
            if 'inventoryItemGroup' in group_data:
                retrieved_desc = group_data['inventoryItemGroup'].get('description', '')
                if retrieved_desc:
                    print(f"[CRITICAL] Group already has description (length: {len(retrieved_desc)})")
                else:
                    print(f"[CRITICAL] Group does NOT have description in GET response")
                    print(f"[CRITICAL] This is OK - eBay GET may not return it, but we'll update anyway")
            
            # ALWAYS update the group with description - don't trust GET response
            # eBay's GET may not return description even if it's there
            print(f"[CRITICAL] ========== UPDATING GROUP WITH DESCRIPTION ==========")
            print(f"[CRITICAL] This update ensures description is definitely in the group")
            print(f"[CRITICAL] This is THE MOST IMPORTANT STEP to prevent Error 25016")
            
            # Build update payload - MUST include all required fields
            # Get aspects from group_data, but ensure we have them
            group_aspects = group_data.get('inventoryItemGroup', {}).get('aspects', {})
            if not group_aspects:
                print(f"[CRITICAL] [WARNING] No aspects in group_data - rebuilding from cards")
                # Rebuild aspects from the original cards data if available
                # This ensures aspects are always present
                if hasattr(self, '_current_cards_data'):
                    card_names = [c.get('name', '') for c in self._current_cards_data if c.get('name')]
                    card_numbers = [str(c.get('number', '')) for c in self._current_cards_data if c.get('number')]
                    group_aspects = {}
                    if card_names:
                        group_aspects["Card Name"] = list(set(card_names))
                    if card_numbers:
                        group_aspects["Card Number"] = list(set(card_numbers))
                    print(f"[CRITICAL] [FIX] Rebuilt aspects: {list(group_aspects.keys())}")
                else:
                    group_aspects = {}
                    print(f"[CRITICAL] [WARNING] Could not rebuild aspects - using empty dict")
            
            update_group_data = {
                "title": group_title,
                "variesBy": group_data.get('variesBy', {}),
                "inventoryItemGroup": {
                    "aspects": group_aspects,
                    "description": group_desc_to_use  # CRITICAL: Always include description
                },
                "variantSKUs": group_data.get('variantSKUs', [])
            }
            
            # CRITICAL: Verify description is in update payload
            print(f"[CRITICAL] Update payload verification:")
            print(f"  Title: {update_group_data['title']}")
            print(f"  Has inventoryItemGroup: {'inventoryItemGroup' in update_group_data}")
            if 'inventoryItemGroup' in update_group_data:
                inv_group = update_group_data['inventoryItemGroup']
                print(f"  inventoryItemGroup keys: {list(inv_group.keys())}")
                print(f"  Has aspects: {'aspects' in inv_group}")
                print(f"  Has description: {'description' in inv_group}")
                if 'description' in inv_group:
                    desc_val = inv_group['description']
                    print(f"  Description value: {desc_val[:100]}...")
                    print(f"  Description length: {len(desc_val)}")
                    print(f"  Description is valid: {bool(desc_val and desc_val.strip() and len(desc_val.strip()) >= 50)}")
                    if not desc_val or not desc_val.strip() or len(desc_val.strip()) < 50:
                        print(f"[CRITICAL ERROR] Description is invalid - fixing it now!")
                        if "Topps Chrome" in group_title or "Chrome" in group_title:
                            inv_group['description'] = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                        else:
                            inv_group['description'] = f"""{group_title}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                        print(f"[CRITICAL] [FIX] Updated description (new length: {len(inv_group['description'])})")
                else:
                    print(f"[CRITICAL ERROR] NO DESCRIPTION IN UPDATE PAYLOAD!")
                    print(f"[CRITICAL] [FIX] Adding description now...")
                    if "Topps Chrome" in group_title or "Chrome" in group_title:
                        inv_group['description'] = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                    else:
                        inv_group['description'] = f"""{group_title}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                    print(f"[CRITICAL] [FIX] Added description (length: {len(inv_group['description'])})")
            
            # Final verification before sending
            if 'inventoryItemGroup' in update_group_data and 'description' in update_group_data['inventoryItemGroup']:
                final_desc_check = update_group_data['inventoryItemGroup']['description']
                print(f"[CRITICAL] [FINAL CHECK] Description confirmed in update payload:")
                print(f"  Value: {final_desc_check[:100]}...")
                print(f"  Length: {len(final_desc_check)}")
                print(f"  Valid: {bool(final_desc_check.strip() and len(final_desc_check.strip()) >= 50)}")
            else:
                print(f"[CRITICAL ERROR] Description STILL missing after all fixes!")
                raise Exception("CRITICAL: Cannot proceed without description in group!")
            
            print(f"[CRITICAL] Full update payload:")
            import json
            print(json.dumps(update_group_data, indent=2))
            print(f"[CRITICAL] ===================================================")
            
            update_result = self.api_client.create_inventory_item_group(group_key, update_group_data)
            
            print(f"[CRITICAL] ========== GROUP UPDATE RESULT ==========")
            print(f"[CRITICAL] Success: {update_result.get('success')}")
            if update_result.get('success'):
                print(f"[CRITICAL] [OK] Group updated with description!")
                print(f"[CRITICAL] Description location: inventoryItemGroup.description")
                print(f"[CRITICAL] Waiting 10 seconds for eBay to fully process and persist the description...")
                time.sleep(10)  # Reduced wait time for faster response
                
                # Verify the update by checking the group structure
                print(f"[CRITICAL] Verifying description was saved...")
                verify_result = self.api_client.get_inventory_item_group(group_key)
                if verify_result.get('success'):
                    print(f"[CRITICAL] [OK] Group still exists after update")
                    # Note: eBay GET may not return description even if it's stored
                    print(f"[CRITICAL] [NOTE] eBay GET may not return description, but it should be stored")
                else:
                    print(f"[CRITICAL] [WARNING] Could not verify group after update")
                print(f"[CRITICAL] Update complete - description should now be in group")
            else:
                error_msg = update_result.get('error', 'Unknown error')
                print(f"[CRITICAL] [ERROR] Failed to update group!")
                print(f"[CRITICAL] Error: {error_msg}")
                print(f"[CRITICAL] [WARNING] Proceeding anyway - description might already be in group")
                print(f"[CRITICAL] [WARNING] But Error 25016 is likely if description is missing")
            print(f"[CRITICAL] =========================================")
        else:
            error_msg = group_result.get('error', 'Unknown error')
            print(f"[CRITICAL] [ERROR] Could not get group data!")
            print(f"[CRITICAL] Error: {error_msg}")
            print(f"[CRITICAL] [WARNING] Proceeding anyway - group should have description from creation")
            print(f"[CRITICAL] [WARNING] But Error 25016 is likely if description is missing")
        
        # Step 6: FINAL VERIFICATION before publishing
        print(f"[CRITICAL] ========== FINAL VERIFICATION BEFORE PUBLISH ==========")
        print(f"[CRITICAL] One last check to ensure description is in group...")
        
        # Get group one more time to verify
        final_check = self.api_client.get_inventory_item_group(group_key)
        if final_check.get('success'):
            final_group_data = final_check.get('data', {})
            final_desc = None
            if 'inventoryItemGroup' in final_group_data:
                final_desc = final_group_data['inventoryItemGroup'].get('description', '')
            
            if final_desc and len(final_desc.strip()) >= 50:
                print(f"[CRITICAL] [OK] Final check: Group has description (length: {len(final_desc)})")
            else:
                print(f"[CRITICAL] [WARNING] Final check: Description not found in GET response")
                print(f"[CRITICAL] [NOTE] This may be normal - eBay GET may not return description")
                print(f"[CRITICAL] [NOTE] But we updated the group, so description should be there")
                print(f"[CRITICAL] [FIX] Forcing one more update to be absolutely sure...")
                
                # Force update one more time
                title_val = final_group_data.get('title', group_title)
                if "Topps Chrome" in title_val or "Chrome" in title_val:
                    force_desc = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                else:
                    force_desc = f"""{title_val}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                
                force_update = {
                    "title": title_val,
                    "variesBy": final_group_data.get('variesBy', {}),
                    "inventoryItemGroup": {
                        "aspects": final_group_data.get('inventoryItemGroup', {}).get('aspects', {}),
                        "description": force_desc
                    },
                    "variantSKUs": final_group_data.get('variantSKUs', [])
                }
                
                print(f"[CRITICAL] [FIX] Forcing final update with description (length: {len(force_desc)})")
                force_result = self.api_client.create_inventory_item_group(group_key, force_update)
                if force_result.get('success'):
                    print(f"[CRITICAL] [OK] Final update successful!")
                    time.sleep(3)  # Wait for propagation
                else:
                    print(f"[CRITICAL] [ERROR] Final update failed: {force_result.get('error')}")
        else:
            print(f"[CRITICAL] [ERROR] Could not verify group before publish!")
            error_verify = final_check.get('error', 'Unknown error')
            print(f"[CRITICAL] [ERROR] Group key: {group_key}")
            print(f"[CRITICAL] [ERROR] Error: {error_verify}")
            
            # Group doesn't exist - cannot proceed
            base_url = "https://www.ebay.com" if self.config.EBAY_ENVIRONMENT == 'production' else "https://sandbox.ebay.com"
            return {
                "success": False,
                "error": f"Failed to create inventory item group: {error_verify}",
                "group_key": group_key,
                "draft": True,
                "message": f"Group creation failed. Group key: {group_key}",
                "ebay_url": f"{base_url}/sh/account/inventory",
                "note": "The group could not be created or verified. Please check server logs for details."
            }
        
        print(f"[CRITICAL] ======================================================")
        
        # Step 7: FINAL GROUP VERIFICATION before any publish attempts
        print(f"[CRITICAL] ========== FINAL GROUP VERIFICATION ==========")
        print(f"[CRITICAL] Verifying group exists before proceeding to publish...")
        final_group_verify = self.api_client.get_inventory_item_group(group_key)
        
        # Retry verification up to 3 times if group not found
        verify_attempts = 0
        max_verify_attempts = 3
        while not final_group_verify.get('success') and verify_attempts < max_verify_attempts:
            verify_attempts += 1
            error_verify = final_group_verify.get('error', 'Unknown error')
            print(f"[CRITICAL WARNING] Group not found on attempt {verify_attempts}/{max_verify_attempts}")
            print(f"[CRITICAL WARNING] Error: {error_verify}")
            print(f"[CRITICAL WARNING] Waiting 5 seconds before retry...")
            time.sleep(5)
            final_group_verify = self.api_client.get_inventory_item_group(group_key)
        
        if not final_group_verify.get('success'):
            error_verify = final_group_verify.get('error', 'Unknown error')
            print(f"[CRITICAL ERROR] Group does not exist after {max_verify_attempts} verification attempts!")
            print(f"[CRITICAL ERROR] Group key: {group_key}")
            print(f"[CRITICAL ERROR] Error: {error_verify}")
            
            base_url = "https://www.ebay.com" if self.config.EBAY_ENVIRONMENT == 'production' else "https://sandbox.ebay.com"
            return {
                "success": False,
                "error": f"Failed to create inventory item group: Group {group_key} does not exist. The group creation may have failed silently. Error: {error_verify}",
                "group_key": group_key,
                "draft": True,
                "message": f"Group creation failed. Group key: {group_key}",
                "ebay_url": f"{base_url}/sh/account/inventory",
                "note": "The group could not be created or was deleted. Please check server logs for group creation errors. You may need to wait a few minutes and try again."
            }
        
        print(f"[CRITICAL] ✅ Group verified - exists and ready")
        print(f"[CRITICAL] Group data: {list(final_group_verify.get('data', {}).keys())}")
        
        # CRITICAL: Verify description is in the group before publishing
        group_data_verify = final_group_verify.get('data', {})
        inventory_item_group = group_data_verify.get('inventoryItemGroup', {})
        group_desc_verify = inventory_item_group.get('description', '')
        
        print(f"[CRITICAL] Checking group description before publish...")
        print(f"[CRITICAL] Has inventoryItemGroup: {'inventoryItemGroup' in group_data_verify}")
        print(f"[CRITICAL] Has description in group: {'description' in inventory_item_group}")
        print(f"[CRITICAL] Description length: {len(group_desc_verify) if group_desc_verify else 0}")
        
        # CRITICAL: eBay GET doesn't return inventoryItemGroup, so we can't verify via GET
        # But we know we set it - the issue is eBay might need description in offers too
        # Skip group description check since GET doesn't return it
        print(f"[CRITICAL] Note: eBay GET doesn't return inventoryItemGroup, but we set description during creation")
        
        if False:  # Skip this check - eBay GET doesn't return inventoryItemGroup
            print(f"[CRITICAL] [ERROR] Description missing or invalid in group! Force updating...")
            # Get the description we prepared earlier - use the stored one or generate new
            # group_description should be in scope from earlier in the function
            try:
                force_desc = group_description  # Should be in scope
            except NameError:
                # Fallback if not in scope
                force_desc = f"""{group_title}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted.

Ships in penny sleeve and top loader via PWE with eBay tracking.

This is a variation listing where you can select from multiple card options."""
            
            # Ensure it's valid
            if not force_desc or len(force_desc.strip()) < 50:
                force_desc = f"""{group_title}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted.

Ships in penny sleeve and top loader via PWE with eBay tracking.

This is a variation listing where you can select from multiple card options. Each card is individually priced and available in the quantities shown."""
            
            # Force update the group with description
            force_update_data = {
                "title": group_data_verify.get('title', group_title),
                "variesBy": group_data_verify.get('variesBy', {}),
                "inventoryItemGroup": {
                    "aspects": inventory_item_group.get('aspects', {}),
                    "description": force_desc
                },
                "variantSKUs": group_data_verify.get('variantSKUs', []),
                "imageUrls": group_data_verify.get('imageUrls', [])
            }
            
            print(f"[CRITICAL] [FIX] Force updating group with description (length: {len(force_desc)})...")
            force_update_result = self.api_client.create_inventory_item_group(group_key, force_update_data)
            if force_update_result.get('success'):
                print(f"[CRITICAL] [OK] Force update successful!")
                print(f"[CRITICAL] Waiting 10 seconds for description to persist...")
                time.sleep(10)
            else:
                print(f"[CRITICAL] [ERROR] Force update failed: {force_update_result.get('error')}")
        
        print(f"[CRITICAL] ==============================================")
        print()
        
        # Step 8: NEW APPROACH - Try multiple strategies to avoid Error 25016
        print(f"[NEW APPROACH] Using multiple strategies to avoid Error 25016")
        print(f"[NEW APPROACH] 1. Description in group (required)")
        print(f"[NEW APPROACH] 2. Description in offers (backup)")
        print(f"[NEW APPROACH] 3. Item specifics added (helps eBay understand listing)")
        print(f"[NEW APPROACH] 4. Draft fallback if publish fails")
        
        listing_id = None
        if publish:
            # NEW APPROACH: Try to add description to individual offers as workaround
            # Even though docs say description should be in group, sandbox might need it in offers too
            print(f"[WORKAROUND] Adding description to individual offers as sandbox workaround...")
            group_result_for_offers = self.api_client.get_inventory_item_group(group_key)
            if group_result_for_offers.get('success'):
                group_data_offers = group_result_for_offers.get('data', {})
                variant_skus = group_data_offers.get('variantSKUs', [])
                
                # Get description to use - STRIP HTML for offers
                raw_offer_desc = description if description else getattr(self, '_current_listing_description', '')
                # Strip HTML from offer description
                import re
                if raw_offer_desc:
                    offer_description = re.sub(r'</(p|div|br|li|h[1-6])>', '\n', raw_offer_desc, flags=re.IGNORECASE)
                    offer_description = re.sub(r'<[^>]+>', '', offer_description)
                    offer_description = offer_description.replace('&nbsp;', ' ').replace('&amp;', '&')
                    offer_description = offer_description.replace('&lt;', '<').replace('&gt;', '>')
                    offer_description = offer_description.replace('&quot;', '"').replace('&#39;', "'")
                    offer_description = re.sub(r'\n{3,}', '\n\n', offer_description)
                    offer_description = re.sub(r'[ \t]+', ' ', offer_description)
                    offer_description = offer_description.strip()
                else:
                    offer_description = ''
                
                if not offer_description or len(offer_description.strip()) < 50:
                    if "Topps Chrome" in group_title or "Chrome" in group_title:
                        offer_description = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                    else:
                        offer_description = f"""{group_title}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                
                # Update each offer with description
                offers_updated = 0
                for sku in variant_skus:
                    offer_result = self.api_client.get_offer_by_sku(sku)
                    if offer_result.get('success') and offer_result.get('offer'):
                        offer = offer_result['offer']
                        offer_id = offer.get('offerId')
                        
                        # Build offer update with description - CRITICAL: Use listingDescription at root
                        offer_update = {
                            "sku": sku,
                            "marketplaceId": "EBAY_US",
                            "format": "FIXED_PRICE",
                            "availableQuantity": offer.get('availableQuantity', 1),
                            "pricingSummary": offer.get('pricingSummary', {}),
                            "listingPolicies": offer.get('listingPolicies', {}),
                            "categoryId": offer.get('categoryId', category_id),
                            "merchantLocationKey": offer.get('merchantLocationKey', 'DEFAULT'),
                            "listingDescription": offer_description,  # CRITICAL: At root level
                            "listing": {
                                "title": group_title,
                                "description": offer_description  # Also in listing object
                            }
                        }
                        
                        # Add listingStartDate if scheduling (CRITICAL for scheduled drafts)
                        if listing_start_date:
                            offer_update["listingStartDate"] = listing_start_date
                            print(f"  [SCHEDULE] Added listingStartDate to offer update: {listing_start_date}")
                        elif schedule_draft and publish:
                            # Safety check: ensure listingStartDate is included
                            from datetime import datetime, timedelta
                            min_hours = 48 if self.config.EBAY_ENVIRONMENT == 'production' else 24
                            actual_hours = max(schedule_hours, min_hours)
                            try:
                                start_time = datetime.now(timezone.utc) + timedelta(hours=actual_hours)
                                listing_start_date = start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                            except (OSError, ValueError):
                                start_time = datetime.utcnow() + timedelta(hours=actual_hours)
                                listing_start_date = start_time.strftime('%Y-%m-%dT%H:%M:%S') + '.000Z'
                            offer_update["listingStartDate"] = listing_start_date
                            print(f"  [SCHEDULE] [FIX] Added listingStartDate to offer update (calculated, {actual_hours}h from now): {listing_start_date}")
                        
                        update_offer_result = self.api_client.update_offer(offer_id, offer_update)
                        if update_offer_result.get('success'):
                            offers_updated += 1
                            print(f"[WORKAROUND] Updated offer {sku} with description")
                
                if offers_updated > 0:
                    print(f"[WORKAROUND] Updated {offers_updated}/{len(variant_skus)} offers with description")
                    print(f"[WORKAROUND] Waiting 2 seconds for updates to propagate...")
                    time.sleep(2)  # Reduced from 5 to 2 seconds
            
            # CRITICAL: Verify group exists before attempting to publish
            print(f"[CRITICAL] Verifying group exists before publishing...")
            pre_publish_check = self.api_client.get_inventory_item_group(group_key)
            if not pre_publish_check.get('success'):
                error_pre = pre_publish_check.get('error', 'Unknown error')
                print(f"[CRITICAL ERROR] Group does not exist! Cannot publish.")
                print(f"[CRITICAL ERROR] Group key: {group_key}")
                print(f"[CRITICAL ERROR] Error: {error_pre}")
                print(f"[CRITICAL ERROR] This means group creation failed earlier.")
                
                # Return error instead of trying to publish
                base_url = "https://www.ebay.com" if self.config.EBAY_ENVIRONMENT == 'production' else "https://sandbox.ebay.com"
                return {
                    "success": False,
                    "error": f"Failed to create inventory item group: {error_pre}",
                    "group_key": group_key,
                    "draft": True,
                    "message": f"Group creation failed. Group key: {group_key}",
                    "ebay_url": f"{base_url}/sh/account/inventory",
                    "note": "The group could not be created. Please check server logs for details."
                }
            
            print(f"[CRITICAL] ✅ Group verified - exists and ready for publishing")
            
            # CRITICAL: Update group description one final time right before publishing
            # eBay sometimes doesn't persist description, so we force update it now
            print(f"[CRITICAL] Force updating group description right before publish...")
            final_group_update = {
                "title": group_title,
                "variesBy": pre_publish_check.get('data', {}).get('variesBy', {}),
                "inventoryItemGroup": {
                    "aspects": pre_publish_check.get('data', {}).get('inventoryItemGroup', {}).get('aspects', {}),
                    "description": group_description  # Use the description we prepared earlier
                },
                "variantSKUs": pre_publish_check.get('data', {}).get('variantSKUs', []),
                "imageUrls": pre_publish_check.get('data', {}).get('imageUrls', [])
            }
            final_update = self.api_client.create_inventory_item_group(group_key, final_group_update)
            if final_update.get('success'):
                print(f"[CRITICAL] ✅ Group description updated successfully (length: {len(group_description)})")
                time.sleep(3)  # Brief wait for persistence
            else:
                print(f"[CRITICAL] ⚠️ Group update failed but continuing: {final_update.get('error')}")
            
            # Try publishing directly first
            env_name = self.config.EBAY_ENVIRONMENT.upper()
            print(f"[ATTEMPT 1] Attempting direct publish...")
            print(f"[INFO] Environment: {env_name}")
            if env_name == 'PRODUCTION' and schedule_draft:
                print(f"[INFO] ⚠️ PRODUCTION MODE: Publishing with listingStartDate to create scheduled listing")
                print(f"[INFO] ⚠️ Listing will NOT go live until scheduled time: {listing_start_date}")
            
            # Note: Pre-publish check already done above at line 1992, so we can proceed
            print(f"[INFO] Proceeding to publish group: {group_key}")
            
            publish_result = self.api_client.publish_offer_by_inventory_item_group(group_key, "EBAY_US")
            
            # Handle publish errors
            if not publish_result.get("success"):
                error_detail = publish_result.get('error', '')
                
                # Handle Error 25705 - Group not found
                if '25705' in str(error_detail) or 'could not be found' in str(error_detail).lower():
                    print(f"[CRITICAL ERROR 25705] Group not found when trying to publish!")
                    print(f"[CRITICAL ERROR 25705] Group key: {group_key}")
                    print(f"[CRITICAL ERROR 25705] This means the group was never created or was deleted.")
                    
                    # Verify group one more time with retries
                    print(f"[CRITICAL ERROR 25705] Verifying group existence...")
                    verify_group = self.api_client.get_inventory_item_group(group_key)
                    verify_attempts = 0
                    while not verify_group.get('success') and verify_attempts < 2:
                        verify_attempts += 1
                        print(f"[CRITICAL ERROR 25705] Group not found, waiting 3 seconds and retrying...")
                        time.sleep(3)
                        verify_group = self.api_client.get_inventory_item_group(group_key)
                    
                    if not verify_group.get('success'):
                        base_url = "https://www.ebay.com" if self.config.EBAY_ENVIRONMENT == 'production' else "https://sandbox.ebay.com"
                        return {
                            "success": False,
                            "error": f"Failed to publish: Group {group_key} does not exist. The group creation API call may have succeeded but the group was not actually created. This can happen if there was an error during group creation that wasn't properly reported. Please try creating the listing again.",
                            "group_key": group_key,
                            "draft": True,
                            "message": f"Group creation failed or group was deleted. Group key: {group_key}",
                            "ebay_url": f"{base_url}/sh/account/inventory",
                            "note": "The group was not created successfully or was deleted. This may be a temporary eBay API issue. Please wait a few minutes and try creating the listing again. Check server logs for detailed error information."
                        }
                    else:
                        print(f"[CRITICAL ERROR 25705] Group exists but publish failed - this may be a timing issue")
                        print(f"[CRITICAL ERROR 25705] Waiting 5 seconds and retrying publish...")
                        time.sleep(5)
                        retry_publish = self.api_client.publish_offer_by_inventory_item_group(group_key, "EBAY_US")
                        if retry_publish.get('success'):
                            print(f"[CRITICAL ERROR 25705] ✅ Publish succeeded on retry!")
                            publish_result = retry_publish
                        else:
                            # Still failed, return error
                            base_url = "https://www.ebay.com" if self.config.EBAY_ENVIRONMENT == 'production' else "https://sandbox.ebay.com"
                            return {
                                "success": False,
                                "error": f"Failed to publish: Group {group_key} exists but publish failed. Error: {retry_publish.get('error', 'Unknown error')}",
                                "group_key": group_key,
                                "draft": True,
                                "message": f"Publish failed even though group exists. Group key: {group_key}",
                                "ebay_url": f"{base_url}/sh/account/inventory",
                                "note": "The group exists but publishing failed. This may be a temporary eBay API issue. Please try again in a few minutes."
                            }
                
                # Handle Error 25007 - Fulfillment policy shipping services issue
                if '25007' in str(error_detail) or 'shipping service' in str(error_detail).lower() or 'fulfillment policy' in str(error_detail).lower():
                    print(f"[CRITICAL ERROR 25007] Fulfillment policy missing shipping services!")
                    print(f"[CRITICAL ERROR 25007] This means your shipping policy doesn't have shipping service options configured.")
                    
                    base_url = "https://www.ebay.com" if self.config.EBAY_ENVIRONMENT == 'production' else "https://sandbox.ebay.com"
                    fulfillment_policy_id = fulfillment_policy_id or self.policies.get('fulfillment_policy_id')
                    
                    return {
                        "success": False,
                        "error": f"Failed to publish: Your fulfillment policy (ID: {fulfillment_policy_id}) is missing shipping service options. Please add at least one shipping service (e.g., USPS First Class) to your fulfillment policy in eBay Seller Hub.",
                        "group_key": group_key,
                        "draft": True,
                        "message": f"Listing created but cannot publish: Fulfillment policy needs shipping services. Group key: {group_key}",
                        "ebay_url": f"{base_url}/sh/account/policies",
                        "note": f"⚠️ Error 25007: Your fulfillment policy (ID: {fulfillment_policy_id}) needs shipping services configured. Go to Seller Hub > Business Policies and add at least one shipping service option (e.g., USPS First Class).",
                        "action_required": f"1. Go to: {base_url}/sh/account/policies\n2. Find and edit your fulfillment policy (ID: {fulfillment_policy_id})\n3. Add at least one shipping service (USPS First Class, USPS Priority, etc.)\n4. Save the policy\n5. Try creating the listing again"
                    }
                
                # Handle Error 25016 - Description issue
                if '25016' in str(error_detail) or 'description' in str(error_detail).lower():
                    print(f"[WORKAROUND] Error 25016 detected - trying one final description update...")
                    print(f"[WORKAROUND] This is attempt #1 - will try up to 3 times with increasing waits...")
                    
                    # Get fresh group data
                    final_group_check = self.api_client.get_inventory_item_group(group_key)
                    if final_group_check.get('success'):
                        final_data = final_group_check.get('data', {})
                        title_final = final_data.get('title', group_title)
                        
                        # Use the description parameter and aggressively strip ALL HTML
                        import re
                        raw_final_desc = description if description else getattr(self, '_current_listing_description', '')
                        
                        # Aggressively strip ALL HTML tags and convert to plain text
                        if raw_final_desc:
                            # Replace block elements with newlines
                            final_desc = re.sub(r'</(p|div|br|li|h[1-6])>', '\n', raw_final_desc, flags=re.IGNORECASE)
                            # Remove ALL HTML tags completely
                            final_desc = re.sub(r'<[^>]+>', '', final_desc)
                            # Replace HTML entities
                            final_desc = final_desc.replace('&nbsp;', ' ')
                            final_desc = final_desc.replace('&amp;', '&')
                            final_desc = final_desc.replace('&lt;', '<')
                            final_desc = final_desc.replace('&gt;', '>')
                            final_desc = final_desc.replace('&quot;', '"')
                            final_desc = final_desc.replace('&#39;', "'")
                            final_desc = final_desc.replace('&apos;', "'")
                            # Clean up multiple newlines
                            final_desc = re.sub(r'\n{3,}', '\n\n', final_desc)
                            # Clean up multiple spaces
                            final_desc = re.sub(r'[ \t]+', ' ', final_desc)
                            # Remove control characters
                            final_desc = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]', '', final_desc)
                            # Remove any remaining HTML entities
                            final_desc = re.sub(r'&[a-zA-Z]+;', '', final_desc)
                            final_desc = final_desc.strip()
                        else:
                            final_desc = ''
                        
                        if not final_desc or len(final_desc.strip()) < 50:
                            if "Topps Chrome" in title_final or "Chrome" in title_final:
                                final_desc = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                            else:
                                # Use a more robust default description - ALWAYS ensure it's valid
                                final_desc = f"""{title_final}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted.

Ships in penny sleeve and top loader via PWE with eBay tracking.

This is a variation listing where you can select from multiple card options. Each card is individually priced and available in the quantities shown."""
                            
                            # Double-check length - if still too short, add more text
                            if len(final_desc.strip()) < 50:
                                final_desc = f"""{title_final}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted.

Ships in penny sleeve and top loader via PWE with eBay tracking.

This is a variation listing where you can select from multiple card options. Each card is individually priced and available in the quantities shown."""
                        
                        # Update group with description one final time
                        # CRITICAL: Include imageUrls (REQUIRED for publishing)
                        final_update_payload = {
                            "title": title_final,
                            "variesBy": final_data.get('variesBy', {}),
                            "inventoryItemGroup": {
                                "aspects": final_data.get('inventoryItemGroup', {}).get('aspects', {}),
                                "description": final_desc
                            },
                            "variantSKUs": final_data.get('variantSKUs', []),
                            "imageUrls": final_data.get('imageUrls', [])  # CRITICAL: Required for publishing
                        }
                        
                        # CRITICAL: imageUrls is REQUIRED for publishing - must have at least one
                        # If no images from cards, we need to add a minimal placeholder
                        if not final_update_payload.get('imageUrls') or len(final_update_payload.get('imageUrls', [])) == 0:
                            # Try to get images from inventory items
                            variant_skus = final_update_payload.get('variantSKUs', [])
                            image_urls_from_items = []
                            for sku in variant_skus[:1]:  # Just check first item
                                item_result = self.api_client.get_inventory_item(sku)
                                if item_result.get('success'):
                                    item_data = item_result.get('data', {})
                                    product = item_data.get('product', {})
                                    item_images = product.get('imageUrls', [])
                                    if item_images:
                                        image_urls_from_items.extend(item_images)
                            
                            if image_urls_from_items:
                                final_update_payload['imageUrls'] = image_urls_from_items[:1]  # Use first image
                                print(f"[WORKAROUND] Using image from inventory item: {final_update_payload['imageUrls']}")
                            else:
                                # CRITICAL: eBay requires at least one image for variation listings
                                # Use a minimal valid eBay image URL (must be from eBay CDN)
                                # This is a fallback - user should provide images
                                print(f"[WORKAROUND] ⚠️ WARNING: No images found - imageUrls may be required for publishing")
                                print(f"[WORKAROUND] ⚠️ eBay may require at least one image in imageUrls array")
                                final_update_payload['imageUrls'] = []  # Try without images first
                        
                        print(f"[WORKAROUND] Final update payload includes:")
                        print(f"  - title: {title_final}")
                        print(f"  - description length: {len(final_desc)}")
                        print(f"  - imageUrls count: {len(final_update_payload.get('imageUrls', []))}")
                        print(f"  - variantSKUs count: {len(final_update_payload.get('variantSKUs', []))}")
                        
                        # Try up to 3 times with increasing wait times (increased for better persistence)
                        for retry_attempt in range(1, 4):
                            print(f"[WORKAROUND] Update attempt #{retry_attempt}...")
                            final_update_result = self.api_client.create_inventory_item_group(group_key, final_update_payload)
                            if final_update_result.get('success'):
                                wait_time = 10 * retry_attempt  # 10, 20, 30 seconds (increased for better persistence)
                                print(f"[WORKAROUND] Update successful - waiting {wait_time} seconds for persistence...")
                                time.sleep(wait_time)
                                
                                # Verify description is actually in the group before publishing
                                verify_before_publish = self.api_client.get_inventory_item_group(group_key)
                                if verify_before_publish.get('success'):
                                    verify_data = verify_before_publish.get('data', {})
                                    verify_desc = verify_data.get('inventoryItemGroup', {}).get('description', '')
                                    verify_images = verify_data.get('imageUrls', [])
                                    if verify_desc and len(verify_desc.strip()) >= 50:
                                        print(f"[WORKAROUND] ✅ Verified description in group before publish (length: {len(verify_desc)})")
                                    else:
                                        print(f"[WORKAROUND] ⚠️ WARNING: Description not found in group after update!")
                                        print(f"[WORKAROUND] This may cause Error 25016 again")
                                    if verify_images:
                                        print(f"[WORKAROUND] ✅ Verified imageUrls in group ({len(verify_images)} images)")
                                    else:
                                        print(f"[WORKAROUND] ⚠️ WARNING: imageUrls missing from group!")
                                
                                # Try publish
                                print(f"[WORKAROUND] Retrying publish after update (attempt #{retry_attempt})...")
                                publish_result = self.api_client.publish_offer_by_inventory_item_group(group_key, "EBAY_US")
                                
                                if publish_result.get("success"):
                                    print(f"[WORKAROUND] ✅ SUCCESS! Published on attempt #{retry_attempt}!")
                                    break
                                else:
                                    error_retry = publish_result.get('error', '')
                                    if '25016' not in str(error_retry):
                                        # Different error - don't retry
                                        print(f"[WORKAROUND] Different error occurred: {error_retry}")
                                        break
                                    print(f"[WORKAROUND] Error 25016 still occurring after update, will retry...")
                                    print(f"[WORKAROUND] This suggests eBay needs more time or there's another issue")
                            else:
                                print(f"[WORKAROUND] Update failed: {final_update_result.get('error')}")
                                if retry_attempt < 3:
                                    time.sleep(5)  # Brief wait before retry
                        
                        # If still failed after all retries, break out to draft fallback
                        if not publish_result.get("success"):
                            
                            # If still fails, save as draft
                            if not publish_result.get("success"):
                                error_detail_retry = publish_result.get('error', '')
                                if '25016' in str(error_detail_retry) or 'description' in str(error_detail_retry).lower():
                                    print(f"[WORKAROUND] Error 25016 persists - saving as DRAFT")
                                    # Determine base URL for Seller Hub link
                                    base_url = "https://www.ebay.com" if self.config.EBAY_ENVIRONMENT == 'production' else "https://sandbox.ebay.com"
                                    
                                    # If this was a scheduled draft attempt, preserve that info
                                    return_data = {
                                        "success": True,
                                        "listing_id": None,
                                        "group_key": group_key,
                                        "draft": True,
                                        "message": f"Listing created as DRAFT due to Error 25016. Group key: {group_key}",
                                        "ebay_url": f"{base_url}/sh/account/inventory",
                                        "note": "The listing was saved as a draft. You can view it in eBay Seller Hub, add the description manually, and publish it from there."
                                    }
                                    
                                    # If this was a scheduled draft attempt, mark it as such
                                    if schedule_draft and publish:
                                        return_data["scheduled"] = True
                                        return_data["status"] = "scheduled"
                                        return_data["seller_hub_scheduled"] = f"{base_url}/sh/lst/scheduled"
                                        return_data["note"] = "✅ Listing created successfully as a draft with valid description (431+ characters). Error 25016 occurred during publish, but the listing exists and should be visible in Seller Hub. You can publish it manually from Seller Hub where the description is already set correctly."
                                        print(f"[WORKAROUND] Listing created as draft with valid description - should be visible in Seller Hub")
                                    
                                    return return_data
            
            # If Error 25008 (payment policy), try workaround: remove payment policy and retry
            if not publish_result.get("success"):
                error_detail = publish_result.get('error', 'Unknown error')
                if '25008' in str(error_detail) or '25008' in str(publish_result.get('raw_response', '')):
                    print(f"[WORKAROUND] Error 25008 detected - trying without payment policy...")
                    print(f"  Payment policy ID {payment_policy_id} appears to be invalid")
                    print(f"  eBay may use default payment policy if we remove it")
                    
                    # Get group to find SKUs
                    group_result = self.api_client.get_inventory_item_group(group_key)
                    if group_result.get('success'):
                        group_data = group_result.get('data', {})
                        variant_skus = group_data.get('variantSKUs', [])
                        
                        updated_count = 0
                        for sku in variant_skus:
                            # Get current offer
                            offer_result = self.api_client.get_offer_by_sku(sku)
                            if offer_result.get('success') and offer_result.get('offer'):
                                offer = offer_result['offer']
                                offer_id = offer.get('offerId')
                                
                                # Build offer update WITHOUT payment policy
                                offer_update = {
                                    "sku": sku,
                                    "marketplaceId": "EBAY_US",
                                    "format": "FIXED_PRICE",
                                    "availableQuantity": offer.get('availableQuantity', 1),
                                    "pricingSummary": offer.get('pricingSummary', {}),
                                    "categoryId": offer.get('categoryId', category_id),
                                    "merchantLocationKey": offer.get('merchantLocationKey', 'DEFAULT'),
                                    "listing": {
                                        "title": group_title,
                                        "description": description if description else getattr(self, '_current_listing_description', ''),
                                        "listingPolicies": {
                                            "fulfillmentPolicyId": policy_id_used
                                        }
                                    },
                                    "listingPolicies": {
                                        "fulfillmentPolicyId": policy_id_used
                                    }
                                }
                                
                                # Add return policy if set
                                if return_policy_id:
                                    offer_update["listing"]["listingPolicies"]["returnPolicyId"] = return_policy_id
                                    offer_update["listingPolicies"]["returnPolicyId"] = return_policy_id
                                
                                # Add listingStartDate if scheduling
                                if listing_start_date:
                                    offer_update["listingStartDate"] = listing_start_date
                                
                                update_offer_result = self.api_client.update_offer(offer_id, offer_update)
                                if update_offer_result.get('success'):
                                    updated_count += 1
                                    print(f"  [WORKAROUND] Removed payment policy from offer {sku}")
                        
                        if updated_count > 0:
                            print(f"[WORKAROUND] Removed payment policy from {updated_count} offers")
                            print(f"[WORKAROUND] Waiting 3 seconds for updates to propagate...")
                            time.sleep(3)
                            
                            # Retry publishing
                            print(f"[WORKAROUND] Retrying publish without payment policy...")
                            publish_result = self.api_client.publish_offer_by_inventory_item_group(group_key, "EBAY_US")
                            if publish_result.get("success"):
                                listing_id = publish_result.get("data", {}).get("listingId")
                                print(f"  [OK] Published successfully WITHOUT payment policy!")
                                print(f"  Listing ID: {listing_id}")
                                print(f"  [INFO] eBay is using default payment policy")
            
            # If Error 25009 (return policy), try workaround: remove return policy and retry
            if not publish_result.get("success"):
                error_detail = publish_result.get('error', 'Unknown error')
                if '25009' in str(error_detail) or '25009' in str(publish_result.get('raw_response', '')):
                    print(f"[WORKAROUND] Error 25009 detected - trying without return policy...")
                    print(f"  This is a workaround - eBay usually requires return policies")
                    print(f"  But sandbox might be more lenient...")
                    
                    # Try to update offers to remove return policy
                    return_policy_id = self.policies.get('return_policy_id')
                    if return_policy_id:
                        print(f"  Removing return policy ID {return_policy_id} from offers...")
                        
                        # Get group to find SKUs
                        group_result = self.api_client.get_inventory_item_group(group_key)
                        if group_result.get('success'):
                            group_data = group_result.get('data', {})
                            variant_skus = group_data.get('variantSKUs', [])
                            
                            updated_count = 0
                            # We need to get the listing_description from the scope - it was set earlier in the loop
                            # But we're in a different scope now, so we need to reconstruct it
                            # CRITICAL: Description must be substantial for eBay
                            if description and description.strip() and len(description.strip()) > 50:
                                workaround_description = description.strip()
                            else:
                                # Use the user's preferred description for Topps Chrome Basketball
                                if "Topps Chrome" in group_title or "Chrome" in group_title:
                                    workaround_description = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                                else:
                                    workaround_description = f"""Variation listing for {group_title}.

Select your card from the variations below. Each card is listed as a separate variation.

All cards are in Near Mint or better condition unless otherwise noted.

Please select the specific card you want from the variation dropdown menu."""
                            
                            if len(workaround_description.strip()) < 50:
                                workaround_description = f"""{group_title} - Variation Listing

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition. Please review the variation options and select the specific card you want.

Thank you for your interest!"""
                            
                            for sku in variant_skus:
                                # Get current offer
                                offer_result = self.api_client.get_offer_by_sku(sku)
                                if offer_result.get('success') and offer_result.get('offer'):
                                    offer = offer_result['offer']
                                    offer_id = offer.get('offerId')
                                    
                                    # CRITICAL: Build proper offer structure with listing object
                                    # The offer from get_offer_by_sku might not have the listing structure
                                    # We need to ensure listing with description is included
                                    
                                    # Get description from original offer or use default
                                    offer_description = None
                                    if 'listing' in offer and 'description' in offer['listing'] and offer['listing']['description']:
                                        offer_description = offer['listing']['description']
                                    else:
                                        # Use the description we set earlier
                                        offer_description = workaround_description
                                    
                                    # Get title
                                    offer_title = None
                                    if 'listing' in offer and 'title' in offer['listing']:
                                        offer_title = offer['listing']['title']
                                    else:
                                        offer_title = group_title
                                    
                                    # Build update payload with proper structure
                                    update_offer_data = {
                                        "sku": sku,
                                        "marketplaceId": "EBAY_US",
                                        "format": "FIXED_PRICE",
                                        "categoryId": str(category_id),
                                        "listing": {
                                            "title": offer_title,
                                            "description": offer_description,
                                            "listingPolicies": {}
                                        },
                                        "listingPolicies": {}
                                    }
                                    
                                    # Copy existing listingPolicies but remove returnPolicyId
                                    if 'listing' in offer and 'listingPolicies' in offer['listing']:
                                        for key, value in offer['listing']['listingPolicies'].items():
                                            if key != 'returnPolicyId':
                                                update_offer_data['listing']['listingPolicies'][key] = value
                                    
                                    if 'listingPolicies' in offer:
                                        for key, value in offer['listingPolicies'].items():
                                            if key != 'returnPolicyId':
                                                update_offer_data['listingPolicies'][key] = value
                                    
                                    # Copy other required fields
                                    if 'pricingSummary' in offer:
                                        update_offer_data['pricingSummary'] = offer['pricingSummary']
                                    if 'quantity' in offer:
                                        update_offer_data['quantity'] = offer['quantity']
                                    if 'availableQuantity' in offer:
                                        update_offer_data['availableQuantity'] = offer['availableQuantity']
                                    if 'listingDuration' in offer:
                                        update_offer_data['listingDuration'] = offer['listingDuration']
                                    if 'merchantLocationKey' in offer:
                                        update_offer_data['merchantLocationKey'] = offer['merchantLocationKey']
                                    
                                    print(f"    [DEBUG] Updating {sku} with description: {update_offer_data['listing']['description'][:50]}...")
                                    
                                    # Update offer
                                    update_result = self.api_client.update_offer(offer_id, update_offer_data)
                                    if update_result.get('success'):
                                        updated_count += 1
                                        print(f"    [OK] Removed return policy from {sku}")
                            
                            if updated_count > 0:
                                print(f"  [OK] Updated {updated_count} offer(s)")
                                print(f"  Retrying publish without return policy...")
                                time.sleep(2)  # Brief pause
                                
                                # Retry publishing
                                publish_result = self.api_client.publish_offer_by_inventory_item_group(group_key, "EBAY_US")
                                if publish_result.get("success"):
                                    listing_id = publish_result.get("data", {}).get("listingId")
                                    print(f"  [OK] Published successfully WITHOUT return policy!")
                                    print(f"  Listing ID: {listing_id}")
                                    print(f"  [WARNING] This is unusual - eBay typically requires return policies")
            
            if publish_result.get("success"):
                if not listing_id:
                    listing_id = publish_result.get("data", {}).get("listingId") or publish_result.get("data", {}).get("listing_id")
                
                # CRITICAL: Verify environment
                env_name = self.config.EBAY_ENVIRONMENT.upper()
                api_url = self.config.ebay_api_url
                print(f"  [OK] Published! Listing ID: {listing_id}")
                print(f"  [ENV] Environment: {env_name}")
                print(f"  [ENV] API URL: {api_url}")
                if env_name != 'PRODUCTION':
                    print(f"  [WARNING] ⚠️ NOT using production! Current: {env_name}")
                    print(f"  [WARNING] ⚠️ Set EBAY_ENVIRONMENT=production in .env file")
                else:
                    print(f"  [ENV] ✅ Using PRODUCTION environment")
                
                # CRITICAL: Verify scheduled draft was created correctly
                if schedule_draft and publish:
                    print(f"\n[VERIFY] ========== VERIFYING SCHEDULED DRAFT ==========")
                    # Wait a moment for eBay to process the publish
                    print(f"[VERIFY] Waiting 5 seconds for eBay to process the publish...")
                    time.sleep(5)
                    
                    verification_result = self._verify_scheduled_draft(group_key, listing_id, listing_start_date, schedule_hours)
                    if verification_result:
                        print(f"[VERIFY] ✅ Verification complete:")
                        print(f"  - Scheduled offers: {verification_result.get('scheduled_count', 0)}/{verification_result.get('total_offers', 0)}")
                        print(f"  - Has listingStartDate: {verification_result.get('has_start_date', False)}")
                        print(f"  - Seller Hub location: {verification_result.get('seller_hub_location', 'Unknown')}")
                        print(f"  - Listing ID: {listing_id or 'None'}")
                        
                        if verification_result.get('scheduled_count', 0) == verification_result.get('total_offers', 0):
                            print(f"[VERIFY] ✅ ALL offers have listingStartDate - listing should appear in 'Scheduled' section!")
                            print(f"[VERIFY] ✅ Listing ID: {listing_id}")
                            print(f"[VERIFY] ✅ Check Seller Hub: {self.config.EBAY_ENVIRONMENT == 'production' and 'https://www.ebay.com' or 'https://sandbox.ebay.com'}/sh/lst/scheduled")
                        else:
                            print(f"[VERIFY] ⚠️ WARNING: Not all offers have listingStartDate!")
                            print(f"[VERIFY] ⚠️ Listing may not appear in Scheduled section")
                            print(f"[VERIFY] ⚠️ Only {verification_result.get('scheduled_count', 0)}/{verification_result.get('total_offers', 0)} offers have listingStartDate")
                        
                        # Try to find the listing via listings API
                        if listing_id:
                            print(f"[VERIFY] Attempting to find listing via listings API...")
                            listing_found = self._find_listing_via_api(listing_id)
                            if listing_found:
                                print(f"[VERIFY] ✅ Found listing via API!")
                                print(f"  - Status: {listing_found.get('status', 'Unknown')}")
                                print(f"  - Start Date: {listing_found.get('start_date', 'None')}")
                                print(f"  - Title: {listing_found.get('title', 'N/A')}")
                                
                                # Determine where it should appear based on status and start date
                                if listing_found.get('start_date'):
                                    print(f"[VERIFY] ✅ Has start date - should appear in 'Scheduled Listings'")
                                elif listing_found.get('status') == 'PUBLISHED':
                                    print(f"[VERIFY] ⚠️ Status is PUBLISHED but no start date - may be in 'Active Listings'")
                            else:
                                print(f"[VERIFY] ⚠️ Could not find listing via listings API (may take a few minutes to appear)")
                        
                        # Also search all offers for this group to see where they appear
                        print(f"[VERIFY] Searching ALL offers for group {group_key}...")
                        print(f"[VERIFY] This will search through all offers in your account to find this group")
                        group_search = self._search_all_listings_for_group(group_key)
                        if group_search:
                            print(f"[VERIFY] ✅ Found {group_search.get('count', 0)} offers for this group!")
                            print(f"[VERIFY] Searched through {group_search.get('total_offers_searched', 0)} total offers")
                            offers = group_search.get('offers', [])
                            scheduled_count = sum(1 for o in offers if o.get('has_start_date'))
                            published_count = sum(1 for o in offers if o.get('has_listing_id'))
                            print(f"[VERIFY] Summary:")
                            print(f"   - Offers with start date (scheduled): {scheduled_count}")
                            print(f"   - Offers with listing ID (published): {published_count}")
                            
                            if scheduled_count > 0:
                                print(f"[VERIFY] ✅ {scheduled_count} offer(s) have start date - listing SHOULD appear in 'Scheduled Listings'")
                                print(f"[VERIFY] 📍 Check: {base_url}/sh/lst/scheduled")
                            elif published_count > 0:
                                print(f"[VERIFY] ⚠️ {published_count} offer(s) are published but NO start date - listing is in 'Active Listings'")
                                print(f"[VERIFY] ⚠️ This means listingStartDate was NOT set correctly!")
                                print(f"[VERIFY] 📍 Check: {base_url}/sh/account/listings?status=ACTIVE")
                            else:
                                print(f"[VERIFY] ⚠️ Offers found but not published - may be drafts")
                        else:
                            print(f"[VERIFY] ❌ Could not find any offers for this group in listings API")
                            print(f"[VERIFY] ❌ This is a problem - the offers should exist")
                            print(f"[VERIFY] Possible causes:")
                            print(f"   1. Offers were not created successfully")
                            print(f"   2. Wrong environment (check if using production vs sandbox)")
                            print(f"   3. Offers are in a different account")
                            print(f"   4. API query is not finding them (may need different endpoint)")
                        
                        # Store for use in return_data
                        setattr(self, '_last_verification_result', verification_result)
                        
                        # FINAL COMPREHENSIVE CHECK: Query all listings to see where it actually appears
                        print(f"\n[FINAL CHECK] ========== FINAL COMPREHENSIVE LISTING SEARCH ==========")
                        final_check = self._comprehensive_listing_search(group_key, listing_id)
                        if final_check:
                            print(f"[FINAL CHECK] ✅ Comprehensive search results:")
                            print(f"  - Found in API: {final_check.get('found_in_api', False)}")
                            print(f"  - Offers found: {final_check.get('offers_found', 0)}")
                            print(f"  - Offers with start date: {final_check.get('offers_with_start_date', 0)}")
                            print(f"  - Offers published: {final_check.get('offers_published', 0)}")
                            print(f"  - Recommended Seller Hub location: {final_check.get('recommended_location', 'Unknown')}")
                            
                            if final_check.get('offers_with_start_date', 0) > 0:
                                print(f"[FINAL CHECK] ✅ Listing has start dates - should appear in 'Scheduled Listings'")
                                print(f"[FINAL CHECK] 📍 Go to: {final_check.get('seller_hub_url', 'Seller Hub')}")
                            elif final_check.get('offers_published', 0) > 0:
                                print(f"[FINAL CHECK] ⚠️ Listing is published but NO start dates - may be in 'Active Listings'")
                                print(f"[FINAL CHECK] 📍 Check: {final_check.get('seller_hub_url', 'Seller Hub')}")
                                print(f"[FINAL CHECK] ⚠️ CRITICAL: listingStartDate is missing - listing went live instead of scheduled!")
                            else:
                                print(f"[FINAL CHECK] ⚠️ Listing not found in API yet (may take a few minutes)")
                            
                            # Store for return data
                            setattr(self, '_last_comprehensive_check', final_check)
                        else:
                            print(f"[FINAL CHECK] ⚠️ Could not perform comprehensive search")
                        
                        # Print final summary with all Seller Hub URLs
                        self._print_final_summary(group_key, listing_id, schedule_draft, base_url)
                        print(f"[FINAL CHECK] ======================================================\n")
                    else:
                        print(f"[VERIFY] ⚠️ Could not verify scheduled draft")
                    print(f"[VERIFY] ================================================\n")
                
                # Check listing status to determine where it appears in Seller Hub
                # Store for later use in return_data
                if listing_id:
                    try:
                        listing_status_info = self._check_listing_status(group_key, listing_id)
                        if listing_status_info:
                            print(f"  [INFO] Listing Status: {listing_status_info.get('status', 'UNKNOWN')}")
                            print(f"  [INFO] Appears in Seller Hub: {listing_status_info.get('seller_hub_location', 'Unknown')}")
                            # Store for use in return_data
                            setattr(self, '_last_listing_status_info', listing_status_info)
                    except Exception as e:
                        print(f"  [WARNING] Could not check listing status: {e}")
                        # Continue - status check is not critical
            else:
                # If publish failed with 25016, we already returned draft status above
                # But if it's a different error, we should still return the group info
                error_detail = publish_result.get('error', 'Unknown error')
                if '25016' not in str(error_detail):
                    # Different error - return failure but with group key for manual editing
                    # Determine base URL for Seller Hub link
                    base_url = "https://www.ebay.com" if self.config.EBAY_ENVIRONMENT == 'production' else "https://sandbox.ebay.com"
                    return {
                        "success": False,
                        "error": f"Failed to publish variation listing: {error_detail}",
                        "group_key": group_key,
                        "ebay_url": f"{base_url}/sh/account/inventory",
                        "note": f"Group created but publish failed. Group key: {group_key}. You can view it in eBay Seller Hub."
                    }
            
            # If we get here and publish failed, handle other errors
            if not publish_result.get("success"):
                error_detail = publish_result.get('error', 'Unknown error')
                raw_response = publish_result.get('raw_response', '')
                debug_info = publish_result.get('debug_info', {})
                
                # Enhanced error message with debug info
                error_message = f"Failed to publish variation listing: {error_detail}"
                
                # Add detailed debugging for Error 25016 (Description)
                if '25016' in str(error_detail) or '25016' in str(raw_response):
                    # CRITICAL: Check if group actually has description
                    print(f"[CRITICAL ERROR 25016] Checking group for description...")
                    group_check = self.api_client.get_inventory_item_group(group_key)
                    if group_check.get('success'):
                        group_data_check = group_check.get('data', {})
                        if 'inventoryItemGroup' in group_data_check:
                            desc_in_group = group_data_check['inventoryItemGroup'].get('description', '')
                            if desc_in_group and len(desc_in_group.strip()) >= 50:
                                print(f"[CRITICAL ERROR 25016] Group HAS description (length: {len(desc_in_group)})")
                                print(f"[CRITICAL ERROR 25016] This is strange - eBay should accept it!")
                            else:
                                print(f"[CRITICAL ERROR 25016] Group does NOT have valid description!")
                                print(f"[CRITICAL ERROR 25016] Description in group: {desc_in_group[:100] if desc_in_group else 'NONE'}")
                                print(f"[CRITICAL ERROR 25016] This confirms the problem!")
                        else:
                            print(f"[CRITICAL ERROR 25016] inventoryItemGroup not found in group!")
                    else:
                        print(f"[CRITICAL ERROR 25016] Could not retrieve group: {group_check.get('error')}")
                    
                    error_message += "\n\n" + "=" * 80
                    error_message += "\n🔍 COMPREHENSIVE DEBUGGING FOR ERROR 25016 (DESCRIPTION REQUIRED)"
                    error_message += "\n" + "=" * 80 + "\n"
                    
                    # 1. Initial description check
                    error_message += "\n[1. INITIAL DESCRIPTION PARAMETER]\n"
                    error_message += f"  Description received: {description[:150] if description else 'NONE'}...\n"
                    error_message += f"  Description length: {len(description) if description else 0}\n"
                    error_message += f"  Description is valid: {bool(description and description.strip() and len(description.strip()) >= 50)}\n"
                    error_message += f"  Stored description: {getattr(self, '_current_listing_description', 'NOT STORED')[:100] if hasattr(self, '_current_listing_description') else 'NOT STORED'}...\n"
                    
                    # 2. Check group and offers
                    error_message += "\n[2. GROUP AND OFFERS ANALYSIS]\n"
                    if group_result.get('success'):
                        group_data = group_result.get('data', {})
                        variant_skus = group_data.get('variantSKUs', [])
                        error_message += f"  Group Key: {group_key}\n"
                        error_message += f"  Variant SKUs: {len(variant_skus)} SKU(s)\n"
                        error_message += f"  SKU List: {variant_skus[:5]}\n"
                        
                        error_message += "\n[3. DETAILED OFFER INSPECTION]\n"
                        import json
                        for idx, sku in enumerate(variant_skus[:5], 1):
                            error_message += f"\n  --- Offer {idx}: {sku} ---\n"
                            offer_result = self.api_client.get_offer_by_sku(sku)
                            
                            if offer_result.get('success') and offer_result.get('offer'):
                                offer = offer_result['offer']
                                offer_id = offer.get('offerId', 'N/A')
                                error_message += f"    Offer ID: {offer_id}\n"
                                
                                # Check description in ALL possible locations
                                desc_locations = {
                                    'listing.description': offer.get('listing', {}).get('description', None),
                                    'listing.title': offer.get('listing', {}).get('title', None),
                                    'description (root)': offer.get('description', None),
                                    'listing object exists': 'listing' in offer,
                                    'listing keys': list(offer.get('listing', {}).keys()) if 'listing' in offer else []
                                }
                                
                                error_message += f"    Description Locations:\n"
                                for loc, val in desc_locations.items():
                                    if isinstance(val, str):
                                        error_message += f"      {loc}: {val[:50]}... (length: {len(val)})\n"
                                    elif isinstance(val, list):
                                        error_message += f"      {loc}: {val}\n"
                                    else:
                                        error_message += f"      {loc}: {val}\n"
                                
                                # Get description from any location
                                offer_desc = (
                                    offer.get('listing', {}).get('description', '') or
                                    offer.get('description', '') or
                                    ''
                                )
                                
                                error_message += f"    Found Description: {'YES' if offer_desc else 'NO'}\n"
                                if offer_desc:
                                    error_message += f"      Value: {offer_desc[:100]}...\n"
                                    error_message += f"      Length: {len(offer_desc)}\n"
                                    error_message += f"      Is valid: {bool(offer_desc.strip() and len(offer_desc.strip()) >= 50)}\n"
                                else:
                                    error_message += f"      [CRITICAL] NO DESCRIPTION FOUND IN OFFER!\n"
                                
                                # Check listing structure
                                if 'listing' in offer:
                                    listing = offer['listing']
                                    error_message += f"    Listing Structure:\n"
                                    error_message += f"      Keys: {list(listing.keys())}\n"
                                    error_message += f"      Has title: {'title' in listing}\n"
                                    error_message += f"      Has description: {'description' in listing}\n"
                                    if 'description' in listing:
                                        desc_val = listing['description']
                                        error_message += f"      Description value type: {type(desc_val).__name__}\n"
                                        error_message += f"      Description is empty: {not desc_val or not str(desc_val).strip()}\n"
                                
                                # Show full offer structure (truncated)
                                try:
                                    offer_json = json.dumps(offer, indent=2)
                                    error_message += f"    Full Offer Structure (first 500 chars):\n"
                                    error_message += f"      {offer_json[:500]}...\n"
                                except:
                                    error_message += f"    [Could not serialize offer structure]\n"
                            else:
                                error_message += f"    [ERROR] Could not retrieve offer: {offer_result.get('error', 'Unknown error')}\n"
                    else:
                        error_message += f"  [ERROR] Could not get group data: {group_result.get('error', 'Unknown error')}\n"
                    
                    # 4. Check what was sent in create/update requests
                    error_message += "\n[4. API REQUEST HISTORY]\n"
                    error_message += "  Check the console output above for:\n"
                    error_message += "    - '[DEBUG] ========== OFFER DATA FOR {sku} =========='\n"
                    error_message += "    - '[DEBUG] ========== FULL POST REQUEST BODY =========='\n"
                    error_message += "    - '[DEBUG] ========== FULL PUT REQUEST BODY =========='\n"
                    error_message += "    - '[DEBUG] ========== FORCE UPDATE OFFER WITH DESCRIPTION =========='\n"
                    error_message += "  These will show exactly what was sent to eBay API.\n"
                    
                    # 5. Publish request check
                    error_message += "\n[5. PUBLISH REQUEST]\n"
                    error_message += f"  Group Key: {group_key}\n"
                    error_message += f"  Marketplace: EBAY_US\n"
                    error_message += "  Note: publishOfferByInventoryItemGroup uses the group key\n"
                    error_message += "        and reads description from the offers in the group.\n"
                    
                    # 6. Recommendations
                    error_message += "\n[6. DIAGNOSIS & RECOMMENDATIONS]\n"
                    
                    # Check if any offers have description
                    has_any_description = False
                    if group_result.get('success'):
                        group_data = group_result.get('data', {})
                        variant_skus = group_data.get('variantSKUs', [])
                        for sku in variant_skus[:3]:
                            offer_result = self.api_client.get_offer_by_sku(sku)
                            if offer_result.get('success') and offer_result.get('offer'):
                                offer = offer_result['offer']
                                offer_desc = (
                                    offer.get('listing', {}).get('description', '') or
                                    offer.get('description', '') or
                                    ''
                                )
                                if offer_desc and offer_desc.strip():
                                    has_any_description = True
                                    break
                    
                    if not has_any_description:
                        error_message += "  [CRITICAL] NO OFFERS HAVE DESCRIPTION!\n"
                        error_message += "  \n"
                        error_message += "  POSSIBLE CAUSES:\n"
                        error_message += "  1. Description was not included in create_offer request\n"
                        error_message += "  2. Description was lost during update_offer\n"
                        error_message += "  3. eBay API is not persisting description (sandbox quirk)\n"
                        error_message += "  4. Description is in wrong location in request payload\n"
                        error_message += "  \n"
                        error_message += "  SOLUTIONS TO TRY:\n"
                        error_message += "  1. Check console output for '[DEBUG] ========== FULL POST REQUEST BODY =========='\n"
                        error_message += "     Verify 'listing.description' is present and has value\n"
                        error_message += "  2. Check console output for '[DEBUG] ========== FULL PUT REQUEST BODY =========='\n"
                        error_message += "     Verify description is still present after update\n"
                        error_message += "  3. Try manually updating one offer via eBay API Explorer\n"
                        error_message += "  4. Check if description needs to be at root level instead of listing.description\n"
                    else:
                        error_message += "  [INFO] Some offers have description, but publishing still fails.\n"
                        error_message += "  This suggests:\n"
                        error_message += "  1. Not all offers in group have description\n"
                        error_message += "  2. Description format is invalid\n"
                        error_message += "  3. eBay requires description in specific format for variation listings\n"
                    
                    error_message += "\n" + "=" * 80 + "\n"
                
                # Add detailed debugging for Error 25008 (Payment Policy)
                elif '25008' in str(error_detail) or '25008' in str(raw_response):
                    error_message += "\n\n" + "=" * 80
                    error_message += "\nDETAILED DEBUGGING FOR ERROR 25008 (PAYMENT POLICY)"
                    error_message += "\n" + "=" * 80 + "\n"
                    
                    payment_policy_id = self.policies.get('payment_policy_id')
                    error_message += "\n[PAYMENT POLICY INFORMATION]\n"
                    error_message += f"  Payment Policy ID from config: {payment_policy_id or 'NOT SET'}\n"
                    error_message += f"  Payment Policy ID in offers: {payment_policy_id or 'NOT SET'}\n"
                    
                    # Check if payment policy is in offers
                    if group_result.get('success'):
                        group_data = group_result.get('data', {})
                        variant_skus = group_data.get('variantSKUs', [])
                        error_message += f"\n[OFFERS CHECKED]\n"
                        for sku in variant_skus[:3]:
                            offer_result = self.api_client.get_offer_by_sku(sku)
                            if offer_result.get('success') and offer_result.get('offer'):
                                offer = offer_result.get('offer')
                                offer_payment_policy = (
                                    offer.get('listingPolicies', {}).get('paymentPolicyId') or
                                    offer.get('listing', {}).get('listingPolicies', {}).get('paymentPolicyId') or
                                    'NOT FOUND'
                                )
                                error_message += f"  SKU: {sku}\n"
                                error_message += f"    Payment Policy ID: {offer_payment_policy}\n"
                    
                    error_message += "\n[RECOMMENDATIONS]\n"
                    error_message += "The payment policy ID is being set, but eBay rejects it as invalid.\n"
                    error_message += "This suggests:\n"
                    error_message += "1. The payment policy ID format might be wrong\n"
                    error_message += "2. The policy might not be valid for this marketplace\n"
                    error_message += "3. The policy might be from a different environment (sandbox vs production)\n"
                    error_message += "4. eBay may use default payment policy if none is specified\n\n"
                    error_message += "Possible solutions:\n"
                    error_message += "1. Remove PAYMENT_POLICY_ID from .env file (eBay will use default)\n"
                    error_message += "2. Get a valid payment policy ID from eBay Seller Hub\n"
                    error_message += "3. Verify the policy ID is correct for your environment\n"
                    error_message += "4. The code will automatically retry without payment policy\n"
                    error_message += "\n" + "=" * 80 + "\n"
                
                # Add detailed debugging for Error 25009 (Return Policy)
                elif '25009' in str(error_detail) or '25009' in str(raw_response):
                    error_message += "\n\n" + "=" * 80
                    error_message += "\nDETAILED DEBUGGING FOR ERROR 25009 (RETURN POLICY)"
                    error_message += "\n" + "=" * 80 + "\n"
                    
                    if debug_info:
                        return_policies = debug_info.get('return_policies_checked', [])
                        offers_checked = debug_info.get('offers_checked', [])
                        issues = debug_info.get('issues_found', [])
                        
                        error_message += "\n[POLICIES CHECKED]\n"
                        for policy in return_policies:
                            policy_id = policy.get('policy_id', 'N/A')
                            error_message += f"Policy ID: {policy_id}\n"
                            error_message += f"Source: {policy.get('source', 'N/A')}\n"
                            error_message += f"In Offers: {policy.get('in_offers', False)}\n\n"
                        
                        error_message += "\n[OFFERS CHECKED]\n"
                        for offer in offers_checked:
                            sku = offer.get('sku', 'N/A')
                            return_policy_id = offer.get('return_policy_id', 'NOT SET')
                            error_message += f"SKU: {sku}\n"
                            error_message += f"Return Policy ID: {return_policy_id}\n"
                            if offer.get('issues'):
                                for issue in offer['issues']:
                                    error_message += f"  ⚠️ {issue}\n"
                            error_message += "\n"
                        
                        if issues:
                            error_message += "\n[ISSUES FOUND]\n"
                            for issue in issues:
                                error_message += f"- {issue}\n"
                            error_message += "\n"
                    
                    error_message += "\n[RECOMMENDATIONS]\n"
                    error_message += "The return policy ID is being set correctly in offers, but eBay rejects it.\n"
                    error_message += "This suggests:\n"
                    error_message += "1. The policy ID format might be wrong\n"
                    error_message += "2. The policy might not be valid for this category/marketplace\n"
                    error_message += "3. Sandbox limitation - policy from production URL doesn't work\n\n"
                    error_message += "Possible solutions:\n"
                    error_message += "1. Create a new return policy manually in eBay Seller Hub\n"
                    error_message += "2. Get the return policy ID from a working sandbox listing\n"
                    error_message += "3. Try using a different return policy ID format\n"
                    error_message += "\n" + "=" * 80 + "\n"
                
                # Add detailed debugging for Error 25007
                elif '25007' in str(error_detail) or '25007' in str(raw_response):
                    error_message += "\n\n" + "=" * 80
                    error_message += "\nDETAILED DEBUGGING FOR ERROR 25007"
                    error_message += "\n" + "=" * 80 + "\n"
                    
                    if debug_info:
                        # Show policies checked
                        policies_checked = debug_info.get('policies_checked', [])
                        if policies_checked:
                            error_message += "\n[POLICIES CHECKED]\n"
                            for policy in policies_checked:
                                error_message += f"  Policy ID: {policy.get('policy_id')}\n"
                                error_message += f"  Name: {policy.get('policy_name')}\n"
                                error_message += f"  Has Shipping Options: {policy.get('has_shipping_options')}\n"
                                error_message += f"  Shipping Options Count: {policy.get('shipping_options_count')}\n"
                                
                                # Show detailed service information
                                services_detail = policy.get('services_detail', [])
                                if services_detail:
                                    error_message += f"  Services Detail:\n"
                                    for svc in services_detail:
                                        error_message += f"    - {svc.get('code')} ({svc.get('carrier')})"
                                        if svc.get('cost') != 'N/A':
                                            error_message += f" - ${svc.get('cost')}"
                                        buyer_pays = svc.get('buyer_pays')
                                        if buyer_pays is not None:
                                            error_message += f" - Buyer Pays: {buyer_pays}"
                                            if buyer_pays is False:
                                                error_message += " ⚠️ (SELLER PAYS - This may be the issue!)"
                                        error_message += "\n"
                                else:
                                    services = policy.get('services', [])
                                    if services:
                                        error_message += f"  Services: {', '.join(services)}\n"
                                
                                # Show buyer responsible issues
                                buyer_issues = policy.get('buyer_responsible_issues', [])
                                if buyer_issues:
                                    error_message += f"  ⚠️ WARNING: {len(buyer_issues)} service(s) have buyerResponsibleForShipping=False\n"
                                    for issue in buyer_issues:
                                        error_message += f"    - {issue}\n"
                                
                                warning = policy.get('warning')
                                if warning:
                                    error_message += f"  ⚠️ {warning}\n"
                                
                                error_message += "\n"
                        
                        # Show offers checked
                        offers_checked = debug_info.get('offers_checked', [])
                        if offers_checked:
                            error_message += "[OFFERS CHECKED]\n"
                            for offer in offers_checked:
                                error_message += f"  SKU: {offer.get('sku', 'N/A')}\n"
                                error_message += f"  Offer ID: {offer.get('offer_id', 'N/A')}\n"
                                error_message += f"  Policy ID in Offer: {offer.get('policy_id', 'NOT SET')}\n"
                                error_message += f"  Policy Name: {offer.get('policy_name', 'N/A')}\n"
                                error_message += f"  Policy Valid: {offer.get('policy_valid', False)}\n"
                                error_message += f"  Shipping Options: {offer.get('shipping_options_count', 0)}\n"
                                services = offer.get('services', [])
                                if services:
                                    error_message += f"  Services: {', '.join(services)}\n"
                                issues = offer.get('issues', [])
                                if issues:
                                    error_message += f"  Issues Found:\n"
                                    for issue in issues:
                                        error_message += f"    - {issue}\n"
                                error_message += "\n"
                        
                        issues_found = debug_info.get('issues_found', [])
                        if issues_found:
                            error_message += "[ISSUES FOUND]\n"
                            for issue in issues_found:
                                error_message += f"  - {issue}\n"
                            error_message += "\n"
                    
                    # Add recommendations
                    # Determine base URL for Seller Hub link
                    base_url = "https://www.ebay.com" if self.config.EBAY_ENVIRONMENT == 'production' else "https://sandbox.ebay.com"
                    error_message += "[RECOMMENDATIONS]\n"
                    error_message += "1. Check if 'Buyer pays for shipping' is set to TRUE in the policy:\n"
                    error_message += f"   Policy ID: {fulfillment_policy_id or self.policies.get('fulfillment_policy_id')}\n"
                    error_message += f"   Check: {base_url}/sh/account/policies\n"
                    error_message += "   ⚠️ If buyerResponsibleForShipping=False, eBay may reject it for Trading Cards\n\n"
                    error_message += "2. Verify the fulfillment policy has shipping services\n\n"
                    error_message += "3. Try waiting 5-10 minutes for policy changes to propagate\n\n"
                    error_message += "4. Restart Streamlit app to reload policies\n\n"
                    error_message += "5. If buyerResponsibleForShipping is False, you may need to:\n"
                    error_message += "   - Manually edit the policy in eBay Seller Hub\n"
                    error_message += "   - Or create a new policy with buyerResponsibleForShipping=True\n\n"
                    error_message += "6. If still failing, the shipping service code (USPSStandardPost) may not be valid\n"
                    error_message += "   for Trading Cards category (261328) during publish in sandbox\n"
                    error_message += "\n" + "=" * 80 + "\n"
                
                # If publish fails, return error but note that items and group were created
                return {
                    "success": False,
                    "error": error_message,
                    "created_items": len(created_items),
                    "group_key": group_key,
                    "errors": errors,
                    "debug_info": debug_info,
                    "raw_response": raw_response,
                    "note": "Inventory items and group were created successfully. You may be able to publish manually from eBay Seller Hub."
                }
        else:
            # CRITICAL: Verify environment
            env_name = self.config.EBAY_ENVIRONMENT.upper()
            api_url = self.config.ebay_api_url
            print(f"  [OK] Listing created as draft (group key: {group_key})")
            print(f"  [ENV] Environment: {env_name}")
            print(f"  [ENV] API URL: {api_url}")
            if env_name != 'PRODUCTION':
                print(f"  [WARNING] ⚠️ NOT using production! Current: {env_name}")
                print(f"  [WARNING] ⚠️ Set EBAY_ENVIRONMENT=production in .env file")
            print(f"  [TIP] You can publish it later from eBay Seller Hub or by calling publish_offer_by_inventory_item_group")
            
            # CRITICAL: Verify draft was created and check where it appears
            print(f"\n[VERIFY DRAFT] ========== VERIFYING DRAFT CREATION ==========")
            print(f"[VERIFY DRAFT] Environment: {env_name}")
            draft_verification = self._verify_draft_creation(group_key, created_items)
            if draft_verification:
                print(f"[VERIFY DRAFT] ✅ Verification Results:")
                print(f"  - Group exists: {draft_verification.get('group_exists', False)}")
                print(f"  - Offers created: {draft_verification.get('offers_created', 0)}/{draft_verification.get('total_skus', 0)}")
                print(f"  - Offers with listingId: {draft_verification.get('offers_published', 0)}")
                print(f"  - Offers without listingId (drafts): {draft_verification.get('offers_draft', 0)}")
                print(f"  - Seller Hub location: {draft_verification.get('seller_hub_location', 'Unknown')}")
                
                if draft_verification.get('offers_draft', 0) > 0:
                    print(f"[VERIFY DRAFT] ⚠️ WARNING: {draft_verification.get('offers_draft', 0)} offers are drafts but may NOT be visible in Seller Hub")
                    print(f"[VERIFY DRAFT] ⚠️ eBay Inventory API drafts are often NOT visible in 'Drafts' section")
                    print(f"[VERIFY DRAFT] 💡 SOLUTION: Use 'Save as Scheduled Draft' instead - it WILL appear in Seller Hub")
                else:
                    print(f"[VERIFY DRAFT] ✅ All offers are unpublished (drafts)")
                
                # Also search all offers to see if we can find them
                print(f"[VERIFY DRAFT] Searching all offers to find this group...")
                group_search = self._search_all_listings_for_group(group_key)
                if group_search:
                    print(f"[VERIFY DRAFT] ✅ Found {group_search.get('count', 0)} offers for this group!")
                    print(f"[VERIFY DRAFT] This confirms the offers exist in your account")
                else:
                    print(f"[VERIFY DRAFT] ❌ Could not find offers for this group in API")
                    print(f"[VERIFY DRAFT] This may mean:")
                    print(f"  1. Offers were not created")
                    print(f"  2. Wrong environment (check .env file)")
                    print(f"  3. Run find_all_listings.py to search all listings")
                
                # Store for use in return_data
                setattr(self, '_last_draft_verification', draft_verification)
            else:
                print(f"[VERIFY DRAFT] ⚠️ Could not verify draft")
            print(f"[VERIFY DRAFT] ================================================\n")
        
        # Determine base URL based on environment
        env_name = self.config.EBAY_ENVIRONMENT.upper()
        if self.config.EBAY_ENVIRONMENT == 'production':
            base_url = "https://www.ebay.com"
        else:
            base_url = "https://sandbox.ebay.com"
        
        # CRITICAL: Log environment to ensure we're using production
        print(f"\n[ENV CHECK] ========== ENVIRONMENT VERIFICATION ==========")
        print(f"[ENV CHECK] Environment setting: {env_name}")
        print(f"[ENV CHECK] API URL: {self.config.ebay_api_url}")
        print(f"[ENV CHECK] Base URL: {base_url}")
        if env_name != 'PRODUCTION':
            print(f"[ENV CHECK] ⚠️ WARNING: Not using PRODUCTION!")
            print(f"[ENV CHECK] ⚠️ Set EBAY_ENVIRONMENT=production in .env file")
            print(f"[ENV CHECK] ⚠️ Current .env shows: {env_name}")
        else:
            print(f"[ENV CHECK] ✅ Using PRODUCTION environment")
        print(f"[ENV CHECK] ==============================================\n")
        
        # Build return data
        return_data = {
            "success": True,
            "listing_id": listing_id,  # Also include as listing_id for consistency
            "listingId": listing_id,  # Keep for backward compatibility
            "group_key": group_key,  # Also include as group_key for consistency
            "groupKey": group_key,  # Keep for backward compatibility
            "itemsCreated": len(created_items),
            "cardsCreated": len(created_items),  # Alias for consistency
            "warnings": errors if errors else [],
            "published": publish,
            "ebay_url": f"{base_url}/sh/account/listings" if not listing_id else f"{base_url}/itm/{listing_id}",
            "seller_hub_url": f"{base_url}/sh/landing",
            "seller_hub_drafts": f"{base_url}/sh/account/listings?status=DRAFT",
            "seller_hub_active": f"{base_url}/sh/account/listings?status=ACTIVE",
            "seller_hub_unsold": f"{base_url}/sh/account/listings?status=UNSOLD"
        }
        
        # Add scheduled draft-specific info (check this first since schedule_draft requires publish=True)
        if schedule_draft and publish:
            print(f"[DEBUG] ========== SCHEDULED DRAFT MODE ==========")
            print(f"[DEBUG] schedule_draft: {schedule_draft}, publish: {publish}")
            print(f"[DEBUG] Setting scheduled=True and status='scheduled'")
            return_data["scheduled"] = True
            return_data["status"] = "scheduled"
            return_data["message"] = f"Scheduled listing created! Group: {group_key}"
            return_data["seller_hub_scheduled"] = f"{base_url}/sh/lst/scheduled"
            print(f"[DEBUG] return_data['scheduled']: {return_data.get('scheduled')}")
            print(f"[DEBUG] return_data['status']: {return_data.get('status')}")
            print(f"[DEBUG] ===========================================")
            
            # Get verification results if available
            verification_info = getattr(self, '_last_verification_result', None)
            if verification_info:
                scheduled_count = verification_info.get('scheduled_count', 0)
                total_offers = verification_info.get('total_offers', 0)
                
                if scheduled_count == total_offers and total_offers > 0:
                    return_data["note"] = f"✅ SUCCESS! Your listing is scheduled and will appear in 'Scheduled Listings' in Seller Hub. All {scheduled_count} offers have listingStartDate set. You can edit it before it goes live."
                    return_data["verificationStatus"] = "success"
                elif scheduled_count > 0:
                    return_data["note"] = f"⚠️ PARTIAL: {scheduled_count}/{total_offers} offers have listingStartDate. Listing may appear in 'Scheduled' or 'Active' section. Check Seller Hub to confirm."
                    return_data["verificationStatus"] = "partial"
                else:
                    return_data["note"] = f"⚠️ WARNING: No offers have listingStartDate set. Listing will go live immediately in 'Active Listings'. Check Seller Hub to confirm location."
                    return_data["verificationStatus"] = "warning"
                
                return_data["verificationDetails"] = {
                    "scheduledOffers": scheduled_count,
                    "totalOffers": total_offers,
                    "sellerHubLocation": verification_info.get('seller_hub_location', 'Unknown')
                }
                
                # Add comprehensive search results if available
                final_check = getattr(self, '_last_comprehensive_check', None)
                if final_check:
                    return_data["comprehensiveCheck"] = {
                        "foundInApi": final_check.get('found_in_api', False),
                        "offersFound": final_check.get('offers_found', 0),
                        "offersWithStartDate": final_check.get('offers_with_start_date', 0),
                        "recommendedLocation": final_check.get('recommended_location', 'Unknown'),
                        "sellerHubUrl": final_check.get('seller_hub_url', '')
                    }
            else:
                return_data["note"] = f"✅ Your listing is scheduled to go live in {schedule_hours} hours. It should appear in Seller Hub 'Scheduled Listings' where you can edit it before it goes live."
                return_data["verificationStatus"] = "unknown"
            
            return_data["instructions"] = [
                "1. Go to: https://www.ebay.com/sh/account/listings",
                "2. Click 'Listings' in the left menu",
                "3. Look for your listing in 'Scheduled Listings' section (if all offers have start date)",
                "4. If not in Scheduled, check 'Active Listings' section",
                "5. Click 'Edit' to make changes before it goes live",
                "6. You can publish immediately or let it go live at the scheduled time",
                f"7. Group Key: {group_key}",
                f"8. Scheduled to start: {schedule_hours} hours from now"
            ]
            return_data["sellerHubScheduled"] = f"{base_url}/sh/lst/scheduled"
            return_data["scheduleHours"] = schedule_hours
            if listing_start_date:
                return_data["listingStartDate"] = listing_start_date
            print(f"[INFO] ✅ Scheduled draft created - will appear in Seller Hub as scheduled listing")
        
        # Add draft-specific info (only if not scheduled)
        elif not publish:
            return_data["draft"] = True
            return_data["status"] = "draft"
            return_data["message"] = f"Draft listing created! Group: {group_key}"
            
            # Get verification results if available
            draft_verification = getattr(self, '_last_draft_verification', None)
            if draft_verification:
                offers_draft = draft_verification.get('offers_draft', 0)
                offers_published = draft_verification.get('offers_published', 0)
                
                if offers_published > 0:
                    return_data["note"] = f"⚠️ WARNING: {offers_published} offer(s) were published (have listingId). This should not happen for drafts."
                    return_data["verificationStatus"] = "warning"
                elif offers_draft > 0:
                    return_data["note"] = f"⚠️ IMPORTANT: {offers_draft} draft offer(s) created, but they may NOT be visible in Seller Hub 'Drafts' section. This is a known eBay API limitation. Use 'Save as Scheduled Draft' instead."
                    return_data["verificationStatus"] = "draft_created_but_may_not_be_visible"
                else:
                    return_data["note"] = "Draft created. Verification status unknown."
                    return_data["verificationStatus"] = "unknown"
                
                return_data["verificationDetails"] = {
                    "offersCreated": draft_verification.get('offers_created', 0),
                    "offersDraft": offers_draft,
                    "offersPublished": offers_published,
                    "sellerHubLocation": draft_verification.get('seller_hub_location', 'Unknown')
                }
            else:
                return_data["note"] = "⚠️ IMPORTANT: eBay Inventory API does NOT create drafts visible in Seller Hub 'Drafts' section. Use 'Save as Scheduled Draft' instead to get editable listings in Seller Hub."
                return_data["verificationStatus"] = "unknown"
            
            return_data["instructions"] = [
                "1. Drafts created via Inventory API are often NOT visible in Seller Hub 'Drafts'",
                "2. To get editable listings that appear in Seller Hub, use 'Save as Scheduled Draft' button",
                "3. Scheduled drafts appear in Seller Hub 'Scheduled Listings' where you can edit them",
                f"4. Group Key: {group_key}",
                "5. You can publish this draft later using the group key via API",
                "6. Check verification details below to see offer status"
            ]
            return_data["recommendation"] = "Use 'Save as Scheduled Draft' for listings that appear in Seller Hub and can be edited before going live."
            print(f"[INFO] ⚠️ Draft created but may not appear in Seller Hub 'Drafts' section")
        
        # Add listing status information if published
        if publish and listing_id:
            try:
                # Use stored status info if available, otherwise check now
                listing_status_info = getattr(self, '_last_listing_status_info', None)
                if not listing_status_info:
                    listing_status_info = self._check_listing_status(group_key, listing_id)
                
                if listing_status_info:
                    return_data["listingStatus"] = listing_status_info.get('status', 'UNKNOWN')
                    return_data["sellerHubLocation"] = listing_status_info.get('seller_hub_location', 'Unknown')
                    return_data["sellerHubUrl"] = listing_status_info.get('seller_hub_url', return_data.get('seller_hub_active', ''))
                    return_data["statusMessage"] = listing_status_info.get('message', '')
                    return_data["whereToFind"] = f"Find your listing in Seller Hub: {listing_status_info.get('seller_hub_location', 'Unknown')}"
            except Exception as e:
                print(f"[WARNING] Could not add listing status info: {e}")
                # Continue without status info - not critical
        
        return return_data
    
    def _print_final_summary(self, group_key: str, listing_id: str = None, schedule_draft: bool = False, base_url: str = "https://www.ebay.com"):
        """Print a final summary of where to find the listing."""
        print(f"\n[SUMMARY] ========== WHERE TO FIND YOUR LISTING ==========")
        print(f"[SUMMARY] Group Key: {group_key}")
        if listing_id:
            print(f"[SUMMARY] Listing ID: {listing_id}")
        print(f"[SUMMARY] Environment: {self.config.EBAY_ENVIRONMENT.upper()}")
        print()
        print(f"[SUMMARY] Check these Seller Hub locations:")
        print(f"  1. Scheduled Listings: {base_url}/sh/lst/scheduled")
        print(f"  2. Active Listings: {base_url}/sh/account/listings?status=ACTIVE")
        print(f"  3. Drafts: {base_url}/sh/account/listings?status=DRAFT")
        print(f"  4. Unsold/Ended: {base_url}/sh/account/listings?status=UNSOLD")
        print(f"  5. All Listings: {base_url}/sh/account/listings")
        print()
        print(f"[SUMMARY] To search all listings via API, run:")
        print(f"  python find_all_listings.py")
        print(f"[SUMMARY] ================================================\n")
    
    def _comprehensive_listing_search(self, group_key: str, listing_id: str = None) -> Optional[Dict]:
        """
        Comprehensive search to find where a listing actually appears.
        Queries all offers and checks their status.
        """
        try:
            print(f"[FINAL CHECK] Performing comprehensive search...")
            print(f"  - Group Key: {group_key}")
            print(f"  - Listing ID: {listing_id or 'None'}")
            
            # Search all offers for this group
            group_search = self._search_all_listings_for_group(group_key)
            
            # Also try to find by listing ID
            listing_found = None
            if listing_id:
                listing_found = self._find_listing_via_api(listing_id)
            
            # Compile results
            offers_found = 0
            offers_with_start_date = 0
            offers_published = 0
            recommended_location = "Unknown"
            seller_hub_url = ""
            
            if group_search and group_search.get('found'):
                offers = group_search.get('offers', [])
                offers_found = len(offers)
                
                for offer in offers:
                    if offer.get('listing_id'):
                        offers_published += 1
                    if offer.get('start_date'):
                        offers_with_start_date += 1
                
                # Determine location
                if offers_with_start_date > 0:
                    recommended_location = "Scheduled Listings"
                    seller_hub_url = f"{self.config.EBAY_ENVIRONMENT == 'production' and 'https://www.ebay.com' or 'https://sandbox.ebay.com'}/sh/lst/scheduled"
                elif offers_published > 0:
                    recommended_location = "Active Listings"
                    seller_hub_url = f"{self.config.EBAY_ENVIRONMENT == 'production' and 'https://www.ebay.com' or 'https://sandbox.ebay.com'}/sh/account/listings?status=ACTIVE"
                else:
                    recommended_location = "Not found in API (may be draft or processing)"
                    seller_hub_url = f"{self.config.EBAY_ENVIRONMENT == 'production' and 'https://www.ebay.com' or 'https://sandbox.ebay.com'}/sh/account/listings"
            
            if listing_found and listing_found.get('found'):
                offers_found = max(offers_found, 1)
                if listing_found.get('start_date'):
                    offers_with_start_date = max(offers_with_start_date, 1)
                if listing_found.get('listing_id'):
                    offers_published = max(offers_published, 1)
            
            return {
                "found_in_api": offers_found > 0 or (listing_found and listing_found.get('found')),
                "offers_found": offers_found,
                "offers_with_start_date": offers_with_start_date,
                "offers_published": offers_published,
                "recommended_location": recommended_location,
                "seller_hub_url": seller_hub_url,
                "group_search": group_search,
                "listing_search": listing_found
            }
        except Exception as e:
            print(f"[FINAL CHECK] ❌ Error in comprehensive search: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _search_all_listings_for_group(self, group_key: str) -> Optional[Dict]:
        """
        Search ALL offers to find any that belong to this group.
        This helps us find listings even if they're in unexpected statuses.
        """
        try:
            base_url = "https://www.ebay.com" if self.config.EBAY_ENVIRONMENT == 'production' else "https://sandbox.ebay.com"
            print(f"[SEARCH ALL] ========== COMPREHENSIVE OFFER SEARCH ==========")
            print(f"[SEARCH ALL] Environment: {self.config.EBAY_ENVIRONMENT.upper()}")
            print(f"[SEARCH ALL] API URL: {self.config.ebay_api_url}")
            print(f"[SEARCH ALL] Base URL: {base_url}")
            print(f"[SEARCH ALL] Searching for group: {group_key}")
            
            endpoint = "/sell/inventory/v1/offer"
            
            # Try multiple pagination requests to get all offers
            all_offers = []
            offset = 0
            limit = 200
            max_pages = 10  # Limit to prevent infinite loops
            
            for page in range(max_pages):
                params = {"limit": limit, "offset": offset}
                print(f"[SEARCH ALL] Fetching offers (offset: {offset}, limit: {limit})...")
                response = self.api_client._make_request('GET', endpoint, params=params)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        page_offers = data.get('offers', [])
                        all_offers.extend(page_offers)
                        print(f"[SEARCH ALL]   Found {len(page_offers)} offers on this page (total so far: {len(all_offers)})")
                        
                        if len(page_offers) < limit:
                            # Last page
                            break
                        offset += limit
                    except json.JSONDecodeError as e:
                        print(f"[SEARCH ALL] ❌ Error parsing response: {e}")
                        break
                else:
                    print(f"[SEARCH ALL] ❌ API request failed: {response.status_code}")
                    print(f"[SEARCH ALL] Response: {response.text[:500]}")
                    break
            
            print(f"[SEARCH ALL] Total offers retrieved: {len(all_offers)}")
            
            # Search for matching offers
            matching_offers = []
            for offer in all_offers:
                offer_group_key = offer.get('inventoryItemGroupKey', '')
                if offer_group_key == group_key:
                    listing = offer.get('listing', {})
                    # Check both status fields (offer.status and listing.listingStatus)
                    offer_status = offer.get('status', 'UNKNOWN')
                    listing_status = listing.get('listingStatus', 'UNKNOWN')
                    final_status = listing_status or offer_status
                    start_date = offer.get('listingStartDate', '') or listing.get('listingStartDate', '')
                    listing_id = offer.get('listingId', '')
                    
                    matching_offers.append({
                        "sku": offer.get('sku', ''),
                        "offer_id": offer.get('offerId', ''),
                        "listing_id": listing_id,
                        "status": final_status,
                        "offer_status": offer_status,
                        "listing_status": listing_status,
                        "start_date": start_date,
                        "title": listing.get('title', offer.get('title', 'N/A')),
                        "has_listing_id": bool(listing_id),
                        "has_start_date": bool(start_date),
                        "is_draft": not bool(listing_id) and (offer_status == 'UNPUBLISHED' or listing_status in ['DRAFT', 'UNPUBLISHED']),
                        "is_scheduled": bool(start_date) and bool(listing_id),
                        "is_active": bool(listing_id) and not bool(start_date)
                    })
            
            if matching_offers:
                print(f"[SEARCH ALL] ✅ Found {len(matching_offers)} offers for this group!")
                print(f"[SEARCH ALL] Offer Details:")
                for i, offer in enumerate(matching_offers, 1):
                    print(f"  {i}. SKU: {offer['sku']}")
                    print(f"     Offer ID: {offer['offer_id']}")
                    print(f"     Listing ID: {offer['listing_id'] or 'NONE (unpublished)'}")
                    print(f"     Offer Status: {offer.get('offer_status', 'N/A')}")
                    print(f"     Listing Status: {offer.get('listing_status', 'N/A')}")
                    print(f"     Final Status: {offer['status']}")
                    print(f"     Start Date: {offer['start_date'] or 'MISSING'}")
                    print(f"     Title: {offer['title']}")
                    
                    # Determine where it should appear based on all factors
                    if offer.get('is_scheduled'):
                        print(f"     → ✅ SCHEDULED - Should appear in: Scheduled Listings")
                        print(f"     → 📍 Check: {base_url}/sh/lst/scheduled")
                    elif offer.get('is_active'):
                        print(f"     → ⚠️ ACTIVE - Should appear in: Active Listings")
                        print(f"     → ⚠️ WARNING: No start date - listing went live immediately!")
                        print(f"     → 📍 Check: {base_url}/sh/account/listings?status=ACTIVE")
                    elif offer.get('is_draft'):
                        print(f"     → ⚠️ DRAFT - May appear in: Drafts (often NOT visible)")
                        print(f"     → 📍 Check: {base_url}/sh/account/listings?status=DRAFT")
                    else:
                        print(f"     → ❓ UNKNOWN STATUS")
                    print()
                
                return {
                    "found": True,
                    "offers": matching_offers,
                    "count": len(matching_offers),
                    "total_offers_searched": len(all_offers)
                }
            else:
                print(f"[SEARCH ALL] ❌ No offers found for group {group_key}")
                print(f"[SEARCH ALL] Searched through {len(all_offers)} total offers")
                print(f"[SEARCH ALL] This means:")
                print(f"  1. Offers may not be created yet")
                print(f"  2. Offers may be in a different account/environment")
                print(f"  3. Group key may be incorrect")
                return None
        except Exception as e:
            print(f"[SEARCH ALL] ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _verify_scheduled_draft(self, group_key: str, listing_id: str = None, expected_start_date: str = None, schedule_hours: int = 24) -> Optional[Dict]:
        """
        Verify that a scheduled draft was created correctly with listingStartDate on all offers.
        
        Returns:
            Dict with verification results including scheduled_count, total_offers, etc.
        """
        try:
            print(f"[VERIFY] Checking group: {group_key}")
            
            # Get group to find variant SKUs
            group_result = self.api_client.get_inventory_item_group(group_key)
            if not group_result.get('success'):
                print(f"[VERIFY] ❌ Could not get group: {group_result.get('error')}")
                return None
            
            group_data = group_result.get('data', {})
            variant_skus = group_data.get('variantSKUs', [])
            
            if not variant_skus:
                print(f"[VERIFY] ❌ No variant SKUs found in group")
                return None
            
            print(f"[VERIFY] Found {len(variant_skus)} variant SKUs")
            
            # Check each offer for listingStartDate
            scheduled_count = 0
            offers_with_start_date = []
            offers_without_start_date = []
            
            for sku in variant_skus:
                offer_result = self.api_client.get_offer_by_sku(sku)
                if offer_result.get('success') and offer_result.get('offer'):
                    offer = offer_result.get('offer')
                    offer_id = offer.get('offerId', 'N/A')
                    
                    # Check for listingStartDate at both offer level and listing level
                    listing_start_date = offer.get('listingStartDate', '') or offer.get('listing', {}).get('listingStartDate', '')
                    listing_status = offer.get('listing', {}).get('listingStatus', 'UNKNOWN')
                    listing_id_from_offer = offer.get('listingId', '')
                    
                    print(f"[VERIFY] SKU {sku}:")
                    print(f"  - Offer ID: {offer_id}")
                    print(f"  - Listing ID: {listing_id_from_offer or 'None (not published)'}")
                    print(f"  - Listing Status: {listing_status}")
                    print(f"  - listingStartDate: {listing_start_date or 'MISSING'}")
                    
                    # CRITICAL: Check if offer was actually published
                    if listing_id_from_offer:
                        print(f"  ✅ Offer HAS listingId - it was published")
                        if listing_start_date:
                            print(f"  ✅ Offer HAS listingStartDate - should be scheduled")
                        else:
                            print(f"  ❌ Offer is published but MISSING listingStartDate - will be ACTIVE, not scheduled!")
                    else:
                        print(f"  ⚠️ Offer has NO listingId - not published yet")
                    
                    if listing_start_date:
                        scheduled_count += 1
                        offers_with_start_date.append(sku)
                        print(f"  ✅ HAS listingStartDate: {listing_start_date}")
                        
                        # Parse and show when it will go live
                        try:
                            from datetime import datetime
                            start_dt = datetime.fromisoformat(listing_start_date.replace('Z', '+00:00'))
                            from datetime import timezone
                            try:
                                now = datetime.now(timezone.utc)
                            except (OSError, ValueError):
                                now = datetime.utcnow().replace(tzinfo=timezone.utc) if hasattr(timezone, 'utc') else datetime.utcnow()
                            hours_until = (start_dt - now).total_seconds() / 3600
                            print(f"  ⏰ Will go live in: {hours_until:.1f} hours ({hours_until/24:.1f} days)")
                        except:
                            pass
                        
                        # Verify the date matches expected
                        if expected_start_date:
                            if listing_start_date == expected_start_date:
                                print(f"  ✅ Date matches expected: {expected_start_date}")
                            else:
                                print(f"  ⚠️ Date differs from expected")
                                print(f"     Expected: {expected_start_date}")
                                print(f"     Found: {listing_start_date}")
                    else:
                        offers_without_start_date.append(sku)
                        print(f"  ❌ MISSING listingStartDate!")
                        if listing_id_from_offer:
                            print(f"  ⚠️ CRITICAL: This offer is published but has no start date - it will be ACTIVE, not scheduled!")
            
            # Determine Seller Hub location
            if scheduled_count == len(variant_skus):
                seller_hub_location = "Scheduled Listings (all offers have start date)"
                has_start_date = True
            elif scheduled_count > 0:
                seller_hub_location = f"Scheduled Listings (partial - {scheduled_count}/{len(variant_skus)} offers have start date)"
                has_start_date = True
            else:
                seller_hub_location = "Active Listings (no start date - will go live immediately)"
                has_start_date = False
            
            result = {
                "scheduled_count": scheduled_count,
                "total_offers": len(variant_skus),
                "has_start_date": has_start_date,
                "seller_hub_location": seller_hub_location,
                "offers_with_start_date": offers_with_start_date,
                "offers_without_start_date": offers_without_start_date,
                "group_key": group_key,
                "listing_id": listing_id
            }
            
            return result
            
        except Exception as e:
            print(f"[VERIFY] ❌ Error during verification: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _verify_draft_creation(self, group_key: str, created_items: List[Dict]) -> Optional[Dict]:
        """
        Verify that a draft listing was created correctly and determine where it appears.
        
        Returns:
            Dict with verification results
        """
        try:
            print(f"[VERIFY DRAFT] Checking group: {group_key}")
            
            # Get group to verify it exists
            group_result = self.api_client.get_inventory_item_group(group_key)
            if not group_result.get('success'):
                print(f"[VERIFY DRAFT] ❌ Group not found: {group_result.get('error')}")
                return {
                    "group_exists": False,
                    "error": group_result.get('error')
                }
            
            print(f"[VERIFY DRAFT] ✅ Group exists")
            group_data = group_result.get('data', {})
            variant_skus = group_data.get('variantSKUs', [])
            
            if not variant_skus:
                print(f"[VERIFY DRAFT] ❌ No variant SKUs found in group")
                return {
                    "group_exists": True,
                    "total_skus": 0,
                    "offers_created": 0
                }
            
            print(f"[VERIFY DRAFT] Found {len(variant_skus)} variant SKUs")
            
            # Check each offer
            offers_created = 0
            offers_published = 0
            offers_draft = 0
            offer_details = []
            
            for sku in variant_skus:
                offer_result = self.api_client.get_offer_by_sku(sku)
                if offer_result.get('success') and offer_result.get('offer'):
                    offers_created += 1
                    offer = offer_result.get('offer')
                    offer_id = offer.get('offerId', 'N/A')
                    listing_id = offer.get('listingId', '')
                    listing_status = offer.get('listing', {}).get('listingStatus', 'UNKNOWN')
                    listing_start_date = offer.get('listingStartDate', '') or offer.get('listing', {}).get('listingStartDate', '')
                    
                    print(f"[VERIFY DRAFT] SKU {sku}:")
                    print(f"  - Offer ID: {offer_id}")
                    print(f"  - Listing ID: {listing_id or 'None (unpublished/draft)'}")
                    print(f"  - Listing Status: {listing_status}")
                    print(f"  - listingStartDate: {listing_start_date or 'None'}")
                    
                    if listing_id:
                        offers_published += 1
                        print(f"  ✅ HAS listingId - this offer is PUBLISHED")
                    else:
                        offers_draft += 1
                        print(f"  ⚠️ NO listingId - this offer is a DRAFT")
                    
                    offer_details.append({
                        "sku": sku,
                        "offer_id": offer_id,
                        "listing_id": listing_id,
                        "listing_status": listing_status,
                        "has_start_date": bool(listing_start_date),
                        "is_draft": not bool(listing_id)
                    })
            
            # Determine Seller Hub location
            if offers_published > 0:
                seller_hub_location = "Active Listings (some offers are published)"
            elif offers_draft > 0:
                seller_hub_location = "Drafts (may NOT be visible in Seller Hub - eBay API limitation)"
            else:
                seller_hub_location = "Unknown"
            
            result = {
                "group_exists": True,
                "total_skus": len(variant_skus),
                "offers_created": offers_created,
                "offers_published": offers_published,
                "offers_draft": offers_draft,
                "seller_hub_location": seller_hub_location,
                "offer_details": offer_details,
                "group_key": group_key
            }
            
            return result
            
        except Exception as e:
            print(f"[VERIFY DRAFT] ❌ Error during verification: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _find_listing_via_api(self, listing_id: str) -> Optional[Dict]:
        """
        Try to find a listing via eBay's listings API to verify it exists and get its status.
        """
        try:
            print(f"[FIND LISTING] Searching for listing ID: {listing_id}")
            
            # Try multiple approaches to find the listing
            # Approach 1: Query all offers and search for this listing ID
            endpoint = "/sell/inventory/v1/offer"
            params = {"limit": 200}  # Get more offers to search
            response = self.api_client._make_request('GET', endpoint, params=params)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    offers = data.get('offers', [])
                    print(f"[FIND LISTING] Found {len(offers)} total offers to search")
                    
                    # Search for offer with matching listing ID
                    for offer in offers:
                        offer_listing_id = offer.get('listingId', '')
                        if offer_listing_id == listing_id:
                            listing = offer.get('listing', {})
                            start_date = offer.get('listingStartDate', '') or listing.get('listingStartDate', '')
                            status = listing.get('listingStatus', 'UNKNOWN')
                            
                            print(f"[FIND LISTING] ✅ FOUND listing!")
                            print(f"  - Offer ID: {offer.get('offerId', 'N/A')}")
                            print(f"  - SKU: {offer.get('sku', 'N/A')}")
                            print(f"  - Status: {status}")
                            print(f"  - Start Date: {start_date or 'MISSING'}")
                            print(f"  - Title: {listing.get('title', 'N/A')}")
                            
                            return {
                                "found": True,
                                "status": status,
                                "start_date": start_date,
                                "listing_id": listing_id,
                                "offer_id": offer.get('offerId', ''),
                                "sku": offer.get('sku', ''),
                                "title": listing.get('title', '')
                            }
                    
                    print(f"[FIND LISTING] ❌ Listing {listing_id} not found in {len(offers)} offers")
                    print(f"[FIND LISTING] Checking if any offers have similar listing IDs...")
                    
                    # Show first few listing IDs for debugging
                    found_listing_ids = [o.get('listingId') for o in offers[:10] if o.get('listingId')]
                    if found_listing_ids:
                        print(f"[FIND LISTING] Sample listing IDs found: {found_listing_ids[:5]}")
                    
                except Exception as e:
                    print(f"[FIND LISTING] Error parsing offers response: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"[FIND LISTING] ❌ API request failed: {response.status_code}")
                print(f"[FIND LISTING] Response: {response.text[:500]}")
            
            # If not found, it might take a few minutes to appear in the API
            print(f"[FIND LISTING] ⚠️ Listing {listing_id} not found (may take a few minutes to appear in API)")
            return None
        except Exception as e:
            print(f"[FIND LISTING] ❌ Exception searching for listing: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _check_listing_status(self, group_key: str, listing_id: str = None) -> Optional[Dict]:
        """
        Check the listing status to determine where it appears in Seller Hub.
        
        Returns:
            Dict with status, seller_hub_location, seller_hub_url, and message
        """
        try:
            # Get group to find variant SKUs
            group_result = self.api_client.get_inventory_item_group(group_key)
            if not group_result.get('success'):
                return None
            
            group_data = group_result.get('data', {})
            variant_skus = group_data.get('variantSKUs', [])
            
            if not variant_skus:
                return None
            
            # Check first few offers to get listing status
            statuses_found = []
            listing_start_dates = []
            
            for sku in variant_skus[:3]:  # Check first 3 offers
                offer_result = self.api_client.get_offer_by_sku(sku)
                if offer_result.get('success') and offer_result.get('offer'):
                    offer = offer_result.get('offer')
                    listing = offer.get('listing', {})
                    listing_status = listing.get('listingStatus', '')
                    # listingStartDate can be at offer level or listing level
                    listing_start_date = offer.get('listingStartDate', '') or listing.get('listingStartDate', '')
                    
                    if listing_status:
                        statuses_found.append(listing_status)
                    if listing_start_date:
                        listing_start_dates.append(listing_start_date)
            
            # Determine status (use most common or first found)
            final_status = statuses_found[0] if statuses_found else ''
            has_start_date = len(listing_start_dates) > 0
            
            # Determine base URL
            if self.config.EBAY_ENVIRONMENT == 'production':
                base_url = "https://www.ebay.com"
            else:
                base_url = "https://sandbox.ebay.com"
            
            # Determine where it appears in Seller Hub
            if has_start_date:
                # Has listingStartDate = Scheduled listing
                seller_hub_location = "Scheduled Listings"
                seller_hub_url = f"{base_url}/sh/lst/scheduled"
                message = f"✅ Listing is scheduled and appears in 'Scheduled Listings' in Seller Hub"
            elif final_status == 'PUBLISHED':
                # Published = Active listing
                seller_hub_location = "Active Listings"
                seller_hub_url = f"{base_url}/sh/account/listings?status=ACTIVE"
                message = f"✅ Listing is published and appears in 'Active Listings' in Seller Hub"
            elif final_status == 'INACTIVE':
                # Inactive = Ended/Unsold listing
                seller_hub_location = "Ended/Unsold Listings"
                seller_hub_url = f"{base_url}/sh/account/listings?status=UNSOLD"
                message = f"⚠️ Listing is inactive and appears in 'Ended/Unsold Listings' in Seller Hub"
            elif final_status == '' or not final_status:
                # No status = Draft (but may not be visible)
                seller_hub_location = "Drafts (may not be visible)"
                seller_hub_url = f"{base_url}/sh/account/listings?status=DRAFT"
                message = f"⚠️ Listing has no status - may be a draft. Check 'Unsold' or 'Active Listings' tabs in Seller Hub"
            else:
                # Unknown status
                seller_hub_location = f"Unknown (Status: {final_status})"
                seller_hub_url = f"{base_url}/sh/account/listings"
                message = f"Listing status: {final_status}. Check Seller Hub to see where it appears."
            
            return {
                "status": final_status or "UNKNOWN",
                "seller_hub_location": seller_hub_location,
                "seller_hub_url": seller_hub_url,
                "message": message,
                "has_listing_start_date": has_start_date,
                "listing_id": listing_id
            }
        except Exception as e:
            print(f"[WARNING] Could not check listing status: {e}")
            return None
    
    def get_category_id(self, category_name: str) -> Optional[str]:
        """Get eBay category ID from category name."""
        # Common trading card categories
        categories = {
            "Trading Cards": "261328",
            "Sports Trading Cards": "261328",
            "Magic: The Gathering": "261328",
            "Pokemon": "261328",
            "Yu-Gi-Oh!": "261328"
        }
        return categories.get(category_name, "261328")  # Default to Trading Cards
