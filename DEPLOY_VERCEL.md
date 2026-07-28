# Deploy CardLister Pro to Vercel

## Important: Read this first

**Vercel is not better than Render for “always active” for this app.**

| | Render Free | Render Starter ($7) | Vercel Free/Hobby |
|--|-------------|---------------------|-------------------|
| Spins down when idle | Yes (~15 min) | No | Cold starts still happen |
| File storage (subscriptions, referrals, tokens) | Ephemeral on redeploy | Better with disk add-on | **Broken** — serverless FS is ephemeral |
| Long eBay listing jobs | Works with gunicorn timeout | Works | **60s max** on Hobby |
| Best for this Flask app | Temporary | **Recommended** | Not recommended |

**Recommendation for always-on:** Keep Render and upgrade the instance to **Starter ($7/month)**. That stops the sleep/spin-down without rewriting the app.

If you still want to try Vercel (preview / testing only), follow below — but subscriptions/referrals/tokens will not reliably persist without a database.

---

## Try Vercel (optional)

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import `mrbiggles524/eBayBot`
3. Framework: Flask (auto-detected from `app.py` + `requirements.txt`)
4. Add the same Environment Variables as on Render
5. Deploy

After deploy, set OAuth redirect to:
```
https://YOUR-PROJECT.vercel.app/callback
```
in both Vercel env (`OAUTH_REDIRECT_URI`) and eBay Developer Portal.

---

## Always-on on Render (recommended)

1. Open your eBayBot service on Render
2. **Settings** → **Instance Type** → change **Free** → **Starter** ($7/mo)
3. Save / redeploy

Your URL stays the same. No code changes. No spin-down.
