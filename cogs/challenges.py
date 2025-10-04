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
    @app_commands.describe(
        title='Challenge title',
        description='Challenge description',
        difficulty='Difficulty level'
    )
    @app_commands.choices(difficulty=[
        app_commands.Choice(name='Easy', value='Easy'),
        app_commands.Choice(name='Medium', value='Medium'),
        app_commands.Choice(name='Hard', value='Hard')
    ])
    async def post_challenge(self, interaction: discord.Interaction, title: str, description: str, difficulty: app_commands.Choice[str]):
        if not self.has_trainer_role(interaction):
            await interaction.response.send_message('❌ Only trainers can post challenges!', ephemeral=True)
            return

        # Create challenge
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

        # Save challenge
        challenge_id = self.data_manager.create_challenge(challenge_data)

        # Create embed
        color_map = {
            'Easy': discord.Color.green(),
            'Medium': discord.Color.orange(),
            'Hard': discord.Color.red()
        }

        embed = discord.Embed(
            title=f'🎯 {title}',
            description=description,
            color=color_map.get(difficulty.value, discord.Color.blue())
        )
        
        embed.add_field(name='📊 Difficulty', value=difficulty.value, inline=True)
        embed.add_field(name='📅 Week', value=f'Week {week_number}', inline=True)
        embed.add_field(name='👤 Posted by', value=interaction.user.mention, inline=True)
        
        embed.add_field(
            name='📝 How to Submit',
            value='Use `/submit` to create your private submission ticket!',
            inline=False
        )
        
        embed.add_field(
            name='🏆 Rewards',
            value='🥇 1st: 10 XP\n🥈 2nd: 7 XP\n🥉 3rd: 5 XP\n✅ Participation: 2 XP',
            inline=False
        )
        
        embed.set_footer(text=f'Posted on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}')
        embed.timestamp = datetime.now()

        await interaction.response.send_message(
            content='@everyone 🚨 **New Coding Challenge Posted!**',
            embed=embed
        )

        print(f'✅ Challenge created: {title} (ID: {challenge_id})')

    @app_commands.command(name='closechallenge', description='Close the current challenge')
    async def close_challenge(self, interaction: discord.Interaction):
        if not self.has_trainer_role(interaction):
            await interaction.response.send_message('❌ Only trainers can close challenges!', ephemeral=True)
            return

        active_challenge = self.data_manager.get_active_challenge()
        if not active_challenge:
            await interaction.response.send_message('❌ No active challenge to close!', ephemeral=True)
            return

        self.data_manager.update_challenge(active_challenge['id'], {'status': 'closed'})

        embed = discord.Embed(
            title='🏁 Challenge Closed!',
            description=f"**{active_challenge['title']}** is now closed for submissions.\n\nTrainers are reviewing submissions...",
            color=discord.Color.red()
        )
        embed.add_field(name='Total Submissions', value=str(len(active_challenge.get('submissions', []))), inline=True)
        embed.add_field(name='Week', value=f"Week {active_challenge['week']}", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='awardwinners', description='Award XP to the top 3 winners')
    @app_commands.describe(
        first='1st place winner',
        second='2nd place winner (optional)',
        third='3rd place winner (optional)'
    )
    async def award_winners(self, interaction: discord.Interaction, first: discord.Member, second: discord.Member = None, third: discord.Member = None):
        if not self.has_trainer_role(interaction):
            await interaction.response.send_message('❌ Only trainers can award winners!', ephemeral=True)
            return

        challenge = self.data_manager.get_active_challenge() or self.data_manager.get_latest_challenge()
        if not challenge:
            await interaction.response.send_message('❌ No challenge found!', ephemeral=True)
            return

        week_key = f"week_{challenge['week']}"
        winners = []

        # Award 1st place
        self.data_manager.ensure_user(first.id, first.name)
        self.data_manager.add_xp(first.id, 10, week_key)
        winners.append(f"🥇 {first.mention} - **10 XP**")

        # Award 2nd place
        if second:
            self.data_manager.ensure_user(second.id, second.name)
            self.data_manager.add_xp(second.id, 7, week_key)
            winners.append(f"🥈 {second.mention} - **7 XP**")

        # Award 3rd place
        if third:
            self.data_manager.ensure_user(third.id, third.name)
            self.data_manager.add_xp(third.id, 5, week_key)
            winners.append(f"🥉 {third.mention} - **5 XP**")

        embed = discord.Embed(
            title='🎉 Winners Announced!',
            description=f"**{challenge['title']}** - Week {challenge['week']}\n\n" + "\n".join(winners),
            color=discord.Color.gold()
        )
        embed.set_footer(text='Congratulations to all winners! 🎊')

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='activechallenge', description='View the current active challenge')
    async def active_challenge(self, interaction: discord.Interaction):
        challenge = self.data_manager.get_active_challenge()
        
        if not challenge:
            await interaction.response.send_message('❌ No active challenge right now!', ephemeral=True)
            return

        embed = discord.Embed(
            title=f'🎯 {challenge["title"]}',
            description=challenge["description"],
            color=discord.Color.blue()
        )
        embed.add_field(name='Difficulty', value=challenge["difficulty"], inline=True)
        embed.add_field(name='Week', value=f'Week {challenge["week"]}', inline=True)
        embed.add_field(name='Submissions', value=str(len(challenge.get("submissions", []))), inline=True)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Challenges(bot))