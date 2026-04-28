import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from videos.models import UserProfile


class Command(BaseCommand):
    help = "Create or update the channel owner admin user."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=False)
        parser.add_argument("--email", required=True)
        parser.add_argument("--password", required=True)

    def handle(self, *args, **options):
        username = options.get("username") or os.getenv("CHANNEL_ADMIN_USERNAME") or "channel_owner"
        email = options["email"].strip().lower()
        password = options["password"]
        if not email or not password:
            raise CommandError("Email and password are required.")

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()
        UserProfile.objects.update_or_create(
            user=user,
            defaults={"role": UserProfile.ROLE_ADMIN, "can_comment": True, "is_banned": False},
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Admin user created: {username}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Admin user updated: {username}"))
