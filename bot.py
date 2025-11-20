#!/usr/bin/env python3
"""
arXiv Papers Discord Bot
Monitors arXiv for new research papers and sends notifications to Discord
"""

import os
import sys
import requests
from datetime import datetime
from typing import Optional, List, Dict

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Configuration
DISCORD_TOKEN = os.getenv('ARXIV_BOT_TOKEN')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')  # Use anon key for read operations
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '0'))
HF_EMBED_API_URL = os.getenv('HF_EMBED_API_URL')
MIN_IMPACT_SCORE = int(os.getenv('MIN_IMPACT_SCORE', '7'))

# Validate environment
if not all([DISCORD_TOKEN, SUPABASE_URL, SUPABASE_KEY, CHANNEL_ID, HF_EMBED_API_URL]):
    print("❌ Missing required environment variables!")
    print(f"   ARXIV_BOT_TOKEN: {'✓' if DISCORD_TOKEN else '✗'}")
    print(f"   SUPABASE_URL: {'✓' if SUPABASE_URL else '✗'}")
    print(f"   SUPABASE_ANON_KEY: {'✓' if SUPABASE_KEY else '✗'}")
    print(f"   CHANNEL_ID: {'✓' if CHANNEL_ID else '✗'}")
    print(f"   HF_EMBED_API_URL: {'✓' if HF_EMBED_API_URL else '✗'}")
    sys.exit(1)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class ArxivBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix='!', intents=intents)
        self.feed_channel: Optional[discord.TextChannel] = None

    async def setup_hook(self):
        """Called when the bot is starting up"""
        # Register slash commands
        await self.tree.sync()

        # Start background tasks
        self.post_papers_task.start()

        print("✓ Bot setup complete")

    async def on_ready(self):
        """Called when the bot is ready"""
        print(f'✓ arXiv Papers Bot logged in as {self.user}')
        print(f'  Bot ID: {self.user.id}')
        print(f'  Feed Channel ID: {CHANNEL_ID}')
        print(f'  Min Impact Score: {MIN_IMPACT_SCORE}')
        print('-' * 60)

        # Get the feed channel
        self.feed_channel = self.get_channel(CHANNEL_ID)
        if not self.feed_channel:
            print(f'⚠️  Warning: Could not find channel with ID {CHANNEL_ID}')

    @tasks.loop(minutes=60)
    async def post_papers_task(self):
        """
        Background task that runs every hour to check for new papers to post
        """
        try:
            if not self.feed_channel:
                print("⚠️  Feed channel not set, skipping post check")
                return

            print(f"\n🔍 Checking for unposted papers (score >= {MIN_IMPACT_SCORE})...")

            # Query Supabase for unposted high-impact papers
            response = supabase.rpc(
                'arxiv_get_unposted_papers',
                {'min_impact_score': MIN_IMPACT_SCORE}
            ).execute()

            papers = response.data

            if not papers:
                print("   No new papers to post")
                return

            print(f"   Found {len(papers)} paper(s) to post")

            # Post each paper
            for paper in papers:
                try:
                    embed = create_paper_embed(paper)
                    await self.feed_channel.send(embed=embed)

                    # Mark as posted in database
                    supabase.table('arxiv_papers').update({
                        'posted_to_discord': True,
                        'last_posted_at': datetime.utcnow().isoformat()
                    }).eq('id', paper['id']).execute()

                    print(f"   ✓ Posted: {paper['title'][:50]}...")

                except Exception as e:
                    print(f"   ❌ Error posting paper {paper['id']}: {e}")
                    continue

        except Exception as e:
            print(f"❌ Error in post_papers_task: {e}")

    @post_papers_task.before_loop
    async def before_post_papers_task(self):
        """Wait until bot is ready before starting the task"""
        await self.wait_until_ready()


def create_paper_embed(paper: Dict) -> discord.Embed:
    """
    Create a rich embed for a paper
    """
    # Determine color based on impact score
    if paper['impact_score'] >= 9:
        color = discord.Color.gold()
    elif paper['impact_score'] >= 7:
        color = discord.Color.blue()
    else:
        color = discord.Color.greyple()

    # Create embed
    embed = discord.Embed(
        title=paper['title'],
        url=paper['url'],
        description=paper['summary'],
        color=color,
        timestamp=datetime.fromisoformat(paper['published_at'])
    )

    # Add fields
    embed.add_field(
        name="Impact Score",
        value=f"{'⭐' * paper['impact_score']} {paper['impact_score']}/10",
        inline=True
    )

    if paper.get('tags'):
        embed.add_field(
            name="Tags",
            value=" • ".join(f"`{tag}`" for tag in paper['tags']),
            inline=True
        )

    embed.add_field(
        name="ArXiv ID",
        value=f"`{paper['arxiv_id']}`",
        inline=True
    )

    embed.set_footer(text="ArXiv Papers Bot")

    return embed


