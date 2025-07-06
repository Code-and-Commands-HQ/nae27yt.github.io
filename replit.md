# Discord Bot with Slash Commands

## Overview

This is a Discord bot built with Python and discord.py that provides comprehensive slash commands for message echoing, embed creation, direct messaging, and role management. The bot features a modular architecture with a web dashboard for monitoring, persistent data storage, and enhanced error handling.

## System Architecture

The application follows a modular monolithic architecture with clear separation of concerns:

**Core Components:**
- `main.py`: Entry point with enhanced bot lifecycle management
- `bot_config.py`: Centralized configuration management with extensive validation
- `cogs/`: Command organization using discord.py's cog system
- `utils/`: Shared utility functions for validation, embed creation, and database operations
- `web_dashboard.py`: Web-based monitoring and management interface
- `static/`: Frontend assets for the web dashboard

**Design Patterns:**
- **Cog Pattern**: Commands are organized into separate cogs for better maintainability
- **Configuration Class**: All settings centralized in BotConfig class with environment variable support
- **Utility Functions**: Reusable validation, embed creation, and database functions
- **Web Dashboard**: Real-time monitoring with WebSocket support

## Key Components

### Bot Core (`main.py`)
- **Purpose**: Enhanced bot initialization with lifecycle management
- **Architecture**: Custom DiscordBot class extending commands.Bot
- **Features**: Advanced logging, graceful shutdown handling, component initialization, and error recovery
- **Integrations**: Database manager and web dashboard integration

### Configuration (`bot_config.py`)
- **Purpose**: Comprehensive configuration management
- **Architecture**: Static configuration class with validation
- **Settings**: Extended cooldowns, rate limiting, embed limits, permissions, colors, logging, and database paths
- **Validation**: Input validation limits and security settings

### Command System

#### General Commands (`cogs/general_commands.py`)
- **Core Commands**:
  - `/say`: Message echoing with content validation and cleaning
  - `/embed`: Advanced embed creation with customizable fields and colors
  - `/dm`: Direct messaging with privacy controls
- **Utility Commands**:
  - `/help`: Interactive help system with detailed command descriptions
  - `/ping`: Bot latency and response time checking
  - `/serverinfo`: Comprehensive server information with statistics
  - `/userinfo`: User profile information with roles, join dates, and activity stats

#### Role Management (`cogs/role_management.py`)
- **Protection System**: Role protection mechanism to prevent manual role assignment
- **Commands**:
  - `/protect-role`: Mark roles as protected (only bot-assignable)
  - `/assign-role`: Safely assign protected roles to users
  - `/unprotect-role`: Remove role protection
  - `/list-protected-roles`: View all protected roles in server
- **Security**: Permission validation and role hierarchy checks

### Database Layer (`utils/database.py`)
- **Purpose**: Persistent data storage for bot state and configuration
- **Architecture**: Async SQLite database with connection pooling
- **Features**: Protected roles storage, role assignment logging, command usage tracking
- **Tables**: Protected roles, role assignments, command usage statistics

### Utility Components

#### Validation (`utils/validation.py`)
- **Purpose**: Input validation and security checks
- **Features**: Message content validation, dangerous pattern detection, content cleaning
- **Security**: Protection against @everyone/@here mentions, invite links, and excessive mentions

#### Embed Utils (`utils/embed_utils.py`)
- **Purpose**: Standardized embed creation and management
- **Features**: Error, success, warning, and info embed templates
- **Consistency**: Unified styling and formatting across all bot responses

### Web Dashboard (`web_dashboard.py`)
- **Purpose**: Real-time monitoring and management interface
- **Architecture**: Async web server with WebSocket support
- **Features**: 
  - Real-time statistics monitoring
  - Guild and user information display
  - Command usage analytics
  - Error tracking and reporting
  - WebSocket-based live updates
- **Frontend**: Bootstrap-based responsive interface with real-time data visualization

## Data Flow

1. **Command Processing**: User interaction → Command validation → Permission checks → Business logic → Database updates → Response generation
2. **Role Management**: Role assignment request → Protection status check → Permission validation → Database logging → Role assignment/removal
3. **Web Dashboard**: Real-time data collection → WebSocket broadcasting → Frontend updates → User interaction handling
4. **Database Operations**: Command execution → Data validation → Async database writes → Result caching

## External Dependencies

- **discord.py**: Core Discord API interaction and bot framework
- **aiosqlite**: Async SQLite database operations
- **aiohttp**: Web server for dashboard functionality
- **aiohttp-cors**: CORS support for web dashboard
- **python-dotenv**: Environment variable management (implied)

## Deployment Strategy

The bot is designed for containerized deployment with the following considerations:

- **Environment Variables**: Bot token and configuration through environment variables
- **File Persistence**: Database and log files require persistent storage
- **Port Exposure**: Web dashboard requires port access for monitoring
- **Process Management**: Graceful shutdown handling with proper cleanup
- **Resource Management**: Async architecture for efficient resource utilization

## Changelog

- July 05, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.