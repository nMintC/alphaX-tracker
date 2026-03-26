"""
Discord bot — pushes rich embed alerts for new follows
and provides management commands.
"""

import asyncio
import logging
from datetime import datetime

import discord
from discord.ext import commands, tasks

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    DISCORD_BOT_TOKEN,
    DISCORD_CHANNEL_ID,
    POLL_INTERVAL_SECONDS,
    TAG_EMOJIS,
    VALID_TAGS,
)
from db.models import add_account, remove_account, get_active_accounts, get_recent_events
from tracker.scraper import XScraper
from tracker.poller import poll_once, NewFollowEvent

logger = logging.getLogger("discord_bot")

# ── Bot Setup ─────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

scraper = XScraper()
poll_count = 0
last_poll_time = None


# ── Embed Builder ─────────────────────────────────────────────────────

def format_followers(count: int) -> str:
    """Format follower count: 1234 → 1.2k, 1234567 → 1.2M"""
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    elif count >= 1_000:
        return f"{count / 1_000:.1f}k"
    return str(count)


# Color per tag so you can visually scan alerts by type
TAG_COLORS = {
    "tier1_vc":     0x7F77DD,  # Purple
    "tier2_vc":     0x5DCAA5,  # Teal
    "alpha_hunter": 0xD85A30,  # Coral
    "founder":      0xEF9F27,  # Amber
    "kol":          0x378ADD,  # Blue
    "trader":       0x97C459,  # Green
    "other":        0x888780,  # Gray
}


def build_follow_embed(event: NewFollowEvent) -> discord.Embed:
    """
    Build a rich Discord embed for a new follow event.
    Styled similar to Orbital Follow.
    """
    tag_emoji = TAG_EMOJIS.get(event.smart_tag, "👤")
    verified = " ✅" if event.followed_verified else ""
    followers_str = format_followers(event.followed_followers)
    color = TAG_COLORS.get(event.smart_tag, 0x1DA1F2)

    name_display = event.followed_name or event.followed_username

    embed = discord.Embed(
        color=color,
        timestamp=datetime.utcnow(),
    )

    # ── Header: followed account name + stats (like Orbital) ──────────
    embed.title = f"{name_display}  ——  {followers_str}{verified}"
    embed.url = f"https://x.com/{event.followed_username}"

    # ── Body: who followed + bio ──────────────────────────────────────
    lines = [
        f"[**{event.smart_username}**](https://x.com/{event.smart_username})"
        f" just followed "
        f"[**{event.followed_username}**](https://x.com/{event.followed_username})",
        "",
    ]

    bio = event.followed_bio or "_No bio_"
    if len(bio) > 280:
        bio = bio[:277] + "..."
    lines.append(f"**Bio:**\n{bio}")

    embed.description = "\n".join(lines)

    # ── Thumbnail: profile picture ────────────────────────────────────
    avatar = event.followed_avatar_url
    if avatar:
        avatar = avatar.replace("_normal", "_200x200")
        embed.set_thumbnail(url=avatar)

    # ── Footer ────────────────────────────────────────────────────────
    embed.set_footer(text=f"Alpha Tracker  •  {tag_emoji} {event.smart_tag}")

    return embed


def build_multi_follow_message(events: list[NewFollowEvent]) -> str:
    """
    When a smart account follows multiple people at once,
    build a summary header message.
    """
    if len(events) <= 1:
        return ""
    smart = events[0].smart_username
    names = ", ".join(f"**@{e.followed_username}**" for e in events[:5])
    extra = f" and {len(events) - 5} more" if len(events) > 5 else ""
    return f"🔔 **@{smart}** just followed {len(events)} accounts: {names}{extra}"


# ── Polling Task ──────────────────────────────────────────────────────

@tasks.loop(seconds=POLL_INTERVAL_SECONDS)
async def poll_loop():
    """Main polling loop that runs every POLL_INTERVAL_SECONDS."""
    global poll_count, last_poll_time

    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        logger.error(f"❌ Could not find channel {DISCORD_CHANNEL_ID}")
        return

    try:
        events = await poll_once(scraper)
        poll_count += 1
        last_poll_time = datetime.utcnow()

        if not events:
            return

        # Group events by smart account (for multi-follow summaries)
        from itertools import groupby
        events_sorted = sorted(events, key=lambda e: e.smart_username)
        for smart_user, group in groupby(events_sorted, key=lambda e: e.smart_username):
            group_events = list(group)

            # If one account followed many people, send a summary first
            summary = build_multi_follow_message(group_events)
            if summary:
                await channel.send(summary)
                await asyncio.sleep(0.5)

            # Send individual embed cards
            for event in group_events:
                embed = build_follow_embed(event)
                content = f"**{event.smart_username}** just followed **{event.followed_username}**"
                await channel.send(content=content, embed=embed)
                await asyncio.sleep(1)  # Avoid Discord rate limits

    except Exception as e:
        logger.error(f"❌ Poll error: {e}", exc_info=True)


@poll_loop.error
async def poll_error_handler(error):
    """Recover from poll errors — don't let the loop die."""
    logger.error(f"❌ Poll loop crashed: {error}", exc_info=True)
    logger.info("🔄 Restarting poll loop in 30 seconds...")
    await asyncio.sleep(30)
    if not poll_loop.is_running():
        poll_loop.start()


@poll_loop.before_loop
async def before_poll():
    """Wait until the bot is ready before starting the poll loop."""
    await bot.wait_until_ready()
    logger.info("🚀 Poll loop starting...")


# ── Bot Events ────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    logger.info(f"🤖 Bot is online as {bot.user}")
    logger.info(f"📡 Alerts channel: {DISCORD_CHANNEL_ID}")
    logger.info(f"⏱️  Poll interval: {POLL_INTERVAL_SECONDS}s")

    accounts = get_active_accounts()
    logger.info(f"👀 Tracking {len(accounts)} smart accounts")

    if not poll_loop.is_running():
        poll_loop.start()


