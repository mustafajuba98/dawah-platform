from django.core.management.base import BaseCommand, CommandError

from videos.models import Playlist, Video, VideoPlaylist
from videos.services.youtube import YouTubeService


class Command(BaseCommand):
    help = "Rebuild VideoPlaylist links from YouTube playlists."

    def add_arguments(self, parser):
        parser.add_argument("--channel", required=True, help="YouTube channel ID")

    def handle(self, *args, **options):
        channel_id = options["channel"].strip()
        if not channel_id:
            raise CommandError("channel is required.")

        service = YouTubeService()
        playlists = service.get_playlists(channel_id)
        created_links = 0
        updated_links = 0

        for playlist in playlists:
            snippet = playlist.get("snippet", {})
            playlist_obj, _ = Playlist.objects.update_or_create(
                playlist_id=playlist.get("id", ""),
                defaults={
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "thumbnail_url": (snippet.get("thumbnails", {}).get("high", {}) or {}).get("url", ""),
                    "video_count": int(playlist.get("contentDetails", {}).get("itemCount", 0)),
                    "is_active": True,
                },
            )
            video_ids = service.get_playlist_video_ids(playlist_obj.playlist_id)
            videos = {v.video_id: v for v in Video.objects.filter(video_id__in=video_ids)}
            for position, vid in enumerate(video_ids, start=1):
                video = videos.get(vid)
                if not video:
                    continue
                _, created = VideoPlaylist.objects.update_or_create(
                    video=video,
                    playlist=playlist_obj,
                    defaults={"position": position},
                )
                if created:
                    created_links += 1
                else:
                    updated_links += 1

        self.stdout.write(self.style.SUCCESS(f"Playlist links rebuilt: created={created_links}, updated={updated_links}"))
