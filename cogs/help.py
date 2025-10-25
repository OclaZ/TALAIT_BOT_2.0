import discord
from discord.ext import commands
from discord import app_commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='help', description='Show all available commands and how to use the bot')
    async def help_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title='📚 talAIt Bot - Complete Command Guide',
            description='Welcome to talAIt! Here are all available commands organized by category:',
            color=discord.Color.blue()
        )
        
        # Member Commands
        embed.add_field(
            name='👥 Member Commands',
            value=(
                '`/leaderboard` - View current monthly rankings\n'
                '`/halloffame` - View all-time champions\n'
                '`/stats [@user]` - View your or another user\'s stats\n'
                '`/activechallenge` - View current active challenge\n'
                '`/challengetimer` - Check time remaining\n'
                '`/submit` - Create submission ticket\n'
                '`/closeticket` - Close your submission ticket\n'
                '`/help` - Show this help message\n'
                '`/about` - Learn about the bot'
            ),
            inline=False
        )
        
        # Pomodoro Commands
        embed.add_field(
            name='🍅 Pomodoro Timer Commands',
            value=(
                '`/pomodoro` - Start focus timer (default: 25min work, 5min break)\n'
                '`/pomodoro-status` - Check your timer status\n'
                '`/pomodoro-pause` - Pause your timer\n'
                '`/pomodoro-resume` - Resume paused timer\n'
                '`/pomodoro-skip` - Skip to next phase\n'
                '`/pomodoro-stop` - Stop timer completely\n'
                '`/pomodoro-focusing` - See who\'s focusing now\n'
                '`/pomodoro-onbreak` - See who\'s on break\n'
                '`/pomodoro-leaderboard` - View session rankings\n'
                '`/pomodoro-help` - Detailed Pomodoro guide'
            ),
            inline=False
        )
        
        # Trainer Commands
        embed.add_field(
            name='🎓 Trainer Commands',
            value=(
                '`/postchallenge` - Post new challenge (duration in MINUTES)\n'
                '`/closechallenge` - Manually close challenge\n'
                '`/extendchallenge` - Add more minutes to challenge\n'
                '`/awardwinners` - Award XP to top 3 winners\n'
                '`/addxp` - Give XP to specific user\n'
                '`/removexp` - Remove XP from user\n'
                '`/listtickets` - View all submission tickets\n'
                '`/listusers` - View all users in leaderboard\n'
                '`/feedback` - Give feedback in ticket\n'
                '`/languages` - View supported languages'
            ),
            inline=False
        )
        
        # Admin Commands
        embed.add_field(
            name='⚙️ Admin Commands',
            value='`/resetmonth` - Manually reset monthly leaderboard',
            inline=False
        )
        
        # XP System
        embed.add_field(
            name='🏆 XP & Rewards System',
            value=(
                '**Challenge Winners:**\n'
                '🥇 **1st Place:** 10 XP + Winner Badge\n'
                '🥈 **2nd Place:** 7 XP + 2nd Place Badge\n'
                '🥉 **3rd Place:** 5 XP + 3rd Place Badge\n'
                '✅ **Participation:** 2 XP\n\n'
                '**Auto-XP System (Tickets):**\n'
                'AI verifies your solution and awards XP based on:\n'
                '• Code correctness and logic\n'
                '• Code quality and style\n'
                '• Submission timing (early bonus)\n'
                '• Effort (lines of code)'
            ),
            inline=False
        )
        
        # How to Participate
        embed.add_field(
            name='📝 How to Participate in Challenges',
            value=(
                '1️⃣ Wait for challenge post (trainers use `/postchallenge`)\n'
                '2️⃣ Use `/submit` to create your private ticket\n'
                '3️⃣ Post your code in the ticket channel\n'
                '4️⃣ Click ✅ button to submit for AI review\n'
                '5️⃣ Get instant AI feedback + XP!\n'
                '6️⃣ Trainers review and award top 3 winners'
            ),
            inline=False
        )
        
        embed.set_footer(text='Use /about for more info • talAIt Bot v2.0')
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='about', description='Learn about talAIt and the bot features')
    async def about(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title='ℹ️ About talAIt Bot',
            description=(
                '**talAIt** is your complete coding challenge companion!\n\n'
                'We help you track challenges, manage submissions, award XP, '
                'and maintain leaderboards for your coding community.'
            ),
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name='🎯 Key Features',
            value=(
                '✅ **Challenge System** - Auto-close timers, multi-language support\n'
                '✅ **Private Tickets** - Submit code in private channels\n'
                '✅ **AI Code Review** - Instant feedback with Gemini AI\n'
                '✅ **Auto-XP System** - Smart XP calculation based on quality\n'
                '✅ **Pomodoro Timers** - Stay focused with live timers\n'
                '✅ **Leaderboards** - Monthly rankings & Hall of Fame\n'
                '✅ **Badge System** - Earn badges for achievements'
            ),
            inline=False
        )
        
        embed.add_field(
            name='🤖 AI-Powered Features',
            value=(
                '**Gemini 2.0 Flash** analyzes your code:\n'
                '• Verifies if solution solves the challenge\n'
                '• Checks correctness, logic, and completeness\n'
                '• Provides detailed feedback\n'
                '• Awards XP automatically based on quality'
            ),
            inline=False
        )
        
        embed.add_field(
            name='🔄 Challenge Flow',
            value=(
                '**1. Post** - Trainer creates challenge with duration\n'
                '**2. Submit** - Users create private tickets\n'
                '**3. AI Review** - Instant automated feedback\n'
                '**4. Award** - Trainers pick top 3 winners\n'
                '**5. Auto-Close** - Challenge closes after timer'
            ),
            inline=False
        )
        
        embed.add_field(
            name='🍅 Pomodoro Technique',
            value=(
                'Built-in productivity timer:\n'
                '• Work in 25-minute focused sessions\n'
                '• Take 5-minute breaks\n'
                '• Long break after 4 sessions\n'
                '• Live countdown with progress bar\n'
                '• See who\'s focusing or on break'
            ),
            inline=False
        )
        
        embed.add_field(
            name='💻 Supported Languages',
            value=(
                'Python, JavaScript, TypeScript, Java, C, C++, C#, Go, Rust, '
                'PHP, Ruby, Swift, Kotlin, SQL, and more!\n'
                'Use `/languages` to see all supported languages.'
            ),
            inline=False
        )
        
        embed.add_field(
            name='📊 Leaderboard System',
            value=(
                '• **Monthly Leaderboard** - Resets every 1st of month\n'
                '• **Hall of Fame** - Permanent all-time rankings\n'
                '• **User Stats** - Track your progress over time\n'
                '• **Badge Collection** - Show off your achievements'
            ),
            inline=False
        )
        
        embed.add_field(
            name='⏰ Challenge Timers',
            value=(
                'Challenges auto-close after set duration:\n'
                '• Default: 30 minutes\n'
                '• Max: 1440 minutes (24 hours)\n'
                '• Extend with `/extendchallenge`\n'
                '• Check remaining time with `/challengetimer`'
            ),
            inline=False
        )
        
        embed.add_field(
            name='🎓 Perfect For',
            value=(
                '• Coding bootcamps and training programs\n'
                '• Programming communities and study groups\n'
                '• Technical interview preparation\n'
                '• Competitive programming practice\n'
                '• Team skill development'
            ),
            inline=False
        )
        
        embed.set_footer(text='Built with ❤️ for the talAIt community • Version 2.0')
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='quickstart', description='Quick start guide for new users')
    async def quickstart(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title='🚀 Quick Start Guide',
            description='Get started with talAIt in 3 easy steps!',
            color=discord.Color.green()
        )
        
        embed.add_field(
            name='Step 1: Wait for a Challenge 📢',
            value=(
                'Trainers will post challenges using `/postchallenge`\n'
                'You\'ll see an @everyone notification with:\n'
                '• Challenge title and description\n'
                '• Difficulty level (Easy/Medium/Hard)\n'
                '• Programming language\n'
                '• Auto-close timer'
            ),
            inline=False
        )
        
        embed.add_field(
            name='Step 2: Submit Your Solution 📝',
            value=(
                '1. Use `/submit` to create your private ticket\n'
                '2. Write your solution in the ticket channel\n'
                '3. Use code blocks: \\`\\`\\`python\\n your code \\n\\`\\`\\`\n'
                '4. Click the ✅ button to submit\n'
                '5. Get instant AI feedback and XP!'
            ),
            inline=False
        )
        
        embed.add_field(
            name='Step 3: Track Your Progress 📊',
            value=(
                '• Use `/stats` to see your XP and rank\n'
                '• Use `/leaderboard` to see top performers\n'
                '• Earn badges for winning challenges\n'
                '• Climb the monthly rankings!'
            ),
            inline=False
        )
        
        embed.add_field(
            name='💡 Pro Tips',
            value=(
                '• Submit early for bonus XP\n'
                '• Write clean, well-commented code\n'
                '• Use `/pomodoro` to stay focused\n'
                '• Check `/challengetimer` for deadline\n'
                '• Ask trainers for help in ticket'
            ),
            inline=False
        )
        
        embed.add_field(
            name='🆘 Need Help?',
            value=(
                '• Use `/help` for full command list\n'
                '• Use `/about` to learn about features\n'
                '• Use `/pomodoro-help` for timer guide\n'
                '• Ask trainers or admins for support'
            ),
            inline=False
        )
        
        embed.set_footer(text='Happy Coding! 🎉')
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='commands', description='View all commands organized by role')
    async def commands_list(self, interaction: discord.Interaction):
        # Determine user role
        user_roles = [role.name.lower() for role in interaction.user.roles]
        is_trainer = any(role in ['formateur', 'admin', 'moderator'] for role in user_roles)
        is_admin = interaction.user.guild_permissions.administrator
        
        embed = discord.Embed(
            title='📋 Available Commands',
            description=f'Commands you can use based on your roles:',
            color=discord.Color.blue()
        )
        
        # Everyone's commands
        embed.add_field(
            name='👤 Your Commands',
            value=(
                '**Challenges:**\n'
                '`/activechallenge` `/challengetimer` `/submit` `/closeticket`\n\n'
                '**Stats:**\n'
                '`/leaderboard` `/halloffame` `/stats`\n\n'
                '**Pomodoro:**\n'
                '`/pomodoro` `/pomodoro-status` `/pomodoro-pause` `/pomodoro-resume`\n'
                '`/pomodoro-stop` `/pomodoro-skip` `/pomodoro-focusing` `/pomodoro-onbreak`\n\n'
                '**Help:**\n'
                '`/help` `/about` `/quickstart` `/commands`'
            ),
            inline=False
        )
        
        if is_trainer:
            embed.add_field(
                name='🎓 Trainer Commands',
                value=(
                    '`/postchallenge` `/closechallenge` `/extendchallenge`\n'
                    '`/awardwinners` `/addxp` `/removexp`\n'
                    '`/listtickets` `/listusers` `/feedback` `/languages`'
                ),
                inline=False
            )
        
        if is_admin:
            embed.add_field(
                name='⚙️ Admin Commands',
                value='`/resetmonth` - Manually reset monthly leaderboard',
                inline=False
            )
        
        embed.set_footer(text=f'{interaction.guild.name} • Use /help for detailed descriptions')
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Help(bot))