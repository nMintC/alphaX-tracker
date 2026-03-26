"""
Polling engine — the heart of the tracker.
Periodically checks each smart account's following list,
diffs against the saved snapshot, and yields new follow events.
"""

import asyncio
import random
import logging
from dataclasses import dataclass

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import REQUEST_DELAY_MIN, REQUEST_DELAY_MAX
from db.models import (
    get_active_accounts,
    get_snapshot,
    add_to_snapshot,
    is_first_run,
    record_follow_event,
)
from tracker.scraper import XScraper

logger = logging.getLogger("poller")


@dataclass
class NewFollowEvent:
    """Represents a detected new follow — passed to the Discord bot."""
    smart_username: str
    smart_tag: str
    followed_username: str
    followed_name: str
    followed_bio: str
    followed_followers: int
    followed_avatar_url: str
    followed_verified: bool


async def poll_once(scraper: XScraper) -> list[NewFollowEvent]:
    """
    Run one full polling cycle across all smart accounts.
    Returns a list of NewFollowEvent for any new follows detected.
    """
    accounts = get_active_accounts()
    all_events = []

    logger.info(f"🔄 Starting poll cycle — {len(accounts)} accounts to check")

    for account in accounts:
        account_id = account["id"]
        username = account["username"]
        tag = account["tag"]

        try:
            # Fetch current following list from X
            following = await scraper.get_following(username)

            if not following:
                logger.warning(f"  ⚠️  @{username}: got empty following list, skipping")
                continue

            current_usernames = {u["username"] for u in following if u["username"]}

            # Build a lookup for profile info
            profile_lookup = {u["username"]: u for u in following}

            # Get previous snapshot from DB
            previous = get_snapshot(account_id)
            first_run = is_first_run(account_id)

            # Diff: who's new?
            new_follows = current_usernames - previous

            if first_run:
                # First time seeing this account — save snapshot, don't alert
                logger.info(f"  🆕 @{username}: first run, saving {len(current_usernames)} follows (no alerts)")
                add_to_snapshot(account_id, list(current_usernames))
            elif new_follows:
                logger.info(f"  🔔 @{username}: {len(new_follows)} new follows detected!")
                add_to_snapshot(account_id, list(new_follows))

                for followed_uname in new_follows:
                    profile = profile_lookup.get(followed_uname, {})

                    event = NewFollowEvent(
                        smart_username=username,
                        smart_tag=tag,
                        followed_username=followed_uname,
                        followed_name=profile.get("name", ""),
                        followed_bio=profile.get("bio", ""),
                        followed_followers=profile.get("followers_count", 0),
                        followed_avatar_url=profile.get("avatar_url", ""),
                        followed_verified=profile.get("verified", False),
                    )
                    all_events.append(event)

                    # Save to history
                    record_follow_event(
                        smart_username=event.smart_username,
                        smart_tag=event.smart_tag,
                        followed_username=event.followed_username,
                        followed_name=event.followed_name,
                        followed_bio=event.followed_bio,
                        followed_followers=event.followed_followers,
                        followed_avatar_url=event.followed_avatar_url,
                        followed_verified=event.followed_verified,
                    )
            else:
                logger.info(f"  ✅ @{username}: no new follows")

        except Exception as e:
            logger.error(f"  ❌ @{username}: error — {e}")

        # Random delay between accounts to look human
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        logger.debug(f"  💤 Sleeping {delay:.1f}s before next account...")
        await asyncio.sleep(delay)

    logger.info(f"✅ Poll cycle complete — {len(all_events)} new follow(s) detected")
    return all_events
