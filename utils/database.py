"""
Database utilities for Discord bot
Contains SQLite database management for persistent data
"""

import sqlite3
import aiosqlite
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from bot_config import BotConfig

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager for bot persistent data"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or BotConfig.DATABASE_PATH
        self.connection = None
        
    async def initialize(self):
        """Initialize database and create tables"""
        try:
            self.connection = await aiosqlite.connect(self.db_path)
            await self._create_tables()
            logger.info(f"Database initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def _create_tables(self):
        """Create database tables if they don't exist"""
        try:
            # Protected roles table
            await self.connection.execute('''
                CREATE TABLE IF NOT EXISTS protected_roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,
                    role_name TEXT NOT NULL,
                    protected_by INTEGER NOT NULL,
                    protected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, role_id)
                )
            ''')
            
            # Role assignment log table
            await self.connection.execute('''
                CREATE TABLE IF NOT EXISTS role_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,
                    assigned_by INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Command usage stats table
            await self.connection.execute('''
                CREATE TABLE IF NOT EXISTS command_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    user_id INTEGER NOT NULL,
                    command_name TEXT NOT NULL,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Bot settings table
            await self.connection.execute('''
                CREATE TABLE IF NOT EXISTS bot_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    setting_name TEXT NOT NULL,
                    setting_value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, setting_name)
                )
            ''')
            
            # Error logs table
            await self.connection.execute('''
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    command_name TEXT,
                    error_message TEXT NOT NULL,
                    error_traceback TEXT,
                    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await self.connection.commit()
            logger.info("Database tables created/verified")
            
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    # Protected Roles Methods
    async def protect_role(self, guild_id: int, role_id: int, role_name: str, protected_by: int) -> bool:
        """
        Protect a role
        
        Args:
            guild_id: Guild ID
            role_id: Role ID
            role_name: Role name
            protected_by: User ID who protected the role
            
        Returns:
            bool: True if successful
        """
        try:
            await self.connection.execute('''
                INSERT OR REPLACE INTO protected_roles 
                (guild_id, role_id, role_name, protected_by, protected_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (guild_id, role_id, role_name, protected_by, datetime.now(timezone.utc)))
            
            await self.connection.commit()
            logger.info(f"Protected role {role_name} (ID: {role_id}) in guild {guild_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to protect role: {e}")
            return False
    
    async def unprotect_role(self, guild_id: int, role_id: int) -> bool:
        """
        Unprotect a role
        
        Args:
            guild_id: Guild ID
            role_id: Role ID
            
        Returns:
            bool: True if successful
        """
        try:
            cursor = await self.connection.execute('''
                DELETE FROM protected_roles 
                WHERE guild_id = ? AND role_id = ?
            ''', (guild_id, role_id))
            
            await self.connection.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Unprotected role {role_id} in guild {guild_id}")
                return True
            else:
                logger.warning(f"Role {role_id} was not protected in guild {guild_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to unprotect role: {e}")
            return False
    
    async def is_role_protected(self, guild_id: int, role_id: int) -> bool:
        """
        Check if a role is protected
        
        Args:
            guild_id: Guild ID
            role_id: Role ID
            
        Returns:
            bool: True if protected
        """
        try:
            cursor = await self.connection.execute('''
                SELECT 1 FROM protected_roles 
                WHERE guild_id = ? AND role_id = ?
            ''', (guild_id, role_id))
            
            result = await cursor.fetchone()
            return result is not None
            
        except Exception as e:
            logger.error(f"Failed to check role protection: {e}")
            return False
    
    async def get_protected_roles(self, guild_id: int) -> List[Dict[str, Any]]:
        """
        Get all protected roles for a guild
        
        Args:
            guild_id: Guild ID
            
        Returns:
            List of protected role data
        """
        try:
            cursor = await self.connection.execute('''
                SELECT role_id, role_name, protected_by, protected_at
                FROM protected_roles 
                WHERE guild_id = ?
                ORDER BY protected_at DESC
            ''', (guild_id,))
            
            rows = await cursor.fetchall()
            return [
                {
                    'role_id': row[0],
                    'role_name': row[1],
                    'protected_by': row[2],
                    'protected_at': row[3]
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Failed to get protected roles: {e}")
            return []
    
    async def get_protected_role_count(self, guild_id: int) -> int:
        """
        Get count of protected roles for a guild
        
        Args:
            guild_id: Guild ID
            
        Returns:
            int: Count of protected roles
        """
        try:
            cursor = await self.connection.execute('''
                SELECT COUNT(*) FROM protected_roles WHERE guild_id = ?
            ''', (guild_id,))
            
            result = await cursor.fetchone()
            return result[0] if result else 0
            
        except Exception as e:
            logger.error(f"Failed to get protected role count: {e}")
            return 0
    
    # Role Assignment Logging
    async def log_role_assignment(self, guild_id: int, user_id: int, role_id: int, 
                                assigned_by: int, action: str) -> bool:
        """
        Log role assignment/removal
        
        Args:
            guild_id: Guild ID
            user_id: User ID
            role_id: Role ID
            assigned_by: User ID who made the assignment
            action: 'assigned' or 'removed'
            
        Returns:
            bool: True if successful
        """
        try:
            await self.connection.execute('''
                INSERT INTO role_assignments 
                (guild_id, user_id, role_id, assigned_by, action, assigned_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (guild_id, user_id, role_id, assigned_by, action, datetime.now(timezone.utc)))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to log role assignment: {e}")
            return False
    
    async def get_role_assignment_history(self, guild_id: int, user_id: int = None, 
                                        limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get role assignment history
        
        Args:
            guild_id: Guild ID
            user_id: Optional user ID filter
            limit: Maximum number of records
            
        Returns:
            List of assignment history
        """
        try:
            if user_id:
                cursor = await self.connection.execute('''
                    SELECT user_id, role_id, assigned_by, action, assigned_at
                    FROM role_assignments 
                    WHERE guild_id = ? AND user_id = ?
                    ORDER BY assigned_at DESC
                    LIMIT ?
                ''', (guild_id, user_id, limit))
            else:
                cursor = await self.connection.execute('''
                    SELECT user_id, role_id, assigned_by, action, assigned_at
                    FROM role_assignments 
                    WHERE guild_id = ?
                    ORDER BY assigned_at DESC
                    LIMIT ?
                ''', (guild_id, limit))
            
            rows = await cursor.fetchall()
            return [
                {
                    'user_id': row[0],
                    'role_id': row[1],
                    'assigned_by': row[2],
                    'action': row[3],
                    'assigned_at': row[4]
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Failed to get role assignment history: {e}")
            return []
    
    # Command Usage Tracking
    async def log_command_usage(self, guild_id: int, user_id: int, command_name: str) -> bool:
        """
        Log command usage
        
        Args:
            guild_id: Guild ID (None for DMs)
            user_id: User ID
            command_name: Command name
            
        Returns:
            bool: True if successful
        """
        try:
            await self.connection.execute('''
                INSERT INTO command_usage 
                (guild_id, user_id, command_name, used_at)
                VALUES (?, ?, ?, ?)
            ''', (guild_id, user_id, command_name, datetime.now(timezone.utc)))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to log command usage: {e}")
            return False
    
    async def get_command_stats(self, guild_id: int = None, days: int = 30) -> Dict[str, int]:
        """
        Get command usage statistics
        
        Args:
            guild_id: Optional guild ID filter
            days: Number of days to look back
            
        Returns:
            Dictionary of command counts
        """
        try:
            cutoff_date = datetime.now(timezone.utc).replace(day=datetime.now().day - days)
            
            if guild_id:
                cursor = await self.connection.execute('''
                    SELECT command_name, COUNT(*) as count
                    FROM command_usage 
                    WHERE guild_id = ? AND used_at >= ?
                    GROUP BY command_name
                    ORDER BY count DESC
                ''', (guild_id, cutoff_date))
            else:
                cursor = await self.connection.execute('''
                    SELECT command_name, COUNT(*) as count
                    FROM command_usage 
                    WHERE used_at >= ?
                    GROUP BY command_name
                    ORDER BY count DESC
                ''', (cutoff_date,))
            
            rows = await cursor.fetchall()
            return {row[0]: row[1] for row in rows}
            
        except Exception as e:
            logger.error(f"Failed to get command stats: {e}")
            return {}
    
    # Settings Management
    async def set_guild_setting(self, guild_id: int, setting_name: str, setting_value: str) -> bool:
        """
        Set guild setting
        
        Args:
            guild_id: Guild ID
            setting_name: Setting name
            setting_value: Setting value
            
        Returns:
            bool: True if successful
        """
        try:
            await self.connection.execute('''
                INSERT OR REPLACE INTO bot_settings 
                (guild_id, setting_name, setting_value, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (guild_id, setting_name, setting_value, datetime.now(timezone.utc)))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to set guild setting: {e}")
            return False
    
    async def get_guild_setting(self, guild_id: int, setting_name: str, default_value: str = None) -> Optional[str]:
        """
        Get guild setting
        
        Args:
            guild_id: Guild ID
            setting_name: Setting name
            default_value: Default value if not found
            
        Returns:
            Setting value or default
        """
        try:
            cursor = await self.connection.execute('''
                SELECT setting_value FROM bot_settings 
                WHERE guild_id = ? AND setting_name = ?
            ''', (guild_id, setting_name))
            
            result = await cursor.fetchone()
            return result[0] if result else default_value
            
        except Exception as e:
            logger.error(f"Failed to get guild setting: {e}")
            return default_value
    
    # Error Logging
    async def log_error(self, guild_id: int, user_id: int, command_name: str, 
                       error_message: str, error_traceback: str = None) -> bool:
        """
        Log error
        
        Args:
            guild_id: Guild ID
            user_id: User ID
            command_name: Command name
            error_message: Error message
            error_traceback: Error traceback
            
        Returns:
            bool: True if successful
        """
        try:
            await self.connection.execute('''
                INSERT INTO error_logs 
                (guild_id, user_id, command_name, error_message, error_traceback, occurred_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (guild_id, user_id, command_name, error_message, error_traceback, datetime.now(timezone.utc)))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
            return False
    
    # Maintenance Methods
    async def cleanup_guild_data(self, guild_id: int) -> bool:
        """
        Clean up data for a guild (when bot leaves)
        
        Args:
            guild_id: Guild ID
            
        Returns:
            bool: True if successful
        """
        try:
            # Clean up protected roles
            await self.connection.execute('DELETE FROM protected_roles WHERE guild_id = ?', (guild_id,))
            
            # Clean up role assignments
            await self.connection.execute('DELETE FROM role_assignments WHERE guild_id = ?', (guild_id,))
            
            # Clean up settings
            await self.connection.execute('DELETE FROM bot_settings WHERE guild_id = ?', (guild_id,))
            
            # Clean up error logs
            await self.connection.execute('DELETE FROM error_logs WHERE guild_id = ?', (guild_id,))
            
            await self.connection.commit()
            logger.info(f"Cleaned up data for guild {guild_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup guild data: {e}")
            return False
    
    async def cleanup_old_data(self, days: int = 90) -> bool:
        """
        Clean up old data
        
        Args:
            days: Number of days to keep
            
        Returns:
            bool: True if successful
        """
        try:
            cutoff_date = datetime.now(timezone.utc).replace(day=datetime.now().day - days)
            
            # Clean up old command usage
            await self.connection.execute('DELETE FROM command_usage WHERE used_at < ?', (cutoff_date,))
            
            # Clean up old role assignments
            await self.connection.execute('DELETE FROM role_assignments WHERE assigned_at < ?', (cutoff_date,))
            
            # Clean up old error logs
            await self.connection.execute('DELETE FROM error_logs WHERE occurred_at < ?', (cutoff_date,))
            
            await self.connection.commit()
            logger.info(f"Cleaned up data older than {days} days")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return False
    
    async def backup_database(self, backup_path: str) -> bool:
        """
        Create database backup
        
        Args:
            backup_path: Backup file path
            
        Returns:
            bool: True if successful
        """
        try:
            async with aiosqlite.connect(backup_path) as backup_db:
                await self.connection.backup(backup_db)
            logger.info(f"Database backed up to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return False
    
    async def close(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
            logger.info("Database connection closed")
