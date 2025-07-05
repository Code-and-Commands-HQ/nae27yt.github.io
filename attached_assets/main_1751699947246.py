#!/usr/bin/env python3
"""
Discord Bot with Slash Commands
Main entry point for the Discord bot with /say, /embed, and /dm commands
"""

import discord
from discord.ext import commands
import asyncio
import logging
import os
from bot_config import BotConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DiscordBot(commands.Bot):
    """Custom Discord Bot class with enhanced functionality"""
    
    def __init__(self):
        # Set up bot intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix=BotConfig.COMMAND_PREFIX,
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        
    async def setup_hook(self):
        """Initialize bot components"""
        try:
            # Load cogs
            await self.load_extension('cogs.general_commands')
            await self.load_extension('cogs.role_management')
            
            # Sync slash commands
            logger.info("Syncing slash commands...")
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
            
        except Exception as e:
            logger.error(f"Error in setup_hook: {e}")
            raise
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"{self.user} has connected to Discord!")
        logger.info(f"Bot is in {len(self.guilds)} guilds")
        
        # Set bot activity
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name="slash commands"
        )
        await self.change_presence(activity=activity)
        
    async def on_command_error(self, ctx, error):
        """Global error handler for commands"""
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Command is on cooldown. Try again in {error.retry_after:.2f} seconds.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("I don't have the necessary permissions to execute this command.")
        else:
            logger.error(f"Unexpected error: {error}")
            await ctx.send("An unexpected error occurred. Please try again later.")
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """Global error handler for slash commands"""
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"Command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
                ephemeral=True
            )
        elif isinstance(error, discord.app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You don't have permission to use this command.",
                ephemeral=True
            )
        elif isinstance(error, discord.app_commands.BotMissingPermissions):
            await interaction.response.send_message(
                "I don't have the necessary permissions to execute this command.",
                ephemeral=True
            )
        else:
            logger.error(f"Unexpected slash command error: {error}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "An unexpected error occurred. Please try again later.",
                    ephemeral=True
                )

async def main():
    """Main function to run the bot"""
    # Validate bot token
    bot_token = os.getenv('DISCORD_BOT_TOKEN')
    if not bot_token:
        logger.error("DISCORD_BOT_TOKEN environment variable is not set!")
        return
    
    # Create and run bot
    bot = DiscordBot()
    
    try:
        await bot.start(bot_token)
    except discord.LoginFailure:
        logger.error("Invalid bot token provided!")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
