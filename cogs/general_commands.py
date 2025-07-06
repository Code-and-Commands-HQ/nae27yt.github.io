"""
General Commands Cog
Contains general utility commands like say, embed, dm, help, ping, etc.
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Union
from bot_config import BotConfig
from utils.validation import ValidationUtils
from utils.embed_utils import EmbedUtils

logger = logging.getLogger(__name__)

class GeneralCommands(commands.Cog, name="General"):
    """General utility commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.command_usage = {}
        
    @app_commands.command(name="say", description="Make the bot say something")
    @app_commands.describe(message="The message to say")
    async def say(self, interaction: discord.Interaction, message: str):
        """Make the bot echo a message"""
        try:
            # Log command usage
            logger.info(f"Say command used by {interaction.user} in {interaction.guild.name if interaction.guild else 'DM'}: {message[:50]}...")
            
            # Validate message
            if not ValidationUtils.validate_message_content(message):
                embed = EmbedUtils.create_error_embed(
                    "Invalid Message",
                    "The message contains invalid content or is too long."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Clean message content
            cleaned_message = ValidationUtils.clean_message_content(message)
            
            # Send the message
            await interaction.response.send_message(cleaned_message)
            
            # Track usage in database
            if hasattr(self.bot, 'db_manager') and self.bot.db_manager.pool:
                await self.bot.db_manager.log_command_usage(
                    "say", 
                    interaction.user.id, 
                    interaction.guild.id if interaction.guild else None
                )
            
        except Exception as e:
            logger.error(f"Error in say command: {e}")
            await self._handle_command_error(interaction, e)
    
    @app_commands.command(name="embed", description="Create a custom embed")
    @app_commands.describe(
        title="The title of the embed",
        description="The description of the embed", 
        color="The color of the embed (hex format: #FF0000 or name: red)"
    )
    async def embed(self, interaction: discord.Interaction, title: str, description: str, color: Optional[str] = None):
        """Create a custom embed"""
        try:
            logger.info(f"Embed command used by {interaction.user} in {interaction.guild.name if interaction.guild else 'DM'}: {title[:30]}...")
            
            # Validate embed content
            if not ValidationUtils.validate_embed_content(title, description):
                embed = EmbedUtils.create_error_embed(
                    "Invalid Embed Content",
                    "The title or description is too long or contains invalid content."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Parse color
            embed_color = EmbedUtils.parse_color(color) if color else BotConfig.DEFAULT_EMBED_COLOR
            
            # Create embed
            embed = discord.Embed(
                title=title,
                description=description,
                color=embed_color,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Add footer with user info
            embed.set_footer(
                text=f"Created by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Track usage in database
            if hasattr(self.bot, 'db_manager') and self.bot.db_manager.pool:
                await self.bot.db_manager.log_command_usage(
                    "embed", 
                    interaction.user.id, 
                    interaction.guild.id if interaction.guild else None
                )
            
        except Exception as e:
            logger.error(f"Error in embed command: {e}")
            await self._handle_command_error(interaction, e)
    
    @app_commands.command(name="dm", description="Send a direct message to a user")
    @app_commands.describe(
        user="The user to send the message to",
        message="The message to send"
    )

    async def dm(self, interaction: discord.Interaction, user: discord.User, message: str):
        """Send a direct message to a user"""
        try:
            logger.info(f"DM sent by {interaction.user} to {user} in {interaction.guild.name if interaction.guild else 'DM'}")
            
            # Validate message
            if not ValidationUtils.validate_message_content(message):
                embed = EmbedUtils.create_error_embed(
                    "Invalid Message",
                    "The message contains invalid content or is too long."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Don't allow DMing bots
            if user.bot:
                embed = EmbedUtils.create_error_embed(
                    "Cannot DM Bot",
                    "You cannot send direct messages to bots."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Don't allow DMing self
            if user == interaction.user:
                embed = EmbedUtils.create_error_embed(
                    "Cannot DM Yourself",
                    "You cannot send a direct message to yourself."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create DM embed
            dm_embed = discord.Embed(
                title="📨 Message from " + interaction.user.display_name,
                description=message,
                color=BotConfig.INFO_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            
            if interaction.guild:
                dm_embed.add_field(
                    name="Server",
                    value=interaction.guild.name,
                    inline=True
                )
            
            dm_embed.set_footer(
                text="This message was sent via bot",
                icon_url=self.bot.user.display_avatar.url
            )
            
            # Try to send the DM
            try:
                await user.send(embed=dm_embed)
                
                # Confirm to sender
                confirm_embed = EmbedUtils.create_success_embed(
                    "Message Sent",
                    f"Your message has been sent to {user.display_name}."
                )
                await interaction.response.send_message(embed=confirm_embed, ephemeral=True)
                
            except discord.Forbidden:
                embed = EmbedUtils.create_error_embed(
                    "Cannot Send DM",
                    f"{user.display_name} has DMs disabled or has blocked the bot."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Track usage
            self._track_command_usage("dm", interaction.user.id)
            
        except Exception as e:
            logger.error(f"Error in dm command: {e}")
            await self._handle_command_error(interaction, e)
    
    @app_commands.command(name="help", description="Get help with bot commands")
    @app_commands.describe(command="Get help for a specific command")
    
    async def help(self, interaction: discord.Interaction, command: Optional[str] = None):
        """Display help information"""
        try:
            logger.info(f"Help command used by {interaction.user}")
            
            if command:
                # Get help for specific command
                embed = await self._get_command_help(command)
            else:
                # Get general help
                embed = await self._get_general_help()
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            await self._handle_command_error(interaction, e)
    
    @app_commands.command(name="ping", description="Check bot latency and status")
    
    async def ping(self, interaction: discord.Interaction):
        """Check bot latency and status"""
        try:
            logger.info(f"Ping command used by {interaction.user}")
            
            # Calculate latency
            latency = round(self.bot.latency * 1000)
            
            # Get bot uptime
            uptime = datetime.now() - self.bot.startup_time
            uptime_str = str(uptime).split('.')[0]  # Remove microseconds
            
            # Create ping embed
            embed = discord.Embed(
                title="🏓 Pong!",
                color=BotConfig.SUCCESS_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="Latency",
                value=f"{latency}ms",
                inline=True
            )
            
            embed.add_field(
                name="Uptime",
                value=uptime_str,
                inline=True
            )
            
            embed.add_field(
                name="Guilds",
                value=str(len(self.bot.guilds)),
                inline=True
            )
            
            # Add status indicator
            if latency < 100:
                status = "🟢 Excellent"
            elif latency < 200:
                status = "🟡 Good"
            else:
                status = "🔴 Poor"
            
            embed.add_field(
                name="Status",
                value=status,
                inline=True
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in ping command: {e}")
            await self._handle_command_error(interaction, e)
    
    @app_commands.command(name="serverinfo", description="Get information about the current server")
    
    async def serverinfo(self, interaction: discord.Interaction):
        """Get detailed server information"""
        try:
            if not interaction.guild:
                embed = EmbedUtils.create_error_embed(
                    "No Server",
                    "This command can only be used in a server."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            logger.info(f"Server info command used by {interaction.user} in {interaction.guild.name}")
            
            guild = interaction.guild
            
            # Create server info embed
            embed = discord.Embed(
                title=f"📊 Server Information",
                description=f"Information about **{guild.name}**",
                color=BotConfig.INFO_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Set server icon
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            
            # Basic info
            embed.add_field(
                name="Server ID",
                value=f"`{guild.id}`",
                inline=True
            )
            
            embed.add_field(
                name="Owner",
                value=guild.owner.mention if guild.owner else "Unknown",
                inline=True
            )
            
            embed.add_field(
                name="Created",
                value=guild.created_at.strftime("%B %d, %Y"),
                inline=True
            )
            
            # Member stats
            embed.add_field(
                name="Members",
                value=f"{guild.member_count:,}",
                inline=True
            )
            
            embed.add_field(
                name="Channels",
                value=f"{len(guild.channels):,}",
                inline=True
            )
            
            embed.add_field(
                name="Roles",
                value=f"{len(guild.roles):,}",
                inline=True
            )
            
            # Additional info
            embed.add_field(
                name="Verification Level",
                value=guild.verification_level.name.title(),
                inline=True
            )
            
            embed.add_field(
                name="Boost Level",
                value=f"Level {guild.premium_tier}",
                inline=True
            )
            
            embed.add_field(
                name="Boosts",
                value=f"{guild.premium_subscription_count:,}",
                inline=True
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in serverinfo command: {e}")
            await self._handle_command_error(interaction, e)
    
    @app_commands.command(name="userinfo", description="Get information about a user")
    @app_commands.describe(user="The user to get information about (defaults to yourself)")
    
    async def userinfo(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """Get detailed user information"""
        try:
            target_user = user or interaction.user
            logger.info(f"User info command used by {interaction.user} for {target_user}")
            
            # Create user info embed
            embed = discord.Embed(
                title=f"👤 User Information",
                description=f"Information about **{target_user.display_name}**",
                color=BotConfig.INFO_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Set user avatar
            embed.set_thumbnail(url=target_user.display_avatar.url)
            
            # Basic info
            embed.add_field(
                name="Username",
                value=f"{target_user.name}#{target_user.discriminator}",
                inline=True
            )
            
            embed.add_field(
                name="User ID",
                value=f"`{target_user.id}`",
                inline=True
            )
            
            embed.add_field(
                name="Bot",
                value="Yes" if target_user.bot else "No",
                inline=True
            )
            
            # Account creation
            embed.add_field(
                name="Account Created",
                value=target_user.created_at.strftime("%B %d, %Y"),
                inline=True
            )
            
            # Server-specific info (if in a guild)
            if interaction.guild and isinstance(target_user, discord.Member):
                embed.add_field(
                    name="Joined Server",
                    value=target_user.joined_at.strftime("%B %d, %Y") if target_user.joined_at else "Unknown",
                    inline=True
                )
                
                # Roles (limit to top 10)
                roles = [role.mention for role in target_user.roles[1:]]  # Skip @everyone
                if roles:
                    roles_text = ", ".join(roles[:10])
                    if len(roles) > 10:
                        roles_text += f" and {len(roles) - 10} more..."
                    embed.add_field(
                        name=f"Roles ({len(roles)})",
                        value=roles_text,
                        inline=False
                    )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in userinfo command: {e}")
            await self._handle_command_error(interaction, e)
    
    async def _get_general_help(self) -> discord.Embed:
        """Get general help embed"""
        embed = discord.Embed(
            title="🤖 Bot Help",
            description="Here are all the available commands:",
            color=BotConfig.INFO_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        
        # General commands
        embed.add_field(
            name="📝 General Commands",
            value="`/say` - Make the bot say something\n"
                  "`/embed` - Create a custom embed\n"
                  "`/dm` - Send a direct message to a user\n"
                  "`/help` - Show this help message",
            inline=False
        )
        
        # Utility commands
        embed.add_field(
            name="🔧 Utility Commands",
            value="`/ping` - Check bot latency\n"
                  "`/serverinfo` - Get server information\n"
                  "`/userinfo` - Get user information",
            inline=False
        )
        
        # Role management commands
        embed.add_field(
            name="🎭 Role Management",
            value="`/protect-role` - Protect a role\n"
                  "`/assign-role` - Assign a protected role\n"
                  "`/unprotect-role` - Unprotect a role\n"
                  "`/list-protected-roles` - List protected roles",
            inline=False
        )
        
        embed.set_footer(
            text="Use /help <command> for detailed help on a specific command",
            icon_url=self.bot.user.display_avatar.url
        )
        
        return embed
    
    async def _get_command_help(self, command_name: str) -> discord.Embed:
        """Get help for a specific command"""
        command_help = {
            "say": {
                "description": "Make the bot echo any message you want",
                "usage": "/say <message>",
                "cooldown": f"{BotConfig.SAY_COOLDOWN}s",
                "examples": ["/say Hello everyone!"]
            },
            "embed": {
                "description": "Create custom embeds with optional colors",
                "usage": "/embed <title> <description> [color]",
                "cooldown": f"{BotConfig.EMBED_COOLDOWN}s",
                "examples": ["/embed \"My Title\" \"My Description\" #FF0000"]
            },
            "dm": {
                "description": "Send direct messages to users through the bot",
                "usage": "/dm <user> <message>",
                "cooldown": f"{BotConfig.DM_COOLDOWN}s",
                "examples": ["/dm @user Hello there!"]
            },
            "ping": {
                "description": "Check bot latency and response time",
                "usage": "/ping",
                "cooldown": f"{BotConfig.INFO_COOLDOWN}s",
                "examples": ["/ping"]
            },
            "serverinfo": {
                "description": "Get detailed information about the current server",
                "usage": "/serverinfo",
                "cooldown": f"{BotConfig.INFO_COOLDOWN}s",
                "examples": ["/serverinfo"]
            },
            "userinfo": {
                "description": "Get information about any user",
                "usage": "/userinfo [user]",
                "cooldown": f"{BotConfig.INFO_COOLDOWN}s",
                "examples": ["/userinfo", "/userinfo @user"]
            }
        }
        
        if command_name.lower() not in command_help:
            return EmbedUtils.create_error_embed(
                "Command Not Found",
                f"No help available for command `{command_name}`"
            )
        
        cmd_info = command_help[command_name.lower()]
        
        embed = discord.Embed(
            title=f"📚 Help: /{command_name}",
            description=cmd_info["description"],
            color=BotConfig.INFO_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="Usage",
            value=f"`{cmd_info['usage']}`",
            inline=False
        )
        
        embed.add_field(
            name="Cooldown",
            value=cmd_info["cooldown"],
            inline=True
        )
        
        if cmd_info["examples"]:
            embed.add_field(
                name="Examples",
                value="\n".join(f"`{example}`" for example in cmd_info["examples"]),
                inline=False
            )
        
        return embed
    
    def _track_command_usage(self, command_name: str, user_id: int):
        """Track command usage for analytics"""
        if command_name not in self.command_usage:
            self.command_usage[command_name] = []
        
        self.command_usage[command_name].append({
            'user_id': user_id,
            'timestamp': datetime.now(timezone.utc)
        })
    
    async def _handle_command_error(self, interaction: discord.Interaction, error: Exception):
        """Handle command errors safely"""
        embed = EmbedUtils.create_error_embed(
            "Command Error",
            "An error occurred while executing this command. Please try again later."
        )
        
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in error handler: {e}")

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(GeneralCommands(bot))
    logger.info("General commands cog loaded successfully")
