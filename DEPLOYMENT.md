# ArXiv Papers Bot - Deployment Guide

Complete step-by-step deployment guide for the hybrid architecture.

## Architecture Overview

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  GitHub Actions │────▶│   Supabase   │◀────│ Discord Bot │
│  (Daily Fetch)  │     │  (Database)  │     │  (Heroku)   │
└─────────────────┘     └──────────────┘     └─────────────┘
         │                                             │
         ▼                                             ▼
┌─────────────────┐                           ┌─────────────┐
│  HF Space API   │◀──────────────────────────│  /search    │
│  (Embeddings)   │                           │  command    │
└─────────────────┘                           └─────────────┘
```

## Prerequisites

Before starting, create accounts and get credentials for:

1. **Discord Developer Portal** → Bot Token
2. **Supabase** → Database URL + API Keys
3. **Google AI Studio** → Gemini API Key
4. **HuggingFace** → Account (for Spaces)
5. **Heroku** → Account
6. **GitHub** → Repository for the code

---

## Step 1: Discord Bot Setup

### 1.1 Create Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application**
3. Name it "ArXiv Papers Bot"
4. Go to **Bot** tab → Click **Add Bot**
5. Under **Token**, click **Reset Token** and copy it
   - ⚠️ Save this as `ARXIV_BOT_TOKEN`
6. Scroll to **Privileged Gateway Intents**
   - **Do NOT** enable any intents (we only use slash commands)

### 1.2 Invite Bot to Server

1. Go to **OAuth2** → **URL Generator**
2. Select scopes:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Select bot permissions:
   - ✅ Send Messages
   - ✅ Embed Links
   - ✅ Read Message History
4. Copy the generated URL
5. Open it in browser and invite to your server

### 1.3 Get Channel ID

1. Enable Developer Mode in Discord:
   - User Settings → Advanced → Developer Mode
2. Right-click the channel where you want papers posted
3. Click **Copy Channel ID**
   - ⚠️ Save this as `CHANNEL_ID`

---

## Step 2: Supabase Setup

### 2.1 Create Project

1. Go to [Supabase](https://supabase.com)
2. Click **New Project**
3. Fill in:
   - **Name**: `arxiv-papers-bot`
   - **Database Password**: Generate a strong password
   - **Region**: Choose closest to your users
4. Click **Create Project** (wait ~2 minutes)

### 2.2 Apply Database Migration

1. In Supabase dashboard, go to **SQL Editor**
2. Open `supabase/migrations/001_initial_schema.sql` from this repo
3. Copy the entire contents
4. Paste into SQL Editor
5. Click **Run** (Cmd/Ctrl + Enter)
6. Verify: Should see "Success. No rows returned"

### 2.3 Get API Keys

1. Go to **Project Settings** → **API**
2. Copy these values:
   - **URL** → Save as `SUPABASE_URL`
   - **anon public** key → Save as `SUPABASE_ANON_KEY`
   - **service_role** key → Save as `SUPABASE_SERVICE_KEY`

⚠️ **SECURITY**: Never commit `SUPABASE_SERVICE_KEY` to Git!

---

## Step 3: HuggingFace Space (Embedding API)

### 3.1 Create Space

1. Go to [HuggingFace Spaces](https://huggingface.co/spaces)
2. Click **Create new Space**
3. Fill in:
   - **Name**: `arxiv-embed-api` (or your choice)
   - **License**: MIT
   - **SDK**: Docker
   - **Hardware**: CPU basic (free)
4. Click **Create Space**

### 3.2 Upload Files

Upload these files from `hf-space/` directory:
- `app.py`
- `requirements.txt`
- `Dockerfile`
- `README.md`

You can either:
- Use the web interface (drag & drop)
- Use Git (clone, add files, commit, push)

### 3.3 Wait for Build

1. HuggingFace will automatically build the Docker image
2. Wait ~5-10 minutes for first build
3. Once running, you'll see "Running" status
4. Test the endpoint:
   - Click on the Space URL
   - Should see a JSON response with `"status": "healthy"`

### 3.4 Get API URL

The URL will be: `https://huggingface.co/spaces/YOUR-USERNAME/arxiv-embed-api`

⚠️ Save this as `HF_EMBED_API_URL`

---

## Step 4: Google Gemini API

### 4.1 Get API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click **Create API Key**
3. Select a Google Cloud project (or create new)
4. Copy the API key
   - ⚠️ Save as `GEMINI_API_KEY`

### 4.2 Verify Free Tier

The free tier includes:
- 15 requests per minute
- 1,500 requests per day
- Sufficient for ~100-200 papers/day

---

## Step 5: GitHub Actions Setup

### 5.1 Push Code to GitHub

```bash
cd arxiv-papers-bot
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/arxiv-papers-bot.git
git push -u origin main
```

### 5.2 Add GitHub Secrets

1. Go to your repo on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these secrets:

