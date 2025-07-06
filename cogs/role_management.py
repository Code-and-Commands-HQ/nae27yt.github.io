"""
Role Management Cog
Contains commands for managing protected roles and role assignments
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
from datetime import datetime, timezone
from typing import Optional, List
from bot_config import BotConfig
from utils.validation import ValidationUtils
from utils.embed_utils import EmbedUtils

logger = logging.getLogger(__name__)

class RoleManagement(commands.Cog, name="Role Management"):
    """Role management commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="protect-role", description="Protect a role from manual assignment")
    @app_commands.describe(role="The role to protect")
    @app_commands.default_permissions(manage_roles=True)
    
    async def protect_role(self, interaction: discord.Interaction, role: discord.Role):
        """Protect a role from manual assignment"""
        try:
            if not interaction.guild:
                embed = EmbedUtils.create_error_embed(
                    "No Server",
                    "This command can only be used in a server."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            logger.info(f"Role {role.name} protected by {interaction.user} in {interaction.guild.name}")
            
            # Check if user has permission
            if not interaction.user.guild_permissions.manage_roles:
                embed = EmbedUtils.create_error_embed(
                    "Permission Denied",
                    "You need 'Manage Roles' permission to use this command."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if bot can manage this role
            if not ValidationUtils.can_manage_role(interaction.guild.me, role):
                embed = EmbedUtils.create_error_embed(
                    "Cannot Manage Role",
                    f"I cannot manage the role {role.mention} because it's above my highest role in the hierarchy."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if role is already protected
            is_protected = await self.bot.db_manager.is_role_protected(interaction.guild.id, role.id)
            if is_protected:
                embed = EmbedUtils.create_warning_embed(
                    "Already Protected",
                    f"The role {role.mention} is already protected."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check protected role limit
            protected_count = await self.bot.db_manager.get_protected_role_count(interaction.guild.id)
            if protected_count >= BotConfig.MAX_PROTECTED_ROLES_PER_GUILD:
                embed = EmbedUtils.create_error_embed(
                    "Limit Reached",
                    f"Maximum number of protected roles ({BotConfig.MAX_PROTECTED_ROLES_PER_GUILD}) reached for this server."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Protect the role
            await self.bot.db_manager.protect_role(
                interaction.guild.id,
                role.id,
                role.name,
                interaction.user.id
            )
            
            # Create success embed
            embed = EmbedUtils.create_success_embed(
                "Role Protected",
                f"The role {role.mention} has been protected. It can now only be assigned using `/assign-role`."
            )
            embed.add_field(
                name="Protected by",
                value=interaction.user.mention,
                inline=True
            )
            embed.add_field(
                name="Protected at",
                value=datetime.now(timezone.utc).strftime("%B %d, %Y at %I:%M %p UTC"),
                inline=True
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in protect role command: {e}")
            await self._handle_command_error(interaction, e)
    
    @app_commands.command(name="assign-role", description="Assign a protected role to a user")
    @app_commands.describe(
        user="The user to assign the role to",
        role="The protected role to assign"
    )
    @app_commands.default_permissions(manage_roles=True)
    
    async def assign_role(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        """Assign a protected role to a user"""
        try:
            if not interaction.guild:
                embed = EmbedUtils.create_error_embed(
                    "No Server",
                    "This command can only be used in a server."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            logger.info(f"Role {role.name} assigned to {user} by {interaction.user} in {interaction.guild.name}")
            
            # Check if user has permission
            if not interaction.user.guild_permissions.manage_roles:
                embed = EmbedUtils.create_error_embed(
                    "Permission Denied",
                    "You need 'Manage Roles' permission to use this command."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if role is protected
            is_protected = await self.bot.db_manager.is_role_protected(interaction.guild.id, role.id)
            if not is_protected:
                embed = EmbedUtils.create_warning_embed(
                    "Role Not Protected",
                    f"The role {role.mention} is not protected. You can assign it manually."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if bot can manage this role
            if not ValidationUtils.can_manage_role(interaction.guild.me, role):
                embed = EmbedUtils.create_error_embed(
                    "Cannot Manage Role",
                    f"I cannot manage the role {role.mention} because it's above my highest role in the hierarchy."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if user already has the role
            if role in user.roles:
                embed = EmbedUtils.create_warning_embed(
                    "Already Has Role",
                    f"{user.mention} already has the role {role.mention}."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Assign the role
            await user.add_roles(role, reason=f"Protected role assigned by {interaction.user}")
            
            # Log the assignment
            await self.bot.db_manager.log_role_assignment(
                interaction.guild.id,
                user.id,
                role.id,
                interaction.user.id,
                'assigned'
            )
            
            # Create success embed
            embed = EmbedUtils.create_success_embed(
                "Role Assigned",
                f"The role {role.mention} has been assigned to {user.mention}."
            )
            embed.add_field(
                name="Assigned by",
                value=interaction.user.mention,
                inline=True
            )
            embed.add_field(
                name="Assigned at",
                value=datetime.now(timezone.utc).strftime("%B %d, %Y at %I:%M %p UTC"),
                inline=True
            )
            
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            embed = EmbedUtils.create_error_embed(
                "Permission Error",
                "I don't have permission to assign this role. Make sure my role is above the role you're trying to assign."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in assign role command: {e}")
            await self._handle_command_error(interaction, e)
    
    @app_commands.command(name="unprotect-role", description="Remove protection from a role")
    @app_commands.describe(role="The role to unprotect")
    @app_commands.default_permissions(manage_roles=True)
    
    async def unprotect_role(self, interaction: discord.Interaction, role: discord.Role):
        """Remove protection from a role"""
        try:
            if not interaction.guild:
                embed = EmbedUtils.create_error_embed(
                    "No Server",
                    "This command can only be used in a server."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            logger.info(f"Role {role.name} unprotected by {interaction.user} in {interaction.guild.name}")
            
            # Check if user has permission
            if not interaction.user.guild_permissions.manage_roles:
                embed = EmbedUtils.create_error_embed(
                    "Permission Denied",
                    "You need 'Manage Roles' permission to use this command."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if role is protected
            is_protected = await self.bot.db_manager.is_role_protected(interaction.guild.id, role.id)
            if not is_protected:
                embed = EmbedUtils.create_warning_embed(
                    "Role Not Protected",
                    f"The role {role.mention} is not currently protected."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Unprotect the role
            await self.bot.db_manager.unprotect_role(interaction.guild.id, role.id)
            
            # Create success embed
            embed = EmbedUtils.create_success_embed(
                "Role Unprotected",
                f"The role {role.mention} has been unprotected. It can now be assigned manually."
            )
            embed.add_field(
                name="Unprotected by",
                value=interaction.user.mention,
                inline=True
            )
            embed.add_field(
                name="Unprotected at",
                value=datetime.now(timezone.utc).strftime("%B %d, %Y at %I:%M %p UTC"),
                inline=True
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in unprotect role command: {e}")
            await self._handle_command_error(interaction, e)
    
    @app_commands.command(name="list-protected-roles", description="List all protected roles in this server")
    
    async def list_protected_roles(self, interaction: discord.Interaction):
        """List all protected roles in the server"""
        try:
            if not interaction.guild:
                embed = EmbedUtils.create_error_embed(
                    "No Server",
                    "This command can only be used in a server."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            logger.info(f"Protected roles listed by {interaction.user} in {interaction.guild.name}")
            
            # Get protected roles
            protected_roles = await self.bot.db_manager.get_protected_roles(interaction.guild.id)
            
            if not protected_roles:
                embed = EmbedUtils.create_info_embed(
                    "No Protected Roles",
                    "There are no protected roles in this server."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create embed
            embed = discord.Embed(
                title="🛡️ Protected Roles",
                description=f"Protected roles in **{interaction.guild.name}**",
                color=BotConfig.INFO_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Add role information
            role_list = []
            for role_data in protected_roles:
                role = interaction.guild.get_role(role_data['role_id'])
                if role:
                    protector = interaction.guild.get_member(role_data['protected_by'])
                    protector_name = protector.display_name if protector else "Unknown"
                    
                    role_list.append(f"**{role.name}** - Protected by {protector_name}")
                else:
                    # Role was deleted, clean up
                    await self.bot.db_manager.unprotect_role(interaction.guild.id, role_data['role_id'])
            
            if role_list:
                # Split into chunks if too long
                chunks = [role_list[i:i+10] for i in range(0, len(role_list), 10)]
                
                for i, chunk in enumerate(chunks):
                    field_name = "Roles" if i == 0 else f"Roles (continued {i+1})"
                    embed.add_field(
                        name=field_name,
                        value="\n".join(chunk),
                        inline=False
                    )
            else:
                embed.description = "All protected roles have been deleted. Database cleaned up."
            
            embed.set_footer(text=f"Total: {len(role_list)} protected roles")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in list protected roles command: {e}")
            await self._handle_command_error(interaction, e)
    
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Monitor role changes and enforce protection"""
        try:
            # Check if roles changed
            if before.roles == after.roles:
                return
            
            # Find added roles
            added_roles = set(after.roles) - set(before.roles)
            
            for role in added_roles:
                # Check if role is protected
                is_protected = await self.bot.db_manager.is_role_protected(after.guild.id, role.id)
                if is_protected:
                    # Remove the role
                    try:
                        await after.remove_roles(role, reason="Protected role manually assigned - removing")
                        logger.warning(f"Removed protected role {role.name} from {after} - insufficient permissions")
                        
                        # Try to notify the user
                        try:
                            embed = EmbedUtils.create_warning_embed(
                                "Protected Role Removed",
                                f"The role **{role.name}** is protected and can only be assigned using `/assign-role`."
                            )
                            await after.send(embed=embed)
                        except discord.Forbidden:
                            pass  # User has DMs disabled
                            
                    except discord.Forbidden:
                        logger.warning(f"Cannot remove protected role {role.name} - insufficient permissions")
                    
        except Exception as e:
            logger.error(f"Error in role protection enforcement: {e}")
    
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
    await bot.add_cog(RoleManagement(bot))
    logger.info("Role management cog loaded successfully")
