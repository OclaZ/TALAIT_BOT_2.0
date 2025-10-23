import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional

class PomodoroTimer:
    def __init__(self, user_id: int, guild_id: int):
        self.user_id = user_id
        self.guild_id = guild_id
        self.work_time = 25  # minutes
        self.short_break = 5  # minutes
        self.long_break = 15  # minutes
        self.sessions_until_long = 4
        self.current_session = 0
        self.is_running = False
        self.is_break = False
        self.timer_task = None
        self.end_time = None
        self.paused_time_left = None
        self.status_message = None
        self.status_message_channel = None
        self.is_stopped = False
        
    def start_work(self):
        self.is_running = True
        self.is_break = False
        self.current_session += 1
        self.end_time = datetime.now() + timedelta(minutes=self.work_time)
        
    def start_break(self):
        self.is_running = True
        self.is_break = True
        is_long = (self.current_session % self.sessions_until_long) == 0
        duration = self.long_break if is_long else self.short_break
        self.end_time = datetime.now() + timedelta(minutes=duration)
        return is_long
        
    def pause(self):
        if self.is_running and self.end_time:
            self.paused_time_left = (self.end_time - datetime.now()).total_seconds()
            self.is_running = False
            return True
        return False
        
    def resume(self):
        if not self.is_running and self.paused_time_left:
            self.end_time = datetime.now() + timedelta(seconds=self.paused_time_left)
            self.is_running = True
            self.paused_time_left = None
            return True
        return False
        
    def stop(self):
        self.is_running = False
        self.is_break = False
        self.paused_time_left = None
        self.end_time = None
        self.is_stopped = True
        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()
        
    def reset_sessions(self):
        self.current_session = 0
        
    def get_time_left(self) -> Optional[int]:
        if self.end_time:
            seconds = (self.end_time - datetime.now()).total_seconds()
            return max(0, int(seconds))
        return None
        
    def get_status_emoji(self):
        if not self.is_running:
            return '⏸️' if self.paused_time_left else '⏹️'
        return '☕' if self.is_break else '🍅'


