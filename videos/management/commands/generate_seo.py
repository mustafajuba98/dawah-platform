from django.core.management.base import BaseCommand

from videos.models import Video
from videos.services.ai_generator import AIDescriptionGenerator


class Command(BaseCommand):
    help = "Generate SEO descriptions and summaries using Gemini."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50, help="Maximum videos to process")

    def handle(self, *args, **options):
        generator = AIDescriptionGenerator(requests_per_minute=10)
        if not generator.enabled:
            self.stdout.write(self.style.WARNING("GEMINI_API_KEY missing, skipped generation."))
            return

        limit = options["limit"]
        queryset = Video.objects.filter(seo_description="").order_by("-published_at")[:limit]
        processed = generator.bulk_generate(queryset)
        self.stdout.write(self.style.SUCCESS(f"Generated AI content for {processed} videos."))
