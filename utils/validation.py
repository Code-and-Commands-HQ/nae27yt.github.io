"""
Validation utilities for Discord bot
Contains functions for validating user input and permissions
"""

import discord
import re
from typing import Optional, Union
from bot_config import BotConfig

class ValidationUtils:
    """Utility class for validation functions"""
    
    @staticmethod
    def validate_message_content(content: str) -> bool:
        """
        Validate message content for safety and length
        
        Args:
            content: Message content to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not content or not content.strip():
            return False
            
        # Check length
        if len(content) > BotConfig.MAX_MESSAGE_LENGTH:
            return False
        
        # Check for dangerous content
        dangerous_patterns = [
            r'@everyone',
            r'@here',
            r'<@&\d+>',  # Role mentions
            r'discord\.gg/\w+',  # Discord invites
            r'https?://discord\.com/invite/\w+',  # Discord invites
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return False
        
        return True
    
    @staticmethod
    def clean_message_content(content: str) -> str:
        """
        Clean message content by removing/escaping dangerous elements
        
        Args:
            content: Content to clean
            
        Returns:
            str: Cleaned content
        """
        # Remove @everyone and @here
        content = re.sub(r'@everyone', '@ everyone', content, flags=re.IGNORECASE)
        content = re.sub(r'@here', '@ here', content, flags=re.IGNORECASE)
        
        # Escape role mentions
        content = re.sub(r'<@&(\d+)>', r'<@ &\1>', content)
        
        # Remove excess whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content
    
    @staticmethod
    def validate_embed_content(title: str, description: str) -> bool:
        """
        Validate embed content for Discord limits
        
        Args:
            title: Embed title
            description: Embed description
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Check title length
        if len(title) > BotConfig.MAX_EMBED_TITLE_LENGTH:
            return False
        
        # Check description length
        if len(description) > BotConfig.MAX_EMBED_DESCRIPTION_LENGTH:
            return False
        
        # Check for empty content
        if not title.strip() or not description.strip():
            return False
        
        return True
    
    @staticmethod
    def validate_dm_content(content: str) -> bool:
        """
        Validate DM content with stricter rules
        
        Args:
            content: DM content to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not content or not content.strip():
            return False
            
        # Check length
        if len(content) > BotConfig.MAX_DM_MESSAGE_LENGTH:
            return False
        
        # Stricter content filtering for DMs
        forbidden_patterns = [
            r'@everyone',
            r'@here',
            r'<@&\d+>',
            r'discord\.gg/\w+',
            r'https?://discord\.com/invite/\w+',
            r'https?://bit\.ly/\w+',  # Shortened URLs
            r'https?://tinyurl\.com/\w+',  # Shortened URLs
        ]
        
        for pattern in forbidden_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return False
        
        return True
    
    @staticmethod
    def can_manage_role(bot_member: discord.Member, role: discord.Role) -> bool:
        """
        Check if bot can manage a specific role
        
        Args:
            bot_member: Bot's member object
            role: Role to check
            
        Returns:
            bool: True if bot can manage the role
        """
        # Bot needs manage_roles permission
        if not bot_member.guild_permissions.manage_roles:
            return False
        
        # Role must be below bot's highest role
        if role >= bot_member.top_role:
            return False
        
        # Cannot manage @everyone role
        if role.is_default():
            return False
        
        return True
    
    @staticmethod
    def can_user_manage_role(user: discord.Member, role: discord.Role) -> bool:
        """
        Check if user can manage a specific role
        
        Args:
            user: User to check
            role: Role to check
            
        Returns:
            bool: True if user can manage the role
        """
        # User needs manage_roles permission
        if not user.guild_permissions.manage_roles:
            return False
        
        # Role must be below user's highest role (unless owner)
        if user != user.guild.owner and role >= user.top_role:
            return False
        
        # Cannot manage @everyone role
        if role.is_default():
            return False
        
        return True
    
    @staticmethod
    def validate_color_string(color_string: str) -> bool:
        """
        Validate color string format
        
        Args:
            color_string: Color string to validate
            
        Returns:
            bool: True if valid color format
        """
        if not color_string:
            return False
        
        # Check hex format
        if re.match(r'^#?[0-9a-fA-F]{6}$', color_string):
            return True
        
        # Check named colors
        named_colors = [
            'red', 'green', 'blue', 'yellow', 'orange', 'purple', 'pink',
            'black', 'white', 'gray', 'grey', 'cyan', 'magenta', 'lime',
            'brown', 'navy', 'olive', 'teal', 'silver', 'maroon'
        ]
        
        return color_string.lower() in named_colors
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for safe file operations
        
        Args:
            filename: Filename to sanitize
            
        Returns:
            str: Sanitized filename
        """
        # Remove dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip('. ')
        
        # Limit length
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        return sanitized
    
    @staticmethod
    def validate_user_permissions(user: discord.Member, required_permissions: list) -> tuple[bool, list]:
        """
        Validate user has required permissions
        
        Args:
            user: User to check
            required_permissions: List of required permission names
            
        Returns:
            tuple: (has_permissions, missing_permissions)
        """
        missing_permissions = []
        
        for perm_name in required_permissions:
            if not getattr(user.guild_permissions, perm_name, False):
                missing_permissions.append(perm_name)
        
        return len(missing_permissions) == 0, missing_permissions
    
    @staticmethod
    def validate_bot_permissions(bot_member: discord.Member, required_permissions: list) -> tuple[bool, list]:
        """
        Validate bot has required permissions
        
        Args:
            bot_member: Bot's member object
            required_permissions: List of required permission names
            
        Returns:
            tuple: (has_permissions, missing_permissions)
        """
        missing_permissions = []
        
        for perm_name in required_permissions:
            if not getattr(bot_member.guild_permissions, perm_name, False):
                missing_permissions.append(perm_name)
        
        return len(missing_permissions) == 0, missing_permissions
    
    @staticmethod
    def is_valid_discord_id(discord_id: Union[str, int]) -> bool:
        """
        Check if a string/int is a valid Discord ID
        
        Args:
            discord_id: ID to validate
            
        Returns:
            bool: True if valid Discord ID
        """
        try:
            id_int = int(discord_id)
            # Discord IDs are 64-bit integers
            return 0 < id_int < (2**63)
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def format_permissions(permissions: list) -> str:
        """
        Format permission list for display
        
        Args:
            permissions: List of permission names
            
        Returns:
            str: Formatted permission string
        """
        if not permissions:
            return "None"
        
        formatted = []
        for perm in permissions:
            # Convert snake_case to Title Case
            formatted_perm = perm.replace('_', ' ').title()
            formatted.append(formatted_perm)
        
        return ', '.join(formatted)