def get_embedding(text: str) -> Optional[List[float]]:
    """
    Get embedding from HuggingFace Space API
    """
    try:
        response = requests.post(
            f"{HF_EMBED_API_URL}/embed",
            json={"text": text},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data['embedding']
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None


def create_bot():
    """Factory function to create and return the bot instance"""
    bot = ArxivBot()

    @bot.tree.command(name="search", description="Search for papers by semantic similarity")
    @app_commands.describe(
        query="What are you looking for? (e.g., 'transformers for computer vision')",
        limit="Number of results to return (1-20)"
    )
    async def search(interaction: discord.Interaction, query: str, limit: int = 5):
        """
        Search papers using semantic vector similarity
        """
        await interaction.response.defer(thinking=True)

        try:
            # Validate limit
            limit = max(1, min(20, limit))

            # Get embedding for query
            embedding = get_embedding(query)

            if not embedding:
                await interaction.followup.send(
                    "❌ Failed to generate embedding. The embedding service might be down.",
                    ephemeral=True
                )
                return

            # Search Supabase using vector similarity
            response = supabase.rpc(
                'arxiv_match_papers',
                {
                    'query_embedding': embedding,
                    'match_threshold': 0.3,
                    'match_count': limit
                }
            ).execute()

            papers = response.data

            if not papers:
                # Fallback to full-text search
                response = supabase.rpc(
                    'arxiv_search_papers_fulltext',
                    {
                        'search_query': query,
                        'match_count': limit
                    }
                ).execute()
                papers = response.data

                if not papers:
                    await interaction.followup.send(
                        f"No papers found for query: `{query}`\nTry different keywords or a broader search.",
                        ephemeral=True
                    )
                    return

            # Create embed with results
            embed = discord.Embed(
                title=f"🔍 Search Results for: {query}",
                description=f"Found {len(papers)} paper(s)",
                color=discord.Color.blue()
            )

            for i, paper in enumerate(papers, 1):
                similarity_text = ""
                if 'similarity' in paper and paper['similarity']:
                    similarity_pct = paper['similarity'] * 100
                    similarity_text = f" ({similarity_pct:.1f}% match)"

                score_stars = "⭐" * (paper.get('impact_score', 5))

                embed.add_field(
                    name=f"{i}. {paper['title'][:100]}{'...' if len(paper['title']) > 100 else ''}",
                    value=(
                        f"{paper.get('summary', 'No summary available')[:150]}...\n"
                        f"**Score:** {score_stars} {paper.get('impact_score', '?')}/10{similarity_text}\n"
                        f"**Link:** {paper['url']}"
                    ),
                    inline=False
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error in /search command: {e}")
            await interaction.followup.send(
                f"❌ An error occurred while searching: {str(e)}",
                ephemeral=True
            )

    @bot.tree.command(name="latest", description="Show the latest papers from arXiv")
    @app_commands.describe(limit="Number of papers to show (1-10)")
    async def latest(interaction: discord.Interaction, limit: int = 5):
        """
        Show the latest papers from the database
        """
        await interaction.response.defer(thinking=True)

        try:
            # Validate limit
            limit = max(1, min(10, limit))

            # Query latest papers
            response = supabase.table('arxiv_papers').select('*').order(
                'published_at', desc=True
            ).limit(limit).execute()

            papers = response.data

            if not papers:
                await interaction.followup.send(
                    "No papers found in the database yet. Check back later!",
                    ephemeral=True
                )
                return

            # Create embed
            embed = discord.Embed(
                title="📰 Latest Papers",
                description=f"Showing {len(papers)} most recent paper(s)",
                color=discord.Color.green()
            )

            for paper in papers:
                score_stars = "⭐" * (paper.get('impact_score', 5))
                tags_text = " • ".join(f"`{tag}`" for tag in paper.get('tags', [])) if paper.get('tags') else "N/A"

                embed.add_field(
                    name=paper['title'],
                    value=(
                        f"{paper.get('summary', 'No summary available')}\n"
                        f"**Score:** {score_stars} {paper.get('impact_score', '?')}/10\n"
                        f"**Tags:** {tags_text}\n"
                        f"**Link:** {paper['url']}"
                    ),
                    inline=False
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error in /latest command: {e}")
            await interaction.followup.send(
                f"❌ An error occurred: {str(e)}",
                ephemeral=True
            )

    @bot.tree.command(name="stats", description="Show bot statistics")
    async def stats(interaction: discord.Interaction):
        """
        Show statistics about the papers database
        """
        try:
            # Get total papers count
            total_response = supabase.table('arxiv_papers').select('id', count='exact').execute()
            total_count = total_response.count

            # Get posted count
            posted_response = supabase.table('arxiv_papers').select(
                'id', count='exact'
            ).eq('posted_to_discord', True).execute()
            posted_count = posted_response.count

            # Get high-impact count
            high_impact_response = supabase.table('arxiv_papers').select(
                'id', count='exact'
            ).gte('impact_score', 8).execute()
            high_impact_count = high_impact_response.count

            # Create embed
            embed = discord.Embed(
                title="📊 Bot Statistics",
                color=discord.Color.purple()
            )

            embed.add_field(name="Total Papers", value=f"{total_count:,}", inline=True)
            embed.add_field(name="Posted to Discord", value=f"{posted_count:,}", inline=True)
            embed.add_field(name="High Impact (8+)", value=f"{high_impact_count:,}", inline=True)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            print(f"Error in /stats command: {e}")
            await interaction.response.send_message(
                f"❌ An error occurred: {str(e)}",
                ephemeral=True
            )

    return bot


if __name__ == "__main__":
    bot = create_bot()
    bot.run(DISCORD_TOKEN)
