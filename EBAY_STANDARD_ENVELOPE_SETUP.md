# eBay Standard Envelope Setup

## Overview

eBay Standard Envelope is a special shipping service for trading cards and similar items under $20. It's designed for Plain White Envelope (PWE) shipping.

## Your Live Account Settings

From your live account, your policy is configured as:
- **Policy Name**: "PWE eBay Shipping Envelope ONLY Cards Under $20"
- **Service**: eBay Standard Envelope for eligible items up to $20
- **Buyer Pays**: $1.99 (first item) + $0.39 (each additional)
- **Handling Time**: Same business day
- **Delivery**: 3-6 business days
- **Restriction**: Items must be under $20 (eBay won't allow label printing if over $20)

## Important Notes

### Sandbox vs Production

⚠️ **eBay Standard Envelope may not be available in Sandbox environment.**

The sandbox environment often has limited shipping service options. eBay Standard Envelope (`US_eBayStandardEnvelope`) might only work in **production**.

### Service Code

The correct service code for eBay Standard Envelope is:
- **Service Code**: `US_eBayStandardEnvelope`
- **Carrier Code**: `USPS`
- **Marketplace**: `EBAY_US` only

### Requirements

1. **Item Price**: Must be under $20.00 (declared selling price)
2. **Category**: Only certain categories are eligible:
   - Trading Cards (specific sub-categories)
   - Coins & Paper Money
   - Postcards
   - Stamps
   - Patches
3. **Shipping Label**: Must use eBay-generated shipping label
4. **Envelope**: Must meet specific dimension and content rules

## For Sandbox Testing

Since eBay Standard Envelope might not work in sandbox, you have two options:

### Option 1: Use Regular USPS Service for Sandbox

For sandbox testing, use a regular USPS service (like `USPSPriority`) that works in sandbox. Your current policy (`6213856000`) uses `USPSPriority` which should work.

### Option 2: Test in Production (Carefully)

If you want to test eBay Standard Envelope, you'll need to:
1. Switch to production environment
2. Create the policy with `US_eBayStandardEnvelope`
3. Test with a low-value item (under $20)

## Creating the Policy (Production)

When ready for production, use this configuration:

```json
{
  "marketplaceId": "EBAY_US",
  "name": "PWE eBay Shipping Envelope ONLY Cards Under $20",
  "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
  "handlingTime": {
    "value": 0,
    "unit": "DAY"
  },
  "shippingOptions": [
    {
      "optionType": "DOMESTIC",
      "costType": "FLAT_RATE",
      "shippingServices": [
        {
          "shippingServiceCode": "US_eBayStandardEnvelope",
          "shippingCarrierCode": "USPS",
          "freeShipping": false,
          "shippingCost": {
            "value": "1.99",
            "currency": "USD"
          },
          "additionalShippingCost": {
            "value": "0.39",
            "currency": "USD"
          },
          "buyerResponsibleForShipping": true,
          "sortOrder": 1
        }
      ]
    }
  ]
}
```

## Current Status

- ✅ Policy structure is correct
- ❌ Service code `US_eBayStandardEnvelope` not accepted in sandbox
- ⚠️ Likely only works in production environment

## Recommendation

For now, continue using your current sandbox policy (`6213856000` with `USPSPriority`) for testing. When you're ready to go live, create a new policy in production with `US_eBayStandardEnvelope`.

## Code Update Needed

When you switch to production and want to use eBay Standard Envelope, update your listing code to:
1. Check if item price is under $20
2. Use eBay Standard Envelope policy for items under $20
3. Use regular shipping policy for items $20 and over

This matches your live account setup where you have a specific policy for cards under $20.
