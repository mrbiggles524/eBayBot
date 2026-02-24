"""
eBay Listing Manager - Web UI
A simple web interface to manage your eBay listings via API.
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
from ebay_api_client import eBayAPIClient
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)
client = eBayAPIClient()

# Store known listings (in production, use a database)
KNOWN_LISTINGS = [
    {
        "group_key": "GROUPSAHF8A3F381768715399",
        "sku": "CARD_DIFF_APPROACH_TEST_1_0",
        "name": "Different Approach Test"
    },
    {
        "group_key": "GROUPSET1768715280",
        "sku": "CARD_SET_NORMAL_FLOW_TEST_CAR_1_0",
        "name": "Normal Flow Test"
    },
    {
        "group_key": "GROUPSET1768714571",
        "sku": "CARD_SET_FINAL_TEST_CARD_1_0",
        "name": "Final Test Listing"
    },
]


@app.route('/')
def index():
    """Main dashboard."""
    return render_template('index.html')


@app.route('/api/listings')
def get_listings():
    """Get all known listings with their current status."""
    listings = []
    
    for listing in KNOWN_LISTINGS:
        group_key = listing['group_key']
        sku = listing['sku']
        
        # Get group info
        group_result = client.get_inventory_item_group(group_key)
        group_data = group_result.get('data', {}) if group_result.get('success') else {}
        
        # Get offer info
        offer_result = client.get_offer_by_sku(sku)
        offer = offer_result.get('offer', {}) if offer_result.get('success') else {}
        
        listings.append({
            "group_key": group_key,
            "sku": sku,
            "name": listing['name'],
            "title": group_data.get('title', 'N/A'),
            "status": offer.get('listingStatus', 'Unknown'),
            "price": offer.get('pricingSummary', {}).get('price', {}).get('value', 'N/A'),
            "quantity": offer.get('availableQuantity', offer.get('quantity', 'N/A')),
            "offer_id": offer.get('offerId', 'N/A'),
            "exists": group_result.get('success', False)
        })
    
    return jsonify(listings)


@app.route('/api/listing/<group_key>')
def get_listing(group_key):
    """Get detailed listing info."""
    # Find SKU for this group
    sku = None
    for listing in KNOWN_LISTINGS:
        if listing['group_key'] == group_key:
            sku = listing['sku']
            break
    
    if not sku:
        # Try to get from group data
        group_result = client.get_inventory_item_group(group_key)
        if group_result.get('success'):
            skus = group_result.get('data', {}).get('variantSKUs', [])
            if skus:
                sku = skus[0]
    
    # Get group info
    group_result = client.get_inventory_item_group(group_key)
    if not group_result.get('success'):
        return jsonify({"error": "Group not found"}), 404
    
    group_data = group_result.get('data', {})
    
    # Get offer info
    offer = {}
    if sku:
        offer_result = client.get_offer_by_sku(sku)
        if offer_result.get('success'):
            offer = offer_result.get('offer', {})
    
    # Get inventory item info
    item = {}
    if sku:
        item_result = client._make_request('GET', f'/sell/inventory/v1/inventory_item/{sku}')
        if item_result.status_code == 200:
            item = item_result.json()
    
    return jsonify({
        "group_key": group_key,
        "sku": sku,
        "title": group_data.get('title', 'N/A'),
        "variant_skus": group_data.get('variantSKUs', []),
        "varies_by": group_data.get('variesBy', {}),
        "status": offer.get('listingStatus', 'Unknown'),
        "price": offer.get('pricingSummary', {}).get('price', {}).get('value', 'N/A'),
        "quantity": offer.get('availableQuantity', offer.get('quantity', 'N/A')),
        "offer_id": offer.get('offerId', 'N/A'),
        "category_id": offer.get('categoryId', 'N/A'),
        "marketplace": offer.get('marketplaceId', 'N/A'),
        "item_aspects": item.get('product', {}).get('aspects', {}),
        "condition": item.get('condition', 'N/A')
    })


@app.route('/api/listing/<group_key>/update', methods=['POST'])
def update_listing(group_key):
    """Update listing price/quantity."""
    data = request.json
    
    # Find SKU for this group
    sku = None
    for listing in KNOWN_LISTINGS:
        if listing['group_key'] == group_key:
            sku = listing['sku']
            break
    
    if not sku:
        return jsonify({"error": "SKU not found for group"}), 404
    
    # Get current offer
    offer_result = client.get_offer_by_sku(sku)
    if not offer_result.get('success'):
        return jsonify({"error": "Offer not found"}), 404
    
    offer = offer_result['offer']
    offer_id = offer.get('offerId')
    
    # Build update
    new_price = data.get('price')
    new_quantity = data.get('quantity')
    
    update_data = {
        "sku": sku,
        "marketplaceId": offer.get('marketplaceId', 'EBAY_US'),
        "format": offer.get('format', 'FIXED_PRICE'),
        "categoryId": offer.get('categoryId'),
        "pricingSummary": {
            "price": {
                "value": str(new_price) if new_price else offer.get('pricingSummary', {}).get('price', {}).get('value', '1.0'),
                "currency": "USD"
            }
        },
        "quantity": int(new_quantity) if new_quantity else offer.get('availableQuantity', 1),
        "availableQuantity": int(new_quantity) if new_quantity else offer.get('availableQuantity', 1),
        "listingDuration": offer.get('listingDuration', 'GTC'),
        "merchantLocationKey": offer.get('merchantLocationKey')
    }
    
    result = client.update_offer(offer_id, update_data)
    
    if result.get('success'):
        return jsonify({"success": True, "message": "Listing updated"})
    else:
        return jsonify({"error": result.get('error', 'Update failed')}), 400


@app.route('/api/listing/<group_key>/delete', methods=['POST'])
def delete_listing(group_key):
    """Delete a listing."""
    global KNOWN_LISTINGS
    
    # Find SKU for this group
    sku = None
    for listing in KNOWN_LISTINGS:
        if listing['group_key'] == group_key:
            sku = listing['sku']
            break
    
    # Get group to find all SKUs
    group_result = client.get_inventory_item_group(group_key)
    if group_result.get('success'):
        variant_skus = group_result.get('data', {}).get('variantSKUs', [])
        
        # Delete offers first
        for variant_sku in variant_skus:
            offer_result = client.get_offer_by_sku(variant_sku)
            if offer_result.get('success'):
                offer = offer_result['offer']
                offer_id = offer.get('offerId')
                client._make_request('DELETE', f'/sell/inventory/v1/offer/{offer_id}')
    
    # Delete group
    result = client.delete_inventory_item_group(group_key)
    
    if result.get('success'):
        # Remove from known listings
        KNOWN_LISTINGS = [l for l in KNOWN_LISTINGS if l['group_key'] != group_key]
        return jsonify({"success": True, "message": "Listing deleted"})
    else:
        return jsonify({"error": result.get('error', 'Delete failed')}), 400


@app.route('/api/listing/add', methods=['POST'])
def add_listing():
    """Add a listing to track."""
    data = request.json
    group_key = data.get('group_key')
    sku = data.get('sku')
    name = data.get('name', 'New Listing')
    
    if not group_key or not sku:
        return jsonify({"error": "group_key and sku are required"}), 400
    
    # Check if already exists
    for listing in KNOWN_LISTINGS:
        if listing['group_key'] == group_key:
            return jsonify({"error": "Listing already tracked"}), 400
    
    KNOWN_LISTINGS.append({
        "group_key": group_key,
        "sku": sku,
        "name": name
    })
    
    return jsonify({"success": True, "message": "Listing added to tracking"})


@app.route('/api/publish/test', methods=['POST'])
def publish_test_listing():
    """Publish a test variation listing."""
    import uuid
    import time as time_module
    
    unique_id = str(uuid.uuid4())[:8].upper()
    group_key = f"VARGROUP_{unique_id}"
    
    # Create 3 card variations
    cards = [
        {"name": "LeBron James", "number": "1", "sku": f"VAR_{unique_id}_1"},
        {"name": "Stephen Curry", "number": "2", "sku": f"VAR_{unique_id}_2"},
        {"name": "Kevin Durant", "number": "3", "sku": f"VAR_{unique_id}_3"},
    ]
    
    created_skus = []
    variation_values = []
    
    # Step 1: Create inventory items
    for card in cards:
        sku = card['sku']
        card_name = card['name']
        card_number = card['number']
        variation_value = f"{card_number} {card_name}"
        variation_values.append(variation_value)
        
        item_data = {
            "sku": sku,
            "product": {
                "title": f"{card_name} #{card_number} - Test Card",
                "description": f"<p>{card_name} #{card_number} trading card.</p><p>Test listing.</p>",
                "aspects": {
                    "Card Name": [card_name],
                    "Card Number": [card_number],
                    "Sport": ["Basketball"],
                    "Card Manufacturer": ["Topps"],
                    "Season": ["2024-25"],
                    "Features": ["Base"],
                    "Type": ["Sports Trading Card"],
                    "Language": ["English"],
                    "Original/Licensed Reprint": ["Original"],
                    "Pick Your Card": [variation_value]
                },
                "imageUrls": ["https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp"]
            },
            "condition": "USED_VERY_GOOD",
            "conditionDescriptors": [{"name": "40001", "values": ["400010"]}],
            "availability": {"shipToLocationAvailability": {"quantity": 1}},
            "packageWeightAndSize": {
                "dimensions": {"width": 4.0, "length": 6.0, "height": 1.0, "unit": "INCH"},
                "weight": {"value": 0.19, "unit": "POUND"}
            }
        }
        
        item_result = client.create_inventory_item(sku, item_data)
        if item_result.get('success'):
            created_skus.append(sku)
    
    if len(created_skus) < 2:
        return jsonify({"error": "Failed to create inventory items"}), 400
    
    # Step 2: Create group with description at ROOT
    group_data = {
        "title": "Test Variation Listing - Please Delete",
        "description": "<p><strong>Test Variation Listing</strong></p><p>Select your card from the variations below.</p>",
        "variantSKUs": created_skus,
        "variesBy": {"specifications": [{"name": "Pick Your Card", "values": variation_values}]},
        "aspects": {"Sport": ["Basketball"], "Card Manufacturer": ["Topps"], "Season": ["2024-25"], "Type": ["Sports Trading Card"]},
        "imageUrls": ["https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp"]
    }
    
    response = client._make_request('PUT', f'/sell/inventory/v1/inventory_item_group/{group_key}', data=group_data)
    if response.status_code not in [200, 201, 204]:
        return jsonify({"error": f"Failed to create group: {response.text}"}), 400
    
    # Step 3: Get policies
    resp = client._make_request('GET', '/sell/account/v1/payment_policy', params={'marketplace_id': 'EBAY_US'})
    payment_policy_id = resp.json().get('paymentPolicies', [{}])[0].get('paymentPolicyId') if resp.status_code == 200 else None
    
    resp = client._make_request('GET', '/sell/account/v1/fulfillment_policy', params={'marketplace_id': 'EBAY_US'})
    fulfillment_policies = resp.json().get('fulfillmentPolicies', []) if resp.status_code == 200 else []
    fulfillment_policy_id = fulfillment_policies[0].get('fulfillmentPolicyId') if fulfillment_policies else None
    
    resp = client._make_request('GET', '/sell/account/v1/return_policy', params={'marketplace_id': 'EBAY_US'})
    return_policy_id = resp.json().get('returnPolicies', [{}])[0].get('returnPolicyId') if resp.status_code == 200 else None
    
    # Step 4: Create offers
    for sku in created_skus:
        offer_data = {
            "sku": sku,
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "listingPolicies": {"paymentPolicyId": payment_policy_id, "fulfillmentPolicyId": fulfillment_policy_id, "returnPolicyId": return_policy_id},
            "merchantLocationKey": "046afc77-1256-4755-9dae-ab4ebe56c8cc",
            "categoryId": "261328",
            "pricingSummary": {"price": {"value": "1.00", "currency": "USD"}},
            "availableQuantity": 1,
            "listingDuration": "GTC"
        }
        client._make_request('POST', '/sell/inventory/v1/offer', data=offer_data)
    
    time_module.sleep(2)
    
    # Step 5: Publish
    publish_data = {"inventoryItemGroupKey": group_key, "marketplaceId": "EBAY_US"}
    response = client._make_request('POST', '/sell/inventory/v1/offer/publish_by_inventory_item_group', data=publish_data)
    
    if response.status_code in [200, 201]:
        listing_id = response.json().get('listingId')
        # Add to known listings
        KNOWN_LISTINGS.append({
            "group_key": group_key,
            "sku": created_skus[0],
            "name": "Test Variation Listing"
        })
        return jsonify({
            "success": True,
            "listing_id": listing_id,
            "url": f"https://www.ebay.com/itm/{listing_id}",
            "group_key": group_key
        })
    else:
        errors = response.json().get('errors', []) if response.text else []
        return jsonify({"error": errors[0].get('message') if errors else "Publish failed"}), 400


if __name__ == '__main__':
    print("=" * 60)
    print("eBay Listing Manager - Web UI")
    print("=" * 60)
    print()
    print("Starting server...")
    print("Open your browser to: http://localhost:5000")
    print()
    print("Press Ctrl+C to stop the server")
    print()
    app.run(debug=True, port=5000)
