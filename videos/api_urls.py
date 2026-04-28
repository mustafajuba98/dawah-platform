from django.urls import path

from videos import api_views

urlpatterns = [
    path("videos/", api_views.api_videos_list, name="api_videos_list"),
    path("search/", api_views.api_search, name="api_search"),
]
