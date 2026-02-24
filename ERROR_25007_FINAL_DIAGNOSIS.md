# Error 25007 - Final Diagnosis

## Current Status

✅ **Policy is correctly configured:**
- Policy ID: `6213856000`
- Has shipping services: `USPSPriority`
- Policy is loaded correctly by listing manager
- All policy IDs match

❌ **Still getting Error 25007 during publishing**

## The Problem

The error occurs specifically during **publishing**, not during offer creation. This suggests eBay does stricter validation during the publish step.

## Possible Causes

1. **Policy Propagation Delay**
   - eBay may need 5-10 minutes to fully process policy changes
   - Try waiting and creating the listing again

2. **Shipping Service Code Validation**
   - `USPSPriority` might not be valid for Trading Cards category (261328) during publish
   - eBay may require different service codes for certain categories

3. **Buyer Responsible Setting**
   - Policy shows `buyerResponsibleForShipping: False` (seller pays)
   - We set it to `True` but it didn't save
   - This might be causing validation issues

4. **Category-Specific Requirements**
   - Trading Cards (261328) might have specific shipping requirements
   - May need tracked shipping or specific service types

## Solutions to Try

### Solution 1: Wait and Retry (Easiest)
1. Wait 5-10 minutes for policy to fully propagate
2. Restart your Streamlit app to reload policies
3. Try creating listing again

### Solution 2: Fix Buyer Responsible Setting
The policy currently shows seller pays, but we want buyer to pay. Try updating via Seller Hub:
1. Go to: https://sandbox.ebay.com/sh/account/policies
2. Find policy ID: `6213856000`
3. Edit and ensure "Buyer pays for shipping" is selected
4. Save the policy
5. Try creating listing again

### Solution 3: Try Different Shipping Service
If the above don't work, we may need to try a different shipping service code that's specifically validated for Trading Cards. Options:
- `USPSPriorityFlatRateEnvelope` (for small packages)
- `USPSGroundAdvantage` (newer service)
- `USPSStandardPost` (economy option)

### Solution 4: Verify via Seller Hub
1. Go to Seller Hub → Account → Business Policies
2. Verify policy `6213856000` has shipping services
3. Try creating a test listing manually in Seller Hub
4. If manual creation works, the issue is API-specific

## Next Steps

1. **First**: Restart Streamlit app and wait 5-10 minutes, then try again
2. **If that fails**: Try updating the policy in Seller Hub to ensure buyer pays
3. **If still failing**: We'll need to try a different shipping service code

## Current Policy Details

- **Policy ID**: 6213856000
- **Name**: Cards Shipping Priority $1.99
- **Service**: USPSPriority
- **Cost**: $1.99
- **Buyer Pays**: Currently False (should be True)
- **Shipping Options**: 1 DOMESTIC option with 1 service

The policy structure is correct - the issue is likely with:
- Policy propagation timing
- Service code validation for category 261328
- Buyer/seller payment responsibility setting