# ── Commands ──────────────────────────────────────────────────────────

@bot.command(name="add")
async def cmd_add(ctx, username: str, tag: str = "other"):
    """Add a smart account to track. Usage: !add username tier1_vc"""
    username = username.lower().strip().lstrip("@")

    if tag not in VALID_TAGS:
        await ctx.send(f"❌ Invalid tag `{tag}`. Valid: {', '.join(VALID_TAGS)}")
        return

    ok = add_account(username, tag)
    if ok:
        emoji = TAG_EMOJIS.get(tag, "👤")
        await ctx.send(f"✅ Now tracking **@{username}** {emoji} `{tag}`")
    else:
        await ctx.send(f"⚠️ **@{username}** is already being tracked.")


@bot.command(name="remove")
async def cmd_remove(ctx, username: str):
    """Stop tracking a smart account. Usage: !remove username"""
    username = username.lower().strip().lstrip("@")
    remove_account(username)
    await ctx.send(f"🗑️ Stopped tracking **@{username}**")


@bot.command(name="list")
async def cmd_list(ctx):
    """Show all tracked smart accounts."""
    accounts = get_active_accounts()
    if not accounts:
        await ctx.send("📭 No accounts being tracked. Use `!add @username tag` to start.")
        return

    lines = []
    current_tag = None
    for acc in accounts:
        if acc["tag"] != current_tag:
            current_tag = acc["tag"]
            emoji = TAG_EMOJIS.get(current_tag, "👤")
            lines.append(f"\n{emoji} **{current_tag}**")
        lines.append(f"  • @{acc['username']}")

    embed = discord.Embed(
        title=f"👀 Tracking {len(accounts)} accounts",
        description="\n".join(lines),
        color=0x1DA1F2,
    )
    await ctx.send(embed=embed)


@bot.command(name="status")
async def cmd_status(ctx):
    """Show bot status."""
    accounts = get_active_accounts()
    uptime = "Running" if poll_loop.is_running() else "Stopped"
    last = last_poll_time.strftime("%H:%M:%S UTC") if last_poll_time else "Never"
    health = "🟢 Healthy" if scraper.is_healthy else "🔴 Errors detected"

    embed = discord.Embed(title="🤖 Bot Status", color=0x2ECC71 if scraper.is_healthy else 0xE24B4A)
    embed.add_field(name="Status", value=uptime, inline=True)
    embed.add_field(name="Scraper", value=health, inline=True)
    embed.add_field(name="Accounts tracked", value=str(len(accounts)), inline=True)
    embed.add_field(name="Poll interval", value=f"{POLL_INTERVAL_SECONDS}s", inline=True)
    embed.add_field(name="Polls completed", value=str(poll_count), inline=True)
    embed.add_field(name="Last poll", value=last, inline=True)
    await ctx.send(embed=embed)


@bot.command(name="recent")
async def cmd_recent(ctx, limit: int = 10):
    """Show recent follow events. Usage: !recent 10"""
    events = get_recent_events(limit)
    if not events:
        await ctx.send("📭 No follow events recorded yet.")
        return

    lines = []
    for e in events:
        emoji = TAG_EMOJIS.get(e["smart_tag"], "👤")
        lines.append(
            f"{emoji} **@{e['smart_username']}** → "
            f"[@{e['followed_username']}](https://x.com/{e['followed_username']}) "
            f"({e['followed_followers']:,} followers)"
        )

    embed = discord.Embed(
        title=f"📜 Last {len(events)} follow events",
        description="\n".join(lines),
        color=0x1DA1F2,
    )
    await ctx.send(embed=embed)


@bot.command(name="poll")
async def cmd_poll(ctx):
    """Trigger a manual poll right now. Usage: !poll"""
    await ctx.send("🔄 Running manual poll...")
    channel = bot.get_channel(DISCORD_CHANNEL_ID)

    try:
        events = await poll_once(scraper)
        if events:
            for event in events:
                embed = build_follow_embed(event)
                await channel.send(
                    content=f"**{event.smart_username}** just followed **{event.followed_username}**",
                    embed=embed,
                )
                await asyncio.sleep(1)
            await ctx.send(f"✅ Found {len(events)} new follow(s)!")
        else:
            await ctx.send("✅ Poll complete — no new follows detected.")
    except Exception as e:
        await ctx.send(f"❌ Poll failed: {e}")


@bot.command(name="commands")
async def cmd_commands(ctx):
    """Show all available commands."""
    embed = discord.Embed(
        title="🔍 Alpha Follow Tracker — Commands",
        color=0x1DA1F2,
    )
    embed.description = "\n".join([
        "**!add** `@username tag` — Start tracking an account",
        f"  Tags: {', '.join(f'`{t}`' for t in VALID_TAGS)}",
        "",
        "**!remove** `@username` — Stop tracking an account",
        "",
        "**!list** — Show all tracked accounts",
        "",
        "**!status** — Bot status and stats",
        "",
        "**!recent** `[count]` — Show recent follow events",
        "",
        "**!poll** — Trigger a manual poll now",
        "",
        "**!commands** — This message",
    ])
    await ctx.send(embed=embed)


# ── Run ───────────────────────────────────────────────────────────────

def run_bot():
    """Start the Discord bot."""
    if not DISCORD_BOT_TOKEN:
        logger.error("❌ DISCORD_BOT_TOKEN not set in .env")
        return
    if not DISCORD_CHANNEL_ID:
        logger.error("❌ DISCORD_CHANNEL_ID not set in .env")
        return

    bot.run(DISCORD_BOT_TOKEN)
