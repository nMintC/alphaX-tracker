# 🚀 Free Deployment Guide

Your bot needs to run 24/7 to catch follows in real-time.
Here are your best free options, ranked by ease of setup.

---

## Option 1: Oracle Cloud (Best — Always Free VPS)

Oracle gives you a free VM that runs forever. This is the best option.

### Setup:
1. Sign up at https://cloud.oracle.com (free tier, credit card required but won't charge)
2. Create a VM instance:
   - Shape: VM.Standard.E2.1.Micro (Always Free)
   - OS: Ubuntu 22.04
   - Download SSH key
3. SSH in and install:
```bash
# Connect
ssh -i your-key.pem ubuntu@your-ip

# Install Python 3.12
sudo apt update && sudo apt install -y python3.12 python3.12-venv python3-pip git

# Clone your project (push to GitHub first)
git clone https://github.com/yourusername/alpha-follow-tracker.git
cd alpha-follow-tracker

# Set up
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env  # Fill in your credentials

# Initialize
python -m db.init_db
python -m db.seed_accounts

# Run with systemd (auto-restart on crash + boot)
sudo nano /etc/systemd/system/alpha-tracker.service
```

4. Create the systemd service file:
```ini
[Unit]
Description=Alpha Follow Tracker
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/alpha-follow-tracker
Environment=PATH=/home/ubuntu/alpha-follow-tracker/venv/bin
ExecStart=/home/ubuntu/alpha-follow-tracker/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

5. Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable alpha-tracker
sudo systemctl start alpha-tracker

# Check status
sudo systemctl status alpha-tracker

# View logs
journalctl -u alpha-tracker -f
```

**Cost: $0 forever** (Oracle Cloud Always Free tier)

---

## Option 2: Railway (Easiest — Free Tier)

Railway has the simplest setup but limited free hours.

### Setup:
1. Push your code to GitHub
2. Go to https://railway.app → New Project → Deploy from GitHub
3. Select your repo
4. Add environment variables (from your .env) in the Railway dashboard
5. Deploy!

**Cost: $0** (500 hours/month free — enough for ~20 days of 24/7 running)
**Tip:** If you run out of hours, just create a new account with a different email.

---

## Option 3: Render (Easy — Free Tier)

### Setup:
1. Push to GitHub
2. Go to https://render.com → New → Background Worker
3. Connect your repo
4. Build command: `pip install -r requirements.txt && python -m db.init_db`
5. Start command: `python main.py`
6. Add env vars in dashboard

**Cost: $0** (750 hours/month free)
**Caveat:** Free tier sleeps after 15 min of inactivity — but since this is a background worker, it should stay alive.

---

## Option 4: Your Own PC / Raspberry Pi

Just run it in a terminal. Good for testing.

### With tmux (keeps running after you close terminal):
```bash
# Install tmux
sudo apt install tmux  # Linux
brew install tmux      # Mac

# Start a session
tmux new -s tracker

# Run the bot
cd alpha-follow-tracker
python main.py

# Detach: press Ctrl+B, then D
# Reattach later: tmux attach -t tracker
```

### With Docker:
```bash
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

**Cost: $0** (just electricity)

---

## Option 5: Fly.io (Generous Free Tier)

### Setup:
1. Install flyctl: `curl -L https://fly.io/install.sh | sh`
2. Sign up: `fly auth signup`
3. Launch:
```bash
cd alpha-follow-tracker
fly launch
# When asked, choose the free tier VM

fly secrets set X_USERNAME=your_user
fly secrets set X_EMAIL=your_email
fly secrets set X_PASSWORD=your_pass
fly secrets set DISCORD_BOT_TOKEN=your_token
fly secrets set DISCORD_CHANNEL_ID=your_channel

fly deploy
```

**Cost: $0** (3 shared VMs free)

---

## Tips for All Platforms

- **Push to GitHub** first (but add `.env`, `cookies.json`, `*.db` to `.gitignore`!)
- **Set env vars** in the platform's dashboard, never commit secrets
- **Monitor logs** for the first few hours to make sure scraping is stable
- If your X burner account gets suspended, create a new one and update the credentials
