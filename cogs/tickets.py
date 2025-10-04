import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from utils.constants import ALLOWED_ROLES
import traceback

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = bot.data_manager

    @app_commands.command(name='submit', description='Create a private ticket to submit your solution')
    async def create_submission_ticket(self, interaction: discord.Interaction):
        # DEFER IMMEDIATELY - This gives us 15 minutes to respond
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Check if there's an active challenge
            active_challenge = self.data_manager.get_active_challenge()
            if not active_challenge:
                await interaction.followup.send(
                    '❌ No active challenge right now! Use `/postchallenge` to create one first.',
                    ephemeral=True
                )
                return

            # Check if user already has a ticket for this challenge
            existing_ticket = self.data_manager.get_user_ticket(interaction.user.id, active_challenge['id'])
            if existing_ticket:
                channel = interaction.guild.get_channel(existing_ticket['channel_id'])
                if channel:
                    await interaction.followup.send(
                        f'✅ You already have a submission ticket: {channel.mention}',
                        ephemeral=True
                    )
                    return

            # Create ticket category if it doesn't exist
            category = discord.utils.get(interaction.guild.categories, name="📝 Submissions")
            if not category:
                category = await interaction.guild.create_category("📝 Submissions")
                print(f'✅ Created category: 📝 Submissions')

            # Get trainer roles for permissions
            trainer_role = discord.utils.get(interaction.guild.roles, name='formateur')
            admin_role = discord.utils.get(interaction.guild.roles, name='admin')
            moderator_role = discord.utils.get(interaction.guild.roles, name='moderator')

            # Create private channel overwrites
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    attach_files=True,
                    embed_links=True,
                    read_message_history=True
                ),
                interaction.guild.me: discord.PermissionOverwrite(
                    read_messages=True, 
                    send_messages=True,
                    manage_channels=True
                )
            }

            # Add permissions for trainer roles
            if trainer_role:
                overwrites[trainer_role] = discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    read_message_history=True
                )
            
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    read_message_history=True
                )
                
            if moderator_role:
                overwrites[moderator_role] = discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    read_message_history=True
                )

            # Create channel
            week_num = active_challenge['week']
            channel_name = f"ticket-{interaction.user.name}-w{week_num}".lower().replace(" ", "-")
            
            print(f'🔄 Creating ticket channel: {channel_name}')
            
            ticket_channel = await interaction.guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                reason=f"Submission ticket for {interaction.user.name}"
            )

            print(f'✅ Created ticket channel: {ticket_channel.name}')

            # Save ticket to database
            ticket_data = {
                'user_id': interaction.user.id,
                'channel_id': ticket_channel.id,
                'challenge_id': active_challenge['id'],
                'created_at': datetime.now().isoformat(),
                'status': 'open',
                'submitted': False
            }
            self.data_manager.create_ticket(ticket_data)

            # Send welcome message in ticket
            embed = discord.Embed(
                title=f'🎯 Submission Ticket - {active_challenge["title"]}',
                description=(
                    f'Welcome {interaction.user.mention}!\n\n'
                    f'This is your **private submission channel** for Week {week_num}.\n\n'
                    f'**Challenge:** {active_challenge["title"]}\n'
                    f'**Difficulty:** {active_challenge["difficulty"]}\n\n'
                    f'📝 **How to submit:**\n'
                    f'1. Post your code here\n'
                    f'2. Explain your approach\n'
                    f'3. Click the ✅ button when ready\n'
                    f'4. Trainers will review privately\n\n'
                    f'⚠️ **Important:**\n'
                    f'• Only you and trainers can see this\n'
                    f'• You can edit/update before marking as submitted\n'
                    f'• Use `/closeticket` when done or to cancel'
                ),
                color=discord.Color.blue()
            )
            embed.set_footer(text='Good luck! 🚀')

            # Add submit button
            view = SubmitView(self.data_manager, active_challenge['id'])
            await ticket_channel.send(embed=embed, view=view)

            # Notify user
            await interaction.followup.send(
                f'✅ Created your submission ticket: {ticket_channel.mention}',
                ephemeral=True
            )
            
            print(f'✅ Ticket created successfully for {interaction.user.name}')
            
        except discord.Forbidden:
            await interaction.followup.send(
                '❌ I don\'t have permission to create channels! Please give me "Manage Channels" permission.',
                ephemeral=True
            )
            print('❌ Missing permissions to create channels')
        except Exception as e:
            await interaction.followup.send(
                f'❌ An error occurred: {str(e)}',
                ephemeral=True
            )
            print(f'❌ Error creating ticket: {e}')
            traceback.print_exc()

    @app_commands.command(name='closeticket', description='Close your submission ticket')
    async def close_ticket(self, interaction: discord.Interaction):
        # Check if command is used in a ticket channel
        if not interaction.channel.name.startswith('ticket-'):
            await interaction.response.send_message(
                '❌ This command only works in ticket channels!',
                ephemeral=True
            )
            return

        # Get ticket data
        ticket = self.data_manager.get_ticket_by_channel(interaction.channel.id)
        if not ticket:
            await interaction.response.send_message(
                '❌ Ticket not found in database!',
                ephemeral=True
            )
            return

        # Check if user owns the ticket or is a trainer
        is_owner = ticket['user_id'] == interaction.user.id
        is_trainer = any(role.name.lower() in ALLOWED_ROLES for role in interaction.user.roles)

        if not (is_owner or is_trainer):
            await interaction.response.send_message(
                '❌ You can only close your own ticket!',
                ephemeral=True
            )
            return

        # Confirm close
        embed = discord.Embed(
            title='🔒 Close Ticket?',
            description='Are you sure you want to close this ticket?',
            color=discord.Color.red()
        )
        
        if ticket['submitted']:
            embed.add_field(
                name='✅ Submission Status',
                value='Your submission has been recorded and will be reviewed.',
                inline=False
            )
        else:
            embed.add_field(
                name='⚠️ Warning',
                value='You have not marked your submission as complete yet!',
                inline=False
            )

        view = CloseConfirmView(interaction.channel, ticket['id'], self.data_manager)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name='listtickets', description='List all open submission tickets (Trainers only)')
    async def list_tickets(self, interaction: discord.Interaction):
        if not any(role.name.lower() in ALLOWED_ROLES for role in interaction.user.roles):
            await interaction.response.send_message(
                '❌ Only trainers can use this command!',
                ephemeral=True
            )
            return

        active_challenge = self.data_manager.get_active_challenge()
        if not active_challenge:
            await interaction.response.send_message(
                '❌ No active challenge!',
                ephemeral=True
            )
            return

        tickets = self.data_manager.get_tickets_by_challenge(active_challenge['id'])
        
        if not tickets:
            await interaction.response.send_message(
                '📋 No submission tickets yet!',
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f'📋 Submission Tickets - Week {active_challenge["week"]}',
            description=f'Total tickets: **{len(tickets)}**',
            color=discord.Color.blue()
        )

        open_tickets = [t for t in tickets if t['status'] == 'open']
        submitted_tickets = [t for t in tickets if t['submitted']]

        embed.add_field(
            name='📊 Statistics',
            value=(
                f'🟢 Open: {len(open_tickets)}\n'
                f'✅ Submitted: {len(submitted_tickets)}\n'
                f'🔒 Closed: {len([t for t in tickets if t["status"] == "closed"])}'
            ),
            inline=False
        )

        # List tickets
        for ticket in tickets[:25]:
            try:
                user = await self.bot.fetch_user(ticket['user_id'])
                channel = interaction.guild.get_channel(ticket['channel_id'])
                
                status = '✅' if ticket['submitted'] else '⏳'
                channel_link = channel.mention if channel else 'Deleted'
                
                embed.add_field(
                    name=f'{status} {user.name}',
                    value=f'Channel: {channel_link}\nStatus: {ticket["status"].title()}',
                    inline=True
                )
            except:
                continue

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='feedback', description='Give feedback on a submission (Trainers only)')
    @app_commands.describe(message='Your feedback message')
    async def give_feedback(self, interaction: discord.Interaction, message: str):
        if not any(role.name.lower() in ALLOWED_ROLES for role in interaction.user.roles):
            await interaction.response.send_message(
                '❌ Only trainers can give feedback!',
                ephemeral=True
            )
            return

        if not interaction.channel.name.startswith('ticket-'):
            await interaction.response.send_message(
                '❌ Use this command in a ticket channel!',
                ephemeral=True
            )
            return

        ticket = self.data_manager.get_ticket_by_channel(interaction.channel.id)
        if not ticket:
            await interaction.response.send_message(
                '❌ Ticket not found!',
                ephemeral=True
            )
            return

        user = await self.bot.fetch_user(ticket['user_id'])

        embed = discord.Embed(
            title='💬 Trainer Feedback',
            description=message,
            color=discord.Color.green()
        )
        embed.set_author(
            name=interaction.user.name,
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )
        embed.timestamp = datetime.now()

        await interaction.channel.send(content=user.mention, embed=embed)
        await interaction.response.send_message('✅ Feedback sent!', ephemeral=True)

