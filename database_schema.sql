-- Discord Bot PostgreSQL Database Schema
-- Generated: 2025-07-06
-- Description: Complete database schema for Discord Companion Bot

-- ============================================
-- DROP TABLES (if you need to reset)
-- ============================================
-- Uncomment these lines if you want to completely reset the database
-- DROP TABLE IF EXISTS error_logs CASCADE;
-- DROP TABLE IF EXISTS bot_statistics CASCADE;
-- DROP TABLE IF EXISTS command_usage CASCADE;
-- DROP TABLE IF EXISTS role_assignments CASCADE;
-- DROP TABLE IF EXISTS protected_roles CASCADE;
-- DROP TABLE IF EXISTS guild_settings CASCADE;

-- ============================================
-- CREATE TABLES
-- ============================================

-- Protected Roles Table
-- Stores roles that are protected from manual assignment
CREATE TABLE IF NOT EXISTS protected_roles (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    role_name VARCHAR(255) NOT NULL,
    protected_by BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(guild_id, role_id)
);

-- Role Assignments Table
-- Logs all role assignments and removals for audit trail
CREATE TABLE IF NOT EXISTS role_assignments (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    assigned_by BIGINT NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    action VARCHAR(20) NOT NULL CHECK (action IN ('assign', 'remove'))
);

-- Command Usage Table
-- Tracks all command usage for analytics
CREATE TABLE IF NOT EXISTS command_usage (
    id SERIAL PRIMARY KEY,
    command_name VARCHAR(100) NOT NULL,
    user_id BIGINT NOT NULL,
    guild_id BIGINT,
    used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);

