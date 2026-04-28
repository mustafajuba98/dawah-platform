from django.urls import path

from videos import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("verify-email/", views.verify_email, name="verify_email"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("favorites/", views.my_favorites, name="my_favorites"),
    path("spirit/toggle-pin/", views.toggle_spirit_pin, name="toggle_spirit_pin"),
    path("video/<str:video_id>/favorite/", views.toggle_favorite, name="toggle_favorite"),
    path("search/", views.search, name="search"),
    path("category/<slug:slug>/", views.category_list, name="category_list"),
    path("video/<str:video_id>/", views.video_detail, name="video_detail"),
    path("playlist/<str:playlist_id>/", views.playlist_detail, name="playlist_detail"),
    path("posts/", views.posts_list, name="posts_list"),
    path("notifications/bot/", views.bot_notifications, name="bot_notifications"),
    path("posts/create/", views.create_post, name="create_post"),
    path("posts/<slug:slug>/", views.post_detail, name="post_detail"),
    path("posts/<slug:slug>/comment/", views.add_post_comment, name="add_post_comment"),
    path("posts/<slug:slug>/like/", views.post_like_toggle, name="post_like_toggle"),
    path("moderation/comments/pending/", views.pending_comments, name="pending_comments"),
    path("comments/<int:comment_id>/<str:action>/", views.moderate_comment, name="moderate_comment"),
    path("moderation/users/", views.users_moderation, name="users_moderation"),
]
