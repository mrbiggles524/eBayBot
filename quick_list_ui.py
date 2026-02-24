"""
Quick List UI - Web interface for listing card sets on eBay
"""
from flask import Flask, render_template, request, jsonify
from ebay_api_client import eBayAPIClient
from card_checklist import CardChecklistFetcher
import sys
import time
import uuid
import re
import json

sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)
client = eBayAPIClient()
checklist_fetcher = CardChecklistFetcher(source='beckett')

# Store listing history
LISTING_HISTORY = []

def clean_text(text):
    clean = re.sub(r'[^a-zA-Z0-9]', '_', str(text))
    return re.sub(r'_+', '_', clean)[:25].upper()

@app.route('/')
def index():
    return render_template('quick_list.html')

@app.route('/api/policies')
def get_policies():
    """Get available policies."""
    policies = {"payment": [], "shipping": [], "returns": []}
    
    # Payment
    resp = client._make_request('GET', '/sell/account/v1/payment_policy', params={'marketplace_id': 'EBAY_US'})
    if resp.status_code == 200:
        policies['payment'] = [{"id": p.get('paymentPolicyId'), "name": p.get('name')} 
                               for p in resp.json().get('paymentPolicies', [])]
    
    # Shipping
    resp = client._make_request('GET', '/sell/account/v1/fulfillment_policy', params={'marketplace_id': 'EBAY_US'})
    if resp.status_code == 200:
        policies['shipping'] = [{"id": p.get('fulfillmentPolicyId'), "name": p.get('name')} 
                                for p in resp.json().get('fulfillmentPolicies', [])]
    
    # Returns
    resp = client._make_request('GET', '/sell/account/v1/return_policy', params={'marketplace_id': 'EBAY_US'})
    if resp.status_code == 200:
        policies['returns'] = [{"id": p.get('returnPolicyId'), "name": p.get('name'), "accepted": p.get('returnsAccepted')} 
                               for p in resp.json().get('returnPolicies', [])]
    
    return jsonify(policies)