-- Bot Statistics Table
-- Stores periodic snapshots of bot performance metrics
CREATE TABLE IF NOT EXISTS bot_statistics (
    id SERIAL PRIMARY KEY,
    guild_count INTEGER NOT NULL,
    user_count INTEGER NOT NULL,
    command_count INTEGER NOT NULL,
    uptime_seconds INTEGER NOT NULL,
    latency_ms INTEGER NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Error Logs Table
-- Comprehensive error logging for debugging and monitoring
CREATE TABLE IF NOT EXISTS error_logs (
    id SERIAL PRIMARY KEY,
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    traceback TEXT,
    user_id BIGINT,
    guild_id BIGINT,
    command_name VARCHAR(100),
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Guild Settings Table
-- Per-guild configuration and preferences
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
);

-- ============================================
-- CREATE INDEXES FOR PERFORMANCE
-- ============================================

-- Protected Roles Indexes
CREATE INDEX IF NOT EXISTS idx_protected_roles_guild 
ON protected_roles(guild_id);

CREATE INDEX IF NOT EXISTS idx_protected_roles_role 
ON protected_roles(role_id);

-- Role Assignments Indexes
CREATE INDEX IF NOT EXISTS idx_role_assignments_guild 
ON role_assignments(guild_id);

CREATE INDEX IF NOT EXISTS idx_role_assignments_user 
ON role_assignments(user_id);

CREATE INDEX IF NOT EXISTS idx_role_assignments_role 
ON role_assignments(role_id);

CREATE INDEX IF NOT EXISTS idx_role_assignments_date 
ON role_assignments(assigned_at);

-- Command Usage Indexes
CREATE INDEX IF NOT EXISTS idx_command_usage_command 
ON command_usage(command_name);

CREATE INDEX IF NOT EXISTS idx_command_usage_user 
ON command_usage(user_id);

CREATE INDEX IF NOT EXISTS idx_command_usage_guild 
ON command_usage(guild_id);

CREATE INDEX IF NOT EXISTS idx_command_usage_date 
ON command_usage(used_at);

-- Bot Statistics Indexes
CREATE INDEX IF NOT EXISTS idx_bot_statistics_date 
ON bot_statistics(recorded_at);

-- Error Logs Indexes
CREATE INDEX IF NOT EXISTS idx_error_logs_occurred 
ON error_logs(occurred_at);

CREATE INDEX IF NOT EXISTS idx_error_logs_type 
ON error_logs(error_type);

CREATE INDEX IF NOT EXISTS idx_error_logs_guild 
ON error_logs(guild_id);

-- Guild Settings Indexes
CREATE INDEX IF NOT EXISTS idx_guild_settings_updated 
ON guild_settings(updated_at);

-- ============================================
-- USEFUL QUERIES FOR ANALYTICS
-- ============================================

-- Most used commands
-- SELECT command_name, COUNT(*) as usage_count 
-- FROM command_usage 
-- WHERE used_at > NOW() - INTERVAL '30 days' 
-- GROUP BY command_name 
-- ORDER BY usage_count DESC;

-- Command success rate
-- SELECT command_name, 
--        COUNT(*) as total_uses,
--        COUNT(CASE WHEN success = TRUE THEN 1 END) as successful_uses,
--        ROUND(COUNT(CASE WHEN success = TRUE THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate
-- FROM command_usage 
-- GROUP BY command_name 
-- ORDER BY success_rate DESC;

-- Daily command usage
-- SELECT DATE(used_at) as date, COUNT(*) as commands_used
-- FROM command_usage 
-- WHERE used_at > NOW() - INTERVAL '30 days'
-- GROUP BY DATE(used_at) 
-- ORDER BY date DESC;

-- Active users by guild
-- SELECT guild_id, COUNT(DISTINCT user_id) as active_users
-- FROM command_usage 
-- WHERE used_at > NOW() - INTERVAL '7 days'
-- GROUP BY guild_id 
-- ORDER BY active_users DESC;

-- Recent errors
-- SELECT error_type, COUNT(*) as error_count
-- FROM error_logs 
-- WHERE occurred_at > NOW() - INTERVAL '24 hours'
-- GROUP BY error_type 
-- ORDER BY error_count DESC;

-- Protected roles by guild
-- SELECT guild_id, COUNT(*) as protected_role_count
-- FROM protected_roles 
-- GROUP BY guild_id 
-- ORDER BY protected_role_count DESC;

-- Bot performance over time
-- SELECT DATE(recorded_at) as date, 
--        AVG(latency_ms) as avg_latency,
--        MAX(guild_count) as max_guilds,
--        SUM(command_count) as total_commands
-- FROM bot_statistics 
-- WHERE recorded_at > NOW() - INTERVAL '30 days'
-- GROUP BY DATE(recorded_at) 
-- ORDER BY date DESC;

-- ============================================
-- FUNCTIONS FOR COMMON OPERATIONS
-- ============================================

-- Function to update guild settings timestamp
CREATE OR REPLACE FUNCTION update_guild_settings_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update guild settings timestamp
DROP TRIGGER IF EXISTS trigger_update_guild_settings_timestamp ON guild_settings;
CREATE TRIGGER trigger_update_guild_settings_timestamp
    BEFORE UPDATE ON guild_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_guild_settings_timestamp();

-- ============================================
-- INITIAL DATA (Optional)
-- ============================================

-- You can uncomment and modify these if you want to insert initial data
-- INSERT INTO guild_settings (guild_id, prefix, moderation_enabled) 
-- VALUES (1234567890, '!', FALSE) 
-- ON CONFLICT (guild_id) DO NOTHING;

-- ============================================
-- PERMISSIONS (Optional)
-- ============================================

-- Grant permissions to bot user (replace 'bot_user' with your actual database user)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO bot_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO bot_user;

-- ============================================
-- BACKUP COMMANDS (Reference)
-- ============================================

-- Create a backup of your database:
-- pg_dump -h localhost -U username -d database_name > backup_$(date +%Y%m%d_%H%M%S).sql

-- Restore from backup:
-- psql -h localhost -U username -d database_name < backup_file.sql

-- ============================================
-- MONITORING QUERIES
-- ============================================

-- Check table sizes
-- SELECT schemaname, tablename, 
--        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
-- FROM pg_tables 
-- WHERE schemaname = 'public' 
-- ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check connection count
-- SELECT count(*) as active_connections 
-- FROM pg_stat_activity 
-- WHERE state = 'active';

-- Check database size
-- SELECT pg_size_pretty(pg_database_size(current_database())) as database_size;