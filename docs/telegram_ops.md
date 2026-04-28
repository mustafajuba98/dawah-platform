# Telegram Operations Guide

## Bot Setup
1. Create bot with BotFather.
2. Add `TELEGRAM_BOT_TOKEN` to `.env`.
3. Start bot locally:
   - `python manage.py run_bot`

## Supported Commands
- `/start`
- `/search <keyword>`
- `/category`
- `/daily`
- `/random`
- `/help`

## Daily Broadcast
Schedule this command on PythonAnywhere task scheduler:
- `python manage.py send_daily_video`

## Troubleshooting
- If messages fail, verify bot token and subscriber activity.
- Ensure bot can send messages to chats that started the bot first.
