# How to Switch to Production and Use Scheduled Drafts

## Quick Steps

### 1. Switch to Production Environment

Edit your `.env` file and change:
```
EBAY_ENVIRONMENT=sandbox
```
to:
```
EBAY_ENVIRONMENT=production
```

### 2. Make Sure You Have Production Credentials

In your `.env` file, ensure you have:
- `EBAY_APP_ID` - Your production App ID
- `EBAY_CERT_ID` - Your production Cert ID  
- `EBAY_PRODUCTION_TOKEN` - Your production OAuth token (or use OAuth)

### 3. Use "Save as Scheduled Draft"

When creating listings:
- ✅ **DO**: Check "Save as Scheduled Draft" 
- ✅ **DO**: Set schedule hours to at least 48 hours (default is 48)
- ❌ **DON'T**: Check "Publish Immediately" (this will make it go live)

### 4. How Scheduled Drafts Work

When you use "Save as Scheduled Draft":
- The listing is published BUT with a future `listingStartDate`
- It appears in Seller Hub as "Scheduled Listings" (not "Active")
- You can edit it before it goes live
- You can publish it immediately from Seller Hub if needed
- It will NOT go live until the scheduled time (minimum 48 hours)

### 5. Verify It Worked

After creating a scheduled draft:
1. Check the console output for `[VERIFY]` messages
2. Look for "✅ ALL offers have listingStartDate"
3. Go to Seller Hub: https://www.ebay.com/sh/account/listings?status=SCHEDULED
4. Your listing should appear in the "Scheduled" section

### 6. If Listing Goes Live Immediately

If the listing goes live instead of staying scheduled:
- Check console for `[VERIFY]` messages
- Look for "❌ MISSING listingStartDate" warnings
- Make sure all offers have `listingStartDate` set
- The verification will show which offers are missing the start date

## Important Notes

- **Scheduled drafts require `publish=True`** - This is how eBay works. The `listingStartDate` prevents it from going live.
- **Minimum 48 hours** - Production uses minimum 48 hours to ensure scheduled status
- **Regular drafts don't appear** - eBay Inventory API doesn't make unpublished drafts visible in Seller Hub. Use scheduled drafts instead.
