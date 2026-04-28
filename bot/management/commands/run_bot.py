from django.core.management.base import BaseCommand

from bot.bot import build_application


class Command(BaseCommand):
    help = "Run Telegram bot polling process."

    def handle(self, *args, **options):
        app = build_application()
        self.stdout.write(self.style.SUCCESS("Telegram bot started."))
        app.run_polling()
