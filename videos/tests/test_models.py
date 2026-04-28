from django.test import TestCase
from django.utils import timezone

from videos.models import SyncLog, Video


class VideoModelTests(TestCase):
    def test_video_defaults(self):
        video = Video.objects.create(
            video_id="abc123",
            title="Test",
            published_at=timezone.now(),
        )
        self.assertEqual(video.category, Video.CATEGORY_OTHER)
        self.assertTrue(video.is_active)


class SyncLogModelTests(TestCase):
    def test_synclog_create(self):
        log = SyncLog.objects.create(status=SyncLog.STATUS_SUCCESS)
        self.assertEqual(log.videos_imported, 0)
