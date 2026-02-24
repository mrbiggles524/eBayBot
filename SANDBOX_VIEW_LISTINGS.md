# How to View Listings in eBay Sandbox

## The Problem

When you click "Sell" on sandbox.ebay.com, it redirects to the live eBay site. This is a known limitation - the sandbox seller hub UI doesn't fully work.

## Solutions

### Method 1: View Specific Listing (If You Have Listing ID)

If your listing was published and you have the `listing_id`, you can view it directly:

```
https://sandbox.ebay.com/itm/{LISTING_ID}
```

Replace `{LISTING_ID}` with your actual listing ID.

**To get the listing ID:**
- Check the Streamlit UI output after creating a listing
- It should show "Listing ID: ..." if the listing was published
- Or run: `python view_sandbox_listings.py`

### Method 2: Use API to View All Listings

Run this script to see all your listings via the API:

```bash
python view_sandbox_listings.py
```

This will show:
- All offers (draft and published listings)
- All inventory items
- Listing IDs (if published)
- Direct links to view listings

### Method 3: Check Streamlit UI Output

When you create a listing in the Streamlit UI, it should display:
- **Offer ID** (if created as draft)
- **Listing ID** (if published)
- **Group Key** (for variation listings)
- **Listing URL** (if available)

Look for these values in the success message after creating a listing.

## Direct Sandbox URLs (Limited)

These URLs might work, but often redirect to production:

- ❌ `https://sandbox.ebay.com/selling` - Usually redirects
- ❌ `https://sandbox.ebay.com/sh/ovw` - Usually redirects  
- ✅ `https://sandbox.ebay.com/itm/{LISTING_ID}` - Works if you have the ID

## Why This Happens

eBay's sandbox environment has limited UI features. The seller hub interface isn't fully functional in sandbox, which is why it redirects to production. This is normal and expected.

## What You Can Do

1. **Use the API** - This is the most reliable way to manage listings in sandbox
2. **View specific listings** - If you have the listing ID, you can view it directly
3. **Check the bot output** - The listing creation code returns IDs you can use

## Next Steps

1. Run `python view_sandbox_listings.py` to see your listings
2. If you created a listing, check the Streamlit UI for the listing ID
3. Use the listing ID to view it at: `https://sandbox.ebay.com/itm/{LISTING_ID}`
