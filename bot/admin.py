from django.contrib import admin

from bot.models import BotNotification, TelegramSubscriber


@admin.register(TelegramSubscriber)
class TelegramSubscriberAdmin(admin.ModelAdmin):
    list_display = ("chat_id", "username", "first_name", "preferred_category", "is_active", "joined_at")
    list_filter = ("is_active", "preferred_category", "joined_at")
    search_fields = ("chat_id", "username", "first_name")


@admin.register(BotNotification)
class BotNotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "sent_count", "status", "sent_at")
    list_filter = ("status", "sent_at")
    search_fields = ("title", "message", "youtube_url")
