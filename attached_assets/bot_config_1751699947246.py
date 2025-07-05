"""
Bot Configuration
Contains all configuration settings for the Discord bot
"""

import os
from typing import List

class BotConfig:
    """Configuration class for the Discord bot"""
    
    # Bot settings
    COMMAND_PREFIX = "!"
    BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', '')
    
    # Cooldown settings (in seconds)
    SAY_COOLDOWN = 3
    EMBED_COOLDOWN = 5
    DM_COOLDOWN = 10
    
    # Rate limiting
    MAX_USES_PER_COOLDOWN = 1
    
    # Embed settings
    MAX_EMBED_TITLE_LENGTH = 256
    MAX_EMBED_DESCRIPTION_LENGTH = 4096
    MAX_EMBED_FIELD_NAME_LENGTH = 256
    MAX_EMBED_FIELD_VALUE_LENGTH = 1024
    MAX_EMBED_FIELDS = 25
    
    # Message settings
    MAX_MESSAGE_LENGTH = 2000
    
    # Color settings for embeds
    DEFAULT_EMBED_COLOR = 0x7289da  # Discord blurple
    ERROR_COLOR = 0xff6b6b
    SUCCESS_COLOR = 0x51cf66
    WARNING_COLOR = 0xffd43b
    
    # Permissions
    REQUIRED_PERMISSIONS = [
        'send_messages',
        'embed_links',
        'read_message_history',
        'use_slash_commands',
        'manage_roles'
    ]
    
    # Role management settings
    ROLE_ASSIGNMENT_FILE = 'protected_roles.json'
    ROLE_ASSIGNMENT_LOG_CHANNEL = None  # Set to channel ID for logging
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'bot.log'
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not cls.BOT_TOKEN:
            errors.append("DISCORD_BOT_TOKEN is not set")
        
        if cls.SAY_COOLDOWN < 0:
            errors.append("SAY_COOLDOWN must be non-negative")
        
        if cls.EMBED_COOLDOWN < 0:
            errors.append("EMBED_COOLDOWN must be non-negative")
        
        if cls.DM_COOLDOWN < 0:
            errors.append("DM_COOLDOWN must be non-negative")
        
        return errors
