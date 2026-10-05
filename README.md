# Telegram Link Resolver Bot

Python + Telegram + MongoDB starter bot.

## Features
- Telegram bot using python-telegram-bot
- MongoDB user storage
- Ban/unban
- Owner statistics
- Render health endpoint
- Ordinary HTTP redirect resolution
- Modular resolver directory for future legitimate integrations

## Setup

1. Copy `.env.example` to `.env`.
2. Fill in `BOT_TOKEN`, `OWNER_ID`, and `MONGO_URI`.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run:

```bash
python bot.py
```

## Render

The included `render.yaml` can be used as a starting point.

Set the secret environment variables in Render.

## Scope

The resolver follows ordinary HTTP redirects. It does not attempt to defeat
CAPTCHA, login requirements, anti-bot challenges, paywalls, or other access
controls.
