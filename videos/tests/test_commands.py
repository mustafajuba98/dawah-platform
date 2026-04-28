from importlib import import_module
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from videos.models import Video


class ImportVideosCommandTests(TestCase):
    def test_import_command_calls_sync(self):
        command_module = import_module("videos.management.commands.import_videos")
        with patch.object(command_module, "YouTubeService") as mock_service_cls:
            service = mock_service_cls.return_value
            service.sync_channel.return_value = type(
                "obj", (), {"status": "success", "videos_imported": 1, "videos_updated": 0, "api_units_used": 1}
            )()
            call_command("import_videos", channel="UC123")
            service.sync_channel.assert_called_once_with("UC123")


class SyncStatsCommandTests(TestCase):
    def test_sync_stats_updates_counts(self):
        video = Video.objects.create(video_id="v123", title="T", published_at=timezone.now())
        command_module = import_module("videos.management.commands.sync_stats")
        with patch.object(command_module, "YouTubeService") as mock_service_cls:
            service = mock_service_cls.return_value
            service.get_video_details.return_value = [
                {"id": "v123", "statistics": {"viewCount": "10", "likeCount": "2"}}
            ]
            call_command("sync_stats")
        video.refresh_from_db()
        self.assertEqual(video.view_count, 10)
        self.assertEqual(video.like_count, 2)
