"""
Seed your initial smart accounts list.
Edit the list below, then run: python -m db.seed_accounts

Just put X usernames — no need for user IDs!
Tags: tier1_vc, tier2_vc, alpha_hunter, founder, kol, trader, other
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.models import add_account

# ═══════════════════════════════════════════════════════════════════════
# Edit this list with the accounts you want to track.
# Format: ("username", "tag")
# ═══════════════════════════════════════════════════════════════════════

ACCOUNTS = [
    # ── Tier 1 VCs ──────────────────────────────────────
    ("cdixon",          "tier1_vc"),       # Chris Dixon (a16z crypto)
    ("hasufl",          "tier1_vc"),       # Hasu (Flashbots / Paradigm)
    ("matthuang",       "tier1_vc"),       # Matt Huang (Paradigm)

    # ── Tier 2 VCs ──────────────────────────────────────
    ("DelpDigital",     "tier2_vc"),       # Delphi Digital
    ("KyleSamani",      "tier2_vc"),       # Kyle Samani (Multicoin)

    # ── Alpha Hunters ───────────────────────────────────
    ("DefiIgnas",       "alpha_hunter"),   # Ignas — DeFi research
    ("MilesDeutscher",  "alpha_hunter"),   # Miles Deutscher
    ("Rewkang",         "alpha_hunter"),   # Andrew Kang

    # ── Founders ────────────────────────────────────────
    ("VitalikButerin",  "founder"),        # Vitalik
    ("StaniKulechov",   "founder"),        # Stani (Aave)

    # ── KOLs ────────────────────────────────────────────
    ("CryptoHayes",     "kol"),            # Arthur Hayes
    ("0xMert_",         "kol"),            # Mert (Helius)

    # ── Traders ─────────────────────────────────────────
    ("HsakaTrades",     "trader"),         # Hsaka
    ("GCRClassic",      "trader"),         # GCR
]


def seed():
    added = 0
    for username, tag in ACCOUNTS:
        ok = add_account(username, tag)
        if ok:
            print(f"  ✅ @{username} ({tag})")
            added += 1
        else:
            print(f"  ⏭️  @{username} already exists, skipping")

    print(f"\n🌱 Added {added} new accounts. Total in list: {len(ACCOUNTS)}")


if __name__ == "__main__":
    seed()
