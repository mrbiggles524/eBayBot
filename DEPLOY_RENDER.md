# Deploy eBay Card Listing Tool to Render (Free Tier)

Render offers a **free tier** for Web Services. Your app will spin down after ~15 minutes of inactivity and spin up on the next request (cold start ~30–60 seconds).

**Multi-user:** Each subscriber uses their own eBay account. They connect via Setup → Connect eBay or paste their token.

---

## Prerequisites

1. **GitHub account** – Push your project to a GitHub repo
2. **Render account** – Sign up at [render.com](https://render.com) (free)
3. **eBay Developer credentials** – App ID, Dev ID, Cert ID, and token (see below)

---

## Owner Setup (manhattanbreaks / You)

As the owner, add these in Render **Environment** (Dashboard → Your Service → Environment):

| Variable | Required | Example / Notes |
|----------|----------|-----------------|
| `OWNER_EMAIL` | Yes | Your login email (e.g. `manhattanbreaks@gmail.com`) |
| `ADMIN_PASSWORD` | Yes | Password for `/admin` (choose a strong one) |
| `SECRET_KEY` | Yes | `python -c "import secrets; print(secrets.token_hex(24))"` |
| `EBAY_APP_ID` | Yes | Your eBay Production App ID |
| `EBAY_DEV_ID` | Yes | Your eBay Dev ID |
| `EBAY_CERT_ID` | Yes | Your eBay Cert ID |
| `EBAY_PRODUCTION_TOKEN` | Yes | Your eBay token (or use OAuth) |
| `EBAY_ENVIRONMENT` | Yes | `production` |
| `PAYPAL_EMAIL` | Optional | For subscription payments |

**OAuth for subscribers:** After first deploy, set:

- `OAUTH_REDIRECT_URI` = `https://YOUR-SERVICE-NAME.onrender.com/callback`
- In eBay Developer Portal → Your App → OAuth Redirect URIs: add that same URL

---

## Option A: One-Click with `render.yaml` (Recommended)

If your repo is on GitHub and contains `render.yaml`:

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New** → **Blueprint**
3. Connect your GitHub account and select the `eBayBot` repository
4. Render will detect `render.yaml` and create the service
5. Add environment variables (see below)
6. Click **Apply**

---

## Option B: Manual Setup

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New** → **Web Service**
3. Connect your GitHub repo (or use a public repo URL)
4. Configure:
   - **Name:** `ebay-card-listing-tool` (or any name)
   - **Region:** Oregon (US West) or closest to you
   - **Branch:** `main` (or your default branch)
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
5. Click **Create Web Service**

---

## Environment Variables (Owner)

In your Render service, go to **Environment** and add the variables listed in **Owner Setup** above.  
After the first deploy, add `OAUTH_REDIRECT_URI` with your Render URL so subscribers can use “Connect eBay”:

```
OAUTH_REDIRECT_URI=https://your-app-name.onrender.com/callback
```

Add that exact URL in eBay Developer Portal → Application Keys → OAuth Redirect URIs.

---

## Free Tier Limits

- **750 hours/month** (enough for one always-on service that sleeps when idle)
- **Spins down** after ~15 minutes of no traffic
- **Cold start** ~30–60 seconds on first request after sleep
- **512 MB RAM**, shared CPU

**Note:** On the free tier, `subscriptions.json` and `user_tokens.json` are stored on the ephemeral filesystem. They persist between requests but may be reset on a new deploy. For production, consider upgrading to use persistent disk or a database.

---

## Troubleshooting

**App won’t start**
- Confirm `gunicorn` and `Flask` are in `requirements.txt`
- Check **Logs** in the Render dashboard for build or runtime errors

**502 Bad Gateway**
- Service may still be starting; wait 1–2 minutes and try again

**Environment variables**
- Ensure no extra spaces or quotes in the values
- Check that keys match your code (e.g. `EBAY_APP_ID`)

---

## Local Testing Before Deploy

To mimic Render locally:

```bash
pip install gunicorn
gunicorn app:app --bind 0.0.0.0:5001
```

Then open `http://localhost:5001`.
