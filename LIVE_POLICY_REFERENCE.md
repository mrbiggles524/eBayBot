# Live Account Policy Reference

## Your Live Account Policy

**Policy URL**: https://www.ebay.com/bp/ship/edit/229316003019?lis=113

**Policy ID**: `229316003019`

**Status**: Currently used by 113 listings

**Policy Name**: "PWE eBay Shipping Envelope ONLY Cards Under $20"

## Policy Details (from your account)

- **Service**: eBay Standard Envelope for eligible items up to $20
- **Buyer Pays**: $1.99 (first item) + $0.39 (each additional)
- **Handling Time**: Same business day
- **Delivery**: 3-6 business days
- **Restriction**: Items must be under $20

## For Sandbox Testing

Since we're in sandbox and eBay Standard Envelope may not be available:

1. **Current Sandbox Policy**: `6213856000` (USPSPriority)
   - Use this for testing in sandbox
   - Works for all price ranges

2. **When Moving to Production**:
   - You can either:
     - Use your existing live policy (`229316003019`)
     - Create a new policy with the same settings
   - The service code should be `US_eBayStandardEnvelope`

## Verifying Service Code

To get the exact service code from your live account:

1. **Via Seller Hub**:
   - Go to: https://www.ebay.com/bp/ship/edit/229316003019?lis=113
   - Check the "Primary service" field
   - Note the exact service code

2. **Via Production API** (if you have access):
   - Switch environment to production
   - Query policy ID `229316003019`
   - Extract the `shippingServiceCode` from the response

## Recommendation

For now:
- Continue using sandbox policy `6213856000` for testing
- When ready for production, you can:
  - Use your existing live policy `229316003019` directly
  - Or create a new one with the same settings

The code is already set up to automatically select the base cards policy for items under $20, so it will work seamlessly when you switch to production.
