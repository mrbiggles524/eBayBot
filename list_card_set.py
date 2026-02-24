"""
=============================================================================
LIST A COMPLETE CARD SET ON EBAY
=============================================================================

This script creates a variation listing with multiple cards from a set.
Each card becomes a variation option that buyers can select.

USAGE:
    python list_card_set.py

BEFORE RUNNING:
    1. Prepare your card data (see CARD_DATA below)
    2. Have your card images uploaded to eBay (or use URLs)
    3. Set your prices

=============================================================================
"""
from ebay_api_client import eBayAPIClient
import sys
import time
import json
import uuid
import re

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CONFIGURE YOUR CARD SET HERE
# =============================================================================

# Set information
SET_NAME = "2024-25 Topps Chrome Basketball"
SET_DESCRIPTION = """<p><strong>2024-25 Topps Chrome Basketball Cards</strong></p>
<p>If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2024-25 Topps flagship basketball set printed on a chromium stock.</p>
<p>Select your card from the variations below. Each card is listed as a separate variation option.</p>
<p>All cards are in Near Mint or better condition unless otherwise noted.</p>
<p>Fast shipping! Cards ship in penny sleeve + top loader for protection.</p>"""

# Category ID for Trading Cards: Sports Trading Cards
CATEGORY_ID = "261328"

# Default price for all cards (can be overridden per card)
DEFAULT_PRICE = 1.00

# Card data - ADD YOUR CARDS HERE
# Format: {"name": "Player Name", "number": "Card Number", "price": price (optional), "image_url": "URL" (optional)}
CARD_DATA = [
    {"name": "LeBron James", "number": "1", "price": 5.00},
    {"name": "Stephen Curry", "number": "2", "price": 4.00},
    {"name": "Kevin Durant", "number": "3", "price": 3.50},
    {"name": "Giannis Antetokounmpo", "number": "4", "price": 3.00},
    {"name": "Luka Doncic", "number": "5", "price": 4.50},
    # Add more cards here...
]

# Default image URL (replace with your actual card images)
# You should upload images to eBay's image hosting or use external URLs
DEFAULT_IMAGE_URL = "https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp"

# =============================================================================
# END CONFIGURATION
# =============================================================================


def clean_sku(text):
    """Create a clean SKU from text."""
    # Remove special characters, keep alphanumeric and underscores
    clean = re.sub(r'[^a-zA-Z0-9]', '_', text)
    # Remove multiple underscores
    clean = re.sub(r'_+', '_', clean)
    # Truncate to reasonable length
    return clean[:30].upper()


