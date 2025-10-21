import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from utils.constants import ALLOWED_ROLES
from utils.code_analyzer import CodeAnalyzer
from utils.auto_xp import AutoXPCalculator
from utils.ai_verifier import AIVerifier
import traceback

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = bot.data_manager

    @app_commands.command(name='submit', description='Create a private ticket to submit your solution')
    async def create_submission_ticket(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            active_challenge = self.data_manager.get_active_challenge(interaction.guild.id)
            if not active_challenge:
                await interaction.followup.send('❌ No active challenge!', ephemeral=True)
                return

            existing_ticket = self.data_manager.get_user_ticket(interaction.guild.id, interaction.user.id, active_challenge['id'])
            if existing_ticket:
                channel = interaction.guild.get_channel(existing_ticket['channel_id'])
                if channel:
                    await interaction.followup.send(f'✅ You already have a ticket: {channel.mention}', ephemeral=True)
                    return

            category = discord.utils.get(interaction.guild.categories, name="📝 Submissions")
            if not category:
                category = await interaction.guild.create_category("📝 Submissions")

            trainer_role = discord.utils.get(interaction.guild.roles, name='formateur')
            admin_role = discord.utils.get(interaction.guild.roles, name='admin')
            moderator_role = discord.utils.get(interaction.guild.roles, name='moderator')

            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True, read_message_history=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
            }

            for role in [trainer_role, admin_role, moderator_role]:
                if role:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True)

            week_num = active_challenge['week']
            channel_name = f"ticket-{interaction.user.name}-w{week_num}".lower().replace(" ", "-")
            
            ticket_channel = await interaction.guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)

            ticket_data = {
                'user_id': interaction.user.id,
                'channel_id': ticket_channel.id,
                'challenge_id': active_challenge['id'],
                'created_at': datetime.now().isoformat(),
                'status': 'open',
                'submitted': False
            }
            self.data_manager.create_ticket(interaction.guild.id, ticket_data)

            embed = discord.Embed(
                title=f'🎯 Submission Ticket - {active_challenge["title"]}',
                description=(
                    f'Welcome {interaction.user.mention}!\n\n'
                    f'**Challenge:** {active_challenge["title"]}\n'
                    f'**Difficulty:** {active_challenge["difficulty"]}\n\n'
                    f'📝 **How to submit:**\n'
                    f'1. Post your code in a code block:\n'
                    f'   \\`\\`\\`python\n'
                    f'   your code here\n'
                    f'   \\`\\`\\`\n'
                    f'2. Explain your approach\n'
                    f'3. Click ✅ button below\n'
                    f'4. Get AI analysis & XP!\n\n'
                    f'🤖 **AI will verify:**\n'
                    f'• Does your code solve the challenge?\n'
                    f'• Is the logic correct?\n'
                    f'• Are there any issues?'
                ),
                color=discord.Color.blue()
            )
            embed.set_footer(text=f'{interaction.guild.name} • Good luck! 🚀')

            view = SubmitView(self.data_manager, active_challenge['id'], interaction.guild.id)
            await ticket_channel.send(embed=embed, view=view)

            await interaction.followup.send(f'✅ Created ticket: {ticket_channel.mention}', ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send('❌ I need "Manage Channels" permission!', ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f'❌ Error: {str(e)}', ephemeral=True)
            traceback.print_exc()

    @app_commands.command(name='closeticket', description='Close your submission ticket')
    async def close_ticket(self, interaction: discord.Interaction):
        if not interaction.channel.name.startswith('ticket-'):
            await interaction.response.send_message('❌ Use in ticket channels only!', ephemeral=True)
            return

        ticket = self.data_manager.get_ticket_by_channel(interaction.guild.id, interaction.channel.id)
        if not ticket:
            await interaction.response.send_message('❌ Ticket not found!', ephemeral=True)
            return

        is_owner = ticket['user_id'] == interaction.user.id
        is_trainer = any(role.name.lower() in ALLOWED_ROLES for role in interaction.user.roles)

        if not (is_owner or is_trainer):
            await interaction.response.send_message('❌ Only your ticket!', ephemeral=True)
            return

        view = CloseConfirmView(interaction.channel, ticket['id'], self.data_manager, interaction.guild.id)
        await interaction.response.send_message('🔒 Close this ticket?', view=view, ephemeral=True)

    @app_commands.command(name='listtickets', description='List all tickets (Trainers)')
    async def list_tickets(self, interaction: discord.Interaction):
        if not any(role.name.lower() in ALLOWED_ROLES for role in interaction.user.roles):
            await interaction.response.send_message('❌ Trainers only!', ephemeral=True)
            return

        active_challenge = self.data_manager.get_active_challenge(interaction.guild.id)
        if not active_challenge:
            await interaction.response.send_message('❌ No active challenge!', ephemeral=True)
            return

        tickets = self.data_manager.get_tickets_by_challenge(interaction.guild.id, active_challenge['id'])
        
        if not tickets:
            await interaction.response.send_message('📋 No tickets yet!', ephemeral=True)
            return

        embed = discord.Embed(title=f'📋 Tickets - Week {active_challenge["week"]}', description=f'Total: **{len(tickets)}**', color=discord.Color.blue())

        submitted = len([t for t in tickets if t['submitted']])
        embed.add_field(name='Stats', value=f'✅ Submitted: {submitted}\n⏳ Pending: {len(tickets) - submitted}', inline=False)

        for ticket in tickets[:10]:
            try:
                user = await self.bot.fetch_user(ticket['user_id'])
                channel = interaction.guild.get_channel(ticket['channel_id'])
                status = '✅' if ticket['submitted'] else '⏳'
                xp = ticket.get('xp_awarded', 0)
                embed.add_field(name=f'{status} {user.name}', value=f'{channel.mention if channel else "Deleted"} | {xp} XP', inline=True)
            except:
                continue

        embed.set_footer(text=interaction.guild.name)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='feedback', description='Give feedback (Trainers)')
    @app_commands.describe(message='Your feedback')
    async def give_feedback(self, interaction: discord.Interaction, message: str):
        if not any(role.name.lower() in ALLOWED_ROLES for role in interaction.user.roles):
            await interaction.response.send_message('❌ Trainers only!', ephemeral=True)
            return

        if not interaction.channel.name.startswith('ticket-'):
            await interaction.response.send_message('❌ Use in ticket!', ephemeral=True)
            return

        ticket = self.data_manager.get_ticket_by_channel(interaction.guild.id, interaction.channel.id)
        if not ticket:
            await interaction.response.send_message('❌ Ticket not found!', ephemeral=True)
            return

        user = await self.bot.fetch_user(ticket['user_id'])

        embed = discord.Embed(title='💬 Trainer Feedback', description=message, color=discord.Color.green())
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now()

        await interaction.channel.send(content=user.mention, embed=embed)
        await interaction.response.send_message('✅ Feedback sent!', ephemeral=True)


