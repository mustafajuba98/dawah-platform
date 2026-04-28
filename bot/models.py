from django.db import models

from videos.models import Video


class TelegramSubscriber(models.Model):
    chat_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=150, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    preferred_category = models.CharField(max_length=50, blank=True, choices=Video.CATEGORY_CHOICES)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-joined_at",)
        indexes = [
            models.Index(fields=["chat_id"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["preferred_category"]),
        ]

    def __str__(self) -> str:
        return self.username or str(self.chat_id)


class BotNotification(models.Model):
    STATUS_SUCCESS = "success"
    STATUS_PARTIAL = "partial"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = (
        (STATUS_SUCCESS, "Success"),
        (STATUS_PARTIAL, "Partial"),
        (STATUS_FAILED, "Failed"),
    )

    title = models.CharField(max_length=400)
    message = models.TextField(blank=True)
    youtube_url = models.URLField(max_length=500, blank=True)
    sent_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUCCESS)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-sent_at",)

    def __str__(self) -> str:
        return f"{self.sent_at:%Y-%m-%d %H:%M} - {self.title}"
