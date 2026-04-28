from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import models


class MosqueLesson(models.Model):
    WEEKDAY_CHOICES = (
        (0, "الاثنين"),
        (1, "الثلاثاء"),
        (2, "الأربعاء"),
        (3, "الخميس"),
        (4, "الجمعة"),
        (5, "السبت"),
        (6, "الأحد"),
    )

    mosque_name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    lesson_time = models.TimeField(null=True, blank=True)
    manual_time_text = models.CharField(max_length=120, blank=True)
    is_weekly = models.BooleanField(default=True)
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAY_CHOICES, null=True, blank=True)
    one_time_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_mosque_lessons"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("is_weekly", "weekday", "one_time_date", "lesson_time", "-created_at")
        indexes = [
            models.Index(fields=["is_weekly"]),
            models.Index(fields=["weekday"]),
            models.Index(fields=["one_time_date"]),
            models.Index(fields=["is_active"]),
        ]

    def clean(self):
        if not self.lesson_time and not self.manual_time_text.strip():
            raise ValidationError("يجب إدخال وقت الدرس كساعة أو كنص يدوي أو الاثنين.")
        if self.is_weekly and self.weekday is None:
            raise ValidationError("الدرس الأسبوعي يحتاج تحديد يوم الأسبوع.")
        if not self.is_weekly and not self.one_time_date:
            raise ValidationError("الدرس الفردي يحتاج تحديد التاريخ.")

    def __str__(self) -> str:
        return f"{self.mosque_name} - {self.title}"


class TodoItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="todo_items")
    title = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    is_done = models.BooleanField(default=False)
    due_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("is_done", "due_at", "-created_at")
        indexes = [
            models.Index(fields=["user", "is_done"]),
            models.Index(fields=["due_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.title}"


class Video(models.Model):
    CATEGORY_AQEEDAH = "aqeedah"
    CATEGORY_FIQH = "fiqh"
    CATEGORY_QURAN = "quran"
    CATEGORY_SEERAH = "seerah"
    CATEGORY_HADITH = "hadith"
    CATEGORY_AKHLAQ = "akhlaq"
    CATEGORY_DAWAH = "dawah"
    CATEGORY_FATAWA = "fatawa"
    CATEGORY_RAMADAN = "ramadan"
    CATEGORY_OTHER = "other"

    CATEGORY_CHOICES = (
        (CATEGORY_AQEEDAH, "عقيدة - Islamic Creed"),
        (CATEGORY_FIQH, "فقه - Islamic Jurisprudence"),
        (CATEGORY_QURAN, "قرآن وتفسير - Quran & Tafsir"),
        (CATEGORY_SEERAH, "سيرة نبوية - Prophetic Biography"),
        (CATEGORY_HADITH, "حديث - Hadith Sciences"),
        (CATEGORY_AKHLAQ, "أخلاق وتزكية - Ethics & Purification"),
        (CATEGORY_DAWAH, "دعوة - Da'wah & Outreach"),
        (CATEGORY_FATAWA, "فتاوى - Islamic Rulings"),
        (CATEGORY_RAMADAN, "رمضان - Ramadan Special"),
        (CATEGORY_OTHER, "أخرى - Other"),
    )

    DIFFICULTY_BEGINNER = "beginner"
    DIFFICULTY_INTERMEDIATE = "intermediate"
    DIFFICULTY_ADVANCED = "advanced"
    DIFFICULTY_GENERAL = "general"
    DIFFICULTY_CHOICES = (
        (DIFFICULTY_BEGINNER, "مبتدئ - Beginner"),
        (DIFFICULTY_INTERMEDIATE, "متوسط - Intermediate"),
        (DIFFICULTY_ADVANCED, "متقدم - Advanced"),
        (DIFFICULTY_GENERAL, "عام - General Audience"),
    )

    video_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    thumbnail_url = models.URLField(max_length=500, blank=True)
    published_at = models.DateTimeField()
    duration_seconds = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    view_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    like_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default=CATEGORY_OTHER)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default=DIFFICULTY_GENERAL)
    ai_summary = models.TextField(blank=True)
    seo_description = models.TextField(blank=True)
    tags = models.CharField(max_length=300, blank=True)
    youtube_category_id = models.CharField(max_length=20, blank=True)
    youtube_category_title = models.CharField(max_length=120, blank=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-published_at",)
        indexes = [
            models.Index(fields=["video_id"]),
            models.Index(fields=["category"]),
            models.Index(fields=["difficulty"]),
            models.Index(fields=["published_at"]),
            models.Index(fields=["is_featured"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["youtube_category_id"]),
        ]

    def __str__(self) -> str:
        return self.title


class Playlist(models.Model):
    playlist_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    thumbnail_url = models.URLField(max_length=500, blank=True)
    video_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("title",)

    def __str__(self) -> str:
        return self.title


class VideoPlaylist(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="playlist_links")
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name="video_links")
    position = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    class Meta:
        unique_together = (("video", "playlist"),)
        ordering = ("playlist", "position")

    def __str__(self) -> str:
        return f"{self.playlist.title} - {self.video.title}"


class SyncLog(models.Model):
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_PARTIAL = "partial"
    STATUS_CHOICES = (
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
        (STATUS_PARTIAL, "Partial"),
    )

    synced_at = models.DateTimeField(auto_now_add=True)
    videos_imported = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    videos_updated = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    api_units_used = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUCCESS)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ("-synced_at",)

    def __str__(self) -> str:
        return f"{self.synced_at:%Y-%m-%d %H:%M} - {self.status}"


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("user", "video"),)
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["video"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} -> {self.video.video_id}"


class EmailVerificationPending(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="email_pending")
    token = models.CharField(max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [models.Index(fields=["expires_at"])]

    def __str__(self) -> str:
        return f"pending:{self.user_id}"


class UserProfile(models.Model):
    ROLE_USER = "user"
    ROLE_MODERATOR = "moderator"
    ROLE_ADMIN = "admin"
    ROLE_CHOICES = (
        (ROLE_USER, "مستخدم"),
        (ROLE_MODERATOR, "مشرف"),
        (ROLE_ADMIN, "أدمن"),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_USER)
    can_comment = models.BooleanField(default=True)
    is_banned = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.username} ({self.role})"


class Post(models.Model):
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=300, unique=True)
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.title


class PostComment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    )

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="post_comments")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies")
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_comments"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self) -> str:
        return f"{self.author} on {self.post}"


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="post_likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("post", "user"),)


class SpiritPin(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="spirit_pins")
    card_hash = models.CharField(max_length=64)
    kind = models.CharField(max_length=30)
    title = models.CharField(max_length=255)
    line_text = models.TextField()
    source = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("user", "card_hash"),)
        ordering = ("-created_at",)
