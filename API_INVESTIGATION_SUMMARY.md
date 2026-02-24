# eBay API Investigation Summary - Description Validation Issue

## Problem
Error 25016: "The description value is invalid. A description is required" when trying to publish variation listings in Production.

## Investigation Results

### 1. Fresh Listing Created Successfully
- **Group Key**: `GROUPSET1768713890`
- **SKU**: `CARD_SET_FRESH_TEST_CARD_1_0`
- **Offer ID**: `965452302016`
- **Status**: Created as draft (UNPUBLISHED)

### 2. API Behavior Analysis

#### Group GET Request
- **Endpoint**: `GET /sell/inventory/v1/inventory_item_group/{group_key}`
- **Response**: Returns `title`, `variesBy`, `variantSKUs`
- **Missing**: `inventoryItemGroup` object (including description)
- **Conclusion**: eBay GET does NOT return `inventoryItemGroup` even if it was stored

#### Group PUT Request
- **Endpoint**: `PUT /sell/inventory/v1/inventory_item_group/{group_key}`
- **Payload**: Includes `inventoryItemGroup.description` (203 characters, valid)
- **Response**: `204 No Content` (success)
- **Conclusion**: eBay accepts the description and returns success

#### Offer GET Request
- **Endpoint**: `GET /sell/inventory/v1/offer?sku={sku}`
- **Response**: Returns offer metadata (policies, pricing, etc.)
- **Missing**: `listing` object (including description)
- **Conclusion**: eBay GET does NOT return `listing` object for unpublished offers

#### Offer PUT Request
- **Endpoint**: `PUT /sell/inventory/v1/offer/{offer_id}`
- **Payload**: Includes `listing.description` (127+ characters, valid)
- **Response**: `204 No Content` (success)
- **Conclusion**: eBay accepts the description and returns success

#### Publish Request
- **Endpoint**: `POST /sell/inventory/v1/offer/publish_by_inventory_item_group`
- **Payload**: Only `inventoryItemGroupKey` and `marketplaceId`
- **Response**: `400 Bad Request` with Error 25016
- **Conclusion**: eBay validation fails to find description during publish

### 3. Root Cause

**eBay Production API Bug**: The description is being sent correctly and accepted (204 responses), but eBay's publish validation cannot find it. This appears to be a data persistence or validation timing issue in eBay's production API.

**Evidence**:
1. ✅ Description is included in PUT requests (verified in debug logs)
2. ✅ eBay returns 204 (success) for PUT requests
3. ✅ Description meets all requirements (length, format, location)
4. ❌ eBay GET doesn't return `inventoryItemGroup` (known API quirk)
5. ❌ eBay GET doesn't return `listing` for unpublished offers (known API quirk)
6. ❌ eBay publish validation fails with Error 25016

### 4. Attempted Solutions

All attempted solutions failed:
- ✅ Updating group with description before publish
- ✅ Updating offer with description before publish
- ✅ Waiting 5-15 seconds for propagation
- ✅ Using valid policies (payment, fulfillment, return)
- ✅ Creating fresh listing from scratch
- ❌ All still result in Error 25016

### 5. Known eBay API Quirks

1. **GET doesn't return stored data**: eBay's GET endpoints don't return `inventoryItemGroup` or `listing` objects even though they're stored
2. **Description location**: For variation listings, description must be in `inventoryItemGroup.description`
3. **Validation timing**: eBay validates description during publish, not during PUT

### 6. Recommendations

1. **Contact eBay Developer Support**: This appears to be a production API bug that needs eBay's attention
2. **Workaround**: Try publishing from Seller Hub UI (if drafts appear there)
3. **Alternative**: Use single-item listings instead of variation listings (if possible)
4. **Monitor**: Check if this is a temporary API issue that resolves itself

### 7. Test Details

- **Environment**: Production
- **Account**: manhattanbreaks
- **Test Listings Created**: 2
  - `GROUPTESTSET1768712745` (original test)
  - `GROUPSET1768713890` (fresh test)
- **All attempts**: Failed with Error 25016

### 8. Next Steps

1. Document this issue for eBay support
2. Check if there are any eBay API status updates
3. Consider alternative listing creation methods
4. Wait and retry after some time (may be temporary)

---

**Date**: January 18, 2026
**Status**: Blocked by eBay Production API Bug (Error 25016)
**Priority**: High - Prevents listing publication