def list_card_set():
    """List a complete card set as a variation listing."""
    client = eBayAPIClient()
    
    print("=" * 80)
    print("LISTING CARD SET ON EBAY")
    print("=" * 80)
    print()
    print(f"Set: {SET_NAME}")
    print(f"Cards: {len(CARD_DATA)}")
    print(f"Default Price: ${DEFAULT_PRICE}")
    print()
    
    if len(CARD_DATA) < 1:
        print("[ERROR] No cards defined! Add cards to CARD_DATA.")
        return
    
    # Generate unique identifiers
    unique_id = str(uuid.uuid4())[:8].upper()
    set_name_clean = clean_sku(SET_NAME)[:15]
    group_key = f"SET_{set_name_clean}_{unique_id}"
    
    print(f"Group Key: {group_key}")
    print()
    
    # Step 1: Get policies first
    print("Step 1: Getting eBay policies...")
    
    resp = client._make_request('GET', '/sell/account/v1/payment_policy', params={'marketplace_id': 'EBAY_US'})
    payment_policy_id = resp.json().get('paymentPolicies', [{}])[0].get('paymentPolicyId') if resp.status_code == 200 else None
    
    resp = client._make_request('GET', '/sell/account/v1/fulfillment_policy', params={'marketplace_id': 'EBAY_US'})
    fulfillment_policies = resp.json().get('fulfillmentPolicies', []) if resp.status_code == 200 else []
    fulfillment_policy_id = None
    # Look for PWE or flat rate shipping policy for cards
    preferred_names = ['PWE', 'FLAT RATE', 'eBay Label', 'Ground Advantage']
    for policy in fulfillment_policies:
        policy_name = policy.get('name', '').upper()
        for pref in preferred_names:
            if pref.upper() in policy_name:
                fulfillment_policy_id = policy.get('fulfillmentPolicyId')
                print(f"  [OK] Using shipping policy: {policy.get('name')}")
                break
        if fulfillment_policy_id:
            break
    if not fulfillment_policy_id and fulfillment_policies:
        fulfillment_policy_id = fulfillment_policies[0].get('fulfillmentPolicyId')
        print(f"  [OK] Using default shipping policy")
    
    resp = client._make_request('GET', '/sell/account/v1/return_policy', params={'marketplace_id': 'EBAY_US'})
    return_policies = resp.json().get('returnPolicies', []) if resp.status_code == 200 else []
    # Find "No Returns Accepted" policy
    return_policy_id = None
    for policy in return_policies:
        if policy.get('returnsAccepted') == False:
            return_policy_id = policy.get('returnPolicyId')
            print(f"  [OK] Using 'No Returns' policy: {policy.get('name')}")
            break
    if not return_policy_id and return_policies:
        return_policy_id = return_policies[0].get('returnPolicyId')
    
    if not all([payment_policy_id, fulfillment_policy_id, return_policy_id]):
        print("[ERROR] Missing required policies. Set up policies in eBay Seller Hub first.")
        return
    
    print(f"  Payment Policy: {payment_policy_id}")
    print(f"  Fulfillment Policy: {fulfillment_policy_id}")
    print(f"  Return Policy: {return_policy_id}")
    print()
    
    # Step 2: Create inventory items for each card
    print("Step 2: Creating inventory items...")
    
    created_skus = []
    variation_values = []
    card_prices = {}
    
    for i, card in enumerate(CARD_DATA):
        card_name = card.get('name', f'Card {i+1}')
        card_number = str(card.get('number', i+1))
        card_price = card.get('price', DEFAULT_PRICE)
        image_url = card.get('image_url', DEFAULT_IMAGE_URL)
        
        # Create SKU
        sku = f"{set_name_clean}_{clean_sku(card_name)}_{card_number}_{unique_id}"
        
        # Create variation value (what buyers see in dropdown)
        variation_value = f"{card_number} {card_name}"
        variation_values.append(variation_value)
        
        # Store price for offer creation
        card_prices[sku] = card_price
        
        # Create inventory item
        item_data = {
            "sku": sku,
            "product": {
                "title": f"{card_name} #{card_number} - {SET_NAME}",
                "description": f"<p>{card_name} #{card_number} from {SET_NAME}</p>",
                "aspects": {
                    "Card Name": [card_name],
                    "Card Number": [card_number],
                    "Sport": ["Basketball"],
                    "Card Manufacturer": ["Topps"],
                    "Season": ["2024-25"],
                    "Features": ["Base", "Chrome"],
                    "Type": ["Sports Trading Card"],
                    "Language": ["English"],
                    "Original/Licensed Reprint": ["Original"],
                    "Pick Your Card": [variation_value]
                },
                "imageUrls": [image_url]
            },
            "condition": "USED_VERY_GOOD",
            "conditionDescriptors": [{"name": "40001", "values": ["400010"]}],
            "availability": {"shipToLocationAvailability": {"quantity": 1}},
            "packageWeightAndSize": {
                "dimensions": {"width": 4.0, "length": 6.0, "height": 1.0, "unit": "INCH"},
                "weight": {"value": 0.19, "unit": "POUND"}
            }
        }
        
        result = client.create_inventory_item(sku, item_data)
        if result.get('success'):
            created_skus.append(sku)
            print(f"  [OK] {card_number}. {card_name} - ${card_price}")
        else:
            print(f"  [ERROR] {card_number}. {card_name} - {result.get('error')}")
    
    if len(created_skus) < 1:
        print("[ERROR] Failed to create any inventory items!")
        return
    
    print()
    print(f"Created {len(created_skus)} inventory items")
    print()
    
    # Step 3: Create inventory item group
    print("Step 3: Creating inventory item group...")
    
    # Truncate title to 80 chars
    group_title = SET_NAME[:80] if len(SET_NAME) <= 80 else SET_NAME[:77] + "..."
    
    group_data = {
        "title": group_title,
        "description": SET_DESCRIPTION,
        "variantSKUs": created_skus,
        "variesBy": {
            "specifications": [{
                "name": "Pick Your Card",
                "values": variation_values
            }]
        },
        "aspects": {
            "Sport": ["Basketball"],
            "Card Manufacturer": ["Topps"],
            "Season": ["2024-25"],
            "Type": ["Sports Trading Card"]
        },
        "imageUrls": [DEFAULT_IMAGE_URL]
    }
    
    response = client._make_request(
        'PUT',
        f'/sell/inventory/v1/inventory_item_group/{group_key}',
        data=group_data
    )
    
    if response.status_code in [200, 201, 204]:
        print(f"  [OK] Group created: {group_key}")
    else:
        print(f"  [ERROR] Group creation failed: {response.status_code}")
        print(f"  {response.text}")
        return
    print()
    
    # Step 4: Create offers for each SKU
    print("Step 4: Creating offers...")
    
    offer_ids = []
    for sku in created_skus:
        price = card_prices.get(sku, DEFAULT_PRICE)
        
        offer_data = {
            "sku": sku,
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "listingPolicies": {
                "paymentPolicyId": payment_policy_id,
                "fulfillmentPolicyId": fulfillment_policy_id,
                "returnPolicyId": return_policy_id
            },
            "merchantLocationKey": "046afc77-1256-4755-9dae-ab4ebe56c8cc",
            "categoryId": CATEGORY_ID,
            "pricingSummary": {
                "price": {
                    "value": str(price),
                    "currency": "USD"
                }
            },
            "availableQuantity": 1,
            "listingDuration": "GTC"
        }
        
        response = client._make_request('POST', '/sell/inventory/v1/offer', data=offer_data)
        
        if response.status_code in [200, 201]:
            offer_id = response.json().get('offerId')
            offer_ids.append(offer_id)
            print(f"  [OK] Offer created for {sku}")
        else:
            print(f"  [ERROR] Offer failed for {sku}: {response.text}")
    
    if len(offer_ids) < 1:
        print("[ERROR] Failed to create any offers!")
        return
    
    print()
    print(f"Created {len(offer_ids)} offers")
    print()
    
    # Step 5: Publish
    print("Step 5: Publishing listing...")
    print()
    print("=" * 80)
    print("[WARNING] This will make the listing LIVE on eBay!")
    print("=" * 80)
    print()
    
    confirm = input("Type 'YES' to publish, or anything else to cancel: ")
    if confirm.strip().upper() != 'YES':
        print()
        print("[CANCELLED] Listing not published.")
        print(f"Group Key: {group_key}")
        print("You can publish later using the group key.")
        return
    
    print()
    print("Publishing...")
    
    time.sleep(2)  # Brief pause for data propagation
    
    publish_data = {
        "inventoryItemGroupKey": group_key,
        "marketplaceId": "EBAY_US"
    }
    
    response = client._make_request(
        'POST',
        '/sell/inventory/v1/offer/publish_by_inventory_item_group',
        data=publish_data
    )
    
    if response.status_code in [200, 201]:
        result = response.json()
        listing_id = result.get('listingId')
        
        print()
        print("=" * 80)
        print("[SUCCESS] LISTING PUBLISHED!")
        print("=" * 80)
        print()
        print(f"Listing ID: {listing_id}")
        print(f"View: https://www.ebay.com/itm/{listing_id}")
        print()
        print(f"Cards listed: {len(created_skus)}")
        print(f"Group Key: {group_key}")
        print()
        print("Check Seller Hub -> Listings -> Active")
        print()
        
        return {
            "success": True,
            "listing_id": listing_id,
            "group_key": group_key,
            "cards": len(created_skus)
        }
    else:
        errors = response.json().get('errors', []) if response.text else []
        
        print()
        print("=" * 80)
        print("[ERROR] Publish Failed")
        print("=" * 80)
        print()
        
        for error in errors:
            print(f"Error {error.get('errorId')}: {error.get('message')}")
        
        print()
        print(f"Group Key: {group_key}")
        print("The listing was created but not published.")
        print("Fix the errors and try publishing again.")
        
        return {"success": False, "group_key": group_key, "errors": errors}


if __name__ == "__main__":
    print()
    print("=" * 80)
    print("EBAY CARD SET LISTING TOOL")
    print("=" * 80)
    print()
    print("This will create a variation listing with the following cards:")
    print()
    for i, card in enumerate(CARD_DATA):
        price = card.get('price', DEFAULT_PRICE)
        print(f"  {card.get('number', i+1)}. {card.get('name')} - ${price:.2f}")
    print()
    print(f"Total cards: {len(CARD_DATA)}")
    print()
    
    proceed = input("Press Enter to continue, or Ctrl+C to cancel...")
    print()
    
    list_card_set()
