from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from videos.models import UserProfile


class Command(BaseCommand):
    help = "Create or update platform owner admin with provided credentials."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--email", required=True)
        parser.add_argument("--password", required=True)

    def handle(self, *args, **options):
        username = options["username"].strip()
        email = options["email"].strip().lower()
        password = options["password"]
        if not username or not email or not password:
            raise CommandError("username/email/password are required.")

        user, _ = User.objects.get_or_create(username=username, defaults={"email": email})
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
        self.stdout.write(self.style.SUCCESS(f"Owner admin ready: {username}"))
