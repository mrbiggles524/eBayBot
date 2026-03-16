# Marketplace Auto-Complete via Tracking

When sellers add a tracking number after shipping, sales **auto-complete when the package is delivered**. No manual reporting needed.

## How it works

1. **Report Shipment** – Seller enters tracking number, buyer email, sale amount (one-time when they ship).
2. **Automatic check** – When anyone visits the marketplace, pending shipments are checked.
3. **When delivered** – Sale is recorded and 5% fees are calculated automatically.

## Enable tracking API

Add to `.env` or Render environment variables:

```
TRACKINGMORE_API_KEY=your_api_key
```

Get a free API key at [trackingmore.com](https://www.trackingmore.com/signup.html) (they offer a free trial).

Supported carriers: USPS, UPS, FedEx (auto-detected from tracking number format).
