# Quick Start Guide

Get your ArXiv Pulse Bot running in 30 minutes!

## Step-by-Step Checklist

### ☐ 1. Set Up Supabase (5 minutes)

1. Go to [supabase.com](https://supabase.com) and create a project
2. Open SQL Editor in the dashboard
3. Copy contents of `supabase/migrations/001_initial_schema.sql`
4. Paste and run in SQL Editor
5. Go to Settings → API and save:
   - Project URL
   - `anon` key
   - `service_role` key

### ☐ 2. Deploy HuggingFace Space (10 minutes)

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Create new Space (Docker SDK)
3. Upload files from `hf-space/` folder
4. Wait for build (~5-10 minutes)
5. Save the Space URL (e.g., `https://huggingface.co/spaces/username/arxiv-embed-api`)

### ☐ 3. Get API Keys (5 minutes)

**Discord Bot:**
1. [Discord Developer Portal](https://discord.com/developers/applications)
2. New Application → Add Bot → Copy Token
3. OAuth2 → URL Generator → bot + application.commands
4. Invite to server
5. Right-click channel → Copy Channel ID

**Gemini API:**
1. [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create API Key → Copy

### ☐ 4. Configure GitHub Actions (5 minutes)

1. Push code to GitHub:
```bash
cd arxiv-papers-bot
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR-USERNAME/arxiv-papers-bot.git
git push -u origin main
```

2. Add GitHub Secrets (Settings → Secrets and variables → Actions):
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - `GEMINI_API_KEY`
   - `HF_EMBED_API_URL`

3. Enable Actions (Actions tab → Enable)

### ☐ 5. Deploy to Heroku (5 minutes)

```bash
# Install Heroku CLI if needed
brew tap heroku/brew && brew install heroku

# Login and create app
heroku login
heroku create your-app-name

# Set environment variables
heroku config:set ARXIV_BOT_TOKEN=your_token
heroku config:set SUPABASE_URL=your_url
heroku config:set SUPABASE_ANON_KEY=your_key
heroku config:set CHANNEL_ID=your_channel_id
heroku config:set HF_EMBED_API_URL=your_hf_url
heroku config:set MIN_IMPACT_SCORE=7

# Deploy
git push heroku main
heroku ps:scale worker=1

# Check logs
heroku logs --tail
```

### ☐ 6. Test (2 minutes)

**Test the bot:**
1. In Discord, type `/search query: transformers`
2. Should see search results

**Test daily job:**
1. GitHub → Actions → Daily ArXiv Paper Fetch
2. Run workflow manually
3. Check Supabase for new entries

**Test auto-posting:**
1. Wait up to 1 hour (or restart Heroku dyno to trigger immediately)
2. High-impact papers should appear in your channel

---

## Environment Variables Summary

| Variable | Where to Use | Value |
|----------|--------------|-------|
| `ARXIV_BOT_TOKEN` | Heroku | Discord bot token |
| `CHANNEL_ID` | Heroku | Discord channel ID |
| `SUPABASE_URL` | Heroku + GitHub | Supabase project URL |
| `SUPABASE_ANON_KEY` | Heroku | Supabase anon key |
| `SUPABASE_SERVICE_KEY` | GitHub | Supabase service key |
| `HF_EMBED_API_URL` | Heroku + GitHub | HF Space URL |
| `GEMINI_API_KEY` | GitHub | Google AI API key |
| `MIN_IMPACT_SCORE` | Heroku (optional) | 1-10, default 7 |

---

## Verification Commands

```bash
# Check bot is running
heroku logs --tail

# Check GitHub Actions ran successfully
# Go to Actions tab on GitHub

# Check HF Space is running
curl https://your-space.hf.space/

# Check Supabase has data
# Go to Supabase dashboard → Table Editor → papers
```

---

## Common Issues

**Bot shows offline:**
- Check Heroku logs for errors
- Verify `ARXIV_BOT_TOKEN` is correct
- Ensure worker dyno is running: `heroku ps`

**No papers being fetched:**
- Check GitHub Actions logs
- Verify all secrets are set correctly
- Check Gemini API quota (15 req/min limit)

**Search command fails:**
- Verify HF Space is running (not sleeping)
- Check `HF_EMBED_API_URL` is correct
- Test endpoint: `curl https://your-space.hf.space/`

**Database errors:**
- Verify SQL migration ran successfully
- Check Supabase logs in dashboard
- Ensure correct API keys are used

---

## Next Steps

Once everything is working:

1. **Customize** impact score threshold: `heroku config:set MIN_IMPACT_SCORE=8`
2. **Monitor** GitHub Actions runs (daily at 08:00 UTC)
3. **Adjust** posting frequency in `.github/workflows/daily-fetch.yml`
4. **Explore** adding custom tags or categories

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed troubleshooting and advanced configuration.

---

## Cost Breakdown

- Supabase: **$0** (free tier)
- HuggingFace: **$0** (free tier)
- GitHub Actions: **$0** (free tier)
- Gemini API: **$0** (free tier)
- Heroku: **$5-7/month** (Basic/Eco dyno)

**Total: ~$5-7/month**

Enjoy your ArXiv Pulse Bot! 🚀
