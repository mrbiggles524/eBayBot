# Fix: Fulfillment Policy Missing Shipping Services

## The Problem

Error: "Please add at least one valid shipping service option to your listing" (Error ID: 25007)

This means your fulfillment policy doesn't have shipping services configured.

## Solution: Update Policy in eBay Seller Hub

Since the API policy creation is having issues, the easiest way is to update your policy in eBay Seller Hub:

### Step 1: Go to eBay Seller Hub
1. Go to: https://sandbox.ebay.com/sh/account/policies
2. Sign in with: `TESTUSER_manbot`

### Step 2: Edit Your Fulfillment Policy
1. Find your fulfillment policy (the one with ID: `229316003019`)
2. Click on it to edit
3. Look for "Shipping Services" or "Shipping Options"
4. Add at least one shipping service:
   - **USPS First Class** (for cards under 1 oz)
   - **USPS Priority Mail** (for heavier items)
   - Or any other shipping service

### Step 3: Save and Try Again
1. Save the policy
2. Go back to Streamlit UI
3. Try creating a listing again

## Alternative: Use a Different Policy

If you can't edit the policy, you can:

1. **Get a different policy ID**:
   - Go to Step 3 (Auto-Configure) in Streamlit UI
   - It will fetch all your policies
   - Select one that has shipping services configured
   - Update the FULFILLMENT_POLICY_ID in .env

2. **Or create a new policy in Seller Hub**:
   - Create a new fulfillment policy with shipping services
   - Use that policy ID instead

## What Shipping Services to Add

For trading cards, common options:
- **USPS First Class** - Good for single cards ($0.60-$3.00)
- **USPS Ground Advantage** - For multiple cards
- **USPS Priority Mail** - For larger orders

Make sure the policy has at least ONE shipping service configured!
