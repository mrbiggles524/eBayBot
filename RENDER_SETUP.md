# Quick Render Setup – eBay Card Listing Tool

Follow these steps to deploy your app live on Render.

---

## 1. Push to GitHub

If not already:

```bash
cd c:\eBayBot
git add .
git commit -m "Deploy to Render"
git push origin main
```

---

## 2. Create Render Account

1. Go to **[render.com](https://render.com)**
2. Sign up (free)
3. Connect your GitHub account

---

## 3. Deploy the App

**Option A: Blueprint (recommended)**

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New** → **Blueprint**
3. Connect GitHub and select the **eBayBot** repo
4. Render will use `render.yaml`
5. Click **Apply**

**Option B: Manual Web Service**

1. Click **New** → **Web Service**
2. Connect your eBayBot repo
3. Use:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
4. Click **Create**

---

## 4. Add Environment Variables

In your service → **Environment**, add:

| Variable | Value |
|----------|-------|
| `OWNER_EMAIL` | Your login email |
| `ADMIN_PASSWORD` | Password for /admin |
| `SECRET_KEY` | Run: `python -c "import secrets; print(secrets.token_hex(24))"` |
| `EBAY_APP_ID` | Your Production App ID |
| `EBAY_DEV_ID` | Your Dev ID |
| `EBAY_CERT_ID` | Your Production Cert ID |
| `EBAY_PRODUCTION_TOKEN` | Your eBay token |
| `EBAY_ENVIRONMENT` | `production` |
| `SERPAPI_KEY` | Your SerpAPI key (for Market Price) |
| `FULFILLMENT_POLICY_ID` | (optional, from Seller Hub) |
| `PAYMENT_POLICY_ID` | (optional) |
| `RETURN_POLICY_ID` | (optional) |
| `MERCHANT_LOCATION_KEY` | (optional) |

---

## 5. OAuth Redirect (after first deploy)

1. After deploy, copy your app URL: `https://YOUR-SERVICE.onrender.com`
2. Add env var: `OAUTH_REDIRECT_URI` = `https://YOUR-SERVICE.onrender.com/callback`
3. In eBay Developer Portal → Your App → OAuth Redirect URIs → add that same URL

---

## 6. Your Live URL

Once deployed, your app will be at:

**https://YOUR-SERVICE-NAME.onrender.com**

(Service name is from the Render dashboard)

---

## Notes

- **Free tier:** App sleeps after ~15 min idle; first request after sleep may take 30–60 sec
- **SerpAPI:** Needed for Market Price; free tier ≈100 searches/month
- **Secrets:** Never commit `.env`; add variables only in Render Dashboard
