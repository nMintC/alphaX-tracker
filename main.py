"""
Alpha Follow Tracker — Entry Point
Starts the Discord bot with the integrated polling loop.

Usage: python main.py
"""

import logging
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-12s │ %(levelname)-5s │ %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("tracker.log", encoding="utf-8"),
    ],
)

# Suppress noisy discord.py logs
logging.getLogger("discord").setLevel(logging.WARNING)
logging.getLogger("discord.http").setLevel(logging.WARNING)

logger = logging.getLogger("main")


def main():
    # Quick pre-flight checks
    from config import X_USERNAME, DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID, DB_PATH

    errors = []
    if not X_USERNAME:
        errors.append("X_USERNAME not set in .env")
    if not DISCORD_BOT_TOKEN:
        errors.append("DISCORD_BOT_TOKEN not set in .env")
    if not DISCORD_CHANNEL_ID:
        errors.append("DISCORD_CHANNEL_ID not set in .env")

    if errors:
        logger.error("❌ Missing configuration:")
        for e in errors:
            logger.error(f"   • {e}")
        logger.error("📝 Copy .env.example to .env and fill in your credentials.")
        sys.exit(1)

    # Check if DB exists
    if not os.path.exists(DB_PATH):
        logger.info("🗄️  Database not found, initializing...")
        from db.init_db import init_db
        init_db()

    from db.models import get_active_accounts
    accounts = get_active_accounts()
    if not accounts:
        logger.warning("⚠️  No smart accounts to track!")
        logger.warning("   Run: python -m db.seed_accounts")
        logger.warning("   Or use !add command in Discord after bot starts")

    # Print startup banner
    logger.info("=" * 50)
    logger.info("🔍 Alpha Follow Tracker")
    logger.info("=" * 50)
    logger.info(f"📊 Tracking {len(accounts)} smart accounts")
    logger.info(f"📡 Discord channel: {DISCORD_CHANNEL_ID}")
    logger.info("🚀 Starting bot...")
    logger.info("")

    # Start the bot (this blocks — the poll loop runs inside)
    from bot.discord_bot import run_bot
    run_bot()


if __name__ == "__main__":
    main()
