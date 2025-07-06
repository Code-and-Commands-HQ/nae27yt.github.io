"""
Embed utilities for Discord bot
Contains functions for creating and managing Discord embeds
"""

import discord
from datetime import datetime, timezone
from typing import Optional, Union
from bot_config import BotConfig

class EmbedUtils:
    """Utility class for embed creation and management"""
    
    @staticmethod
    def create_error_embed(title: str, description: str) -> discord.Embed:
        """
        Create an error embed
        
        Args:
            title: Error title
            description: Error description
            
        Returns:
            discord.Embed: Error embed
        """
        embed = discord.Embed(
            title=f"❌ {title}",
            description=description,
            color=BotConfig.ERROR_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        return embed
    
    @staticmethod
    def create_success_embed(title: str, description: str) -> discord.Embed:
        """
        Create a success embed
        
        Args:
            title: Success title
            description: Success description
            
        Returns:
            discord.Embed: Success embed
        """
        embed = discord.Embed(
            title=f"✅ {title}",
            description=description,
            color=BotConfig.SUCCESS_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        return embed
    
    @staticmethod
    def create_warning_embed(title: str, description: str) -> discord.Embed:
        """
        Create a warning embed
        
        Args:
            title: Warning title
            description: Warning description
            
        Returns:
            discord.Embed: Warning embed
        """
        embed = discord.Embed(
            title=f"⚠️ {title}",
            description=description,
            color=BotConfig.WARNING_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        return embed
    
    @staticmethod
    def create_info_embed(title: str, description: str) -> discord.Embed:
        """
        Create an info embed
        
        Args:
            title: Info title
            description: Info description
            
        Returns:
            discord.Embed: Info embed
        """
        embed = discord.Embed(
            title=f"ℹ️ {title}",
            description=description,
            color=BotConfig.INFO_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        return embed
    
    @staticmethod
    def parse_color(color_string: str) -> int:
        """
        Parse color string to Discord color integer
        
        Args:
            color_string: Color string (hex or name)
            
        Returns:
            int: Color integer
        """
        if not color_string:
            return BotConfig.DEFAULT_EMBED_COLOR
        
        # Named colors
        named_colors = {
            'red': 0xFF0000,
            'green': 0x00FF00,
            'blue': 0x0000FF,
            'yellow': 0xFFFF00,
            'orange': 0xFFA500,
            'purple': 0x800080,
            'pink': 0xFFC0CB,
            'black': 0x000000,
            'white': 0xFFFFFF,
            'gray': 0x808080,
            'grey': 0x808080,
            'cyan': 0x00FFFF,
            'magenta': 0xFF00FF,
            'lime': 0x00FF00,
            'brown': 0xA52A2A,
            'navy': 0x000080,
            'olive': 0x808000,
            'teal': 0x008080,
            'silver': 0xC0C0C0,
            'maroon': 0x800000,
            'discord': BotConfig.DEFAULT_EMBED_COLOR,
            'blurple': BotConfig.DEFAULT_EMBED_COLOR
        }
        
        # Check named colors first
        if color_string.lower() in named_colors:
            return named_colors[color_string.lower()]
        
        # Try hex format
        try:
            # Remove # if present
            hex_color = color_string.lstrip('#')
            
            # Validate hex format
            if len(hex_color) == 6 and all(c in '0123456789abcdefABCDEF' for c in hex_color):
                return int(hex_color, 16)
        except ValueError:
            pass
        
        # Return default if parsing fails
        return BotConfig.DEFAULT_EMBED_COLOR
    
    @staticmethod
    def create_paginated_embed(
        title: str,
        items: list,
        items_per_page: int = 10,
        page: int = 1,
        color: int = None
    ) -> discord.Embed:
        """
        Create a paginated embed
        
        Args:
            title: Embed title
            items: List of items to paginate
            items_per_page: Items per page
            page: Current page number
            color: Embed color
            
        Returns:
            discord.Embed: Paginated embed
        """
        if color is None:
            color = BotConfig.DEFAULT_EMBED_COLOR
        
        total_pages = (len(items) + items_per_page - 1) // items_per_page
        page = max(1, min(page, total_pages))
        
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page
        page_items = items[start_index:end_index]
        
        embed = discord.Embed(
            title=title,
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        
        if page_items:
            embed.description = '\n'.join(page_items)
        else:
            embed.description = "No items found."
        
        embed.set_footer(text=f"Page {page}/{total_pages} • Total items: {len(items)}")
        
        return embed
    
    @staticmethod
    def create_stats_embed(
        title: str,
        stats: dict,
        color: int = None
    ) -> discord.Embed:
        """
        Create a statistics embed
        
        Args:
            title: Embed title
            stats: Dictionary of statistics
            color: Embed color
            
        Returns:
            discord.Embed: Statistics embed
        """
        if color is None:
            color = BotConfig.INFO_COLOR
        
        embed = discord.Embed(
            title=title,
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        
        for key, value in stats.items():
            embed.add_field(
                name=key,
                value=str(value),
                inline=True
            )
        
        return embed
    
    @staticmethod
    def create_user_embed(user: discord.User, additional_info: dict = None) -> discord.Embed:
        """
        Create a user information embed
        
        Args:
            user: Discord user
            additional_info: Additional information dictionary
            
        Returns:
            discord.Embed: User embed
        """
        embed = discord.Embed(
            title=f"User: {user.display_name}",
            color=BotConfig.INFO_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        embed.add_field(
            name="Username",
            value=f"{user.name}#{user.discriminator}",
            inline=True
        )
        
        embed.add_field(
            name="ID",
            value=f"`{user.id}`",
            inline=True
        )
        
        embed.add_field(
            name="Created",
            value=user.created_at.strftime("%B %d, %Y"),
            inline=True
        )
        
        embed.add_field(
            name="Bot",
            value="Yes" if user.bot else "No",
            inline=True
        )
        
        if additional_info:
            for key, value in additional_info.items():
                embed.add_field(
                    name=key,
                    value=str(value),
                    inline=True
                )
        
        return embed
    
    @staticmethod
    def create_guild_embed(guild: discord.Guild) -> discord.Embed:
        """
        Create a guild information embed
        
        Args:
            guild: Discord guild
            
        Returns:
            discord.Embed: Guild embed
        """
        embed = discord.Embed(
            title=f"Server: {guild.name}",
            color=BotConfig.INFO_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(
            name="ID",
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
        
        embed.add_field(
            name="Verification",
            value=guild.verification_level.name.title(),
            inline=True
        )
        
        return embed
    
    @staticmethod
    def truncate_text(text: str, max_length: int) -> str:
        """
        Truncate text to fit within Discord limits
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            
        Returns:
            str: Truncated text
        """
        if len(text) <= max_length:
            return text
        
        return text[:max_length - 3] + "..."
    
    @staticmethod
    def format_list(items: list, numbered: bool = False) -> str:
        """
        Format a list for embed display
        
        Args:
            items: List of items
            numbered: Whether to number the items
            
        Returns:
            str: Formatted list
        """
        if not items:
            return "None"
        
        if numbered:
            return '\n'.join(f"{i+1}. {item}" for i, item in enumerate(items))
        else:
            return '\n'.join(f"• {item}" for item in items)
    
    @staticmethod
    def validate_embed_limits(embed: discord.Embed) -> tuple[bool, list]:
        """
        Validate embed against Discord limits
        
        Args:
            embed: Embed to validate
            
        Returns:
            tuple: (is_valid, errors)
        """
        errors = []
        
        # Title limit
        if embed.title and len(embed.title) > BotConfig.MAX_EMBED_TITLE_LENGTH:
            errors.append(f"Title exceeds {BotConfig.MAX_EMBED_TITLE_LENGTH} characters")
        
        # Description limit
        if embed.description and len(embed.description) > BotConfig.MAX_EMBED_DESCRIPTION_LENGTH:
            errors.append(f"Description exceeds {BotConfig.MAX_EMBED_DESCRIPTION_LENGTH} characters")
        
        # Field limits
        if len(embed.fields) > BotConfig.MAX_EMBED_FIELDS:
            errors.append(f"Too many fields (max {BotConfig.MAX_EMBED_FIELDS})")
        
        for field in embed.fields:
            if len(field.name) > BotConfig.MAX_EMBED_FIELD_NAME_LENGTH:
                errors.append(f"Field name exceeds {BotConfig.MAX_EMBED_FIELD_NAME_LENGTH} characters")
            if len(field.value) > BotConfig.MAX_EMBED_FIELD_VALUE_LENGTH:
                errors.append(f"Field value exceeds {BotConfig.MAX_EMBED_FIELD_VALUE_LENGTH} characters")
        
        # Footer limit
        if embed.footer and embed.footer.text and len(embed.footer.text) > BotConfig.MAX_EMBED_FOOTER_LENGTH:
            errors.append(f"Footer exceeds {BotConfig.MAX_EMBED_FOOTER_LENGTH} characters")
        
        # Total character limit (6000)
        total_chars = 0
        if embed.title:
            total_chars += len(embed.title)
        if embed.description:
            total_chars += len(embed.description)
        if embed.footer and embed.footer.text:
            total_chars += len(embed.footer.text)
        
        for field in embed.fields:
            total_chars += len(field.name) + len(field.value)
        
        if total_chars > 6000:
            errors.append("Total embed characters exceed 6000")
        
        return len(errors) == 0, errors
