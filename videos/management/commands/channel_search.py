import os

from django.core.management.base import BaseCommand, CommandError

from videos.services.youtube import YouTubeService


class Command(BaseCommand):
    help = "Search for videos inside a specific YouTube channel."

    def add_arguments(self, parser):
        parser.add_argument("--q", required=True, help="Search keyword")
        parser.add_argument("--channel", required=False, help="YouTube channel ID")
        parser.add_argument("--limit", type=int, default=10, help="Number of results")

    def handle(self, *args, **options):
        query = options["q"].strip()
        channel_id = options.get("channel") or os.getenv("YOUTUBE_CHANNEL_ID")
        if not channel_id:
            raise CommandError("Missing channel id. Set YOUTUBE_CHANNEL_ID or pass --channel.")

        service = YouTubeService()
        results = service.search_channel_videos(channel_id=channel_id, query=query, max_results=options["limit"])
        if not results:
            self.stdout.write(self.style.WARNING("No results found."))
            return

        for idx, item in enumerate(results, start=1):
            video_id = item.get("id", {}).get("videoId", "")
            title = item.get("snippet", {}).get("title", "")
            self.stdout.write(f"{idx}. {title}\n   https://www.youtube.com/watch?v={video_id}")
