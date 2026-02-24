# Return Policy Error 25009 - Comprehensive Fix

## Problem
- Return policy ID `243552423019` is being set correctly in all offers
- eBay still rejects it as invalid (Error 25009)
- API can't query/create return policies in sandbox

## What I've Implemented

### 1. Enhanced Debugging
- Detailed Error 25009 debugging shows:
  - Return policy ID from config
  - Return policy ID in each offer
  - Any mismatches or issues
  - Full error details

### 2. Automatic Workaround
- When Error 25009 occurs, the code now:
  1. Automatically removes return policy from all offers
  2. Retries publishing without return policy
  3. This is a workaround - eBay usually requires return policies, but sandbox might be lenient

### 3. Comprehensive Fix Scripts
- `fix_return_policy_comprehensive.py` - Tries multiple approaches to find/create return policy
- `set_return_policy_robust.py` - Sets return policy with verification
- Multiple query methods attempted

## Current Status
- ✅ Return policy ID set in `.env`: `243552423019`
- ✅ Code includes return policy in offers
- ✅ Enhanced debugging for Error 25009
- ✅ Automatic workaround implemented
- ⚠️ API can't verify policy exists (sandbox limitation)

## Next Steps
1. **Restart Streamlit app** (to load updated code)
2. **Try creating a listing**
3. **If Error 25009 occurs:**
   - The code will automatically try without return policy
   - Check the detailed debug output
   - The workaround might work if sandbox is lenient

## If Workaround Doesn't Work
The return policy ID from the URL (`243552423019`) might be:
- From production (not sandbox)
- In a different format
- Not valid for this category/marketplace

**Options:**
1. Create a new return policy manually in eBay Seller Hub (if accessible)
2. Get return policy ID from a working sandbox listing
3. Contact eBay support about sandbox return policy limitations

## Files Modified
- `ebay_listing.py` - Added Error 25009 workaround and enhanced debugging
- `ebay_api_client.py` - Added `_debug_return_policy_error()` method
- `.env` - Set `RETURN_POLICY_ID=243552423019`

## Testing
The code will now:
1. Try publishing with return policy (normal flow)
2. If Error 25009: automatically remove return policy and retry
3. Show detailed debugging information

Try creating a listing now - the automatic workaround should kick in if needed!
