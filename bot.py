#!/usr/bin/env python3
"""
arXiv Papers Discord Bot
Monitors arXiv for new research papers and sends notifications to Discord
"""

import os
import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()


class ArxivBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        # Note: message_content intent not needed for slash commands
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        """Called when the bot is starting up"""
        await self.tree.sync()

    async def on_ready(self):
        """Called when the bot is ready"""
        print(f'✓ arXiv Papers Bot logged in as {self.user}')
        print(f'  Bot ID: {self.user.id}')
        print('-' * 60)


def create_bot():
    """Factory function to create and return the bot instance"""
    return ArxivBot()


if __name__ == "__main__":
    # For standalone testing
    bot = create_bot()
    token = os.getenv('ARXIV_BOT_TOKEN')

    if not token:
        print("❌ ARXIV_BOT_TOKEN not found in environment")
        exit(1)

    bot.run(token)
