# CardLister Pro - New Features Added

This document summarizes the extended features implemented for CardLister Pro.

## 1. Auto-Fetch Card Images
- **Module:** `features/card_images.py`
- **API:** `POST /api/fetch-images`
- **Usage:** Click "🖼️ Fetch Images" after loading a checklist. Fetches images from Beckett page, eBay sold listings, or uses placeholder.
- **UI:** Button in Step 2 Fetch Checklist section.

## 2. Market Price Lookup
- **Module:** `features/market_prices.py`
- **API:** `POST /api/market-price`
- **Usage:** Query eBay sold listings for price guidance. Returns min, max, avg, median.
- **Note:** Call from client when pricing individual cards (can be wired to a "Suggest Price" button).

## 3. Cardboard Connection Support
- **Location:** `card_checklist.py` – `_fetch_base_cards_from_cardboardconnection()`
- **Usage:** Paste Cardboard Connection checklist URLs in the same URL field. Supports base cards from cardboardconnection.com.

## 4. Saved Checklist Presets
- **Module:** `features/presets.py`
- **API:** `GET/POST/DELETE /api/presets`
- **Storage:** `data/checklist_presets.json`
- **Usage:** Save URL + type + filters for quick reload.

## 5. Smart Tiered Pricing
- **Module:** `features/tiered_pricing.py`
- **API:** `POST /api/apply-tiered-pricing`
- **Usage:** Click "📊 Tiered Pricing" – applies rookie +50%, insert +30%, parallel +25%, autograph $5.
- **UI:** Button in Step 2 Fetch Checklist section.

## 6. Listing Templates
- **Module:** `features/listing_templates.py`
- **API:** `GET/POST/DELETE /api/templates`
- **Storage:** `data/listing_templates.json`
- **Usage:** Save/load templates via existing "Save Template" / "Load Template" (uses localStorage; API available for server-side).

## 7. Duplicate Detection
- **Module:** `features/duplicate_detection.py`
- **API:** `POST /api/check-duplicates`
- **Usage:** Pass proposed title + existing listings; returns similar listings with similarity score.

## 8. Staggered Publishing
- **Module:** `features/staggered_publish.py`
- **Usage:** Backend utility for scheduling listings with delay between each (avoids rate limits).

## 9. Bulk Edit & Bulk Relist
- **Module:** `features/bulk_ops.py`
- **Classes:** `BulkEditManager`, `BulkRelistManager`
- **Usage:** Framework for bulk price/quantity updates and relisting unsold items.

## 10. Analytics Dashboard
- **Module:** `features/analytics.py`
- **API:** `GET /api/analytics?days=30`
- **Usage:** Click "📈 Analytics" – shows payment summary, transaction count, best sellers.
- **UI:** Button in header, opens modal.

## 11. Sale Notifications
- **Module:** `features/notifications.py`
- **Usage:** Configure `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` to enable email alerts for sales.

## 12. Grading Integration (PSA/BGS/SGC)
- **Module:** `features/grading.py`
- **API:** `POST /api/grading-aspects`
- **Usage:** Get eBay item specifics for graded cards. Pass grader, grade, cert number.

## 13. Image Watermarking
- **Module:** `features/watermark.py`
- **Usage:** Add text watermark to images before upload. Requires Pillow. Call from server when processing images.

## 14. PWA (Progressive Web App)
- **Files:** `static/manifest.json`
- **Usage:** Add to home screen on mobile. Manifest linked in `app.html` head.

## 15. Per-Card Images in Listings
- **Usage:** When "Fetch Images" fills `imageUrl` on cards, those URLs are sent to the create-listing API and used per card.

## Data Storage
- `data/checklist_presets.json` – saved presets per user
- `data/listing_templates.json` – saved templates per user

## Environment Variables (Optional)
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `NOTIFY_FROM_EMAIL` – for sale notifications
