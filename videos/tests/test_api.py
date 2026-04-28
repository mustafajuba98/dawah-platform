from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from videos.models import Video


class APITests(TestCase):
    def setUp(self):
        Video.objects.create(video_id="v1", title="Aqeedah Intro", description="desc", published_at=timezone.now())

    def test_api_videos_list(self):
        response = self.client.get(reverse("api_videos_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)

    def test_api_search_requires_query(self):
        response = self.client.get(reverse("api_search"))
        self.assertEqual(response.status_code, 400)

    def test_api_search(self):
        response = self.client.get(reverse("api_search"), {"q": "Aqeedah"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 1)
