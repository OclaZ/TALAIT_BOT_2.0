
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

class Challenges(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = bot.data_manager

    def has_trainer_role(self, interaction: discord.Interaction):
        allowed_roles = ['formateur', 'admin', 'moderator']
        return any(role.name.lower() in allowed_roles for role in interaction.user.roles)

    @app_commands.command(name='postchallenge', description='Post a new weekly challenge')
    @app_commands.describe(title='Challenge title', description='Challenge description', difficulty='Difficulty level')
    @app_commands.choices(difficulty=[
        app_commands.Choice(name='Easy', value='Easy'),
        app_commands.Choice(name='Medium', value='Medium'),
        app_commands.Choice(name='Hard', value='Hard')
    ])
    async def post_challenge(self, interaction: discord.Interaction, title: str, description: str, difficulty: app_commands.Choice[str]):
        if not self.has_trainer_role(interaction):
            await interaction.response.send_message('❌ Only trainers can post challenges!', ephemeral=True)
            return

        week_number = datetime.now().isocalendar()[1]
        challenge_data = {
            'title': title,
            'description': description,
            'difficulty': difficulty.value,
            'week': week_number,
            'posted_by': interaction.user.id,
            'posted_at': datetime.now().isoformat(),
            'status': 'active',
            'submissions': []
        }

        challenge_id = self.data_manager.create_challenge(interaction.guild.id, challenge_data)

        color_map = {'Easy': discord.Color.green(), 'Medium': discord.Color.orange(), 'Hard': discord.Color.red()}
        embed = discord.Embed(title=f'🎯 {title}', description=description, color=color_map.get(difficulty.value, discord.Color.blue()))
        embed.add_field(name='📊 Difficulty', value=difficulty.value, inline=True)
        embed.add_field(name='📅 Week', value=f'Week {week_number}', inline=True)
        embed.add_field(name='👤 Posted by', value=interaction.user.mention, inline=True)
        embed.add_field(name='📝 How to Submit', value='Use `/submit` to create your private submission ticket!', inline=False)
        embed.add_field(name='🏆 Rewards', value='🥇 1st: 10 XP\n🥈 2nd: 7 XP\n🥉 3rd: 5 XP\n✅ Participation: 2 XP', inline=False)
        embed.set_footer(text=f'{interaction.guild.name} • {datetime.now().strftime("%B %d, %Y")}')
        embed.timestamp = datetime.now()

        await interaction.response.send_message(content='@everyone 🚨 **New Coding Challenge!**', embed=embed)
        print(f'✅ Challenge created in {interaction.guild.name}: {title} (ID: {challenge_id})')

    @app_commands.command(name='closechallenge', description='Close the current challenge')
    async def close_challenge(self, interaction: discord.Interaction):
        if not self.has_trainer_role(interaction):
            await interaction.response.send_message('❌ Only trainers!', ephemeral=True)
            return

        active_challenge = self.data_manager.get_active_challenge(interaction.guild.id)
        if not active_challenge:
            await interaction.response.send_message('❌ No active challenge!', ephemeral=True)
            return

        self.data_manager.update_challenge(interaction.guild.id, active_challenge['id'], {'status': 'closed'})

        embed = discord.Embed(title='🏁 Challenge Closed!', description=f"**{active_challenge['title']}** is now closed.", color=discord.Color.red())
        embed.add_field(name='Total Submissions', value=str(len(active_challenge.get('submissions', []))), inline=True)
        embed.add_field(name='Week', value=f"Week {active_challenge['week']}", inline=True)
        embed.set_footer(text=interaction.guild.name)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='awardwinners', description='Award XP to the top 3 winners')
    @app_commands.describe(first='1st place winner', second='2nd place winner (optional)', third='3rd place winner (optional)')
    async def award_winners(self, interaction: discord.Interaction, first: discord.Member, second: discord.Member = None, third: discord.Member = None):
        if not self.has_trainer_role(interaction):
            await interaction.response.send_message('❌ Only trainers!', ephemeral=True)
            return

        challenge = self.data_manager.get_active_challenge(interaction.guild.id) or self.data_manager.get_latest_challenge(interaction.guild.id)
        if not challenge:
            await interaction.response.send_message('❌ No challenge found!', ephemeral=True)
            return

        week_key = f"week_{challenge['week']}"
        winners = []

        self.data_manager.ensure_user(interaction.guild.id, first.id, first.name)
        self.data_manager.add_xp(interaction.guild.id, first.id, 10, week_key)
        winners.append(f"🥇 {first.mention} - **10 XP**")

        if second:
            self.data_manager.ensure_user(interaction.guild.id, second.id, second.name)
            self.data_manager.add_xp(interaction.guild.id, second.id, 7, week_key)
            winners.append(f"🥈 {second.mention} - **7 XP**")

        if third:
            self.data_manager.ensure_user(interaction.guild.id, third.id, third.name)
            self.data_manager.add_xp(interaction.guild.id, third.id, 5, week_key)
            winners.append(f"🥉 {third.mention} - **5 XP**")

        embed = discord.Embed(title='🎉 Winners Announced!', description=f"**{challenge['title']}** - Week {challenge['week']}\n\n" + "\n".join(winners), color=discord.Color.gold())
        embed.set_footer(text=f'{interaction.guild.name} • Congratulations! 🎊')

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='activechallenge', description='View the current active challenge')
    async def active_challenge(self, interaction: discord.Interaction):
        challenge = self.data_manager.get_active_challenge(interaction.guild.id)
        
        if not challenge:
            await interaction.response.send_message('❌ No active challenge!', ephemeral=True)
            return

        embed = discord.Embed(title=f'🎯 {challenge["title"]}', description=challenge["description"], color=discord.Color.blue())
        embed.add_field(name='Difficulty', value=challenge["difficulty"], inline=True)
        embed.add_field(name='Week', value=f'Week {challenge["week"]}', inline=True)
        embed.add_field(name='Submissions', value=str(len(challenge.get("submissions", []))), inline=True)
        embed.set_footer(text=interaction.guild.name)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Challenges(bot))