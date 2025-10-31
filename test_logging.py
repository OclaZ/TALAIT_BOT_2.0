"""
Test script for the logging system
Run this to verify the logging system is working correctly
"""

import os
import sys
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Load environment
load_dotenv()

# Import logging system
from utils.logger import setup_logging, get_logger

def test_logging_system():
    """Test all aspects of the logging system"""

    print("=" * 60)
    print("TESTING LOGGING SYSTEM")
    print("=" * 60)

    # Initialize logging
    print("\n1. Initializing logging system...")
    setup_logging()
    logger = get_logger("test")
    print("✅ Logging system initialized")

    # Test different log levels
    print("\n2. Testing log levels...")
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    logger.critical("This is a CRITICAL message")
    print("✅ All log levels tested")

    # Test module-specific loggers
    print("\n3. Testing module-specific loggers...")
    bot_logger = get_logger("bot")
    bot_logger.info("Bot logger test message")

    admin_logger = get_logger("cogs.admin")
    admin_logger.info("Admin cog logger test message")

    data_logger = get_logger("data_manager")
    data_logger.info("Data manager logger test message")
    print("✅ Module loggers tested")

    # Test structured logging
    print("\n4. Testing structured log messages...")
    logger.info("Command execution | /addxp | User: test_user | XP: +10 | Guild: TestGuild")
    logger.info("Challenge created | ID: 123 | Title: Test Challenge | Difficulty: Medium")
    logger.error("Error occurred | Module: test | Error: This is a test error")
    print("✅ Structured logging tested")

    # Verify log files exist
    print("\n5. Verifying log files...")
    log_files = [
        "logs/bot.log",
        "logs/commands.log",
        "logs/errors.log"
    ]

    all_exist = True
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            print(f"✅ {log_file} exists ({size} bytes)")
        else:
            print(f"❌ {log_file} NOT FOUND")
            all_exist = False

    if not all_exist:
        print("\n⚠️ Some log files are missing! They will be created when the bot starts.")

    # Check configuration
    print("\n6. Checking configuration...")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    retention_days = os.getenv("LOG_RETENTION_DAYS", "3")
    print(f"✅ Log Level: {log_level}")
    print(f"✅ Retention Days: {retention_days}")

    # Summary
    print("\n" + "=" * 60)
    print("LOGGING SYSTEM TEST COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Check the log files in the logs/ directory")
    print("2. Verify log rotation settings in .env")
    print("3. Run the bot to see logging in action")
    print("\nLog files location: logs/")
    print("- logs/bot.log      (main activity log)")
    print("- logs/commands.log (command usage)")
    print("- logs/errors.log   (errors only)")
    print("\nFor more information, see LOGGING_GUIDE.md")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_logging_system()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