class SubmitView(discord.ui.View):
    def __init__(self, data_manager, challenge_id, guild_id):
        super().__init__(timeout=None)
        self.data_manager = data_manager
        self.challenge_id = challenge_id
        self.guild_id = guild_id
        self.code_analyzer = CodeAnalyzer()
        self.xp_calculator = AutoXPCalculator()
        self.ai_verifier = AIVerifier()

    @discord.ui.button(label='Mark as Submitted ✅', style=discord.ButtonStyle.green, custom_id='submit_solution')
    async def submit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        ticket = self.data_manager.get_ticket_by_channel(self.guild_id, interaction.channel.id)
        
        if not ticket:
            await interaction.followup.send('❌ Ticket not found!', ephemeral=True)
            return

        if ticket['user_id'] != interaction.user.id:
            await interaction.followup.send('❌ Only ticket owner!', ephemeral=True)
            return

        if ticket['submitted']:
            await interaction.followup.send('✅ Already submitted!', ephemeral=True)
            return

        code_content = await self._extract_code(interaction.channel)
        
        if not code_content:
            await interaction.followup.send('❌ No code found! Use \\`\\`\\`python code \\`\\`\\`', ephemeral=True)
            return
        
        print(f"📝 Code found: {len(code_content)} chars")
        
        language = self._detect_language(code_content)
        analysis = self.code_analyzer.analyze(code_content, language)
        
        challenge = self.data_manager.get_active_challenge(self.guild_id)
        if not challenge:
            await interaction.followup.send('❌ Challenge not found!', ephemeral=True)
            return
        
        ai_result = self.ai_verifier.verify_solution(
            challenge_title=challenge['title'],
            challenge_description=challenge['description'],
            challenge_difficulty=challenge['difficulty'],
            submitted_code=code_content,
            language=language
        )
        
        print(f"🤖 AI: Solves={ai_result['solves_challenge']}, Score={ai_result['overall_score']}")
        
        submission_count = len(challenge.get('submissions', []))
        submission_rank = submission_count + 1
        
        xp_result = self.xp_calculator.calculate(
            code_quality=analysis['overall'],
            submission_number=submission_rank,
            total_lines=analysis['line_count'],
            solves_challenge=ai_result['solves_challenge'],
            ai_overall_score=ai_result['overall_score']
        )
        
        print(f"⭐ XP: {xp_result['total_xp']}")
        
        week_key = f"week_{challenge['week']}"
        self.data_manager.ensure_user(self.guild_id, interaction.user.id, interaction.user.name)
        self.data_manager.add_xp(self.guild_id, interaction.user.id, xp_result['total_xp'], week_key)
        
        self.data_manager.update_ticket(self.guild_id, ticket['id'], {
            'submitted': True,
            'quality_score': ai_result['overall_score'],
            'xp_awarded': xp_result['total_xp']
        })
        
        submission_data = {
            'user_id': interaction.user.id,
            'ticket_id': ticket['id'],
            'channel_id': interaction.channel.id,
            'submitted_at': datetime.now().isoformat(),
            'quality_score': ai_result['overall_score'],
            'xp_awarded': xp_result['total_xp'],
            'solves_challenge': ai_result['solves_challenge']
        }
        self.data_manager.add_submission(self.guild_id, self.challenge_id, submission_data)
        
        color = discord.Color.green() if ai_result['solves_challenge'] else discord.Color.red()
        
        embed = discord.Embed(title='🤖 AI Code Review Complete!', description=f'Your {language} solution has been analyzed', color=color)
        
        challenge_emoji = '✅' if ai_result['solves_challenge'] else '❌'
        embed.add_field(
            name=f'{challenge_emoji} Challenge Verification',
            value=(
                f"**Solves Challenge:** {'Yes ✅' if ai_result['solves_challenge'] else 'No ❌'}\n"
                f"**AI Score:** {ai_result['overall_score']}/100\n\n"
                f"├─ Correctness: {ai_result['correctness_score']}/100\n"
                f"├─ Logic: {ai_result['logic_score']}/100\n"
                f"└─ Completeness: {ai_result['completeness_score']}/100"
            ),
            inline=False
        )
        
        if ai_result['feedback']:
            feedback_text = ai_result['feedback'][:400]
            embed.add_field(name='💬 AI Feedback', value=feedback_text, inline=False)
        
        if ai_result['issues']:
            issues_text = '\n'.join(f"• {issue}" for issue in ai_result['issues'][:3])
            embed.add_field(name='⚠️ Issues', value=issues_text, inline=False)
        
        if ai_result['strengths']:
            strengths_text = '\n'.join(f"• {strength}" for strength in ai_result['strengths'][:3])
            embed.add_field(name='💪 Strengths', value=strengths_text, inline=False)
        
        quality_bar = self._progress_bar(analysis['overall'])
        embed.add_field(
            name='📊 Code Quality',
            value=(
                f"**Score: {analysis['overall']}/100** {quality_bar}\n"
                f"✓ Syntax: {analysis['correctness']}/100 | "
                f"📖 Style: {analysis['readability']}/100 | "
                f"⚡ Efficiency: {analysis['efficiency']}/100"
            ),
            inline=False
        )
        
        xp_emoji = '🌟' if xp_result['total_xp'] >= 8 else '⭐' if xp_result['total_xp'] >= 5 else '💧'
        embed.add_field(
            name=f'{xp_emoji} XP Awarded: **{xp_result["total_xp"]} XP**',
            value=xp_result['breakdown'],
            inline=False
        )
        
        embed.set_footer(text=f'{interaction.guild.name} • Submission #{submission_rank}')
        embed.timestamp = datetime.now()
        
        await interaction.followup.send(embed=embed)
        
        button.disabled = True
        button.label = 'Submitted ✅'
        await interaction.message.edit(view=self)
        
        print(f'✅ Complete for {interaction.user.name} in {interaction.guild.name}')
    
    async def _extract_code(self, channel) -> str:
        code_blocks = []
        async for message in channel.history(limit=50):
            if '```' in message.content:
                blocks = message.content.split('```')
                for i, block in enumerate(blocks):
                    if i % 2 == 1:
                        lines = block.strip().split('\n')
                        if lines and lines[0].strip().lower() in ['python', 'py', 'java', 'cpp', 'c', 'js']:
                            block = '\n'.join(lines[1:])
                        code_blocks.append(block.strip())
            
            for attachment in message.attachments:
                if attachment.filename.endswith(('.py', '.java', '.cpp', '.js', '.txt')):
                    try:
                        content = await attachment.read()
                        code_blocks.append(content.decode('utf-8'))
                    except:
                        pass
        
        return '\n\n'.join(code_blocks)
    
    def _detect_language(self, code: str) -> str:
        if 'def ' in code or 'import ' in code:
            return 'python'
        elif 'public class' in code:
            return 'java'
        elif '#include' in code:
            return 'cpp'
        elif 'function ' in code or 'const ' in code:
            return 'javascript'
        return 'python'
    
    def _progress_bar(self, score: int) -> str:
        filled = int((score / 100) * 10)
        empty = 10 - filled
        if score >= 90:
            return '🟩' * filled + '⬜' * empty
        elif score >= 70:
            return '🟨' * filled + '⬜' * empty
        else:
            return '🟧' * filled + '⬜' * empty


class CloseConfirmView(discord.ui.View):
    def __init__(self, channel, ticket_id, data_manager, guild_id):
        super().__init__(timeout=60)
        self.channel = channel
        self.ticket_id = ticket_id
        self.data_manager = data_manager
        self.guild_id = guild_id

    @discord.ui.button(label='Yes, Close', style=discord.ButtonStyle.red)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.data_manager.update_ticket(self.guild_id, self.ticket_id, {'status': 'closed'})
        await interaction.response.send_message('🔒 Closing...', ephemeral=True)
        import asyncio
        await asyncio.sleep(3)
        await self.channel.delete()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.gray)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('❌ Cancelled', ephemeral=True)
        await interaction.message.delete()


async def setup(bot):
    await bot.add_cog(Tickets(bot))