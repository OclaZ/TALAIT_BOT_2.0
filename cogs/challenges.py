import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from utils.constants import SUPPORTED_LANGUAGES

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
        difficulty='Difficulty level',
        language='Programming language (optional, defaults to Any Language)'
    )
    @app_commands.choices(
        difficulty=[
            app_commands.Choice(name='Easy', value='Easy'),
            app_commands.Choice(name='Medium', value='Medium'),
            app_commands.Choice(name='Hard', value='Hard')
        ],
        language=[
            app_commands.Choice(name='🌐 Any Language', value='any'),
            app_commands.Choice(name='🐍 Python', value='python'),
            app_commands.Choice(name='📜 JavaScript', value='javascript'),
            app_commands.Choice(name='☕ Java', value='java'),
            app_commands.Choice(name='⚡ C++', value='cpp'),
            app_commands.Choice(name='🔧 C', value='c'),
            app_commands.Choice(name='💎 C#', value='csharp'),
            app_commands.Choice(name='🔷 Go', value='go'),
            app_commands.Choice(name='🦀 Rust', value='rust'),
            app_commands.Choice(name='🐘 PHP', value='php'),
            app_commands.Choice(name='💎 Ruby', value='ruby'),
            app_commands.Choice(name='🦅 Swift', value='swift'),
            app_commands.Choice(name='🎯 Kotlin', value='kotlin'),
            app_commands.Choice(name='📘 TypeScript', value='typescript'),
            app_commands.Choice(name='🗃️ SQL', value='sql')
        ]
    )
    async def post_challenge(
        self, 
        interaction: discord.Interaction, 
        title: str, 
        description: str, 
        difficulty: app_commands.Choice[str],
        language: app_commands.Choice[str] = None
    ):
        if not self.has_trainer_role(interaction):
            await interaction.response.send_message('❌ Only trainers can post challenges!', ephemeral=True)
            return

        # Default to 'any' if no language specified
        lang_key = language.value if language else 'any'
        lang_info = SUPPORTED_LANGUAGES.get(lang_key, SUPPORTED_LANGUAGES['any'])

        week_number = datetime.now().isocalendar()[1]
        challenge_data = {
            'title': title,
            'description': description,
            'difficulty': difficulty.value,
            'language': lang_key,
            'week': week_number,
            'posted_by': interaction.user.id,
            'posted_at': datetime.now().isoformat(),
            'status': 'active',
            'submissions': []
        }

        challenge_id = self.data_manager.create_challenge(interaction.guild.id, challenge_data)

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
        embed.add_field(name='💻 Language', value=f'{lang_info["emoji"]} {lang_info["name"]}', inline=True)
        embed.add_field(name='👤 Posted by', value=interaction.user.mention, inline=True)
        
        # Show code example if not "any language"
        if lang_key != 'any':
            code_example = f'```{lang_info["code_block"]}\n{lang_info["example"]}\n```'
            embed.add_field(
                name=f'📝 Example ({lang_info["name"]})',
                value=code_example,
                inline=False
            )
        
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
        
        embed.set_footer(text=f'{interaction.guild.name} • {datetime.now().strftime("%B %d, %Y")}')
        embed.timestamp = datetime.now()

        await interaction.response.send_message(
            content='@everyone 🚨 **New Coding Challenge!**',
            embed=embed
        )
        
        print(f'✅ Challenge created in {interaction.guild.name}: {title} ({lang_info["name"]}, ID: {challenge_id})')

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

        lang_key = active_challenge.get('language', 'any')
        lang_info = SUPPORTED_LANGUAGES.get(lang_key, SUPPORTED_LANGUAGES['any'])

        embed = discord.Embed(
            title='🏁 Challenge Closed!',
            description=f"**{active_challenge['title']}** is now closed.",
            color=discord.Color.red()
        )
        embed.add_field(name='Total Submissions', value=str(len(active_challenge.get('submissions', []))), inline=True)
        embed.add_field(name='Week', value=f"Week {active_challenge['week']}", inline=True)
        embed.add_field(name='Language', value=f'{lang_info["emoji"]} {lang_info["name"]}', inline=True)
        embed.set_footer(text=interaction.guild.name)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='awardwinners', description='Award XP to the top 3 winners')
    @app_commands.describe(
        first='1st place winner',
        second='2nd place winner (optional)',
        third='3rd place winner (optional)'
    )
    async def award_winners(
        self, 
        interaction: discord.Interaction, 
        first: discord.Member, 
        second: discord.Member = None, 
        third: discord.Member = None
    ):
        if not self.has_trainer_role(interaction):
            await interaction.response.send_message('❌ Only trainers!', ephemeral=True)
            return

        challenge = self.data_manager.get_active_challenge(interaction.guild.id) or \
                   self.data_manager.get_latest_challenge(interaction.guild.id)
        if not challenge:
            await interaction.response.send_message('❌ No challenge found!', ephemeral=True)
            return

        week_key = f"week_{challenge['week']}"
        winners = []

        self.data_manager.ensure_user(interaction.guild.id, first.id, first.name)
        self.data_manager.add_xp(interaction.guild.id, first.id, 10, week_key)
        self.data_manager.add_badge(interaction.guild.id, first.id, f"🥇 Winner W{challenge['week']}")
        winners.append(f"🥇 {first.mention} - **10 XP**")

        if second:
            self.data_manager.ensure_user(interaction.guild.id, second.id, second.name)
            self.data_manager.add_xp(interaction.guild.id, second.id, 7, week_key)
            self.data_manager.add_badge(interaction.guild.id, second.id, f"🥈 2nd Place W{challenge['week']}")
            winners.append(f"🥈 {second.mention} - **7 XP**")

        if third:
            self.data_manager.ensure_user(interaction.guild.id, third.id, third.name)
            self.data_manager.add_xp(interaction.guild.id, third.id, 5, week_key)
            self.data_manager.add_badge(interaction.guild.id, third.id, f"🥉 3rd Place W{challenge['week']}")
            winners.append(f"🥉 {third.mention} - **5 XP**")

        lang_key = challenge.get('language', 'any')
        lang_info = SUPPORTED_LANGUAGES.get(lang_key, SUPPORTED_LANGUAGES['any'])

        embed = discord.Embed(
            title='🎉 Winners Announced!',
            description=f"**{challenge['title']}** - Week {challenge['week']}\n{lang_info['emoji']} {lang_info['name']}\n\n" + "\n".join(winners),
            color=discord.Color.gold()
        )
        embed.set_footer(text=f'{interaction.guild.name} • Congratulations! 🎊')

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='activechallenge', description='View the current active challenge')
    async def active_challenge(self, interaction: discord.Interaction):
        challenge = self.data_manager.get_active_challenge(interaction.guild.id)
        
        if not challenge:
            await interaction.response.send_message('❌ No active challenge!', ephemeral=True)
            return

        lang_key = challenge.get('language', 'any')
        lang_info = SUPPORTED_LANGUAGES.get(lang_key, SUPPORTED_LANGUAGES['any'])

        embed = discord.Embed(
            title=f'🎯 {challenge["title"]}',
            description=challenge["description"],
            color=discord.Color.blue()
        )
        embed.add_field(name='Difficulty', value=challenge["difficulty"], inline=True)
        embed.add_field(name='Week', value=f'Week {challenge["week"]}', inline=True)
        embed.add_field(name='Language', value=f'{lang_info["emoji"]} {lang_info["name"]}', inline=True)
        embed.add_field(name='Submissions', value=str(len(challenge.get("submissions", []))), inline=True)
        
        if lang_key != 'any':
            code_example = f'```{lang_info["code_block"]}\n{lang_info["example"]}\n```'
            embed.add_field(name=f'Example ({lang_info["name"]})', value=code_example, inline=False)
        
        embed.set_footer(text=interaction.guild.name)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='languages', description='View all supported programming languages')
    async def list_languages(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title='💻 Supported Programming Languages',
            description='talAIt bot supports code analysis for all these languages!',
            color=discord.Color.blue()
        )
        
        # Group languages
        popular = ['python', 'javascript', 'java', 'cpp', 'csharp']
        web = ['javascript', 'typescript', 'php', 'sql']
        systems = ['c', 'cpp', 'rust', 'go']
        mobile = ['swift', 'kotlin', 'java']
        
        popular_langs = '\n'.join([
            f"{SUPPORTED_LANGUAGES[lang]['emoji']} **{SUPPORTED_LANGUAGES[lang]['name']}**"
            for lang in popular if lang in SUPPORTED_LANGUAGES
        ])
        
        other_langs = '\n'.join([
            f"{info['emoji']} **{info['name']}**"
            for key, info in SUPPORTED_LANGUAGES.items()
            if key not in popular and key != 'any'
        ])
        
        embed.add_field(name='🌟 Popular', value=popular_langs, inline=False)
        embed.add_field(name='📚 Other Languages', value=other_langs, inline=False)
        embed.add_field(
            name='🌐 Any Language',
            value=f"{SUPPORTED_LANGUAGES['any']['emoji']} Trainers can allow any language!",
            inline=False
        )
        
        embed.set_footer(text='Use /postchallenge to specify a language')
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Challenges(bot))