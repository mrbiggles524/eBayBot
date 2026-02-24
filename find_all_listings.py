"""
Comprehensive script to find ALL listings in your account.
This will search through all offers to find where your listings actually are.
"""
import sys
import json
from datetime import datetime
from ebay_api_client import eBayAPIClient
from config import Config

sys.stdout.reconfigure(encoding='utf-8')

def find_all_listings():
    """Find all listings in the account."""
    print("=" * 80)
    print("COMPREHENSIVE LISTING SEARCH")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    env_name = config.EBAY_ENVIRONMENT.upper()
    api_url = config.ebay_api_url
    
    print(f"Environment: {env_name}")
    print(f"API URL: {api_url}")
    print()
    
    if env_name != 'PRODUCTION':
        print("⚠️ WARNING: Not using PRODUCTION!")
        print("⚠️ Set EBAY_ENVIRONMENT=production in .env file")
        print()
    else:
        print("✅ Using PRODUCTION environment")
        print()
    
    # Get all offers with pagination
    print("Fetching ALL offers from your account...")
    print()
    
    all_offers = []
    offset = 0
    limit = 200
    max_pages = 20
    
    for page in range(max_pages):
        try:
            params = {"limit": limit, "offset": offset}
            response = client._make_request('GET', '/sell/inventory/v1/offer', params=params)
            
            if response.status_code == 200:
                data = response.json()
                offers = data.get('offers', [])
                all_offers.extend(offers)
                print(f"Page {page + 1}: Found {len(offers)} offers (total: {len(all_offers)})")
                
                if len(offers) < limit:
                    break
                offset += limit
            else:
                print(f"Error on page {page + 1}: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                break
        except Exception as e:
            print(f"Error fetching page {page + 1}: {e}")
            break
    
    print()
    print(f"Total offers found: {len(all_offers)}")
    print()
    
    # Categorize offers
    drafts = []
    scheduled = []
    active = []
    groups = {}
    
    for offer in all_offers:
        offer_id = offer.get('offerId', '')
        sku = offer.get('sku', '')
        listing_id = offer.get('listingId', '')
        status = offer.get('status', 'UNKNOWN')
        listing = offer.get('listing', {})
        listing_status = listing.get('listingStatus', 'UNKNOWN')
        start_date = offer.get('listingStartDate', '') or listing.get('listingStartDate', '')
        group_key = offer.get('inventoryItemGroupKey', '')
        title = listing.get('title', offer.get('title', 'No title'))
        
        offer_info = {
            "offer_id": offer_id,
            "sku": sku,
            "listing_id": listing_id,
            "status": listing_status or status,
            "start_date": start_date,
            "title": title,
            "group_key": group_key
        }
        
        # Categorize
        if not listing_id:
            drafts.append(offer_info)
        elif start_date:
            # Check if start date is in future
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                now = datetime.utcnow().replace(tzinfo=start_dt.tzinfo)
                if start_dt > now:
                    scheduled.append(offer_info)
                else:
                    active.append(offer_info)
            except:
                if start_date:
                    scheduled.append(offer_info)
                else:
                    active.append(offer_info)
        else:
            active.append(offer_info)
        
        # Track groups
        if group_key:
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(offer_info)
    
    # Print results
    print("=" * 80)
    print("LISTING CATEGORIES")
    print("=" * 80)
    print()
    
    print(f"DRAFTS (Unpublished): {len(drafts)}")
    if drafts:
        print("  These should appear in Seller Hub 'Drafts' (if visible):")
        for i, draft in enumerate(drafts[:10], 1):
            print(f"  {i}. {draft['title'][:50]}")
            print(f"     SKU: {draft['sku']}, Offer ID: {draft['offer_id']}")
            print(f"     Group: {draft['group_key'] or 'None'}")
    print()
    
    print(f"SCHEDULED: {len(scheduled)}")
    if scheduled:
        print("  These should appear in Seller Hub 'Scheduled Listings':")
        for i, sched in enumerate(scheduled[:10], 1):
            print(f"  {i}. {sched['title'][:50]}")
            print(f"     Listing ID: {sched['listing_id']}")
            print(f"     Start Date: {sched['start_date']}")
            print(f"     Group: {sched['group_key'] or 'None'}")
            try:
                start_dt = datetime.fromisoformat(sched['start_date'].replace('Z', '+00:00'))
                now = datetime.utcnow().replace(tzinfo=start_dt.tzinfo)
                hours = (start_dt - now).total_seconds() / 3600
                print(f"     Goes live in: {hours:.1f} hours ({hours/24:.1f} days)")
            except:
                pass
    print()
    
    print(f"ACTIVE: {len(active)}")
    if active:
        print("  These should appear in Seller Hub 'Active Listings':")
        for i, act in enumerate(active[:10], 1):
            print(f"  {i}. {act['title'][:50]}")
            print(f"     Listing ID: {act['listing_id']}")
            print(f"     Group: {act['group_key'] or 'None'}")
    print()
    
    print(f"VARIATION GROUPS: {len(groups)}")
    if groups:
        print("  Variation listings (grouped):")
        for group_key, offers in list(groups.items())[:5]:
            print(f"  Group: {group_key}")
            print(f"    Offers: {len(offers)}")
            scheduled_in_group = sum(1 for o in offers if o.get('start_date'))
            published_in_group = sum(1 for o in offers if o.get('listing_id'))
            print(f"    - Published: {published_in_group}")
            print(f"    - Scheduled: {scheduled_in_group}")
            if offers:
                print(f"    - Title: {offers[0].get('title', 'N/A')[:50]}")
    print()
    
    # Seller Hub URLs
    base_url = "https://www.ebay.com" if env_name == 'PRODUCTION' else "https://sandbox.ebay.com"
    print("=" * 80)
    print("SELLER HUB LINKS")
    print("=" * 80)
    print()
    print(f"Drafts: {base_url}/sh/account/listings?status=DRAFT")
    print(f"Scheduled: {base_url}/sh/account/listings?status=SCHEDULED")
    print(f"Active: {base_url}/sh/account/listings?status=ACTIVE")
    print(f"Unsold/Ended: {base_url}/sh/account/listings?status=UNSOLD")
    print(f"All Listings: {base_url}/sh/account/listings")
    print()

if __name__ == "__main__":
    find_all_listings()
