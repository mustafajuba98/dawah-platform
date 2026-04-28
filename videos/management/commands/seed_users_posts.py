import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from videos.models import Post, PostComment, PostLike, UserProfile


class Command(BaseCommand):
    help = "Seed random active users, moderators, posts, comments, and likes."

    def handle(self, *args, **options):
        rng = random.Random(42)

        moderators = []
        for i in range(1, 3):
            username = f"moderator{i}"
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@example.com", "is_active": True},
            )
            user.set_password("Test12345mM")
            user.is_active = True
            user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={"role": UserProfile.ROLE_MODERATOR, "can_comment": True, "is_banned": False},
            )
            moderators.append(user)

        normal_users = []
        for i in range(1, 9):
            username = f"user{i}"
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@example.com", "is_active": True},
            )
            user.set_password("Test12345mM")
            user.is_active = True
            user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={"role": UserProfile.ROLE_USER, "can_comment": True, "is_banned": False},
            )
            normal_users.append(user)

        authors_pool = moderators + normal_users[:2]
        posts = []
        for i in range(1, 7):
            title = f"مقال تجريبي رقم {i}"
            slug = slugify(title) or f"post-{i}"
            if Post.objects.filter(slug=slug).exists():
                slug = f"{slug}-{i}"
            post, _ = Post.objects.get_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "content": f"هذا محتوى تجريبي للمقال {i}. الهدف اختبار التعليقات والإعجابات والإشراف.",
                    "author": rng.choice(authors_pool),
                    "is_published": True,
                },
            )
            posts.append(post)

        all_users = moderators + normal_users
        comments_created = 0
        for post in posts:
            for _ in range(5):
                author = rng.choice(all_users)
                status = PostComment.STATUS_APPROVED if author in moderators else PostComment.STATUS_PENDING
                PostComment.objects.create(
                    post=post,
                    author=author,
                    content=f"تعليق تجريبي من {author.username} على {post.title}",
                    status=status,
                    reviewed_by=rng.choice(moderators) if status == PostComment.STATUS_APPROVED else None,
                )
                comments_created += 1

            for liker in rng.sample(all_users, k=min(4, len(all_users))):
                PostLike.objects.get_or_create(post=post, user=liker)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed completed: moderators={len(moderators)}, users={len(normal_users)}, posts={len(posts)}, comments={comments_created}"
            )
        )
