import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
from utils.constants import ALLOWED_ROLES
from utils.logger import get_logger

logger = get_logger("cogs.admin")

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = bot.data_manager
        self.monthly_reset.start()
        logger.info("Admin cog initialized")

    def cog_unload(self):
        self.monthly_reset.cancel()
        logger.info("Admin cog unloaded")

    @app_commands.command(name='removexp', description='Remove XP from a user')
    @app_commands.describe(user='The user to remove XP from', amount='Amount of XP to remove')
    async def remove_xp(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if not any(role.name.lower() in ALLOWED_ROLES for role in interaction.user.roles):
            logger.warning(f"Unauthorized removexp attempt | User: {interaction.user.name} | Guild: {interaction.guild.name}")
            await interaction.response.send_message('❌ Only trainers can use this!', ephemeral=True)
            return

        user_data = self.data_manager.get_user(interaction.guild.id, user.id)

        if not user_data:
            await interaction.response.send_message('❌ User not found!', ephemeral=True)
            return

        self.data_manager.remove_xp(interaction.guild.id, user.id, amount)
        updated_data = self.data_manager.get_user(interaction.guild.id, user.id)

        logger.info(f"/removexp | Removed {amount} XP from {user.name} | By: {interaction.user.name} | New XP: {updated_data['xp']} | Guild: {interaction.guild.name}")
        await interaction.response.send_message(f'✅ Removed {amount} XP from {user.mention}. Current XP: {updated_data["xp"]}')

    @app_commands.command(name='resetmonth', description='Manually reset the monthly leaderboard (Admin only)')
    async def reset_month(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            logger.warning(f"Unauthorized resetmonth attempt | User: {interaction.user.name} | Guild: {interaction.guild.name}")
            await interaction.response.send_message('❌ Admins only!', ephemeral=True)
            return

        month_key = self.data_manager.get_month_key()
        self.data_manager.reset_monthly_leaderboard(interaction.guild.id)

        logger.info(f"/resetmonth | Manual reset executed | By: {interaction.user.name} | Month: {month_key} | Guild: {interaction.guild.name}")
        await interaction.response.send_message(f'✅ Monthly leaderboard reset! Data saved to Hall of Fame for {month_key}')

    @app_commands.command(name='listusers', description='List all users in the leaderboard')
    async def list_users(self, interaction: discord.Interaction):
        if not any(role.name.lower() in ALLOWED_ROLES for role in interaction.user.roles):
            await interaction.response.send_message('❌ Trainers only!', ephemeral=True)
            return
        
        leaderboard = self.data_manager.get_leaderboard(interaction.guild.id)
        
        if not leaderboard:
            await interaction.response.send_message('❌ No users!', ephemeral=True)
            return
        
        sorted_users = sorted(leaderboard.items(), key=lambda x: x[1]['xp'], reverse=True)
        
        embed = discord.Embed(title=f'👥 All Users in {interaction.guild.name}', description=f'Total users: {len(sorted_users)}', color=discord.Color.blue())
        
        for idx, (user_id, data) in enumerate(sorted_users[:25], 1):
            embed.add_field(name=f"{idx}. {data['username']}", value=f"{data['xp']} XP", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tasks.loop(hours=24)
    async def monthly_reset(self):
        now = datetime.now()

        if now.day == 1 and now.hour == 0:
            logger.info("Automatic monthly reset task triggered")
            for guild in self.bot.guilds:
                month_key = self.data_manager.get_month_key()
                self.data_manager.reset_monthly_leaderboard(guild.id)
                logger.info(f'✅ Monthly reset completed | Guild: {guild.name} | Month: {month_key}')

    @monthly_reset.before_loop
    async def before_monthly_reset(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Admin(bot))


