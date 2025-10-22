import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from utils.data_manager import DataManager
import traceback
import asyncio

# Load environment variables
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize data manager
data_manager = DataManager()
bot.data_manager = data_manager

@bot.event
async def on_ready():
    print('='*50)
    print(f'✅ {bot.user} is now online!')
    print(f'📊 Bot ID: {bot.user.id}')
    print(f'🏠 Servers: {len(bot.guilds)}')
    print('='*50)
    
    # Wait a bit for all cogs to fully load
    await asyncio.sleep(2)
    
    try:
        print('🔄 Syncing commands...')
        
        # Check what commands are registered
        commands_before = bot.tree.get_commands()
        print(f'📝 Commands in tree: {len(commands_before)}')
        
        # Sync to Discord
        synced = await bot.tree.sync()
        
        print(f'\n✅ Synced {len(synced)} slash command(s) to Discord')
        
        if len(synced) > 0:
            print('\n📋 Available Commands:')
            for cmd in synced:
                print(f'  /{cmd.name} - {cmd.description}')
        else:
            print('⚠️ No commands synced!')
            print('💡 Try restarting Discord app and waiting 2-3 minutes')
        
        print('='*50)
    except Exception as e:
        print(f'❌ Error syncing commands: {e}')
        traceback.print_exc()
    
    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="talAIt challenges | /help"
        )
    )

@bot.event
async def on_guild_join(guild):
    print(f'✅ Joined new server: {guild.name} (ID: {guild.id})')

async def load_cogs():
    """Load all cog extensions"""
    cogs = [
        'cogs.leaderboard',
        'cogs.admin',
        'cogs.tickets',
        'cogs.challenges',
        'cogs.pomodoro',
    ]
    
    print('🔄 Loading cogs...')
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f'✅ Loaded {cog}')
        except Exception as e:
            print(f'❌ Failed to load {cog}: {e}')
            traceback.print_exc()
    
    print('='*50)

async def main():
    """Main function to start the bot"""
    async with bot:
        await load_cogs()
        await bot.start(os.getenv('DISCORD_TOKEN'))

if __name__ == '__main__':
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n👋 Bot stopped by user')
    except Exception as e:
        print(f'❌ Fatal error: {e}')
        traceback.print_exc()