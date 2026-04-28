import os

from django.core.management.base import BaseCommand, CommandError

from videos.services.youtube import YouTubeService


class Command(BaseCommand):
    help = "Import and sync all channel videos from YouTube."

    def add_arguments(self, parser):
        parser.add_argument("--channel", type=str, required=False, help="YouTube channel ID")

    def handle(self, *args, **options):
        channel_id = options.get("channel") or os.getenv("YOUTUBE_CHANNEL_ID")
        if not channel_id:
            raise CommandError("Missing channel ID. Pass --channel or set YOUTUBE_CHANNEL_ID.")

        service = YouTubeService()
        sync_log = service.sync_channel(channel_id)
        self.stdout.write(
            self.style.SUCCESS(
                f"Sync completed: status={sync_log.status}, "
                f"imported={sync_log.videos_imported}, updated={sync_log.videos_updated}, "
                f"units={sync_log.api_units_used}"
            )
        )
        if sync_log.status == "failed":
            raise CommandError(f"Import failed: {sync_log.error_message or 'unknown error'}")
