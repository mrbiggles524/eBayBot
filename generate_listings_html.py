"""
Generate an HTML file showing all your sandbox listings.
This bypasses the sandbox UI issues.
"""
import sys
import os
from ebay_api_client import eBayAPIClient
from config import Config
import json
from datetime import datetime

def generate_html():
    """Generate HTML file with all listings."""
    print("=" * 80)
    print("Generating HTML View of Your Listings")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print("Fetching listings...")
    print()
    
    # Get inventory items
    items_response = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 100})
    
    if items_response.status_code != 200:
        print(f"[ERROR] Failed to fetch inventory items: {items_response.status_code}")
        return
    
    items_data = items_response.json()
    inventory_items = items_data.get('inventoryItems', [])
    print(f"Found {len(inventory_items)} inventory item(s)")
    
    # Get offers for each item
    offers_with_details = []
    print("Fetching offer details...")
    
    for i, item in enumerate(inventory_items, 1):
        sku = item.get('sku')
        if sku:
            print(f"  [{i}/{len(inventory_items)}] {sku[:50]}...")
            offer_result = client.get_offer_by_sku(sku)
            if offer_result.get('success') and offer_result.get('offer'):
                offer = offer_result['offer']
                
                # Get title
                title = (
                    offer.get('listing', {}).get('title', '') or
                    offer.get('title', '') or
                    offer.get('product', {}).get('title', '') or
                    'Untitled Listing'
                )
                
                listing_id = offer.get('listingId')
                offer_id = offer.get('offerId')
                group_key = offer.get('inventoryItemGroupKey', '')
                status = offer.get('status', 'UNKNOWN')
                
                # Get pricing
                pricing = offer.get('pricingSummary', {})
                price = pricing.get('price', {}).get('value', 'N/A') if pricing else 'N/A'
                currency = pricing.get('price', {}).get('currency', 'USD') if pricing else 'USD'
                
                # Get quantity
                quantity = offer.get('availableQuantity', offer.get('quantity', 'N/A'))
                
                # Get description
                description = offer.get('listing', {}).get('description', '') or ''
                
                # Get category
                category_id = offer.get('categoryId', 'N/A')
                
                offers_with_details.append({
                    'title': title,
                    'sku': sku,
                    'offer_id': offer_id,
                    'listing_id': listing_id,
                    'group_key': group_key,
                    'status': status,
                    'price': price,
                    'currency': currency,
                    'quantity': quantity,
                    'description': description[:200] + '...' if len(description) > 200 else description,
                    'category_id': category_id
                })
    
    print()
    print(f"Found {len(offers_with_details)} listings with details")
    print()
    
    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your eBay Sandbox Listings</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
        }}
        h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        .subtitle {{
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .listings {{
            display: grid;
            gap: 20px;
        }}
        .listing-card {{
            background: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 15px;
            padding: 25px;
            transition: all 0.3s ease;
        }}
        .listing-card:hover {{
            border-color: #667eea;
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.2);
            transform: translateY(-2px);
        }}
        .listing-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .listing-title {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
            flex: 1;
            min-width: 300px;
        }}
        .listing-status {{
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .status-draft {{
            background: #ffc107;
            color: #856404;
        }}
        .status-published {{
            background: #28a745;
            color: white;
        }}
        .status-unpublished {{
            background: #dc3545;
            color: white;
        }}
        .listing-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .detail-item {{
            background: white;
            padding: 12px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .detail-label {{
            font-size: 0.8em;
            color: #7f8c8d;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}
        .detail-value {{
            font-size: 1.1em;
            color: #2c3e50;
            font-weight: 600;
        }}
        .price {{
            color: #28a745;
            font-size: 1.3em;
        }}
        .listing-link {{
            margin-top: 15px;
            padding: 12px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            display: inline-block;
            font-weight: bold;
            transition: all 0.3s ease;
        }}
        .listing-link:hover {{
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }}
        .listing-link:disabled {{
            background: #95a5a6;
            cursor: not-allowed;
        }}
        .no-link {{
            color: #95a5a6;
            font-style: italic;
        }}
        .description {{
            margin-top: 15px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            color: #5a6c7d;
            font-size: 0.95em;
            line-height: 1.6;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e9ecef;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📦 Your eBay Sandbox Listings</h1>
        <p class="subtitle">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Environment: {config.EBAY_ENVIRONMENT.upper()}</p>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{len(offers_with_details)}</div>
                <div class="stat-label">Total Listings</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len([o for o in offers_with_details if o['listing_id']])}</div>
                <div class="stat-label">Published</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len([o for o in offers_with_details if not o['listing_id']])}</div>
                <div class="stat-label">Drafts</div>
            </div>
        </div>
        
        <div class="listings">
"""
    
    # Add each listing
    for listing in offers_with_details:
        status_class = 'status-draft' if not listing['listing_id'] else 'status-published'
        status_text = 'Draft' if not listing['listing_id'] else 'Published'
        
        if listing['status'] == 'UNPUBLISHED':
            status_class = 'status-unpublished'
            status_text = 'Unpublished'
        
        listing_url = f"https://sandbox.ebay.com/itm/{listing['listing_id']}" if listing['listing_id'] else None
        
        html_content += f"""
            <div class="listing-card">
                <div class="listing-header">
                    <div class="listing-title">{listing['title']}</div>
                    <div class="listing-status {status_class}">{status_text}</div>
                </div>
                
                <div class="listing-details">
                    <div class="detail-item">
                        <div class="detail-label">SKU</div>
                        <div class="detail-value">{listing['sku']}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Price</div>
                        <div class="detail-value price">${listing['price']} {listing['currency']}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Quantity</div>
                        <div class="detail-value">{listing['quantity']}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Offer ID</div>
                        <div class="detail-value">{listing['offer_id']}</div>
                    </div>
                    {f'<div class="detail-item"><div class="detail-label">Listing ID</div><div class="detail-value">{listing["listing_id"]}</div></div>' if listing['listing_id'] else ''}
                    {f'<div class="detail-item"><div class="detail-label">Group Key</div><div class="detail-value">{listing["group_key"]}</div></div>' if listing['group_key'] else ''}
                    <div class="detail-item">
                        <div class="detail-label">Category</div>
                        <div class="detail-value">{listing['category_id']}</div>
                    </div>
                </div>
                
                {f'<div class="description"><strong>Description:</strong> {listing["description"] or "No description"}</div>' if listing['description'] else ''}
                
                {f'<a href="{listing_url}" target="_blank" class="listing-link">🔗 View Listing on eBay Sandbox</a>' if listing_url else '<div class="no-link">⚠️ Draft listing - no direct link available. Publish to get a viewable link.</div>'}
            </div>
"""
    
    html_content += """
        </div>
        
        <div class="footer">
            <p>This page was generated from eBay Sandbox API data.</p>
            <p>Note: Draft listings cannot be viewed directly. Publish them to get listing IDs and viewable links.</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Save HTML file
    html_file = 'my_listings.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    file_path = os.path.abspath(html_file)
    print(f"[SUCCESS] HTML file generated!")
    print(f"File: {file_path}")
    print()
    
    # Try to open in browser
    import webbrowser
    try:
        webbrowser.open(f'file:///{file_path.replace(os.sep, "/")}')
        print("[OK] Opened in your default browser!")
    except Exception as e:
        print(f"[NOTE] Could not auto-open browser: {e}")
        print(f"Please open this file manually: {file_path}")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    generate_html()
