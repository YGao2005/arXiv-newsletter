# arXiv Pulse Bot 📚🤖

> AI-powered research paper discovery with semantic search and impact scoring

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.3+-blue.svg)](https://discordpy.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Discover breakthrough research papers from arXiv with AI-powered impact scoring and semantic search. Get daily updates on high-impact papers directly in your Discord server.

## Features

✨ **AI Impact Scoring** - Papers rated 1-10 by Google Gemini based on significance
🔍 **Semantic Search** - Find papers by meaning, not just keywords
📰 **Smart Daily Feed** - Auto-posts high-impact papers (customizable threshold)
🏷️ **Auto-Tagging** - Papers automatically categorized (CV, NLP, LLM, etc.)
📊 **Rich Embeds** - Beautiful paper cards with summaries and metadata
⚡ **Slash Commands** - Modern Discord interface with `/search`, `/latest`, `/stats`

## Architecture

### Split-Brain Design

This bot uses a **split-brain architecture** to maximize free tier resources:

### Shared Database Support 🔄

**NEW:** This bot is designed to share a Supabase database with other bots! All tables use the `arxiv_` prefix to avoid conflicts.

Perfect for multi-bot setups where you've hit Supabase's 2-project free tier limit. See [SHARED_DATABASE.md](SHARED_DATABASE.md) for details.

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  GitHub Actions │────▶│   Supabase   │◀────│ Discord Bot │
│  (Daily Fetch)  │     │  (Database)  │     │  (Heroku)   │
│  - Fetch papers │     │  - pgvector  │     │  - Commands │
│  - AI scoring   │     │  - RLS       │     │  - Feed     │
└─────────────────┘     └──────────────┘     └─────────────┘
         │                                             │
         ▼                                             ▼
┌─────────────────┐                           ┌─────────────┐
│  HF Space API   │◀──────────────────────────│  /search    │
│  (Embeddings)   │                           │  command    │
└─────────────────┘                           └─────────────┘
```

**Why this architecture?**
- GitHub Actions handles heavy ML processing (free 2000 min/month)
- HuggingFace Space provides embedding API (free CPU tier)
- Supabase stores papers with vector search (free 500MB)
- Heroku runs lightweight bot 24/7 ($5-7/month)

**Total cost: ~$5-7/month** (only Heroku paid)

## Quick Start

### Prerequisites

You'll need accounts for:
- [Discord Developer Portal](https://discord.com/developers/applications) - Bot token
- [Supabase](https://supabase.com) - PostgreSQL database with pgvector
- [Google AI Studio](https://makersuite.google.com) - Gemini API key
- [HuggingFace](https://huggingface.co) - Embedding API hosting
- [Heroku](https://heroku.com) - Bot hosting ($5-7/month)
- [GitHub](https://github.com) - For Actions (free)

### Deployment

**See [DEPLOYMENT.md](DEPLOYMENT.md) for complete step-by-step instructions.**

Quick overview:
1. Set up Supabase database (apply SQL migrations)
2. Deploy HuggingFace Space (embedding API)
3. Configure GitHub Actions (daily paper fetching)
4. Deploy bot to Heroku
5. Test with `/search transformers`

### Local Development

```bash
# Clone and install
git clone https://github.com/yourusername/arxiv-papers-bot.git
cd arxiv-papers-bot
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run bot locally
python bot.py
```

## Commands

### `/search <query> [limit]`
Semantic search for papers using AI embeddings.

**Example:**
```
/search query: transformers for computer vision
/search query: efficient language models limit: 10
```

### `/latest [limit]`
Show the most recently published papers.

**Example:**
```
/latest
/latest limit: 10
```

### `/stats`
Show bot statistics (total papers, posted count, high-impact count).

## How It Works

### Daily Paper Fetching (GitHub Actions)
1. Runs every day at 08:00 UTC
2. Queries arXiv for yesterday's CS papers
3. Generates 384-dim embeddings using sentence-transformers
4. Scores papers 1-10 with Gemini (impact, novelty, significance)
5. Creates one-sentence summaries and auto-tags
6. Stores in Supabase with vector embeddings

### Automatic Feed Posting (Discord Bot)
1. Checks database every hour
2. Finds unposted papers with score ≥ 7 (configurable)
3. Posts rich embeds to designated channel
4. Marks as posted to avoid duplicates

### Semantic Search (`/search`)
1. User query → HF Space → 384-dim embedding
2. Supabase pgvector cosine similarity search
3. Returns top matches with similarity scores
4. Fallback to full-text search if no results

## Project Structure

```
arxiv-papers-bot/
├── bot.py                      # Discord bot (Heroku)
├── requirements.txt            # Bot dependencies
├── Procfile                    # Heroku config
├── .env.example               # Environment template
├── supabase/
│   ├── migrations/
│   │   └── 001_initial_schema.sql  # Database setup
│   └── README.md              # Database docs
├── hf-space/                  # HuggingFace Space
│   ├── app.py                 # Flask embedding API
│   ├── Dockerfile             # Container config
│   ├── requirements.txt       # API dependencies
│   └── README.md              # API docs
├── .github/
│   └── workflows/
│       ├── daily-fetch.yml    # GitHub Actions config
│       ├── fetch_papers.py    # Paper fetching script
│       └── requirements.txt   # Fetcher dependencies
├── DEPLOYMENT.md              # Step-by-step deployment guide
└── README.md                  # This file
```

## Environment Variables

### Discord Bot (Heroku)
- `ARXIV_BOT_TOKEN` - Discord bot token
- `CHANNEL_ID` - Channel for posting papers
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anon/public key
- `HF_EMBED_API_URL` - HuggingFace Space URL
- `MIN_IMPACT_SCORE` - Threshold for auto-posting (default: 7)

### GitHub Actions
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_KEY` - Supabase service role key
- `GEMINI_API_KEY` - Google Gemini API key
- `HF_EMBED_API_URL` - HuggingFace Space URL

## Customization

### Adjust Impact Score Threshold
```bash
heroku config:set MIN_IMPACT_SCORE=8  # Only post very high-impact papers
```

### Change Posting Frequency
Edit `.github/workflows/daily-fetch.yml`:
```yaml
schedule:
  - cron: '0 8 * * *'  # Change time (currently 08:00 UTC)
```

### Modify Tags
Edit `.github/workflows/fetch_papers.py` in the Gemini prompt:
```python
tags = ["CV", "NLP", "LLM", "RL", "Your-Custom-Tag"]
```

### Customize Embed Colors
Edit `bot.py` in the `create_paper_embed` function:
```python
if paper['impact_score'] >= 9:
    color = discord.Color.gold()  # Change colors here
```

## Future Enhancements

Potential features to add:
- [ ] User-specific subscriptions (tags, authors, keywords)
- [ ] Weekly digest summaries
- [ ] Paper recommendation engine
- [ ] Integration with other sources (OpenReview, PapersWithCode)
- [ ] Author alerts (follow specific researchers)
- [ ] Citation tracking
- [ ] Related papers suggestions

## Troubleshooting

### Bot not responding to commands
- Check Heroku logs: `heroku logs --tail`
- Verify bot has necessary permissions in Discord
- Ensure slash commands are synced (restart bot)

### Papers not being fetched
- Check GitHub Actions logs
- Verify Gemini API key and rate limits
- Ensure HF Space is running

### Search not working
- Check if HF Space is sleeping (test endpoint)
- Verify `HF_EMBED_API_URL` is correct
- Check Heroku logs for errors

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed troubleshooting.

## Tech Stack

- **Discord Bot**: discord.py 2.3+
- **Database**: Supabase (PostgreSQL + pgvector)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **AI Scoring**: Google Gemini 1.5 Flash
- **API Hosting**: HuggingFace Spaces (Docker)
- **Automation**: GitHub Actions
- **Hosting**: Heroku

## Resources

- [arXiv API Documentation](https://arxiv.org/help/api)
- [Supabase pgvector Guide](https://supabase.com/docs/guides/ai/vector-columns)
- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Sentence Transformers](https://www.sbert.net/)

## License

MIT License - Free to use, modify, and distribute.

## Acknowledgments

- arXiv for free access to research papers
- Supabase for pgvector support
- HuggingFace for free ML hosting
- Google for Gemini API free tier

---

**Built with ❤️ for the research community** | [Report Issues](https://github.com/yourusername/arxiv-papers-bot/issues) | [Contribute](https://github.com/yourusername/arxiv-papers-bot)