@app.route('/api/list', methods=['POST'])
def create_listing():
    """Create and publish a listing."""
    data = request.json
    
    set_name = data.get('setName', 'Card Set')
    description = data.get('description', '')
    cards = data.get('cards', [])
    image_url = data.get('imageUrl', 'https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp')
    payment_id = data.get('paymentPolicyId')
    shipping_id = data.get('shippingPolicyId')
    return_id = data.get('returnPolicyId')
    publish = data.get('publish', False)
    
    if not cards:
        return jsonify({"error": "No cards provided"}), 400
    
    # Generate IDs
    uid = str(uuid.uuid4())[:6].upper()
    set_clean = clean_text(set_name)[:10]
    group_key = f"SET_{set_clean}_{uid}"
    
    results = {
        "groupKey": group_key,
        "setName": set_name,
        "cardsCreated": 0,
        "errors": [],
        "status": "creating"
    }
    
    # Create inventory items
    skus = []
    variations = []
    prices = {}
    
    for card in cards:
        num = str(card.get('number', ''))
        name = card.get('name', '')
        price = float(card.get('price', 1.00))
        card_image = card.get('imageUrl', image_url)
        
        sku = f"{set_clean}_{clean_text(name)}_{num}_{uid}"
        var_value = f"{num} {name}"
        variations.append(var_value)
        prices[sku] = price
        
        item = {
            "sku": sku,
            "product": {
                "title": f"{name} #{num} - {set_name}"[:80],
                "description": f"<p>{name} #{num}</p>",
                "aspects": {
                    "Card Name": [name],
                    "Card Number": [str(num)],
                    "Sport": ["Basketball"],
                    "Card Manufacturer": ["Topps"],
                    "Season": ["2024-25"],
                    "Features": ["Base", "Chrome"],
                    "Type": ["Sports Trading Card"],
                    "Language": ["English"],
                    "Original/Licensed Reprint": ["Original"],
                    "Pick Your Card": [var_value]
                },
                "imageUrls": [card_image]
            },
            "condition": "USED_VERY_GOOD",
            "conditionDescriptors": [{"name": "40001", "values": ["400010"]}],
            "availability": {"shipToLocationAvailability": {"quantity": int(card.get('quantity', 1))}},
            "packageWeightAndSize": {
                "dimensions": {"width": 4.0, "length": 6.0, "height": 1.0, "unit": "INCH"},
                "weight": {"value": 0.19, "unit": "POUND"}
            }
        }
        
        result = client.create_inventory_item(sku, item)
        if result.get('success'):
            skus.append(sku)
            results["cardsCreated"] += 1
        else:
            results["errors"].append(f"#{num} {name}: {result.get('error', 'Unknown error')[:50]}")
    
    if not skus:
        results["status"] = "failed"
        results["error"] = "Failed to create any inventory items"
        return jsonify(results), 400
    
    # Create group
    if not description:
        description = f"""<p><strong>{set_name}</strong></p>
<p>Select your card from the dropdown menu.</p>
<p>All cards are in Near Mint or better condition.</p>
<p>Ships in penny sleeve + top loader via PWE with eBay tracking.</p>"""
    
    group = {
        "title": set_name[:80],
        "description": description,
        "variantSKUs": skus,
        "variesBy": {"specifications": [{"name": "Pick Your Card", "values": variations}]},
        "aspects": {"Sport": ["Basketball"], "Card Manufacturer": ["Topps"], "Season": ["2024-25"], "Type": ["Sports Trading Card"]},
        "imageUrls": [image_url]
    }
    
    resp = client._make_request('PUT', f'/sell/inventory/v1/inventory_item_group/{group_key}', data=group)
    if resp.status_code not in [200, 201, 204]:
        results["status"] = "failed"
        results["error"] = f"Failed to create group: {resp.text[:100]}"
        return jsonify(results), 400
    
    # Create offers
    for sku in skus:
        offer = {
            "sku": sku,
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "listingPolicies": {
                "paymentPolicyId": payment_id,
                "fulfillmentPolicyId": shipping_id,
                "returnPolicyId": return_id
            },
            "merchantLocationKey": "046afc77-1256-4755-9dae-ab4ebe56c8cc",
            "categoryId": "261328",
            "pricingSummary": {"price": {"value": str(prices[sku]), "currency": "USD"}},
            "availableQuantity": 1,
            "listingDuration": "GTC"
        }
        client._make_request('POST', '/sell/inventory/v1/offer', data=offer)
    
    results["offersCreated"] = len(skus)
    results["status"] = "ready"
    
    # Publish if requested
    if publish:
        time.sleep(2)
        resp = client._make_request('POST', '/sell/inventory/v1/offer/publish_by_inventory_item_group',
                                    data={"inventoryItemGroupKey": group_key, "marketplaceId": "EBAY_US"})
        
        if resp.status_code in [200, 201]:
            listing_id = resp.json().get('listingId')
            results["status"] = "published"
            results["listingId"] = listing_id
            results["listingUrl"] = f"https://www.ebay.com/itm/{listing_id}"
            
            # Save to history
            LISTING_HISTORY.append({
                "groupKey": group_key,
                "setName": set_name,
                "listingId": listing_id,
                "cards": len(skus),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            errors = resp.json().get('errors', []) if resp.text else []
            results["status"] = "publish_failed"
            results["publishError"] = errors[0].get('message') if errors else "Unknown error"
    
    return jsonify(results)

@app.route('/api/history')
def get_history():
    """Get listing history."""
    return jsonify(LISTING_HISTORY)

@app.route('/api/fetch-checklist', methods=['POST'])
def fetch_checklist():
    """Fetch checklist from Beckett or Cardsmiths URL."""
    data = request.json
    url = data.get('url', '')
    checklist_type = data.get('type', 'base')
    default_price = float(data.get('defaultPrice', 1.00))
    default_qty = int(data.get('defaultQty', 1))
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    try:
        print(f"[FETCH] ========================================")
        print(f"[FETCH] API ENDPOINT CALLED")
        print(f"[FETCH] URL: {url}")
        print(f"[FETCH] Type: {checklist_type}")
        print(f"[FETCH] ========================================")
        
        print(f"[FETCH] Calling checklist_fetcher.fetch_from_beckett_url...")
        result = checklist_fetcher.fetch_from_beckett_url(url, checklist_type=checklist_type)
        print(f"[FETCH] Fetcher returned result type: {type(result)}")
        print(f"[FETCH] Result is tuple: {isinstance(result, tuple)}")
        
        # Handle tuple return (cards, description)
        if isinstance(result, tuple):
            cards, description = result
            print(f"[FETCH] ========================================")
            print(f"[FETCH] STEP 1: Unpacked tuple")
            print(f"[FETCH] Cards: {len(cards) if cards else 0}")
            print(f"[FETCH] Description: {len(description) if description else 0} chars")
            print(f"[FETCH] ========================================")
        else:
            cards = result
            description = None
            print(f"[FETCH] ========================================")
            print(f"[FETCH] STEP 1: Result is NOT tuple - using as cards directly")
            print(f"[FETCH] Cards type: {type(cards)}, length: {len(cards) if cards else 0}")
            print(f"[FETCH] ========================================")
        
        print(f"[FETCH] ========================================")
        print(f"[FETCH] STEP 2: After unpacking")
        print(f"[FETCH] Cards count: {len(cards) if cards else 0}")
        print(f"[FETCH] Checklist type: '{checklist_type}'")
        if cards and len(cards) > 0:
            print(f"[FETCH] First card: {cards[0]}")
            if len(cards) > 1:
                print(f"[FETCH] Last card: {cards[-1]}")
        print(f"[FETCH] ========================================")
        
        # ABSOLUTE HARD STOP: If base cards and count > 300, REJECT IMMEDIATELY
        # THIS CHECK CANNOT BE BYPASSED - IT RETURNS IMMEDIATELY
        if checklist_type == 'base':
            if not cards:
                print(f"[FETCH] No cards returned for base type")
            else:
                card_count = len(cards)
                print(f"[FETCH] ========================================")
                print(f"[FETCH] STEP 3: Checking card count")
                print(f"[FETCH] Card count: {card_count}")
                print(f"[FETCH] ========================================")
                if card_count > 300:
                    print(f"[FETCH] ========================================")
                    print(f"[FETCH] HARD STOP TRIGGERED!")
                    print(f"[FETCH] Got {card_count} cards for base type!")
                    print(f"[FETCH] THIS IS IMPOSSIBLE - REJECTING IMMEDIATELY")
                    print(f"[FETCH] Returning EMPTY cards array")
                    print(f"[FETCH] ========================================")
                    # Return empty result - this cannot be bypassed
                    return jsonify({
                        "success": False,
                        "cards": [],
                        "count": 0,
                        "setName": "",
                        "source": "beckett",
                        "error": f"Parser returned {card_count} cards (max 300). Cards cleared.",
                        "version": "2.5",
                        "timestamp": __import__('datetime').datetime.now().isoformat()
                    })
                else:
                    print(f"[FETCH] Card count OK: {card_count} (max 300)")
        
        # CRITICAL: If base cards and count > 300, REJECT IMMEDIATELY (DUPLICATE CHECK)
        if checklist_type == 'base':
            if len(cards) > 300:
                print(f"[FETCH] ========================================")
                print(f"[FETCH] FATAL ERROR: Got {len(cards)} cards but base set should be max 300!")
                print(f"[FETCH] REJECTING ALL CARDS - returning error")
                print(f"[FETCH] ========================================")
                return jsonify({
                    "error": f"Parser error: Got {len(cards)} cards but base set should be max 300. This indicates inserts were included.",
                    "success": False,
                    "cards": [],
                    "count": 0,
                    "version": "2.5",
                    "timestamp": __import__('datetime').datetime.now().isoformat(),
                    "server_version": "2.4"
                }), 500
            
            # Check for prefixed cards (inserts)
            prefixed = [c for c in cards if '-' in str(c.get('number', ''))]
            if prefixed:
                print(f"[FETCH] ERROR: Found {len(prefixed)} cards with prefixes!")
                print(f"[FETCH] First few prefixed cards:")
                for c in prefixed[:5]:
                    print(f"[FETCH]   {c.get('number')} {c.get('name')}")
                return jsonify({
                    "error": "Parser error: Base cards should not contain insert cards.",
                    "success": False,
                    "cards": [],
                    "count": 0,
                    "version": "2.5",
                    "timestamp": __import__('datetime').datetime.now().isoformat(),
                    "server_version": "2.4"
                }), 500
            
            print(f"[FETCH] Validation passed: {len(cards)} base cards")
        
        if not cards:
            return jsonify({
                "error": "No cards found. Check the URL and try again.",
                "success": False,
                "cards": [],
                "count": 0,
                "version": "2.5",
                "timestamp": __import__('datetime').datetime.now().isoformat(),
                "server_version": "2.4"
            }), 404
        
        # Format cards for the UI
        formatted_cards = []
        for card in cards:
            formatted_cards.append({
                "number": str(card.get('number', '')),
                "name": card.get('name', ''),
                "team": card.get('team', ''),
                "price": default_price,
                "quantity": default_qty,
                "imageUrl": card.get('image_url', '')
            })
        
        # FINAL CHECK: After formatting, if base cards and count > 300, REJECT
        if checklist_type == 'base' and len(formatted_cards) > 300:
            print(f"[FETCH] ========================================")
            print(f"[FETCH] FINAL CHECK FAILED: {len(formatted_cards)} cards after formatting!")
            print(f"[FETCH] REJECTING - returning error")
            print(f"[FETCH] ========================================")
            return jsonify({
                "error": f"Parser error: Got {len(formatted_cards)} cards but base set should be max 300.",
                "success": False,
                "cards": [],
                "count": 0,
                "version": "2.5",
                "timestamp": __import__('datetime').datetime.now().isoformat(),
                "server_version": "2.4"
            }), 500
        
        # Try to extract set name from URL
        set_name = ""
        if 'cardsmithsbreaks.com' in url:
            # Extract from URL like: /full-checklist/2025-26-topps-chrome-basketball-hobby/
            match = re.search(r'/full-checklist/([^/]+)/?', url)
            if match:
                set_name = match.group(1).replace('-', ' ').replace('hobby', '').strip().title()
        elif 'beckett.com' in url:
            # Extract from URL like: /news/2025-26-topps-chrome-basketball-cards/
            match = re.search(r'/news/([^/]+)/?', url)
            if match:
                set_name = match.group(1).replace('-', ' ').replace('cards', '').strip().title()
        
        # ONE MORE FINAL CHECK before returning response
        if checklist_type == 'base' and len(formatted_cards) > 300:
            print(f"[FETCH] ========================================")
            print(f"[FETCH] LAST CHECK FAILED!")
            print(f"[FETCH] {len(formatted_cards)} cards - FORCING 0")
            print(f"[FETCH] ========================================")
            formatted_cards = []
            formatted_count = 0
        
        print(f"[FETCH] ========================================")
        print(f"[FETCH] STEP 6: Building response")
        print(f"[FETCH] Formatted count: {len(formatted_cards)}")
        print(f"[FETCH] Checklist type: {checklist_type}")
        print(f"[FETCH] ========================================")
        
        response_data = {
            "success": True,
            "cards": formatted_cards,
            "count": len(formatted_cards),
            "setName": set_name,
            "source": "beckett" if 'beckett.com' in url else ("cardsmiths" if 'cardsmithsbreaks.com' in url else "universal"),
            "checklistType": checklist_type
        }
        
        # ABSOLUTE FINAL CHECK: Never return more than 300 cards for base type
        if checklist_type == 'base' and response_data['count'] > 300:
            print(f"[FETCH] ========================================")
            print(f"[FETCH] ABSOLUTE FINAL CHECK FAILED!")
            print(f"[FETCH] Response data has {response_data['count']} cards - FORCING 0")
            print(f"[FETCH] ========================================")
            response_data['cards'] = []
            response_data['count'] = 0
            response_data['error'] = f"Parser returned {len(formatted_cards)} cards (max 300). Cards cleared."
            response_data['success'] = False
        
        # CRITICAL: Set version/timestamp IMMEDIATELY - cannot be missing
        response_data['version'] = '2.5'
        response_data['timestamp'] = __import__('datetime').datetime.now().isoformat()
        response_data['server_version'] = '2.5'
        
        # Validate version is set
        if not response_data.get('version'):
            print(f"[FETCH] ERROR: Version not set! Forcing to 2.4")
            response_data['version'] = '2.5'
        
        print(f"[FETCH] ========================================")
        print(f"[FETCH] FINAL RESPONSE:")
        print(f"[FETCH] Success: {response_data['success']}")
        print(f"[FETCH] Count: {response_data['count']}")
        print(f"[FETCH] Source: {response_data['source']}")
        print(f"[FETCH] Version: {response_data['version']}")
        if len(formatted_cards) > 0:
            print(f"[FETCH] First formatted card: {formatted_cards[0]}")
            if len(formatted_cards) > 1:
                print(f"[FETCH] Last formatted card: {formatted_cards[-1]}")
        print(f"[FETCH] ========================================")
        
        # Include description if available
        if description:
            response_data["description"] = description
        
        # FINAL FINAL CHECK: Make absolutely sure version is set
        if 'version' not in response_data or not response_data['version']:
            response_data['version'] = '2.5'
        if 'timestamp' not in response_data or not response_data['timestamp']:
            response_data['timestamp'] = __import__('datetime').datetime.now().isoformat()
        if 'server_version' not in response_data or not response_data['server_version']:
            response_data['server_version'] = '2.5'
        
        print(f"[FETCH] ========================================")
        print(f"[FETCH] ABOUT TO RETURN JSON RESPONSE")
        print(f"[FETCH] Version in response: {response_data.get('version')}")
        print(f"[FETCH] Count in response: {response_data.get('count')}")
        print(f"[FETCH] Success in response: {response_data.get('success')}")
        print(f"[FETCH] ========================================")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"[FETCH] ========================================")
        print(f"[FETCH] EXCEPTION CAUGHT!")
        print(f"[FETCH] Error type: {type(e).__name__}")
        print(f"[FETCH] Error message: {str(e)}")
        print(f"[FETCH] ========================================")
        import traceback
        traceback.print_exc()
        print(f"[FETCH] ========================================")
        return jsonify({
            "error": str(e),
            "error_type": type(e).__name__,
            "success": False,
            "cards": [],
            "count": 0,
            "version": "2.5",
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "server_version": "2.4"
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("Quick List UI - eBay Card Listing Tool")
    print("=" * 60)
    print()
    print("Open your browser to: http://localhost:5001")
    print()
    app.run(debug=True, port=5001)
