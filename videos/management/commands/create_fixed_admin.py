from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from videos.models import UserProfile


class Command(BaseCommand):
    help = "Create one-time fixed super admin from constants in this file."

    # Edit these values whenever you need a different owner account.
    ADMIN_USERNAME = "mustafa"
    ADMIN_EMAIL = "justjoba3@gmail.com"
    ADMIN_PASSWORD = "123123mM"

    def handle(self, *args, **options):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.WARNING("Superuser already exists. This command is one-time only."))
            return

        user = User.objects.create_user(
            username=self.ADMIN_USERNAME,
            email=self.ADMIN_EMAIL,
            password=self.ADMIN_PASSWORD,
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )
        UserProfile.objects.update_or_create(
            user=user,
            defaults={"role": UserProfile.ROLE_ADMIN, "can_comment": True, "is_banned": False},
        )
        self.stdout.write(self.style.SUCCESS(f"Fixed admin created: {self.ADMIN_USERNAME}"))
