from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Run core sync pipeline: import_videos + sync_stats."

    def add_arguments(self, parser):
        parser.add_argument("--channel", required=False, help="Optional channel id passed to import_videos")

    def handle(self, *args, **options):
        channel = options.get("channel")
        self.stdout.write("1) Running import_videos ...")
        try:
            if channel:
                call_command("import_videos", channel=channel)
            else:
                call_command("import_videos")
        except Exception as exc:
            self.stdout.write(self.style.ERROR("Core data refresh aborted: import_videos failed."))
            raise CommandError(str(exc)) from exc

        self.stdout.write("2) Running sync_stats ...")
        call_command("sync_stats")
        self.stdout.write(self.style.SUCCESS("Core data refresh completed successfully."))
