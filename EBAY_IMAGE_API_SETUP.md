# eBay API for Card Images - Setup Guide

CardPilot fetches card images from eBay using the **eBay Browse API**. No extra API key is needed—it uses the same credentials as your main app.

## What You Need

- **EBAY_APP_ID** – Your eBay application ID
- **EBAY_CERT_ID** – Your eBay certificate ID  
- **OAuth scope**: `commerce.browse.product` (Buy API – Browse)

These are the same App ID and Cert ID you already use for listing. You only need to enable one additional scope.

---

## Step 1: eBay Developer Portal

1. Go to **[developer.ebay.com](https://developer.ebay.com)**
2. Sign in → **My Account** → **Application Keys** (or **Application Settings**)
3. Select your application (the one that has your App ID and Cert ID)

---

## Step 2: Enable Buy API / Browse Scope

1. In your application settings, find the **OAuth Scopes** or **API Access** section
2. Add or enable the scope:
   ```
   https://api.ebay.com/oauth/api_scope/commerce.browse.product
   ```
3. It may appear as:
   - **Buy API** → **Browse** → **Read**
   - **Commerce Browse Product**
   - **Browse product catalog**
4. Save your changes

---

## Step 3: Environment Variables

Set these in `.env` or in Render:

| Variable      | Description                                   | Example        |
|---------------|-----------------------------------------------|----------------|
| `EBAY_APP_ID` | Your eBay App ID                              | `YourApp-PRD-...` |
| `EBAY_CERT_ID`| Your eBay Cert ID                             | `PRD-...`      |

If these are already set for listing, no changes are needed.

---

## How It Works

1. CardPilot requests an **application access token** using App ID + Cert ID (client credentials).
2. With that token it calls:
   ```
   GET https://api.ebay.com/buy/browse/v1/item_summary/search
   ?q=2024-25 Topps Chrome Basketball Pascal Siakam #43
   &category_ids=261328
   ```
3. eBay returns search results with image URLs (`i.ebayimg.com`).
4. Those URLs are used for your card preview images.

---

## Fallback Sources

If the Browse API is not configured or returns no results, CardPilot uses:

1. **SerpAPI eBay** – Requires `SERPAPI_KEY` (paid).
2. **SerpAPI Google Images** – Same key.
3. **eBay HTML scrape** – Free fallback (can be blocked or slow).

So even without the Browse API, image fetching can still work with SerpAPI or scraping.

---

## Troubleshooting

| Problem | Possible cause |
|---------|----------------|
| No images, only placeholders | Scope `commerce.browse.product` not enabled |
| Token error | Check App ID and Cert ID in `.env` |
| 403 / access denied | App not approved for production; verify in Developer Portal |
| Slow or no results | Try adding `SERPAPI_KEY` for a more reliable fallback |

---

## Summary

1. Add scope **`commerce.browse.product`** to your eBay app.  
2. Use existing **EBAY_APP_ID** and **EBAY_CERT_ID**.  
3. No extra keys or APIs are required for eBay image fetching.
