"""
PostgreSQL Database Manager for Discord Bot
Handles all database operations with PostgreSQL backend
"""

import asyncio
import asyncpg
import logging
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class PostgreSQLManager:
    """PostgreSQL database manager for the Discord bot"""
    
    def __init__(self):
        self.pool = None
        self.database_url = os.getenv('DATABASE_URL')
        
    async def initialize(self):
        """Initialize the PostgreSQL connection pool and create tables"""
        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            
            logger.info("PostgreSQL connection pool created")
            
            # Create tables
            await self.create_tables()
            logger.info("PostgreSQL database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL database: {e}")
            raise
    
    async def create_tables(self):
        """Create all necessary database tables"""
        async with self.pool.acquire() as conn:
            # Protected roles table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS protected_roles (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    role_id BIGINT NOT NULL,
                    role_name VARCHAR(255) NOT NULL,
                    protected_by BIGINT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(guild_id, role_id)
                )
            ''')
            
            # Role assignments table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS role_assignments (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    role_id BIGINT NOT NULL,
                    assigned_by BIGINT NOT NULL,
                    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    action VARCHAR(20) NOT NULL CHECK (action IN ('assign', 'remove'))
                )
            ''')
            
            # Command usage table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS command_usage (
                    id SERIAL PRIMARY KEY,
                    command_name VARCHAR(100) NOT NULL,
                    user_id BIGINT NOT NULL,
                    guild_id BIGINT,
                    used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT
                )
            ''')
            
            # Bot statistics table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS bot_statistics (
                    id SERIAL PRIMARY KEY,
                    guild_count INTEGER NOT NULL,
                    user_count INTEGER NOT NULL,
                    command_count INTEGER NOT NULL,
                    uptime_seconds INTEGER NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            ''')
            
            # Error logs table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS error_logs (
                    id SERIAL PRIMARY KEY,
                    error_type VARCHAR(100) NOT NULL,
                    error_message TEXT NOT NULL,
                    traceback TEXT,
                    user_id BIGINT,
                    guild_id BIGINT,
                    command_name VARCHAR(100),
                    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            ''')
            
            # Guild settings table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id BIGINT PRIMARY KEY,
                    prefix VARCHAR(10) DEFAULT '!',
                    log_channel_id BIGINT,
                    welcome_channel_id BIGINT,
                    auto_role_id BIGINT,
                    moderation_enabled BOOLEAN DEFAULT FALSE,
                    settings JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            ''')
            
            # Create indexes for better performance
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_protected_roles_guild ON protected_roles(guild_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_role_assignments_guild ON role_assignments(guild_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_command_usage_command ON command_usage(command_name)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_command_usage_user ON command_usage(user_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_error_logs_occurred ON error_logs(occurred_at)')
    
    # Protected Roles Methods
    async def add_protected_role(self, guild_id: int, role_id: int, role_name: str, protected_by: int) -> bool:
        """Add a role to the protected roles list"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO protected_roles (guild_id, role_id, role_name, protected_by)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (guild_id, role_id) DO UPDATE SET
                        role_name = EXCLUDED.role_name,
                        protected_by = EXCLUDED.protected_by,
                        created_at = NOW()
                ''', guild_id, role_id, role_name, protected_by)
                
                logger.info(f"Protected role {role_name} added for guild {guild_id}")
                return True
        except Exception as e:
            logger.error(f"Error adding protected role: {e}")
            return False
    
    async def remove_protected_role(self, guild_id: int, role_id: int) -> bool:
        """Remove a role from the protected roles list"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute('''
                    DELETE FROM protected_roles 
                    WHERE guild_id = $1 AND role_id = $2
                ''', guild_id, role_id)
                
                return result == "DELETE 1"
        except Exception as e:
            logger.error(f"Error removing protected role: {e}")
            return False
    
    async def get_protected_roles(self, guild_id: int) -> List[Dict[str, Any]]:
        """Get all protected roles for a guild"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT role_id, role_name, protected_by, created_at
                    FROM protected_roles 
                    WHERE guild_id = $1
                    ORDER BY created_at DESC
                ''', guild_id)
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting protected roles: {e}")
            return []
    
    async def is_role_protected(self, guild_id: int, role_id: int) -> bool:
        """Check if a role is protected"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval('''
                    SELECT EXISTS(
                        SELECT 1 FROM protected_roles 
                        WHERE guild_id = $1 AND role_id = $2
                    )
                ''', guild_id, role_id)
                
                return result
        except Exception as e:
            logger.error(f"Error checking protected role: {e}")
            return False
    
    # Role Assignment Logging
    async def log_role_assignment(self, guild_id: int, user_id: int, role_id: int, assigned_by: int, action: str):
        """Log role assignment/removal"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO role_assignments (guild_id, user_id, role_id, assigned_by, action)
                    VALUES ($1, $2, $3, $4, $5)
                ''', guild_id, user_id, role_id, assigned_by, action)
        except Exception as e:
            logger.error(f"Error logging role assignment: {e}")
    
    # Command Usage Tracking
    async def log_command_usage(self, command_name: str, user_id: int, guild_id: int = None, success: bool = True, error_message: str = None):
        """Log command usage"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO command_usage (command_name, user_id, guild_id, success, error_message)
                    VALUES ($1, $2, $3, $4, $5)
                ''', command_name, user_id, guild_id, success, error_message)
        except Exception as e:
            logger.error(f"Error logging command usage: {e}")
    
    async def get_command_statistics(self) -> List[Dict[str, Any]]:
        """Get command usage statistics"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT 
                        command_name,
                        COUNT(*) as usage_count,
                        COUNT(*) FILTER (WHERE success = true) as success_count,
                        COUNT(*) FILTER (WHERE success = false) as error_count,
                        MAX(used_at) as last_used
                    FROM command_usage
                    GROUP BY command_name
                    ORDER BY usage_count DESC
                ''')
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting command statistics: {e}")
            return []
    
    # Bot Statistics
    async def save_bot_statistics(self, guild_count: int, user_count: int, command_count: int, uptime_seconds: int, latency_ms: int):
        """Save bot statistics"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO bot_statistics (guild_count, user_count, command_count, uptime_seconds, latency_ms)
                    VALUES ($1, $2, $3, $4, $5)
                ''', guild_count, user_count, command_count, uptime_seconds, latency_ms)
        except Exception as e:
            logger.error(f"Error saving bot statistics: {e}")
    
    async def get_bot_statistics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get bot statistics history"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT *
                    FROM bot_statistics
                    WHERE recorded_at >= NOW() - INTERVAL '%s hours'
                    ORDER BY recorded_at DESC
                ''', hours)
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting bot statistics history: {e}")
            return []
    
    # Error Logging
    async def log_error(self, error_type: str, error_message: str, traceback: str = None, user_id: int = None, guild_id: int = None, command_name: str = None):
        """Log an error"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO error_logs (error_type, error_message, traceback, user_id, guild_id, command_name)
                    VALUES ($1, $2, $3, $4, $5, $6)
                ''', error_type, error_message, traceback, user_id, guild_id, command_name)
        except Exception as e:
            logger.error(f"Error logging error: {e}")
    
    async def get_recent_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent errors"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT *
                    FROM error_logs
                    ORDER BY occurred_at DESC
                    LIMIT $1
                ''', limit)
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting recent errors: {e}")
            return []
    
    # Guild Settings
    async def get_guild_settings(self, guild_id: int) -> Dict[str, Any]:
        """Get guild settings"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('''
                    SELECT * FROM guild_settings WHERE guild_id = $1
                ''', guild_id)
                
                if row:
                    return dict(row)
                else:
                    # Create default settings
                    await conn.execute('''
                        INSERT INTO guild_settings (guild_id) VALUES ($1)
                        ON CONFLICT (guild_id) DO NOTHING
                    ''', guild_id)
                    return {'guild_id': guild_id, 'prefix': '!', 'settings': {}}
        except Exception as e:
            logger.error(f"Error getting guild settings: {e}")
            return {'guild_id': guild_id, 'prefix': '!', 'settings': {}}
    
    async def update_guild_settings(self, guild_id: int, **kwargs):
        """Update guild settings"""
        try:
            async with self.pool.acquire() as conn:
                # Build dynamic update query
                set_clauses = []
                values = []
                param_count = 1
                
                for key, value in kwargs.items():
                    if key in ['prefix', 'log_channel_id', 'welcome_channel_id', 'auto_role_id', 'moderation_enabled', 'settings']:
                        set_clauses.append(f"{key} = ${param_count + 1}")
                        values.append(value)
                        param_count += 1
                
                if set_clauses:
                    set_clauses.append(f"updated_at = NOW()")
                    query = f'''
                        INSERT INTO guild_settings (guild_id, {', '.join(kwargs.keys())})
                        VALUES ($1, {', '.join([f'${i+2}' for i in range(len(kwargs))])})
                        ON CONFLICT (guild_id) DO UPDATE SET
                        {', '.join(set_clauses)}
                    '''
                    await conn.execute(query, guild_id, *values)
        except Exception as e:
            logger.error(f"Error updating guild settings: {e}")
    
    async def close(self):
        """Close the database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")