"""
X/Twitter scraper using Twikit (free, no API key needed).
Handles login, session management, and data fetching.
"""

import asyncio
import os
import logging
from twikit import Client

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import X_USERNAME, X_EMAIL, X_PASSWORD, MAX_FOLLOWING_PAGES

logger = logging.getLogger("scraper")

COOKIES_FILE = "cookies.json"


class XScraper:
    def __init__(self):
        self.client = Client("en-US")
        self._logged_in = False
        self._consecutive_errors = 0

    async def login(self, force_fresh: bool = False):
        """Login to X. Uses saved cookies if available, otherwise logs in fresh."""
        if self._logged_in and not force_fresh:
            return

        # Try loading saved cookies first (avoids re-login)
        if not force_fresh and os.path.exists(COOKIES_FILE):
            try:
                self.client.load_cookies(COOKIES_FILE)
                self._logged_in = True
                logger.info("✅ Loaded saved session cookies")
                return
            except Exception as e:
                logger.warning(f"⚠️  Could not load cookies: {e}")

        # Fresh login
        try:
            await self.client.login(
                auth_info_1=X_USERNAME,
                auth_info_2=X_EMAIL,
                password=X_PASSWORD,
                cookies_file=COOKIES_FILE,
                enable_ui_metrics=True,  # Reduces suspension risk
            )
            self._logged_in = True
            self._consecutive_errors = 0
            logger.info("✅ Logged in to X successfully")
        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            raise

    async def _handle_rate_limit(self, retry_after: int = 60):
        """Wait when we hit a rate limit."""
        logger.warning(f"⏳ Rate limited. Waiting {retry_after}s...")
        await asyncio.sleep(retry_after)

    async def _safe_request(self, func, *args, retries: int = 2, **kwargs):
        """
        Wrapper that handles common twikit errors:
        - TooManyRequests → wait and retry
        - Auth errors → re-login and retry
        - Other errors → log and return None
        """
        for attempt in range(retries + 1):
            try:
                result = await func(*args, **kwargs)
                self._consecutive_errors = 0
                return result
            except Exception as e:
                error_str = str(e).lower()

                # Rate limit
                if "too many" in error_str or "rate" in error_str or "429" in error_str:
                    wait = 60 * (attempt + 1)  # Back off: 60s, 120s, 180s
                    await self._handle_rate_limit(wait)
                    continue

                # Auth / session expired
                if "unauthorized" in error_str or "403" in error_str or "login" in error_str:
                    logger.warning("🔑 Session expired, re-logging in...")
                    self._logged_in = False
                    try:
                        await self.login(force_fresh=True)
                        continue
                    except Exception:
                        pass

                # Account suspended or locked
                if "suspend" in error_str or "locked" in error_str:
                    logger.error("🚨 Account may be suspended! Check your burner account.")
                    self._consecutive_errors += 1
                    return None

                # Unknown error
                self._consecutive_errors += 1
                if attempt < retries:
                    logger.warning(f"⚠️  Attempt {attempt + 1} failed: {e}. Retrying...")
                    await asyncio.sleep(10)
                else:
                    logger.error(f"❌ All retries failed: {e}")
                    return None

        return None

    async def get_following(self, username: str) -> list[dict]:
        """
        Get the list of accounts that `username` is following.
        Returns a list of dicts with user info.
        """
        await self.login()

        following = []

        # Get user first
        user = await self._safe_request(
            self.client.get_user_by_screen_name, username
        )
        if not user:
            logger.warning(f"User @{username} not found")
            return []

        # Fetch following list (paginated)
        result = await self._safe_request(user.get_following)
        if not result:
            return []

        page = 0
        while result and page < MAX_FOLLOWING_PAGES:
            for u in result:
                following.append({
                    "username": (u.screen_name or "").lower(),
                    "name": u.name or "",
                    "bio": u.description or "",
                    "followers_count": u.followers_count or 0,
                    "avatar_url": u.profile_image_url or "",
                    "verified": getattr(u, "is_blue_verified", False),
                })
            page += 1

            # Try to get next page
            try:
                result = await result.next()
            except Exception:
                break

        logger.info(f"📋 @{username}: fetched {len(following)} following")
        return following

    async def get_user_info(self, username: str) -> dict | None:
        """Get profile info for a single user."""
        await self.login()
        user = await self._safe_request(
            self.client.get_user_by_screen_name, username
        )
        if not user:
            return None
        return {
            "username": (user.screen_name or "").lower(),
            "name": user.name or "",
            "bio": user.description or "",
            "followers_count": user.followers_count or 0,
            "avatar_url": user.profile_image_url or "",
            "verified": getattr(user, "is_blue_verified", False),
        }

    @property
    def is_healthy(self) -> bool:
        """Check if the scraper is working (no consecutive errors)."""
        return self._consecutive_errors < 5
