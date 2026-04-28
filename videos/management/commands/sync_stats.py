from django.core.management.base import BaseCommand

from videos.models import Video
from videos.services.youtube import YouTubeService


class Command(BaseCommand):
    help = "Sync view and like stats for existing videos."

    def handle(self, *args, **options):
        service = YouTubeService()
        video_ids = list(Video.objects.values_list("video_id", flat=True))
        details = service.get_video_details(video_ids)
        detail_map = {item["id"]: item for item in details if item.get("id")}

        updated = 0
        for video in Video.objects.all():
            detail = detail_map.get(video.video_id)
            if not detail:
                continue
            stats = detail.get("statistics", {})
            video.view_count = int(stats.get("viewCount", 0))
            video.like_count = int(stats.get("likeCount", 0))
            video.save(update_fields=["view_count", "like_count", "updated_at"])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"Updated stats for {updated} videos."))
