from django.contrib import admin

from videos.models import (
    EmailVerificationPending,
    Favorite,
    Playlist,
    Post,
    PostComment,
    PostLike,
    SyncLog,
    UserProfile,
    Video,
    VideoPlaylist,
)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "video_id",
        "category",
        "youtube_category_title",
        "difficulty",
        "view_count",
        "is_featured",
        "is_active",
        "published_at",
    )
    list_filter = ("category", "difficulty", "is_featured", "is_active", "published_at")
    search_fields = ("title", "description", "video_id", "tags")
    ordering = ("-published_at",)


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ("title", "playlist_id", "video_count", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title", "playlist_id", "description")


@admin.register(VideoPlaylist)
class VideoPlaylistAdmin(admin.ModelAdmin):
    list_display = ("playlist", "video", "position")
    search_fields = ("playlist__title", "video__title", "video__video_id")
    list_select_related = ("playlist", "video")


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ("synced_at", "status", "videos_imported", "videos_updated", "api_units_used")
    list_filter = ("status", "synced_at")
    readonly_fields = ("synced_at",)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "video", "created_at")
    search_fields = ("user__username", "user__email", "video__title", "video__video_id")
    list_filter = ("created_at",)


@admin.register(EmailVerificationPending)
class EmailVerificationPendingAdmin(admin.ModelAdmin):
    list_display = ("user", "expires_at", "created_at")
    search_fields = ("user__username", "user__email")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "can_comment", "is_banned", "updated_at")
    list_filter = ("role", "can_comment", "is_banned")
    search_fields = ("user__username", "user__email")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "is_published", "created_at")
    list_filter = ("is_published", "created_at")
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ("post", "author", "status", "reviewed_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("post__title", "author__username", "content")


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "created_at")
    search_fields = ("post__title", "user__username")