| Name | Value |
|------|-------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Your Supabase service role key |
| `GEMINI_API_KEY` | Your Gemini API key |
| `HF_EMBED_API_URL` | Your HuggingFace Space URL |

### 5.3 Enable Actions

1. Go to **Actions** tab
2. Click **I understand my workflows, go ahead and enable them**

### 5.4 Test the Workflow

Manually trigger the workflow:
1. Go to **Actions** → **Daily ArXiv Paper Fetch**
2. Click **Run workflow** → **Run workflow**
3. Watch the logs to ensure it completes successfully

---

## Step 6: Heroku Deployment

### 6.1 Install Heroku CLI

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Windows
# Download installer from https://devcenter.heroku.com/articles/heroku-cli
```

### 6.2 Login to Heroku

```bash
heroku login
```

### 6.3 Create Heroku App

```bash
cd arxiv-papers-bot
heroku create arxiv-papers-bot-YOUR-NAME
```

### 6.4 Set Environment Variables

```bash
heroku config:set ARXIV_BOT_TOKEN=your_discord_token
heroku config:set SUPABASE_URL=your_supabase_url
heroku config:set SUPABASE_ANON_KEY=your_anon_key
heroku config:set CHANNEL_ID=your_channel_id
heroku config:set HF_EMBED_API_URL=your_hf_space_url
heroku config:set MIN_IMPACT_SCORE=7
```

### 6.5 Deploy to Heroku

```bash
git push heroku main
```

### 6.6 Scale the Worker

```bash
heroku ps:scale worker=1
```

### 6.7 Check Logs

```bash
heroku logs --tail
```

You should see:
```
✓ arXiv Papers Bot logged in as ArXiv Papers Bot#1234
  Bot ID: 1234567890
  Feed Channel ID: 9876543210
```

---

## Step 7: Verification & Testing

### 7.1 Test Slash Commands

In Discord, type `/` and you should see:
- `/search` - Search for papers
- `/latest` - Show latest papers
- `/stats` - Show bot statistics

Try: `/search query: transformers for computer vision`

### 7.2 Test Daily Job

The GitHub Actions workflow runs daily at 08:00 UTC. To test manually:
1. Go to GitHub → Actions → Daily ArXiv Paper Fetch
2. Click **Run workflow**
3. Monitor the logs
4. Check Supabase to see new papers added

### 7.3 Test Auto-Posting

After the daily job runs:
1. Wait up to 1 hour (bot checks hourly)
2. High-impact papers (score ≥ 7) should appear in Discord
3. Check the designated channel

---

## Maintenance

### Update Dependencies

```bash
# Update bot dependencies
pip install --upgrade -r requirements.txt

# Commit and redeploy
git add requirements.txt
git commit -m "Update dependencies"
git push heroku main
```

### Monitor Costs

All services should remain free if you stay within limits:
- **Supabase**: 500MB database, 2GB bandwidth/month
- **HuggingFace**: CPU basic space (sleeps after inactivity)
- **GitHub Actions**: 2,000 minutes/month
- **Heroku**: Basic dyno ($7/month) or Eco ($5/month)
- **Gemini**: 1,500 requests/day

### Adjust Impact Score Threshold

To change which papers get posted:

```bash
heroku config:set MIN_IMPACT_SCORE=8  # Only post very high impact
```

### Check Logs

```bash
# Heroku logs
heroku logs --tail

# GitHub Actions logs
# Check on GitHub Actions tab

# HuggingFace logs
# Check on Space settings → Logs
```

---

## Troubleshooting

### Bot Not Responding to Commands

1. Check Heroku logs: `heroku logs --tail`
2. Verify bot is online in Discord
3. Ensure channel permissions are correct
4. Re-sync commands: Restart the dyno

### Papers Not Being Fetched

1. Check GitHub Actions logs
2. Verify Gemini API key is valid
3. Check rate limits (15 req/min)
4. Verify HF Space is running

### Embedding Service Down

1. Check HF Space status
2. Verify Space hasn't been paused
3. Test endpoint: `curl https://your-space.hf.space/`

### Database Errors

1. Check Supabase dashboard for errors
2. Verify RLS policies are correct
3. Check API key permissions

---

## Cost Breakdown

| Service | Free Tier | Estimated Usage | Cost |
|---------|-----------|-----------------|------|
| Supabase | 500MB DB | ~100MB/month | $0 |
| HF Spaces | CPU Basic | Always-on | $0 |
| GitHub Actions | 2000 min/month | ~30 min/month | $0 |
| Heroku | N/A | 24/7 dyno | $5-7/month |
| Gemini API | 1500 req/day | ~100 req/day | $0 |
| **Total** | | | **$5-7/month** |

The only paid service is Heroku. Everything else stays free!

---

## Next Steps

- Set up monitoring/alerts
- Add more slash commands
- Customize impact scoring logic
- Add paper categories/filters
- Implement user preferences

Enjoy your ArXiv Papers Bot! 🚀
