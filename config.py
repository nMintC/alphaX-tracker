import os
from dotenv import load_dotenv

load_dotenv()

# ── X/Twitter credentials (burner account!) ───────────────────────────
X_USERNAME = os.getenv("X_USERNAME", "")
X_EMAIL = os.getenv("X_EMAIL", "")
X_PASSWORD = os.getenv("X_PASSWORD", "")

# ── Discord ───────────────────────────────────────────────────────────
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

# ── Polling ───────────────────────────────────────────────────────────
# How often to run a full poll cycle (seconds)
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "120"))

# Random delay range between each account fetch (seconds)
# This makes your scraping look more human-like
REQUEST_DELAY_MIN = int(os.getenv("REQUEST_DELAY_MIN", "5"))
REQUEST_DELAY_MAX = int(os.getenv("REQUEST_DELAY_MAX", "15"))

# Max following pages to fetch per account (each page ≈ 20 users)
# For accounts following thousands, we only check the most recent follows
MAX_FOLLOWING_PAGES = 1

# ── Database ──────────────────────────────────────────────────────────
DB_PATH = os.getenv("DB_PATH", "alpha_tracker.db")

# ── Smart Account Tags ────────────────────────────────────────────────
VALID_TAGS = [
    "tier1_vc",      # a16z, Paradigm, etc.
    "tier2_vc",      # Mid-tier VCs
    "alpha_hunter",  # Known alpha callers
    "founder",       # Notable crypto founders
    "kol",           # Key opinion leaders
    "trader",        # Whale traders
    "other",
]

# Tag display emojis for Discord embeds
TAG_EMOJIS = {
    "tier1_vc":     "🏦",
    "tier2_vc":     "🏛️",
    "alpha_hunter": "🎯",
    "founder":      "⚡",
    "kol":          "📢",
    "trader":       "📈",
    "other":        "👤",
}
