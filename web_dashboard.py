"""
Web Dashboard for Discord Bot
Provides a web interface for monitoring and managing the bot
"""

import asyncio
from datetime import datetime, timezone
import json
import logging
from typing import Dict, Any
from aiohttp import web, WSMsgType
import aiohttp_cors
from bot_config import BotConfig

logger = logging.getLogger(__name__)

class WebDashboard:
    """Web dashboard for bot monitoring and management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.app = web.Application()
        self.runner = None
        self.site = None
        self.websockets = set()
        self.setup_routes()
    
    def setup_routes(self):
        """Setup web routes"""
        # Static routes
        self.app.router.add_get('/', self.dashboard_page)
        self.app.router.add_get('/api/stats', self.get_stats)
        self.app.router.add_get('/api/guilds', self.get_guilds)
        self.app.router.add_get('/api/commands', self.get_commands)
        self.app.router.add_get('/api/errors', self.get_errors)
        self.app.router.add_get('/ws', self.websocket_handler)
        
        # Static files
        self.app.router.add_static('/', 'static/', name='static')
        
        # CORS setup
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Add CORS to all routes
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    async def dashboard_page(self, request):
        """Serve the dashboard HTML page"""
        try:
            with open('static/dashboard.html', 'r') as f:
                content = f.read()
            return web.Response(text=content, content_type='text/html')
        except FileNotFoundError:
            return web.Response(text="Dashboard not found", status=404)
    
    async def get_stats(self, request):
        """Get bot statistics"""
        try:
            uptime = datetime.now() - self.bot.startup_time
            uptime_str = str(uptime).split('.')[0]
            
            stats = {
                'bot_name': self.bot.user.name if self.bot.user else 'Unknown',
                'bot_id': self.bot.user.id if self.bot.user else 0,
                'guild_count': len(self.bot.guilds),
                'user_count': sum(guild.member_count for guild in self.bot.guilds),
                'uptime': uptime_str,
                'latency': round(self.bot.latency * 1000),
                'command_count': len(self.bot.tree.get_commands()),
                'error_count': getattr(self.bot, 'error_count', 0),
                'status': 'online' if self.bot.is_ready() else 'offline'
            }
            
            return web.json_response(stats)
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_guilds(self, request):
        """Get guild information"""
        try:
            guilds = []
            for guild in self.bot.guilds:
                guild_data = {
                    'id': guild.id,
                    'name': guild.name,
                    'member_count': guild.member_count,
                    'owner': guild.owner.name if guild.owner else 'Unknown',
                    'created_at': guild.created_at.isoformat(),
                    'icon_url': guild.icon.url if guild.icon else None
                }
                guilds.append(guild_data)
            
            return web.json_response(guilds)
            
        except Exception as e:
            logger.error(f"Error getting guilds: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_commands(self, request):
        """Get command usage statistics"""
        try:
            command_stats = getattr(self.bot, 'command_stats', {})
            
            commands = []
            for cmd in self.bot.tree.get_commands():
                usage_count = command_stats.get(cmd.name, 0)
                commands.append({
                    'name': cmd.name,
                    'description': cmd.description,
                    'usage_count': usage_count
                })
            
            return web.json_response(commands)
            
        except Exception as e:
            logger.error(f"Error getting commands: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_errors(self, request):
        """Get recent errors"""
        try:
            # Get recent errors from database if available
            if hasattr(self.bot, 'db_manager'):
                # This would require implementing get_recent_errors in DatabaseManager
                errors = []
            else:
                errors = []
            
            return web.json_response(errors)
            
        except Exception as e:
            logger.error(f"Error getting errors: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def websocket_handler(self, request):
        """Handle WebSocket connections for real-time updates"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.websockets.add(ws)
        logger.info("WebSocket client connected")
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self.handle_websocket_message(ws, data)
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
                    break
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.websockets.discard(ws)
            logger.info("WebSocket client disconnected")
        
        return ws
    
    async def handle_websocket_message(self, ws, data):
        """Handle incoming WebSocket messages"""
        try:
            message_type = data.get('type')
            
            if message_type == 'ping':
                await ws.send_text(json.dumps({'type': 'pong'}))
            elif message_type == 'get_stats':
                stats = await self.get_stats_data()
                await ws.send_text(json.dumps({'type': 'stats', 'data': stats}))
            
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    async def get_stats_data(self):
        """Get stats data for WebSocket"""
        uptime = datetime.now() - self.bot.startup_time
        uptime_str = str(uptime).split('.')[0]
        
        return {
            'guild_count': len(self.bot.guilds),
            'user_count': sum(guild.member_count for guild in self.bot.guilds),
            'uptime': uptime_str,
            'latency': round(self.bot.latency * 1000),
            'error_count': getattr(self.bot, 'error_count', 0),
            'timestamp': datetime.now().isoformat()
        }
    
    async def broadcast_stats(self):
        """Broadcast stats to all connected WebSocket clients"""
        if not self.websockets:
            return
        
        try:
            stats = await self.get_stats_data()
            message = json.dumps({'type': 'stats_update', 'data': stats})
            
            # Send to all connected clients
            disconnected = set()
            for ws in self.websockets:
                try:
                    await ws.send_text(message)
                except Exception:
                    disconnected.add(ws)
            
            # Remove disconnected clients
            for ws in disconnected:
                self.websockets.discard(ws)
                
        except Exception as e:
            logger.error(f"Error broadcasting stats: {e}")
    
    async def start(self):
        """Start the web dashboard"""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(
                self.runner,
                BotConfig.DASHBOARD_HOST,
                BotConfig.DASHBOARD_PORT
            )
            
            await self.site.start()
            
            logger.info(f"Web dashboard started on http://{BotConfig.DASHBOARD_HOST}:{BotConfig.DASHBOARD_PORT}")
            
            # Start periodic stats broadcast
            asyncio.create_task(self.periodic_stats_broadcast())
            
        except Exception as e:
            logger.error(f"Failed to start web dashboard: {e}")
            raise
    
    async def stop(self):
        """Stop the web dashboard"""
        try:
            if self.site:
                await self.site.stop()
            
            if self.runner:
                await self.runner.cleanup()
            
            # Close all WebSocket connections
            for ws in self.websockets:
                await ws.close()
            
            logger.info("Web dashboard stopped")
            
        except Exception as e:
            logger.error(f"Error stopping web dashboard: {e}")
    
    async def periodic_stats_broadcast(self):
        """Periodically broadcast stats to WebSocket clients"""
        while not self.bot.is_closed():
            try:
                await self.broadcast_stats()
                await asyncio.sleep(30)  # Broadcast every 30 seconds
            except Exception as e:
                logger.error(f"Error in periodic stats broadcast: {e}")
                await asyncio.sleep(30)