class SubmitView(discord.ui.View):
    def __init__(self, data_manager, challenge_id):
        super().__init__(timeout=None)
        self.data_manager = data_manager
        self.challenge_id = challenge_id

    @discord.ui.button(label='Mark as Submitted ✅', style=discord.ButtonStyle.green, custom_id='submit_solution')
    async def submit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket = self.data_manager.get_ticket_by_channel(interaction.channel.id)
        
        if not ticket:
            await interaction.response.send_message('❌ Ticket not found!', ephemeral=True)
            return

        if ticket['user_id'] != interaction.user.id:
            await interaction.response.send_message(
                '❌ Only the ticket owner can mark as submitted!',
                ephemeral=True
            )
            return

        if ticket['submitted']:
            await interaction.response.send_message(
                '✅ Already marked as submitted!',
                ephemeral=True
            )
            return

        # Mark as submitted
        self.data_manager.update_ticket(ticket['id'], {'submitted': True})
        
        # Add submission to challenge
        submission_data = {
            'user_id': interaction.user.id,
            'ticket_id': ticket['id'],
            'channel_id': interaction.channel.id,
            'submitted_at': datetime.now().isoformat()
        }
        self.data_manager.add_submission(self.challenge_id, submission_data)

        embed = discord.Embed(
            title='✅ Submission Recorded!',
            description=(
                'Your submission has been marked as complete!\n\n'
                '**What happens next:**\n'
                '• Trainers will review your code\n'
                '• You\'ll receive feedback here\n'
                '• Winners announced after review\n\n'
                'You can still send messages here to add notes or corrections.'
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text='Good luck! 🍀')

        await interaction.response.send_message(embed=embed)
        
        # Disable button
        button.disabled = True
        button.label = 'Submitted ✅'
        await interaction.message.edit(view=self)

class CloseConfirmView(discord.ui.View):
    def __init__(self, channel, ticket_id, data_manager):
        super().__init__(timeout=60)
        self.channel = channel
        self.ticket_id = ticket_id
        self.data_manager = data_manager

    @discord.ui.button(label='Yes, Close Ticket', style=discord.ButtonStyle.red)
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Update ticket status
        self.data_manager.update_ticket(self.ticket_id, {'status': 'closed'})

        await interaction.response.send_message(
            '🔒 Ticket will be deleted in 5 seconds...',
            ephemeral=True
        )
        
        import asyncio
        await asyncio.sleep(5)
        await self.channel.delete()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.gray)
    async def cancel_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('❌ Cancelled.', ephemeral=True)
        await interaction.message.delete()

async def setup(bot):
    await bot.add_cog(Tickets(bot))