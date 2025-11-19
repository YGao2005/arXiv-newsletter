# arXiv Papers Discord Bot 📚

> Automated notifications for new arXiv research papers in your Discord server

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.3+-blue.svg)](https://discordpy.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Stay updated with the latest research papers from arXiv. This Discord bot monitors arXiv categories and posts new papers to your server with customizable filtering.

## Status

🚧 **Work in Progress** - This bot is currently a skeleton implementation. Contributions welcome!

## Planned Features

- 📄 **Daily Paper Digests** - Automated notifications for new papers in your areas of interest
- 🎯 **Category Filtering** - Monitor specific arXiv categories (cs.AI, cs.LG, cs.CV, etc.)
- 🔍 **Keyword Matching** - Filter papers by keywords in title/abstract
- 💬 **Interactive Commands** - Search, browse, and get paper recommendations
- 📊 **Paper Summaries** - AI-generated summaries of paper abstracts
- 🔖 **Bookmark System** - Save interesting papers for later reading
- 📈 **Trending Papers** - Track most cited/downloaded papers

## Quick Start

### Prerequisites

- Python 3.11+
- Discord Bot Token ([Create one here](https://discord.com/developers/applications))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/arxiv-papers-bot.git
cd arxiv-papers-bot

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your bot token
```

### Configuration

```bash
# .env
ARXIV_BOT_TOKEN=your_discord_bot_token
ARXIV_CATEGORIES=cs.AI,cs.LG,cs.CV
CHECK_INTERVAL_HOURS=24
```

### Running

```bash
python bot.py
```

## Planned Commands

- `/papers today` - View papers published today
- `/papers search <query>` - Search arXiv by keyword
- `/subscribe <category>` - Subscribe to a category
- `/unsubscribe <category>` - Unsubscribe from a category
- `/categories` - List available arXiv categories
- `/bookmark <paper_id>` - Save a paper for later

## arXiv Categories

Popular categories:
- `cs.AI` - Artificial Intelligence
- `cs.LG` - Machine Learning
- `cs.CV` - Computer Vision
- `cs.CL` - Computation and Language (NLP)
- `cs.RO` - Robotics
- `stat.ML` - Machine Learning (Statistics)

[Full category list](https://arxiv.org/category_taxonomy)

## Architecture

```
arxiv-papers-bot/
├── bot.py              # Main bot logic
├── scrapers/          # arXiv API integration
├── filters/           # Keyword and category filtering
├── utils/             # Paper formatting, summaries
└── database/          # User subscriptions, bookmarks
```

## Deployment Modes

1. **Standalone**: Run as independent bot
2. **Multi-Bot**: Deploy with [discord-bots-launcher](https://github.com/yourusername/discord-bots-launcher)

## Contributing

This is a skeleton project - **contributions highly encouraged!**

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Implement your feature
4. Submit a Pull Request

### Priority Features

- [ ] Implement arXiv API scraping
- [ ] Add daily digest scheduler
- [ ] Create category subscription system
- [ ] Build Discord commands
- [ ] Add paper summaries (using AI)
- [ ] Implement bookmark system

## Resources

- [arXiv API Documentation](https://arxiv.org/help/api)
- [arXiv Python Library](https://github.com/lukasschwab/arxiv.py)
- [Discord.py Documentation](https://discordpy.readthedocs.io/)

## License

MIT License - see [LICENSE](LICENSE) for details

## Acknowledgments

- arXiv for providing free access to scientific papers
- Built with [arxiv.py](https://github.com/lukasschwab/arxiv.py)

---

**Help build the future of academic Discord bots!** | [Contribute](https://github.com/yourusername/arxiv-papers-bot) | [Report Issues](https://github.com/yourusername/arxiv-papers-bot/issues)
