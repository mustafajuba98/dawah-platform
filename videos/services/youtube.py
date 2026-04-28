from __future__ import annotations

import isodate
import logging
import os
import time
from typing import Any

from django.utils import timezone
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from videos.models import Playlist, SyncLog, Video, VideoPlaylist

logger = logging.getLogger(__name__)


class YouTubeService:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY", "")
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY is missing.")
        self.client = build("youtube", "v3", developerKey=self.api_key)

    def _execute_with_retry(self, request: Any, retries: int = 3) -> dict[str, Any]:
        for attempt in range(1, retries + 1):
            try:
                return request.execute()
            except HttpError as exc:
                if attempt == retries:
                    raise
                logger.warning("YouTube API transient error: %s", exc)
                time.sleep(attempt * 2)
        return {}

    def get_channel_uploads_playlist_id(self, channel_id: str) -> str:
        response = self._execute_with_retry(
            self.client.channels().list(part="contentDetails", id=channel_id, maxResults=1)
        )
        items = response.get("items", [])
        if not items:
            raise ValueError("Channel not found or has no content details.")
        return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

    def get_all_videos(self, playlist_id: str) -> list[dict[str, Any]]:
        videos: list[dict[str, Any]] = []
        next_page_token = None
        while True:
            response = self._execute_with_retry(
                self.client.playlistItems().list(
                    part="snippet,contentDetails",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token,
                )
            )
            videos.extend(response.get("items", []))
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
        return videos

    def get_playlist_video_ids(self, playlist_id: str) -> list[str]:
        items = self.get_all_videos(playlist_id)
        return [item.get("contentDetails", {}).get("videoId", "") for item in items if item.get("contentDetails")]

    def get_video_details(self, video_ids: list[str]) -> list[dict[str, Any]]:
        details: list[dict[str, Any]] = []
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i : i + 50]
            if not batch:
                continue
            response = self._execute_with_retry(
                self.client.videos().list(part="contentDetails,statistics,snippet", id=",".join(batch))
            )
            details.extend(response.get("items", []))
        return details

    def get_playlists(self, channel_id: str) -> list[dict[str, Any]]:
        playlists: list[dict[str, Any]] = []
        next_page_token = None
        while True:
            response = self._execute_with_retry(
                self.client.playlists().list(
                    part="snippet,contentDetails",
                    channelId=channel_id,
                    maxResults=50,
                    pageToken=next_page_token,
                )
            )
            playlists.extend(response.get("items", []))
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
        return playlists

    def search_channel_videos(self, channel_id: str, query: str, max_results: int = 25) -> list[dict[str, Any]]:
        response = self._execute_with_retry(
            self.client.search().list(
                part="snippet",
                channelId=channel_id,
                q=query,
                maxResults=min(max_results, 50),
                type="video",
                order="relevance",
            )
        )
        return response.get("items", [])

    def get_video_categories(self, region_code: str = "EG") -> dict[str, str]:
        response = self._execute_with_retry(
            self.client.videoCategories().list(part="snippet", regionCode=region_code)
        )
        categories = {}
        for item in response.get("items", []):
            categories[item.get("id", "")] = item.get("snippet", {}).get("title", "")
        return categories

    @staticmethod
    def _parse_duration(duration: str) -> int:
        try:
            return int(isodate.parse_duration(duration).total_seconds())
        except Exception:
            return 0

    def sync_channel(self, channel_id: str) -> SyncLog:
        imported = 0
        updated = 0
        api_units = 0
        status = SyncLog.STATUS_SUCCESS
        error_message = ""

        try:
            category_map = self.get_video_categories("EG")
            uploads_id = self.get_channel_uploads_playlist_id(channel_id)
            api_units += 1
            playlist_items = self.get_all_videos(uploads_id)
            api_units += (len(playlist_items) // 50) + 1

            video_ids = [item["contentDetails"]["videoId"] for item in playlist_items if item.get("contentDetails")]
            details = self.get_video_details(video_ids)
            api_units += (len(video_ids) // 50) + 1 if video_ids else 0

            details_by_id = {item["id"]: item for item in details if item.get("id")}

            for item in playlist_items:
                snippet = item.get("snippet", {})
                vid = item.get("contentDetails", {}).get("videoId")
                if not vid:
                    continue
                detail = details_by_id.get(vid, {})
                stat = detail.get("statistics", {})
                content = detail.get("contentDetails", {})

                defaults = {
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "thumbnail_url": (snippet.get("thumbnails", {}).get("high", {}) or {}).get("url", ""),
                    "published_at": snippet.get("publishedAt", timezone.now()),
                    "duration_seconds": self._parse_duration(content.get("duration", "PT0S")),
                    "view_count": int(stat.get("viewCount", 0)),
                    "like_count": int(stat.get("likeCount", 0)),
                    "youtube_category_id": detail.get("snippet", {}).get("categoryId", ""),
                    "youtube_category_title": category_map.get(detail.get("snippet", {}).get("categoryId", ""), ""),
                    "is_active": True,
                }
                obj, created = Video.objects.update_or_create(video_id=vid, defaults=defaults)
                if created:
                    imported += 1
                else:
                    updated += 1

            channel_playlists = self.get_playlists(channel_id)
            for playlist in channel_playlists:
                snippet = playlist.get("snippet", {})
                playlist_obj, _ = Playlist.objects.update_or_create(
                    playlist_id=playlist.get("id", ""),
                    defaults={
                        "title": snippet.get("title", ""),
                        "description": snippet.get("description", ""),
                        "thumbnail_url": (snippet.get("thumbnails", {}).get("high", {}) or {}).get("url", ""),
                        "video_count": int(playlist.get("contentDetails", {}).get("itemCount", 0)),
                        "is_active": True,
                    },
                )
                api_units += 1

                linked_ids = self.get_playlist_video_ids(playlist_obj.playlist_id)
                existing = {v.video_id: v for v in Video.objects.filter(video_id__in=linked_ids)}
                for pos, vid in enumerate(linked_ids, start=1):
                    video_obj = existing.get(vid)
                    if not video_obj:
                        continue
                    VideoPlaylist.objects.update_or_create(
                        video=video_obj,
                        playlist=playlist_obj,
                        defaults={"position": pos},
                    )
        except Exception as exc:
            logger.exception("Failed to sync channel.")
            status = SyncLog.STATUS_FAILED
            error_message = str(exc)

        return SyncLog.objects.create(
            videos_imported=imported,
            videos_updated=updated,
            api_units_used=api_units,
            status=status,
            error_message=error_message,
        )
