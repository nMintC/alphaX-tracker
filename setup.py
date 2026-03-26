#!/usr/bin/env python3
"""
🔍 Alpha Follow Tracker — Interactive Setup
Run this once to set up everything: python setup.py
"""

import os
import sys
import shutil


def banner():
    print()
    print("=" * 52)
    print("  🔍 Alpha Follow Tracker — Setup")
    print("=" * 52)
    print()


def step(num, title):
    print(f"\n{'─' * 52}")
    print(f"  Step {num}: {title}")
    print(f"{'─' * 52}\n")


def check_python():
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 10):
        print(f"❌ Python 3.10+ required. You have {v.major}.{v.minor}")
        sys.exit(1)
    print(f"✅ Python {v.major}.{v.minor}.{v.micro}")


def setup_env():
    if os.path.exists(".env"):
        overwrite = input("  .env already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != "y":
            print("  ⏭️  Keeping existing .env")
            return

    print("  You'll need:")
    print("  1. A burner X/Twitter account (username, email, password)")
    print("  2. A Discord bot token")
    print("  3. A Discord channel ID for alerts")
    print()

    x_user = input("  X username (burner account): ").strip()
    x_email = input("  X email: ").strip()
    x_pass = input("  X password: ").strip()
    print()
    print("  📖 Create a Discord bot at: https://discord.com/developers/applications")
    print("     → New Application → Bot → Copy Token")
    print("     → OAuth2 → URL Generator → check 'bot' → check 'Send Messages' + 'Embed Links'")
    print("     → Copy the invite URL and open it to add the bot to your server")
    print()
    dc_token = input("  Discord bot token: ").strip()
    print()
    print("  📖 Get channel ID: Enable Developer Mode in Discord settings")
    print("     → Right-click your alerts channel → Copy Channel ID")
    print()
    dc_channel = input("  Discord channel ID: ").strip()

    with open(".env", "w") as f:
        f.write(f"# ── X/Twitter (burner account!) ──\n")
        f.write(f"X_USERNAME={x_user}\n")
        f.write(f"X_EMAIL={x_email}\n")
        f.write(f"X_PASSWORD={x_pass}\n\n")
        f.write(f"# ── Discord ──\n")
        f.write(f"DISCORD_BOT_TOKEN={dc_token}\n")
        f.write(f"DISCORD_CHANNEL_ID={dc_channel}\n")

    print("\n  ✅ .env created!")


def install_deps():
    print("  Installing Python packages...")
    os.system(f"{sys.executable} -m pip install -r requirements.txt -q")
    print("  ✅ Dependencies installed!")


def init_database():
    print("  Creating database tables...")
    os.system(f"{sys.executable} -m db.init_db")


def seed_accounts():
    print("  The default seed list has 14 accounts (VCs, alpha hunters, founders, traders).")
    print("  You can edit db/seed_accounts.py later to customize.")
    print()
    seed = input("  Seed default smart accounts? (Y/n): ").strip().lower()
    if seed != "n":
        os.system(f"{sys.executable} -m db.seed_accounts")


def main():
    banner()

    step(1, "Check Python version")
    check_python()

    step(2, "Install dependencies")
    install_deps()

    step(3, "Configure credentials")
    setup_env()

    step(4, "Initialize database")
    init_database()

    step(5, "Seed smart accounts")
    seed_accounts()

    print("\n" + "=" * 52)
    print("  🎉 Setup complete!")
    print("=" * 52)
    print()
    print("  Run the bot:")
    print("    python main.py")
    print()
    print("  Discord commands:")
    print("    !list      — Show tracked accounts")
    print("    !add @user tier1_vc  — Track a new account")
    print("    !remove @user        — Stop tracking")
    print("    !status    — Bot status")
    print("    !poll      — Manual poll")
    print("    !recent    — Recent follow events")
    print("    !commands  — All commands")
    print()


if __name__ == "__main__":
    main()
