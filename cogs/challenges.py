import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from utils.constants import SUPPORTED_LANGUAGES
import asyncio

class Challenges(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = bot.data_manager
        self.auto_close_tasks = {}

    def cog_unload(self):
        """Cancel all auto-close tasks when cog unloads"""
        for task in self.auto_close_tasks.values():
            task.cancel()

    def has_trainer_role(self, interaction: discord.Interaction):
        allowed_roles = ['formateur', 'admin', 'moderator']
        return any(role.name.lower() in allowed_roles for role in interaction.user.roles)

    @app_commands.command(name='postchallenge', description='Post a new weekly challenge with auto-close timer')
    @app_commands.describe(
        title='Challenge title',
        description='Challenge description',
        difficulty='Difficulty level',
        duration='Duration in minutes before auto-close (default: 30 min, max: 1440 = 24h)',
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
        duration: int = 30,
        language: app_commands.Choice[str] = None
    ):
        if not self.has_trainer_role(interaction):
            await interaction.response.send_message('❌ Only trainers can post challenges!', ephemeral=True)
            return

        # Validate duration (1 minute to 24 hours = 1440 minutes)
        if not (1 <= duration <= 1440):
            await interaction.response.send_message('❌ Duration must be between 1-1440 minutes (1 min to 24 hours)!', ephemeral=True)
            return

        # Default to 'any' if no language specified
        lang_key = language.value if language else 'any'
        lang_info = SUPPORTED_LANGUAGES.get(lang_key, SUPPORTED_LANGUAGES['any'])

        week_number = datetime.now().isocalendar()[1]
        close_time = datetime.now() + timedelta(minutes=duration)
        
        challenge_data = {
            'title': title,
            'description': description,
            'difficulty': difficulty.value,
            'language': lang_key,
            'week': week_number,
            'posted_by': interaction.user.id,
            'posted_at': datetime.now().isoformat(),
            'close_time': close_time.isoformat(),
            'duration_minutes': duration,
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
        
        # Show duration and close time
        days = duration // 24
        hours = duration % 24
        duration_text = f'{days}d {hours}h' if days > 0 else f'{hours}h'
        
        embed.add_field(
            name='⏰ Auto-Close',
            value=f'In {duration_text}\n{close_time.strftime("%b %d at %I:%M %p")}',
            inline=True
        )
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

        challenge_message = await interaction.response.send_message(
            content='@everyone 🚨 **New Coding Challenge!**',
            embed=embed
        )
        
        # Start auto-close timer
        task_key = f"{interaction.guild.id}_{challenge_id}"
        task = asyncio.create_task(
            self._auto_close_challenge(
                interaction.guild,
                interaction.channel,
                challenge_id,
                duration,
                lang_info
            )
        )
        self.auto_close_tasks[task_key] = task
        
        print(f'✅ Challenge created in {interaction.guild.name}: {title} ({lang_info["name"]}, ID: {challenge_id}, closes in {duration}m)')

    async def _auto_close_challenge(self, guild: discord.Guild, channel: discord.TextChannel, challenge_id: int, duration_minutes: float, lang_info: dict):
        """Automatically close challenge after specified duration"""
        try:
            # Wait for the duration (convert minutes to seconds)
            await asyncio.sleep(duration_minutes * 60)
            
            # Get challenge data
            challenge = self.data_manager.get_challenge_by_id(guild.id, challenge_id)
            
            if not challenge or challenge['status'] != 'active':
                return
            
            # Close the challenge
            self.data_manager.update_challenge(guild.id, challenge_id, {'status': 'closed'})
            
            # Send closure message
            hours = int(duration_minutes // 60)
            minutes = int(duration_minutes % 60)
            
            if hours > 0 and minutes > 0:
                duration_text = f'{hours} hours {minutes} minutes'
            elif hours > 0:
                duration_text = f'{hours} hours'
            else:
                duration_text = f'{minutes} minutes'
            
            embed = discord.Embed(
                title='⏰ Challenge Auto-Closed!',
                description=f"**{challenge['title']}** has automatically closed after {duration_text}.",
                color=discord.Color.red()
            )
            embed.add_field(name='Total Submissions', value=str(len(challenge.get('submissions', []))), inline=True)
            embed.add_field(name='Week', value=f"Week {challenge['week']}", inline=True)
            embed.add_field(name='Language', value=f'{lang_info["emoji"]} {lang_info["name"]}', inline=True)
            embed.add_field(
                name='📝 Next Steps',
                value='Trainers: Use `/awardwinners` to announce the top 3!',
                inline=False
            )
            embed.set_footer(text=f'{guild.name} • No more submissions accepted')
            embed.timestamp = datetime.now()
            
            await channel.send(embed=embed)
            
            # Clean up task
            task_key = f"{guild.id}_{challenge_id}"
            if task_key in self.auto_close_tasks:
                del self.auto_close_tasks[task_key]
            
            print(f'⏰ Auto-closed challenge #{challenge_id} in {guild.name}')
            
        except asyncio.CancelledError:
            print(f'⚠️ Auto-close task cancelled for challenge #{challenge_id}')
        except Exception as e:
            print(f'❌ Error auto-closing challenge #{challenge_id}: {e}')

    @app_commands.command(name='closechallenge', description='Manually close the current challenge')
    async def close_challenge(self, interaction: discord.Interaction):
        if not self.has_trainer_role(interaction):
            await interaction.response.send_message('❌ Only trainers!', ephemeral=True)
            return

        active_challenge = self.data_manager.get_active_challenge(interaction.guild.id)
        if not active_challenge:
            await interaction.response.send_message('❌ No active challenge!', ephemeral=True)
            return

        # Cancel auto-close task if exists
        task_key = f"{interaction.guild.id}_{active_challenge['id']}"
        if task_key in self.auto_close_tasks:
            self.auto_close_tasks[task_key].cancel()
            del self.auto_close_tasks[task_key]

        self.data_manager.update_challenge(interaction.guild.id, active_challenge['id'], {'status': 'closed'})

        lang_key = active_challenge.get('language', 'any')
        lang_info = SUPPORTED_LANGUAGES.get(lang_key, SUPPORTED_LANGUAGES['any'])

        embed = discord.Embed(
            title='🏁 Challenge Manually Closed!',
            description=f"**{active_challenge['title']}** has been closed by {interaction.user.mention}.",
            color=discord.Color.red()
        )
        embed.add_field(name='Total Submissions', value=str(len(active_challenge.get('submissions', []))), inline=True)
        embed.add_field(name='Week', value=f"Week {active_challenge['week']}", inline=True)
        embed.add_field(name='Language', value=f'{lang_info["emoji"]} {lang_info["name"]}', inline=True)
        embed.set_footer(text=interaction.guild.name)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='extendchallenge', description='Extend the auto-close time of active challenge')
    @app_commands.describe(minutes='Additional minutes to extend (1-1440)')
    async def extend_challenge(self, interaction: discord.Interaction, minutes: int):
        if not self.has_trainer_role(interaction):
            await interaction.response.send_message('❌ Only trainers!', ephemeral=True)
            return

        if not (1 <= minutes <= 1440):
            await interaction.response.send_message('❌ Extension must be 1-1440 minutes (1 min to 24 hours)!', ephemeral=True)
            return

        active_challenge = self.data_manager.get_active_challenge(interaction.guild.id)
        if not active_challenge:
            await interaction.response.send_message('❌ No active challenge!', ephemeral=True)
            return

        # Cancel existing auto-close task
        task_key = f"{interaction.guild.id}_{active_challenge['id']}"
        if task_key in self.auto_close_tasks:
            self.auto_close_tasks[task_key].cancel()
            del self.auto_close_tasks[task_key]

        # Calculate new close time
        old_close_time = datetime.fromisoformat(active_challenge['close_time'])
        new_close_time = old_close_time + timedelta(minutes=minutes)
        new_duration_minutes = active_challenge['duration_minutes'] + minutes

        # Update challenge
        self.data_manager.update_challenge(interaction.guild.id, active_challenge['id'], {
            'close_time': new_close_time.isoformat(),
            'duration_minutes': new_duration_minutes
        })

        # Calculate remaining time in minutes
        remaining_minutes = (new_close_time - datetime.now()).total_seconds() / 60

        # Start new auto-close task
        lang_key = active_challenge.get('language', 'any')
        lang_info = SUPPORTED_LANGUAGES.get(lang_key, SUPPORTED_LANGUAGES['any'])
        
        task = asyncio.create_task(
            self._auto_close_challenge(
                interaction.guild,
                interaction.channel,
                active_challenge['id'],
                remaining_minutes,
                lang_info
            )
        )
        self.auto_close_tasks[task_key] = task

        hours_ext = minutes // 60
        mins_ext = minutes % 60
        
        if hours_ext > 0 and mins_ext > 0:
            ext_text = f'{hours_ext}h {mins_ext}min'
        elif hours_ext > 0:
            ext_text = f'{hours_ext}h'
        else:
            ext_text = f'{mins_ext}min'

        remaining_hours = int(remaining_minutes // 60)
        remaining_mins = int(remaining_minutes % 60)
        
        if remaining_hours > 0 and remaining_mins > 0:
            remaining_text = f'{remaining_hours}h {remaining_mins}min'
        elif remaining_hours > 0:
            remaining_text = f'{remaining_hours}h'
        else:
            remaining_text = f'{remaining_mins}min'

        embed = discord.Embed(
            title='⏰ Challenge Extended!',
            description=f"**{active_challenge['title']}** extended by {ext_text}.",
            color=discord.Color.green()
        )
        embed.add_field(name='New Close Time', value=new_close_time.strftime("%b %d at %I:%M %p"), inline=True)
        embed.add_field(name='Time Remaining', value=remaining_text, inline=True)
        embed.set_footer(text=interaction.guild.name)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='challengetimer', description='Check time remaining for active challenge')
    async def challenge_timer(self, interaction: discord.Interaction):
        active_challenge = self.data_manager.get_active_challenge(interaction.guild.id)
        
        if not active_challenge:
            await interaction.response.send_message('❌ No active challenge!', ephemeral=True)
            return

        close_time = datetime.fromisoformat(active_challenge['close_time'])
        time_left = close_time - datetime.now()
        
        if time_left.total_seconds() <= 0:
            await interaction.response.send_message('⏰ Challenge should be closed!', ephemeral=True)
            return

        total_minutes = int(time_left.total_seconds() / 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60

        lang_key = active_challenge.get('language', 'any')
        lang_info = SUPPORTED_LANGUAGES.get(lang_key, SUPPORTED_LANGUAGES['any'])

        embed = discord.Embed(
            title=f'⏰ {active_challenge["title"]}',
            description='Time remaining until auto-close',
            color=discord.Color.blue()
        )
        
        if hours > 0 and minutes > 0:
            time_text = f'{hours}h {minutes}min'
        elif hours > 0:
            time_text = f'{hours}h'
        else:
            time_text = f'{minutes}min'
        
        embed.add_field(name='⏱️ Time Left', value=time_text, inline=True)
        embed.add_field(name='Closes At', value=close_time.strftime("%b %d at %I:%M %p"), inline=True)
        embed.add_field(name='Submissions', value=str(len(active_challenge.get('submissions', []))), inline=True)
        embed.add_field(name='Language', value=f'{lang_info["emoji"]} {lang_info["name"]}', inline=True)
        embed.add_field(name='Difficulty', value=active_challenge['difficulty'], inline=True)
        embed.add_field(name='Week', value=f"Week {active_challenge['week']}", inline=True)
        
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
        
        # Show time remaining
        if 'close_time' in challenge:
            close_time = datetime.fromisoformat(challenge['close_time'])
            time_left = close_time - datetime.now()
            if time_left.total_seconds() > 0:
                total_minutes = int(time_left.total_seconds() / 60)
                hours = total_minutes // 60
                minutes = total_minutes % 60
                
                if hours > 0 and minutes > 0:
                    time_text = f'{hours}h {minutes}min'
                elif hours > 0:
                    time_text = f'{hours}h'
                else:
                    time_text = f'{minutes}min'
                    
                embed.add_field(name='⏰ Closes In', value=time_text, inline=True)
        
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
        
        popular = ['python', 'javascript', 'java', 'cpp', 'csharp']
        
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