class Pomodoro(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_timers: Dict[int, PomodoroTimer] = {}
        
    def _get_timer_key(self, user_id: int, guild_id: int) -> int:
        return hash(f"{guild_id}_{user_id}")
        
    def _get_timer(self, user_id: int, guild_id: int) -> Optional[PomodoroTimer]:
        key = self._get_timer_key(user_id, guild_id)
        return self.active_timers.get(key)
        
    def _create_timer(self, user_id: int, guild_id: int) -> PomodoroTimer:
        key = self._get_timer_key(user_id, guild_id)
        timer = PomodoroTimer(user_id, guild_id)
        self.active_timers[key] = timer
        return timer
    
    def _remove_timer(self, user_id: int, guild_id: int):
        key = self._get_timer_key(user_id, guild_id)
        if key in self.active_timers:
            del self.active_timers[key]

    @app_commands.command(name='pomodoro', description='Start a Pomodoro timer with live updates')
    @app_commands.describe(
        work='Work duration in minutes (default: 25)',
        short_break='Short break duration (default: 5)',
        long_break='Long break duration (default: 15)',
        sessions='Sessions until long break (default: 4)'
    )
    async def start_pomodoro(
        self, 
        interaction: discord.Interaction,
        work: int = 25,
        short_break: int = 5,
        long_break: int = 15,
        sessions: int = 4
    ):
        # Validate inputs
        if not (1 <= work <= 120):
            await interaction.response.send_message('❌ Work time must be between 1-120 minutes!', ephemeral=True)
            return
        if not (1 <= short_break <= 60):
            await interaction.response.send_message('❌ Short break must be between 1-60 minutes!', ephemeral=True)
            return
        if not (1 <= long_break <= 60):
            await interaction.response.send_message('❌ Long break must be between 1-60 minutes!', ephemeral=True)
            return
        if not (1 <= sessions <= 10):
            await interaction.response.send_message('❌ Sessions must be between 1-10!', ephemeral=True)
            return
            
        timer = self._get_timer(interaction.user.id, interaction.guild.id)
        
        if timer and timer.is_running:
            await interaction.response.send_message('❌ You already have an active Pomodoro! Use `/pomodoro-stop` first.', ephemeral=True)
            return
            
        # Create or update timer
        if not timer:
            timer = self._create_timer(interaction.user.id, interaction.guild.id)
            
        timer.work_time = work
        timer.short_break = short_break
        timer.long_break = long_break
        timer.sessions_until_long = sessions
        timer.start_work()
        
        embed = discord.Embed(
            title='🍅 Pomodoro Started!',
            description=f'{interaction.user.mention} is focusing...',
            color=discord.Color.red()
        )
        embed.add_field(name='⏰ Work Time', value=f'{work} minutes', inline=True)
        embed.add_field(name='☕ Short Break', value=f'{short_break} minutes', inline=True)
        embed.add_field(name='🌙 Long Break', value=f'{long_break} minutes', inline=True)
        embed.add_field(name='🔄 Sessions Until Long', value=f'{sessions}', inline=True)
        embed.add_field(name='📍 Current Session', value=f'#{timer.current_session}', inline=True)
        embed.set_footer(text='Stay focused! Live timer below...')
        
        await interaction.response.send_message(embed=embed)
        
        # Create live timer message
        timer_embed = self._create_timer_embed(timer, interaction.user)
        timer_message = await interaction.channel.send(embed=timer_embed)
        timer.status_message = timer_message
        timer.status_message_channel = interaction.channel
        
        # Start timer loop
        timer.timer_task = asyncio.create_task(self._run_timer(interaction.user, interaction.guild, timer))
        timer.is_stopped = False

    @app_commands.command(name='pomodoro-status', description='Check your Pomodoro timer status')
    async def pomodoro_status(self, interaction: discord.Interaction):
        timer = self._get_timer(interaction.user.id, interaction.guild.id)
        
        if not timer:
            await interaction.response.send_message('❌ You don\'t have an active Pomodoro timer!', ephemeral=True)
            return
            
        time_left = timer.get_time_left()
        
        if not time_left and not timer.paused_time_left:
            await interaction.response.send_message('❌ No active timer!', ephemeral=True)
            return
            
        minutes_left = (timer.paused_time_left or time_left) // 60
        seconds_left = (timer.paused_time_left or time_left) % 60
        
        status = 'Break' if timer.is_break else 'Work'
        emoji = timer.get_status_emoji()
        
        embed = discord.Embed(
            title=f'{emoji} Pomodoro Status',
            color=discord.Color.orange() if timer.is_break else discord.Color.red()
        )
        
        embed.add_field(name='Mode', value=status, inline=True)
        embed.add_field(name='Time Left', value=f'{minutes_left}m {seconds_left}s', inline=True)
        embed.add_field(name='Session', value=f'#{timer.current_session}', inline=True)
        
        embed.add_field(name='⏰ Config', value=f'Work: {timer.work_time}m | Short: {timer.short_break}m | Long: {timer.long_break}m', inline=False)
        
        if timer.paused_time_left:
            embed.add_field(name='⏸️ Status', value='Paused', inline=False)
        elif timer.is_running:
            embed.add_field(name='▶️ Status', value='Running', inline=False)
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='pomodoro-pause', description='Pause your Pomodoro timer')
    async def pomodoro_pause(self, interaction: discord.Interaction):
        timer = self._get_timer(interaction.user.id, interaction.guild.id)
        
        if not timer:
            await interaction.response.send_message('❌ You don\'t have an active timer!', ephemeral=True)
            return
            
        if timer.pause():
            time_left = int(timer.paused_time_left)
            minutes = time_left // 60
            seconds = time_left % 60
            
            await interaction.response.send_message(
                f'⏸️ Pomodoro paused! Time remaining: {minutes}m {seconds}s\nUse `/pomodoro-resume` to continue.',
                ephemeral=True
            )
        else:
            await interaction.response.send_message('❌ Timer is not running!', ephemeral=True)

    @app_commands.command(name='pomodoro-resume', description='Resume your Pomodoro timer')
    async def pomodoro_resume(self, interaction: discord.Interaction):
        timer = self._get_timer(interaction.user.id, interaction.guild.id)
        
        if not timer:
            await interaction.response.send_message('❌ You don\'t have an active timer!', ephemeral=True)
            return
            
        if timer.resume():
            await interaction.response.send_message('▶️ Pomodoro resumed!', ephemeral=True)
            # Restart timer loop
            timer.timer_task = asyncio.create_task(self._run_timer(interaction.user, interaction.guild, timer))
            timer.is_stopped = False
        else:
            await interaction.response.send_message('❌ Timer is not paused!', ephemeral=True)

    @app_commands.command(name='pomodoro-stop', description='Stop your Pomodoro timer completely')
    async def pomodoro_stop(self, interaction: discord.Interaction):
        timer = self._get_timer(interaction.user.id, interaction.guild.id)
        
        if not timer:
            await interaction.response.send_message('❌ You don\'t have an active timer!', ephemeral=True)
            return
            
        sessions_completed = timer.current_session
        
        # Stop the timer and cancel the task
        timer.stop()
        
        # Delete live timer message if it exists
        if timer.status_message:
            try:
                await timer.status_message.delete()
            except:
                pass
        
        # Remove timer completely
        self._remove_timer(interaction.user.id, interaction.guild.id)
        
        embed = discord.Embed(
            title='🛑 Pomodoro Stopped',
            description=f'Timer completely stopped. You completed **{sessions_completed}** session(s).',
            color=discord.Color.blue()
        )
        embed.set_footer(text='Use /pomodoro to start a new session!')
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='pomodoro-skip', description='Skip to the next Pomodoro phase')
    async def pomodoro_skip(self, interaction: discord.Interaction):
        timer = self._get_timer(interaction.user.id, interaction.guild.id)
        
        if not timer or not timer.is_running:
            await interaction.response.send_message('❌ You don\'t have an active timer!', ephemeral=True)
            return
            
        current_phase = 'break' if timer.is_break else 'work'
        
        # End current phase immediately
        timer.end_time = datetime.now()
        
        await interaction.response.send_message(f'⏭️ Skipped {current_phase} phase!', ephemeral=True)

    @app_commands.command(name='pomodoro-focusing', description='View all users currently focusing')
    async def pomodoro_focusing(self, interaction: discord.Interaction):
        focusing_users = []
        
        for timer in self.active_timers.values():
            if timer.guild_id == interaction.guild.id and timer.is_running and not timer.is_break:
                try:
                    user = await self.bot.fetch_user(timer.user_id)
                    time_left = timer.get_time_left()
                    minutes = time_left // 60
                    seconds = time_left % 60
                    focusing_users.append((user, timer, minutes, seconds))
                except:
                    continue
        
        if not focusing_users:
            await interaction.response.send_message('🍅 No one is focusing right now!', ephemeral=True)
            return
        
        embed = discord.Embed(
            title='🍅 Currently Focusing',
            description=f'{len(focusing_users)} member(s) are in focus mode',
            color=discord.Color.red()
        )
        
        for user, timer, minutes, seconds in focusing_users:
            embed.add_field(
                name=f'🔴 {user.name}',
                value=f'Session #{timer.current_session} • {minutes}m {seconds}s left',
                inline=False
            )
        
        embed.set_footer(text='Keep up the great work! 💪')
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='pomodoro-onbreak', description='View all users currently on break')
    async def pomodoro_onbreak(self, interaction: discord.Interaction):
        break_users = []
        
        for timer in self.active_timers.values():
            if timer.guild_id == interaction.guild.id and timer.is_running and timer.is_break:
                try:
                    user = await self.bot.fetch_user(timer.user_id)
                    time_left = timer.get_time_left()
                    minutes = time_left // 60
                    seconds = time_left % 60
                    is_long = (timer.current_session % timer.sessions_until_long) == 0
                    break_users.append((user, timer, minutes, seconds, is_long))
                except:
                    continue
        
        if not break_users:
            await interaction.response.send_message('☕ No one is on break right now!', ephemeral=True)
            return
        
        embed = discord.Embed(
            title='☕ Currently On Break',
            description=f'{len(break_users)} member(s) are taking a break',
            color=discord.Color.orange()
        )
        
        for user, timer, minutes, seconds, is_long in break_users:
            break_type = '🌙 Long Break' if is_long else '☕ Short Break'
            embed.add_field(
                name=f'{user.name}',
                value=f'{break_type} • {minutes}m {seconds}s left',
                inline=False
            )
        
        embed.set_footer(text='Enjoy your rest! 😊')
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='pomodoro-leaderboard', description='View Pomodoro leaderboard')
    async def pomodoro_leaderboard(self, interaction: discord.Interaction):
        # Count active sessions per user
        user_sessions = {}
        
        for timer in self.active_timers.values():
            if timer.guild_id == interaction.guild.id and timer.current_session > 0:
                user_id = timer.user_id
                if user_id not in user_sessions:
                    user_sessions[user_id] = 0
                user_sessions[user_id] += timer.current_session
        
        if not user_sessions:
            await interaction.response.send_message('📊 No Pomodoro sessions yet! Start one with `/pomodoro`', ephemeral=True)
            return
            
        sorted_users = sorted(user_sessions.items(), key=lambda x: x[1], reverse=True)
        
        embed = discord.Embed(
            title='🍅 Pomodoro Leaderboard',
            description=f'Most productive members in {interaction.guild.name}',
            color=discord.Color.red()
        )
        
        medals = ['🥇', '🥈', '🥉']
        
        for idx, (user_id, sessions) in enumerate(sorted_users[:10]):
            try:
                user = await self.bot.fetch_user(user_id)
                medal = medals[idx] if idx < 3 else f'{idx + 1}.'
                embed.add_field(
                    name=f'{medal} {user.name}',
                    value=f'{sessions} sessions 🍅',
                    inline=False
                )
            except:
                continue
                
        embed.set_footer(text='Keep up the great work! 💪')
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='pomodoro-help', description='Learn how to use Pomodoro timers')
    async def pomodoro_help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title='🍅 Pomodoro Technique Guide',
            description='A time management method to boost productivity!',
            color=discord.Color.red()
        )
        
        embed.add_field(
            name='📚 What is Pomodoro?',
            value='Work in focused 25-minute intervals with short breaks in between.',
            inline=False
        )
        
        embed.add_field(
            name='🎯 How It Works',
            value=(
                '1️⃣ Work for 25 minutes (1 Pomodoro)\n'
                '2️⃣ Take a 5-minute break\n'
                '3️⃣ After 4 Pomodoros, take a 15-minute break\n'
                '4️⃣ Repeat!'
            ),
            inline=False
        )
        
        embed.add_field(
            name='💻 Commands',
            value=(
                '`/pomodoro` - Start timer with live updates\n'
                '`/pomodoro-status` - Check current timer\n'
                '`/pomodoro-pause` - Pause timer\n'
                '`/pomodoro-resume` - Resume timer\n'
                '`/pomodoro-skip` - Skip to next phase\n'
                '`/pomodoro-stop` - Stop timer completely\n'
                '`/pomodoro-focusing` - See who\'s focusing\n'
                '`/pomodoro-onbreak` - See who\'s on break\n'
                '`/pomodoro-leaderboard` - View rankings'
            ),
            inline=False
        )
        
        embed.add_field(
            name='⚙️ Custom Configuration',
            value=(
                'Example: `/pomodoro work:30 short_break:10 long_break:20 sessions:3`\n'
                'Customize every parameter to fit your workflow!'
            ),
            inline=False
        )
        
        embed.add_field(
            name='💡 Tips',
            value=(
                '• Use DMs for notifications\n'
                '• Eliminate distractions during work\n'
                '• Actually take your breaks!\n'
                '• Track your sessions with leaderboard'
            ),
            inline=False
        )
        
        embed.set_footer(text='Stay focused and productive! 🚀')
        
        await interaction.response.send_message(embed=embed)

    def _create_timer_embed(self, timer: PomodoroTimer, user: discord.User) -> discord.Embed:
        """Create a live timer embed"""
        time_left = timer.get_time_left() or 0
        minutes = time_left // 60
        seconds = time_left % 60
        
        status = 'Break Time ☕' if timer.is_break else 'Focus Time 🍅'
        color = discord.Color.orange() if timer.is_break else discord.Color.red()
        
        embed = discord.Embed(
            title=f'{status}',
            description=f'**{user.name}** - Session #{timer.current_session}',
            color=color
        )
        
        # Progress bar
        total_seconds = (timer.long_break if timer.is_break and (timer.current_session % timer.sessions_until_long) == 0 
                        else timer.short_break if timer.is_break else timer.work_time) * 60
        progress = int((1 - time_left / total_seconds) * 20)
        bar = '█' * progress + '░' * (20 - progress)
        
        embed.add_field(
            name='⏱️ Time Remaining',
            value=f'```{minutes:02d}:{seconds:02d}```\n{bar}',
            inline=False
        )
        
        embed.set_footer(text='Updates every 5 seconds')
        embed.timestamp = datetime.now()
        
        return embed

    async def _run_timer(self, user: discord.User, guild: discord.Guild, timer: PomodoroTimer):
        """Main timer loop with live updates"""
        try:
            last_update = datetime.now()
            
            while timer.is_running and not timer.is_stopped:
                time_left = timer.get_time_left()
                
                # Update live message every 5 seconds
                if timer.status_message and (datetime.now() - last_update).total_seconds() >= 5:
                    try:
                        updated_embed = self._create_timer_embed(timer, user)
                        await timer.status_message.edit(embed=updated_embed)
                        last_update = datetime.now()
                    except:
                        pass
                
                if time_left is None or time_left <= 0:
                    # Check if timer was stopped
                    if timer.is_stopped:
                        break
                        
                    # Timer finished
                    if timer.is_break:
                        # Break ended, start work
                        embed = discord.Embed(
                            title='✅ Break Time Over!',
                            description=f'Time to get back to work! 💪',
                            color=discord.Color.green()
                        )
                        embed.add_field(name='Next Session', value=f'#{timer.current_session + 1}', inline=True)
                        embed.set_footer(text='Ready to focus?')
                        
                        try:
                            await user.send(embed=embed)
                        except:
                            pass
                        
                        # Check again if stopped before starting new session
                        if timer.is_stopped:
                            break
                            
                        timer.start_work()
                        
                    else:
                        # Work ended, start break
                        is_long_break = timer.start_break()
                        break_type = 'Long' if is_long_break else 'Short'
                        duration = timer.long_break if is_long_break else timer.short_break
                        
                        embed = discord.Embed(
                            title='🎉 Work Session Complete!',
                            description=f'Great job! Take a {break_type.lower()} break.',
                            color=discord.Color.gold()
                        )
                        embed.add_field(name='Sessions Completed', value=f'{timer.current_session}', inline=True)
                        embed.add_field(name='Break Duration', value=f'{duration} minutes', inline=True)
                        embed.set_footer(text=f'{break_type} Break • Relax and recharge!')
                        
                        try:
                            await user.send(embed=embed)
                        except:
                            pass
                    
                    # Update live message immediately
                    if timer.status_message and not timer.is_stopped:
                        try:
                            updated_embed = self._create_timer_embed(timer, user)
                            await timer.status_message.edit(embed=updated_embed)
                        except:
                            pass
                
                # Check if stopped during sleep
                if timer.is_stopped:
                    break
                    
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            print(f'⏹️ Timer task cancelled for {user.name}')
        except Exception as e:
            print(f'Timer error: {e}')


async def setup(bot):
    await bot.add_cog(Pomodoro(bot))