# Dawah Platform (Django 5.2)

Production-grade Islamic YouTube channel platform built on Django 5.2.

## Features
- YouTube channel import and sync
- Search and category browsing
- AI summary/SEO/tag generation via Gemini
- Telegram bot commands and daily broadcast
- Admin panel and API endpoints

## Setup
1. Create virtualenv and install dependencies:
   - `pip install -r requirements.txt`
2. Copy env file:
   - `copy .env.example .env`
3. Run migrations:
   - `python manage.py migrate`
4. Create superuser:
   - `python manage.py createsuperuser`
5. Run server:
   - `python manage.py runserver`

## Commands
- `python manage.py import_videos --channel UCxxxx`
- `python manage.py sync_stats`
- `python manage.py generate_seo --limit 50`
- `python manage.py run_bot`
- `python manage.py send_daily_video`
