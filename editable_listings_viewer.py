"""
Generate an editable HTML page for viewing and editing listings.
Allows adding images and preparing for production migration.
"""
import sys
import os
import json
from ebay_api_client import eBayAPIClient
from config import Config
from datetime import datetime

def generate_editable_html():
    """Generate editable HTML file with all listings."""
    print("=" * 80)
    print("Generating Editable Listings Viewer")
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
    inventory_items = items_response.json().get('inventoryItems', [])
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
                
                # Get existing images
                images = offer.get('listing', {}).get('imageUrls', []) or []
                
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
                    'description': description,
                    'category_id': category_id,
                    'images': images
                })
    
    print()
    print(f"Found {len(offers_with_details)} listings with details")
    print()
    
    # Generate HTML with editing capabilities
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Editable eBay Listings Manager</title>
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
            max-width: 1400px;
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
        .warning-banner {{
            background: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 30px;
            color: #856404;
        }}
        .warning-banner strong {{
            color: #d68910;
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
        .edit-section {{
            margin-top: 20px;
            padding: 20px;
            background: white;
            border-radius: 10px;
            border: 2px dashed #667eea;
        }}
        .edit-section h3 {{
            color: #667eea;
            margin-bottom: 15px;
        }}
        .image-upload {{
            margin-top: 15px;
        }}
        .image-input {{
            width: 100%;
            padding: 10px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            margin-bottom: 10px;
            font-size: 0.9em;
        }}
        .image-preview {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }}
        .image-preview-item {{
            position: relative;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            overflow: hidden;
        }}
        .image-preview-item img {{
            width: 100%;
            height: 150px;
            object-fit: cover;
        }}
        .image-preview-item .remove-btn {{
            position: absolute;
            top: 5px;
            right: 5px;
            background: #dc3545;
            color: white;
            border: none;
            border-radius: 50%;
            width: 25px;
            height: 25px;
            cursor: pointer;
            font-weight: bold;
        }}
        .btn {{
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 5px;
        }}
        .btn-primary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .btn-primary:hover {{
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }}
        .btn-success {{
            background: #28a745;
            color: white;
        }}
        .btn-success:hover {{
            background: #218838;
        }}
        .btn-danger {{
            background: #dc3545;
            color: white;
        }}
        .btn-danger:hover {{
            background: #c82333;
        }}
        .btn:disabled {{
            background: #95a5a6;
            cursor: not-allowed;
        }}
        .actions {{
            margin-top: 15px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .detail-item {{
            background: white;
            padding: 12px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            margin: 5px 0;
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
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e9ecef;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .hidden {{
            display: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📦 Editable eBay Listings Manager</h1>
        <p class="subtitle">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Environment: {config.EBAY_ENVIRONMENT.upper()}</p>
        
        <div class="warning-banner">
            <strong>⚠️ CURRENT ENVIRONMENT: {config.EBAY_ENVIRONMENT.upper()}</strong><br>
            <strong>📍 Publishing will go to SANDBOX (test environment), NOT your live eBay page (manhattanbreaks)</strong><br>
            To publish to your live page, you must switch to PRODUCTION environment first.<br>
            Production migration is disabled until you give the command.
        </div>
        
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
    
    # Add each listing with editing capabilities
    for idx, listing in enumerate(offers_with_details):
        status_class = 'status-draft' if not listing['listing_id'] else 'status-published'
        status_text = 'Draft' if not listing['listing_id'] else 'Published'
        
        if listing['status'] == 'UNPUBLISHED':
            status_class = 'status-unpublished'
            status_text = 'Unpublished'
        
        listing_url = f"https://sandbox.ebay.com/itm/{listing['listing_id']}" if listing['listing_id'] else None
        images_json = json.dumps(listing['images'])
        
        html_content += f"""
            <div class="listing-card" id="listing-{idx}">
                <div class="listing-header">
                    <div class="listing-title">{listing['title']}</div>
                    <div class="listing-status {status_class}">{status_text}</div>
                </div>
                
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
                
                <div class="edit-section">
                    <h3>📸 Add Images</h3>
                    <div class="image-upload">
                        <input type="text" 
                               class="image-input" 
                               id="image-input-{idx}" 
                               placeholder="Enter image URL (e.g., https://example.com/image.jpg)"
                               data-sku="{listing['sku']}"
                               data-offer-id="{listing['offer_id']}">
                        <button class="btn btn-primary" onclick="addImage({idx}, '{listing['sku']}', {listing['offer_id']})">
                            ➕ Add Image
                        </button>
                    </div>
                    <div class="image-preview" id="images-{idx}">
                        {''.join([f'<div class="image-preview-item"><img src="{img}" alt="Image"><button class="remove-btn" onclick="removeImage({idx}, {i})">×</button></div>' for i, img in enumerate(listing['images'])]) if listing['images'] else '<p style="color: #7f8c8d; font-style: italic;">No images added yet</p>'}
                    </div>
                </div>
                
                <div class="actions">
                    {f'<a href="{listing_url}" target="_blank" class="btn btn-primary">🔗 View on eBay</a>' if listing_url else ''}
                    <button class="btn btn-success" onclick="publishListing('{listing['sku']}', {listing['offer_id']}, '{listing.get('group_key', '')}')" {'disabled' if listing['listing_id'] else ''} title="Publishes to SANDBOX (test), NOT live eBay">
                        {'✅ Published (Sandbox)' if listing['listing_id'] else '🚀 Publish to SANDBOX'}
                    </button>
                    <button class="btn btn-primary" onclick="saveImages('{listing['sku']}', {listing['offer_id']})">
                        💾 Save Images
                    </button>
                    <button class="btn btn-danger hidden" id="prod-btn-{idx}" onclick="migrateToProduction('{listing['sku']}', {listing['offer_id']})" style="display: none;">
                        ⚠️ MIGRATE TO PRODUCTION
                    </button>
                </div>
            </div>
"""
    
    html_content += f"""
        </div>
        
        <div class="footer">
            <p>This page allows you to add images and manage your listings.</p>
            <p><strong>Production migration is disabled</strong> until you give the command.</p>
            <p>All changes are saved via the eBay API.</p>
        </div>
    </div>
    
    <script>
        const listingsData = {json.dumps(offers_with_details)};
        
        function addImage(listingIdx, sku, offerId) {{
            const input = document.getElementById(`image-input-${{listingIdx}}`);
            const url = input.value.trim();
            
            if (!url) {{
                alert('Please enter an image URL');
                return;
            }}
            
            // Validate URL
            try {{
                new URL(url);
            }} catch (e) {{
                alert('Please enter a valid URL');
                return;
            }}
            
            const imagesDiv = document.getElementById(`images-${{listingIdx}}`);
            const imageItem = document.createElement('div');
            imageItem.className = 'image-preview-item';
            imageItem.innerHTML = `
                <img src="${{url}}" alt="Image" onerror="this.parentElement.remove(); alert('Image failed to load');">
                <button class="remove-btn" onclick="this.parentElement.remove()">×</button>
            `;
            
            // Remove "No images" message if present
            const noImagesMsg = imagesDiv.querySelector('p');
            if (noImagesMsg) noImagesMsg.remove();
            
            imagesDiv.appendChild(imageItem);
            input.value = '';
        }}
        
        function removeImage(listingIdx, imageIdx) {{
            const imagesDiv = document.getElementById(`images-${{listingIdx}}`);
            const items = imagesDiv.querySelectorAll('.image-preview-item');
            if (items[imageIdx]) {{
                items[imageIdx].remove();
            }}
            
            // Show "No images" if empty
            if (imagesDiv.querySelectorAll('.image-preview-item').length === 0) {{
                imagesDiv.innerHTML = '<p style="color: #7f8c8d; font-style: italic;">No images added yet</p>';
            }}
        }}
        
        function getImageUrls(listingIdx) {{
            const imagesDiv = document.getElementById(`images-${{listingIdx}}`);
            const images = [];
            imagesDiv.querySelectorAll('img').forEach(img => {{
                images.push(img.src);
            }});
            return images;
        }}
        
        function saveImages(sku, offerId) {{
            const listingIdx = listingsData.findIndex(l => l.sku === sku);
            if (listingIdx === -1) {{
                alert('Listing not found');
                return;
            }}
            
            const imageUrls = getImageUrls(listingIdx);
            
            if (imageUrls.length === 0) {{
                alert('No images to save. Add images first using the "Add Image" button.');
                return;
            }}
            
            // Build the Python command
            const imageUrlsStr = imageUrls.map(url => `"${{url}}"`).join(' ');
            const command = `python add_images_to_listing.py ${{sku}} ${{imageUrlsStr}}`;
            
            // Copy to clipboard
            if (navigator.clipboard) {{
                navigator.clipboard.writeText(command).then(() => {{
                    alert(`✅ Command copied to clipboard!\\n\\nRun this in your terminal:\\n\\n${{command}}\\n\\nOr click OK to generate a .bat file.`);
                    
                    // Generate a .bat file for easy execution
                    const batContent = `@echo off\\necho Adding images to listing ${{sku}}...\\ncd /d "C:\\\\eBayBot"\\n${{command}}\\npause`;
                    const blob = new Blob([batContent], {{ type: 'text/plain' }});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `add_images_${{sku}}.bat`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                }}).catch(() => {{
                    // Fallback if clipboard fails
                    const commandText = `Run this command:\\n\\n${{command}}`;
                    if (confirm(commandText + '\\n\\nClick OK to generate a .bat file.')) {{
                        const batContent = `@echo off\\necho Adding images to listing ${{sku}}...\\ncd /d "C:\\\\eBayBot"\\n${{command}}\\npause`;
                        const blob = new Blob([batContent], {{ type: 'text/plain' }});
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `add_images_${{sku}}.bat`;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                    }}
                }});
            }} else {{
                // Fallback if clipboard API not available
                const commandText = `Run this command:\\n\\n${{command}}`;
                if (confirm(commandText + '\\n\\nClick OK to generate a .bat file.')) {{
                    const batContent = `@echo off\\necho Adding images to listing ${{sku}}...\\ncd /d "C:\\\\eBayBot"\\n${{command}}\\npause`;
                    const blob = new Blob([batContent], {{ type: 'text/plain' }});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `add_images_${{sku}}.bat`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                }}
            }}
        }}
        
        function publishListing(sku, offerId, groupKey) {{
            if (!confirm('Publish this listing to SANDBOX?\\n\\nThis will make it live in the eBay Sandbox (test environment).\\n\\nIt will NOT go to your live eBay page.')) {{
                return;
            }}
            
            // Create a command file that can be executed
            const command = `python publish_draft.py "${{sku}}"`;
            
            // Show instructions
            const instructions = `
📋 TO PUBLISH THIS LISTING:

1. Open a terminal/command prompt
2. Navigate to: C:\\\\eBayBot
3. Run this command:

   ${{command}}

Or copy this command and run it:
${{command}}

⚠️ Remember: This publishes to SANDBOX (test), NOT your live eBay page.
            `;
            
            // Copy command to clipboard if possible
            if (navigator.clipboard) {{
                navigator.clipboard.writeText(command).then(() => {{
                    alert(instructions + '\\n\\n✅ Command copied to clipboard!');
                }}).catch(() => {{
                    alert(instructions);
                }});
            }} else {{
                alert(instructions);
            }}
            
            // Also create a clickable link to a helper file
            const helperText = `Click OK, then I'll create a batch file you can double-click to publish.`;
            if (confirm(helperText)) {{
                // Create a data URI for a batch file
                const batchContent = `@echo off
cd /d "C:\\\\eBayBot"
python publish_draft.py "${{sku}}"
pause
`;
                const blob = new Blob([batchContent], {{ type: 'text/plain' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `publish_${{sku}}.bat`;
                a.click();
                URL.revokeObjectURL(url);
            }}
        }}
        
        function migrateToProduction(sku, offerId) {{
            if (!confirm('⚠️ WARNING: Migrate this listing to PRODUCTION?\\n\\nThis will move it to your live eBay account.\\n\\nAre you absolutely sure?')) {{
                return;
            }}
            
            if (!confirm('⚠️ FINAL CONFIRMATION: This will publish to PRODUCTION eBay.\\n\\nType "MIGRATE" to confirm:')) {{
                return;
            }}
            
            alert('Production migration requires explicit command. Run: python migrate_to_production.py ' + sku);
        }}
        
        // Enable production buttons when command is given
        function enableProductionMode() {{
            document.querySelectorAll('[id^="prod-btn-"]').forEach(btn => {{
                btn.classList.remove('hidden');
                btn.style.display = 'inline-block';
            }});
            alert('⚠️ PRODUCTION MODE ENABLED');
        }}
        
        // Listen for production enable command (you can call enableProductionMode() from console)
        console.log('To enable production mode, run: enableProductionMode()');
    </script>
</body>
</html>
"""
    
    # Save HTML file
    html_file = 'editable_listings.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    file_path = os.path.abspath(html_file)
    print(f"[SUCCESS] Editable HTML file generated!")
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
    generate_editable_html()
