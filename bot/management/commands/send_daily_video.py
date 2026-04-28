import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from telegram import Bot

from bot.models import BotNotification, TelegramSubscriber
from videos.models import Video


class Command(BaseCommand):
    help = "Send a daily featured/random video to active subscribers."

    def handle(self, *args, **options):
        from os import getenv

        token = getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            self.stdout.write(self.style.WARNING("TELEGRAM_BOT_TOKEN missing, skipped."))
            return

        bot = Bot(token=token)
        recent_videos = Video.objects.filter(
            is_active=True,
            published_at__gte=timezone.now() - timedelta(days=30),
        )
        featured = recent_videos.filter(is_featured=True)
        candidates = list(featured or recent_videos)
        if not candidates:
            self.stdout.write(self.style.WARNING("No candidate videos found."))
            return

        selected = random.choice(candidates)
        text = f"{selected.title}\nhttps://www.youtube.com/watch?v={selected.video_id}\n{selected.seo_description[:200]}"

        sent = 0
        failed = 0
        for subscriber in TelegramSubscriber.objects.filter(is_active=True):
            try:
                bot.send_message(chat_id=subscriber.chat_id, text=text)
                sent += 1
            except Exception:
                failed += 1
                continue

        status = BotNotification.STATUS_SUCCESS
        if sent == 0 and failed > 0:
            status = BotNotification.STATUS_FAILED
        elif failed > 0:
            status = BotNotification.STATUS_PARTIAL
        BotNotification.objects.create(
            title=selected.title,
            message=selected.seo_description[:500],
            youtube_url=f"https://www.youtube.com/watch?v={selected.video_id}",
            sent_count=sent,
            status=status,
        )

        self.stdout.write(self.style.SUCCESS(f"Sent daily video to {sent} subscribers."))
