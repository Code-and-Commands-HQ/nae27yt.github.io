#!/usr/bin/env python3
"""
Discord Bot with Enhanced Error Handling and Management
Main entry point for the Discord bot with improved lifecycle management
"""

import discord
from discord.ext import commands
import asyncio
import logging
import os
import sys
import signal
from datetime import datetime
from dotenv import load_dotenv
from bot_config import BotConfig
from utils.postgres_database import PostgreSQLManager
from web_dashboard import WebDashboard

# Load environment variables from .env file
load_dotenv()

# Configure logging with better formatting
logging.basicConfig(
    level=getattr(logging, BotConfig.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BotConfig.LOG_FILE, mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class DiscordBot(commands.Bot):
    """Enhanced Discord Bot class with improved error handling and lifecycle management"""
    
    def __init__(self):
        # Set up bot intents - using only default intents to avoid privileged intent issues
        intents = discord.Intents.default()
        # Note: message_content intent is privileged and requires enabling in Discord Developer Portal
        
        super().__init__(
            command_prefix=BotConfig.COMMAND_PREFIX,
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        
        # Initialize components
        self.db_manager = PostgreSQLManager()
        self.web_dashboard = WebDashboard(self)
        self.startup_time = datetime.now()
        self.command_stats = {}
        self.error_count = 0
        self.last_sync_time = None
        
        # Bot state management
        self.is_shutting_down = False
        self.sync_in_progress = False
        
    async def setup_hook(self):
        """Initialize bot components with enhanced error handling"""
        try:
            logger.info("Starting bot setup...")
            
            # Initialize database
            await self.db_manager.initialize()
            logger.info("Database initialized successfully")
            
            # Load cogs with individual error handling
            cogs_to_load = [
                'cogs.general_commands',
                'cogs.role_management'
            ]
            
            loaded_cogs = []
            for cog in cogs_to_load:
                try:
                    await self.load_extension(cog)
                    loaded_cogs.append(cog)
                    logger.info(f"Successfully loaded cog: {cog}")
                except Exception as e:
                    logger.error(f"Failed to load cog {cog}: {e}")
                    continue
            
            if not loaded_cogs:
                logger.error("No cogs were loaded successfully!")
                return
            
            # Sync slash commands with rate limiting protection
            await self._sync_commands_safely()
            
            # Start web dashboard
            await self.web_dashboard.start()
            logger.info("Web dashboard started on port 5000")
            
        except Exception as e:
            logger.error(f"Critical error in setup_hook: {e}")
            raise
    
    async def _sync_commands_safely(self):
        """Sync commands with built-in rate limiting protection"""
        if self.sync_in_progress:
            logger.warning("Command sync already in progress, skipping...")
            return
            
        try:
            self.sync_in_progress = True
            
            # Check if we synced recently to avoid rate limits
            if self.last_sync_time:
                time_since_sync = (datetime.now() - self.last_sync_time).total_seconds()
                if time_since_sync < 60:  # Don't sync more than once per minute
                    logger.info(f"Skipping sync - last sync was {time_since_sync:.1f}s ago")
                    return
            
            logger.info("Syncing slash commands...")
            synced = await self.tree.sync()
            self.last_sync_time = datetime.now()
            logger.info(f"Successfully synced {len(synced)} slash commands")
            
            # Log command names for debugging
            command_names = [cmd.name for cmd in synced]
            logger.info(f"Synced commands: {', '.join(command_names)}")
            
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited during command sync. Retry after: {e.retry_after}s")
                await asyncio.sleep(e.retry_after)
            else:
                logger.error(f"HTTP error during command sync: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during command sync: {e}")
        finally:
            self.sync_in_progress = False
    
    async def on_ready(self):
        """Called when bot is ready with enhanced logging"""
        logger.info(f"🤖 {self.user} has connected to Discord!")
        logger.info(f"📊 Bot is in {len(self.guilds)} guilds")
        logger.info(f"🏓 Bot latency: {round(self.latency * 1000)}ms")
        
        # Log guild information
        for guild in self.guilds:
            logger.info(f"  📍 Guild: {guild.name} (ID: {guild.id}, Members: {guild.member_count})")
        
        # Set bot activity
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.guilds)} servers | /help"
        )
        await self.change_presence(activity=activity)
        
        # Log startup completion
        startup_duration = (datetime.now() - self.startup_time).total_seconds()
        logger.info(f"✅ Bot startup completed in {startup_duration:.2f}s")
    
    async def on_guild_join(self, guild):
        """Handle joining a new guild"""
        logger.info(f"📥 Joined new guild: {guild.name} (ID: {guild.id}, Members: {guild.member_count})")
        
        # Update presence
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.guilds)} servers | /help"
        )
        await self.change_presence(activity=activity)
    
    async def on_guild_remove(self, guild):
        """Handle leaving a guild"""
        logger.info(f"📤 Left guild: {guild.name} (ID: {guild.id})")
        
        # Clean up guild data
        await self.db_manager.cleanup_guild_data(guild.id)
        
        # Update presence
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.guilds)} servers | /help"
        )
        await self.change_presence(activity=activity)
    
    async def on_app_command_completion(self, interaction: discord.Interaction, command):
        """Track command usage for analytics"""
        command_name = command.name
        if command_name not in self.command_stats:
            self.command_stats[command_name] = 0
        self.command_stats[command_name] += 1
        
        logger.info(f"🔧 Command '{command_name}' used by {interaction.user} in {interaction.guild.name if interaction.guild else 'DM'}")
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """Enhanced global error handler for slash commands"""
        self.error_count += 1
        
        # Log the error with context
        logger.error(f"❌ Slash command error in {interaction.command.name if interaction.command else 'unknown'}: {error}")
        logger.error(f"   User: {interaction.user} | Guild: {interaction.guild.name if interaction.guild else 'DM'}")
        
        try:
            # Handle specific error types
            if isinstance(error, discord.app_commands.CommandOnCooldown):
                await self._handle_cooldown_error(interaction, error)
            elif isinstance(error, discord.app_commands.MissingPermissions):
                await self._handle_permission_error(interaction, error)
            elif isinstance(error, discord.app_commands.BotMissingPermissions):
                await self._handle_bot_permission_error(interaction, error)
            elif isinstance(error, discord.app_commands.CommandNotFound):
                await self._handle_command_not_found(interaction, error)
            else:
                await self._handle_generic_error(interaction, error)
                
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
    
    async def _handle_cooldown_error(self, interaction: discord.Interaction, error):
        """Handle cooldown errors"""
        embed = discord.Embed(
            title="⏰ Command on Cooldown",
            description=f"Please wait {error.retry_after:.1f} seconds before using this command again.",
            color=BotConfig.WARNING_COLOR
        )
        await self._safe_response(interaction, embed=embed, ephemeral=True)
    
    async def _handle_permission_error(self, interaction: discord.Interaction, error):
        """Handle user permission errors"""
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You don't have permission to use this command.",
            color=BotConfig.ERROR_COLOR
        )
        await self._safe_response(interaction, embed=embed, ephemeral=True)
    
    async def _handle_bot_permission_error(self, interaction: discord.Interaction, error):
        """Handle bot permission errors"""
        missing_perms = ', '.join(error.missing_permissions)
        embed = discord.Embed(
            title="🤖 Bot Missing Permissions",
            description=f"I need the following permissions to execute this command:\n`{missing_perms}`",
            color=BotConfig.ERROR_COLOR
        )
        await self._safe_response(interaction, embed=embed, ephemeral=True)
    
    async def _handle_command_not_found(self, interaction: discord.Interaction, error):
        """Handle command not found errors"""
        embed = discord.Embed(
            title="❓ Command Not Found",
            description="This command wasn't found. Try `/help` to see available commands.",
            color=BotConfig.WARNING_COLOR
        )
        await self._safe_response(interaction, embed=embed, ephemeral=True)
    
    async def _handle_generic_error(self, interaction: discord.Interaction, error):
        """Handle generic errors"""
        embed = discord.Embed(
            title="⚠️ An Error Occurred",
            description="An unexpected error occurred. Please try again later.",
            color=BotConfig.ERROR_COLOR
        )
        embed.add_field(name="Error ID", value=f"`{self.error_count}`", inline=False)
        await self._safe_response(interaction, embed=embed, ephemeral=True)
    
    async def _safe_response(self, interaction: discord.Interaction, **kwargs):
        """Safely respond to interaction avoiding timeout errors"""
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(**kwargs)
            else:
                await interaction.followup.send(**kwargs)
        except discord.NotFound:
            logger.warning("Interaction expired - unable to respond")
        except discord.HTTPException as e:
            logger.error(f"HTTP error in safe response: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in safe response: {e}")
    
    async def close(self):
        """Enhanced cleanup on bot shutdown"""
        if self.is_shutting_down:
            return
            
        self.is_shutting_down = True
        logger.info("🛑 Bot shutdown initiated...")
        
        try:
            # Stop web dashboard
            await self.web_dashboard.stop()
            logger.info("Web dashboard stopped")
            
            # Close database connections
            await self.db_manager.close()
            logger.info("Database connections closed")
            
            # Call parent close
            await super().close()
            logger.info("✅ Bot shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

# Global bot instance
bot = None

async def main():
    """Main function to run the bot with enhanced error handling"""
    global bot
    
    # Validate configuration
    config_errors = BotConfig.validate_config()
    if config_errors:
        logger.error("Configuration validation failed:")
        for error in config_errors:
            logger.error(f"  - {error}")
        return
    
    # Validate bot token
    bot_token = os.getenv('DISCORD_BOT_TOKEN')
    if not bot_token:
        logger.error("❌ DISCORD_BOT_TOKEN environment variable is not set!")
        return
    
    # Create bot instance
    bot = DiscordBot()
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(bot.close())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info("🚀 Starting Discord bot...")
        await bot.start(bot_token)
    except discord.LoginFailure:
        logger.error("❌ Invalid bot token provided!")
    except discord.HTTPException as e:
        logger.error(f"❌ HTTP error: {e}")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
    finally:
        if bot and not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
