# PythonAnywhere Deployment Guide

1. Create PythonAnywhere account.
2. Open Bash console.
3. Clone repository.
4. Install dependencies:
   - `pip install --user -r requirements.txt`
5. Create `.env` and set production values.
6. Run:
   - `python manage.py migrate`
   - `python manage.py collectstatic --noinput`
7. In Web tab, create Django app and point WSGI to project.
8. Set source and working directories.
9. Reload web app.
10. Add scheduled tasks:
    - `python manage.py import_videos --channel <CHANNEL_ID>` (daily/weekly)
    - `python manage.py sync_stats` (daily)
    - `python manage.py generate_seo --limit 50` (daily)
    - `python manage.py send_daily_video` (daily 7:00 AM)
