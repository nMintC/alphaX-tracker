# 🔍 Alpha Follow Tracker

A free Discord bot that monitors crypto smart accounts on X (Twitter) and alerts you
whenever they follow someone new — just like Orbital Follow.

## How It Works

```
Every 2 minutes:
  For each smart account →
    Fetch their following list (via Twikit, free, no API key needed)
    Compare with previous snapshot
    If new follows detected →
      Grab the new account's profile info
      Push a rich embed alert to your Discord channel
```

## What You Get

Discord alerts showing:
- 🟢 Who the smart account just followed
- 👤 The followed account's username, bio, follower count
- 🖼️ Profile picture
- ⏰ Timestamp

## Setup

### 1. Prerequisites
- Python 3.10+
- A burner X/Twitter account (don't use your main!)
- A Discord bot token ([create one here](https://discord.com/developers/applications))

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
- X burner account login
- Discord bot token
- Discord channel ID where alerts go

### 4. Initialize database
```bash
python -m db.init_db
```

### 5. Add smart accounts to track
Edit `db/seed_accounts.py` with the X usernames you want to monitor,
then run:
```bash
python -m db.seed_accounts
```

### 6. Run!
```bash
python main.py
```

## Adding / Removing Accounts

You can manage tracked accounts via Discord commands:
- `!add @username tier1_vc` — Add an account to track
- `!remove @username` — Stop tracking an account
- `!list` — Show all tracked accounts
- `!status` — Show bot status and last poll time

## Safety Tips (Important!)

- **Use a burner X account** — scraping can get accounts suspended
- **Don't track too many accounts** — start with 10-20, max ~50
- **Polling interval is 2 min** — don't lower it, you'll get rate limited
- **Random delays** between each account fetch (5-15 sec)

## Free Hosting Options

- **Oracle Cloud** — Always-free VPS (best option, runs 24/7)
- **Railway** — Free tier (500 hours/month)
- **Your own PC** — Just keep the terminal open
- **Raspberry Pi** — Perfect for running 24/7 at home

## Project Structure

```
alpha-tracker/
├── main.py              # Entry point
├── config.py            # Configuration
├── .env.example
├── requirements.txt
├── db/
│   ├── init_db.py       # Create tables
│   ├── models.py        # DB helpers
│   └── seed_accounts.py # Initial smart accounts
├── tracker/
│   ├── scraper.py       # Twikit wrapper (fetches X data)
│   └── poller.py        # Main polling loop + diff logic
└── bot/
    └── discord_bot.py   # Discord bot + embed alerts
```
