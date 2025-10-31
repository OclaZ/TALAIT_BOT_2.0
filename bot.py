import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from utils.data_manager import DataManager
from utils.logger import setup_logging, get_logger
import traceback
import asyncio

# Load environment variables
load_dotenv()

# Initialize logging system
setup_logging()
logger = get_logger("bot")

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
    logger.info('='*50)
    logger.info(f'✅ {bot.user} is now online!')
    logger.info(f'📊 Bot ID: {bot.user.id}')
    logger.info(f'🏠 Servers: {len(bot.guilds)}')

    # Log server details
    for guild in bot.guilds:
        logger.info(f'  - {guild.name} (ID: {guild.id}, Members: {guild.member_count})')

    logger.info('='*50)

    # Wait a bit for all cogs to fully load
    await asyncio.sleep(2)

    try:
        logger.info('🔄 Syncing commands...')

        # Check what commands are registered
        commands_before = bot.tree.get_commands()
        logger.info(f'📝 Commands in tree: {len(commands_before)}')

        # Sync to Discord
        synced = await bot.tree.sync()

        logger.info(f'✅ Synced {len(synced)} slash command(s) to Discord')

        if len(synced) > 0:
            logger.info('📋 Available Commands:')
            for cmd in synced:
                logger.info(f'  /{cmd.name} - {cmd.description}')
        else:
            logger.warning('⚠️ No commands synced!')
            logger.info('💡 Try restarting Discord app and waiting 2-3 minutes')

        logger.info('='*50)
    except Exception as e:
        logger.error(f'❌ Error syncing commands: {e}')
        logger.error(traceback.format_exc())

    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="talAIt challenges | /help"
        )
    )
    logger.info('Bot status set to: Watching talAIt challenges | /help')

@bot.event
async def on_guild_join(guild):
    logger.info(f'✅ Joined new server: {guild.name} (ID: {guild.id}, Members: {guild.member_count})')

async def load_cogs():
    """Load all cog extensions"""
    cogs = [
        'cogs.leaderboard',
        'cogs.admin',
        'cogs.tickets',
        'cogs.challenges',
        'cogs.pomodoro',
        'cogs.help',
    ]

    logger.info('🔄 Loading cogs...')
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f'✅ Loaded {cog}')
        except Exception as e:
            logger.error(f'❌ Failed to load {cog}: {e}')
            logger.error(traceback.format_exc())

    logger.info('='*50)

async def main():
    """Main function to start the bot"""
    logger.info('🚀 Starting TALAIT_BOT...')
    async with bot:
        await load_cogs()
        await bot.start(os.getenv('DISCORD_TOKEN'))

if __name__ == '__main__':
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('\n👋 Bot stopped by user')
    except Exception as e:
        logger.critical(f'❌ Fatal error: {e}')
        logger.critical(traceback.format_exc())