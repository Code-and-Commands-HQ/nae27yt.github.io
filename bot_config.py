"""
Enhanced Bot Configuration
Contains all configuration settings for the Discord bot with validation
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class BotConfig:
    """Enhanced configuration class for the Discord bot"""
    
    # Bot settings
    COMMAND_PREFIX = os.getenv('BOT_COMMAND_PREFIX', '!')
    BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', '')
    
    # Cooldown settings (in seconds)
    SAY_COOLDOWN = 5
    EMBED_COOLDOWN = 10
    DM_COOLDOWN = 15
    ROLE_COOLDOWN = 30
    INFO_COOLDOWN = 3
    
    # Rate limiting
    MAX_USES_PER_COOLDOWN = 1
    COMMAND_SYNC_COOLDOWN = 60  # Minimum time between command syncs
    
    # Embed settings
    MAX_EMBED_TITLE_LENGTH = 256
    MAX_EMBED_DESCRIPTION_LENGTH = 4096
    MAX_EMBED_FIELD_NAME_LENGTH = 256
    MAX_EMBED_FIELD_VALUE_LENGTH = 1024
    MAX_EMBED_FIELDS = 25
    MAX_EMBED_FOOTER_LENGTH = 2048
    
    # Message settings
    MAX_MESSAGE_LENGTH = 2000
    MAX_DM_MESSAGE_LENGTH = 2000
    
    # Color settings for embeds
    DEFAULT_EMBED_COLOR = 0x7289da  # Discord blurple
    ERROR_COLOR = 0xff5555
    SUCCESS_COLOR = 0x50fa7b
    WARNING_COLOR = 0xffb86c
    INFO_COLOR = 0x8be9fd
    
    # Permission settings
    REQUIRED_PERMISSIONS = [
        'send_messages',
        'embed_links',
        'read_message_history',
        'use_slash_commands',
        'manage_roles',
        'view_channel'
    ]
    
    # Database settings
    DATABASE_PATH = 'bot_data.db'
    DATABASE_BACKUP_INTERVAL = 3600  # 1 hour
    
    # Role management settings
    ROLE_ASSIGNMENT_LOG_CHANNEL = None  # Set to channel ID for logging
    MAX_PROTECTED_ROLES_PER_GUILD = 50
    ROLE_HIERARCHY_PROTECTION = True
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'bot.log')
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Web dashboard settings
    DASHBOARD_HOST = os.getenv('DASHBOARD_HOST', '0.0.0.0')
    DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', '5000'))
    DASHBOARD_DEBUG = os.getenv('DASHBOARD_DEBUG', 'False').lower() == 'true'
    
    # Security settings
    ALLOWED_FILE_EXTENSIONS = ['.txt', '.log', '.json']
    MAX_FILE_SIZE = 8 * 1024 * 1024  # 8MB
    
    # Performance settings
    INTERACTION_TIMEOUT = 15  # seconds
    COMMAND_CLEANUP_INTERVAL = 300  # 5 minutes
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Bot token validation
        if not cls.BOT_TOKEN:
            errors.append("DISCORD_BOT_TOKEN environment variable is not set")
        elif len(cls.BOT_TOKEN) < 50:
            errors.append("DISCORD_BOT_TOKEN appears to be invalid (too short)")
        
        # Cooldown validation
        cooldown_settings = [
            ('SAY_COOLDOWN', cls.SAY_COOLDOWN),
            ('EMBED_COOLDOWN', cls.EMBED_COOLDOWN),
            ('DM_COOLDOWN', cls.DM_COOLDOWN),
            ('ROLE_COOLDOWN', cls.ROLE_COOLDOWN),
            ('INFO_COOLDOWN', cls.INFO_COOLDOWN)
        ]
        
        for setting_name, value in cooldown_settings:
            if not isinstance(value, (int, float)) or value < 0:
                errors.append(f"{setting_name} must be a non-negative number")
        
        # Embed limits validation
        embed_limits = [
            ('MAX_EMBED_TITLE_LENGTH', cls.MAX_EMBED_TITLE_LENGTH, 256),
            ('MAX_EMBED_DESCRIPTION_LENGTH', cls.MAX_EMBED_DESCRIPTION_LENGTH, 4096),
            ('MAX_EMBED_FIELD_NAME_LENGTH', cls.MAX_EMBED_FIELD_NAME_LENGTH, 256),
            ('MAX_EMBED_FIELD_VALUE_LENGTH', cls.MAX_EMBED_FIELD_VALUE_LENGTH, 1024),
            ('MAX_EMBED_FIELDS', cls.MAX_EMBED_FIELDS, 25)
        ]
        
        for setting_name, value, max_allowed in embed_limits:
            if not isinstance(value, int) or value <= 0:
                errors.append(f"{setting_name} must be a positive integer")
            elif value > max_allowed:
                errors.append(f"{setting_name} cannot exceed {max_allowed} (Discord limit)")
        
        # Color validation
        color_settings = [
            ('DEFAULT_EMBED_COLOR', cls.DEFAULT_EMBED_COLOR),
            ('ERROR_COLOR', cls.ERROR_COLOR),
            ('SUCCESS_COLOR', cls.SUCCESS_COLOR),
            ('WARNING_COLOR', cls.WARNING_COLOR),
            ('INFO_COLOR', cls.INFO_COLOR)
        ]
        
        for setting_name, value in color_settings:
            if not isinstance(value, int) or value < 0 or value > 0xFFFFFF:
                errors.append(f"{setting_name} must be a valid hex color (0x000000 to 0xFFFFFF)")
        
        # Database path validation
        if not cls.DATABASE_PATH:
            errors.append("DATABASE_PATH cannot be empty")
        
        # Port validation
        if not isinstance(cls.DASHBOARD_PORT, int) or cls.DASHBOARD_PORT <= 0 or cls.DASHBOARD_PORT > 65535:
            errors.append("DASHBOARD_PORT must be a valid port number (1-65535)")
        
        return errors
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Get configuration as dictionary for debugging"""
        return {
            'command_prefix': cls.COMMAND_PREFIX,
            'cooldowns': {
                'say': cls.SAY_COOLDOWN,
                'embed': cls.EMBED_COOLDOWN,
                'dm': cls.DM_COOLDOWN,
                'role': cls.ROLE_COOLDOWN,
                'info': cls.INFO_COOLDOWN
            },
            'embed_limits': {
                'title': cls.MAX_EMBED_TITLE_LENGTH,
                'description': cls.MAX_EMBED_DESCRIPTION_LENGTH,
                'field_name': cls.MAX_EMBED_FIELD_NAME_LENGTH,
                'field_value': cls.MAX_EMBED_FIELD_VALUE_LENGTH,
                'max_fields': cls.MAX_EMBED_FIELDS
            },
            'colors': {
                'default': hex(cls.DEFAULT_EMBED_COLOR),
                'error': hex(cls.ERROR_COLOR),
                'success': hex(cls.SUCCESS_COLOR),
                'warning': hex(cls.WARNING_COLOR),
                'info': hex(cls.INFO_COLOR)
            },
            'database_path': cls.DATABASE_PATH,
            'dashboard_port': cls.DASHBOARD_PORT,
            'log_level': cls.LOG_LEVEL
        }
    
    @classmethod
    def log_config(cls, logger):
        """Log current configuration for debugging"""
        logger.info("Bot Configuration:")
        config = cls.get_config_dict()
        for key, value in config.items():
            logger.info(f"  {key}: {value}")
