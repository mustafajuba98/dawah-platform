from django.test import TestCase
from django.utils import timezone

from bot.models import TelegramSubscriber
from videos.models import Video


class TelegramSubscriberTests(TestCase):
    def test_create_subscriber(self):
        sub = TelegramSubscriber.objects.create(chat_id=1001)
        self.assertTrue(sub.is_active)


class BotDataTests(TestCase):
    def test_video_url_source_exists(self):
        video = Video.objects.create(video_id="x", title="title", published_at=timezone.now())
        self.assertEqual(video.video_id, "x")
