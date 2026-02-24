# Base Cards Shipping Setup - eBay Label Service

## Overview

This setup allows you to use eBay's shipping label service for base cards under $20. The customer pays $1.99 for shipping, but you'll use eBay Labels which costs you only ~$0.70 for 1 oz (up to 3 oz for $1.99).

## How It Works

1. **Fulfillment Policy**: Sets what the customer pays ($1.99 flat rate, up to 3 oz)
2. **eBay Labels API**: After sale, you purchase labels via eBay Logistics API at discounted rates
3. **Profit Margin**: Customer pays $1.99, you pay ~$0.70-1.99 depending on weight

## Current Setup

Your existing fulfillment policy (ID: `6213834000`) is already configured with:
- **Shipping Service**: USPS First Class
- **Customer Pays**: $1.99 (flat rate)
- **Package**: Up to 3 oz, 6 x 4 x 1 inches

## Configuration

### Option 1: Use Existing Policy (Recommended)

Since your existing policy already has the right configuration, you can use it for base cards:

1. Add to your `.env` file:
   ```
   BASE_CARDS_FULFILLMENT_POLICY_ID=6213834000
   ```

2. The system will automatically use this policy when:
   - All cards in a listing are under $20, OR
   - You explicitly set `use_base_cards_policy=True` when creating a listing

### Option 2: Create Separate Policy (If Needed)

If you want a separate policy specifically for base cards:

1. Run: `python create_base_cards_policy.py`
2. Copy the Policy ID from the output
3. Add to `.env`:
   ```
   BASE_CARDS_FULFILLMENT_POLICY_ID=<new_policy_id>
   ```

## Using in Code

### Automatic Selection (Based on Price)

```python
# If all cards are under $20, base cards policy is used automatically
listing_manager.create_variation_listing(
    cards=cards,
    title="Base Cards Set",
    description="...",
    category_id="261328",
    price=15.00,  # Under $20 - will use base cards policy
    ...
)
```

### Manual Selection

```python
# Explicitly use base cards policy
listing_manager.create_variation_listing(
    cards=cards,
    title="Base Cards Set",
    description="...",
    category_id="261328",
    price=25.00,  # Over $20, but force base cards policy
    use_base_cards_policy=True,  # Force base cards policy
    ...
)

# Or use specific policy ID
listing_manager.create_variation_listing(
    cards=cards,
    title="Base Cards Set",
    description="...",
    category_id="261328",
    price=25.00,
    fulfillment_policy_id="6213834000",  # Use specific policy
    ...
)
```

## After Sale - Purchasing eBay Labels

When a card sells, you'll need to purchase shipping labels using eBay's Logistics API:

1. **Get Shipping Quote**:
   ```python
   # Use eBay Logistics API
   POST /sell/logistics/v1/shipping_quote
   {
     "destinationAddress": {...},
     "packageSpecification": {
       "weight": {"value": "0.1875", "unit": "POUND"},  # 3 oz
       "dimensions": {"length": "6", "width": "4", "height": "1", "unit": "INCH"}
     }
   }
   ```

2. **Create Label**:
   ```python
   # Create label from quote
   POST /sell/logistics/v1/shipment/create_from_shipping_quote
   ```

3. **Cost**: You'll pay ~$0.70 for 1 oz, up to $1.99 for 3 oz (customer paid $1.99)

## Package Specifications

- **Weight**: 3 oz (0.1875 pounds)
- **Dimensions**: 6 x 4 x 1 inches
- **Service**: USPS First Class (via eBay Labels)

## Notes

- The fulfillment policy only sets what the **customer pays**
- You purchase labels **after the sale** using eBay Logistics API
- eBay Labels are typically cheaper than standard USPS rates
- Tracking is automatically added when using eBay Labels
- Make sure you have billing agreements set up for label purchases

## Troubleshooting

**Policy not found?**
- Check that `BASE_CARDS_FULFILLMENT_POLICY_ID` is set in `.env`
- If not set, it defaults to `FULFILLMENT_POLICY_ID`

**Want to use different policy?**
- Set `BASE_CARDS_FULFILLMENT_POLICY_ID` to a different policy ID
- Or pass `fulfillment_policy_id` parameter directly when creating listing
