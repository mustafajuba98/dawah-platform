from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse

from videos.models import Video


def _serialize_video(video: Video) -> dict:
    return {
        "video_id": video.video_id,
        "title": video.title,
        "description": video.description,
        "thumbnail_url": video.thumbnail_url,
        "published_at": video.published_at.isoformat(),
        "duration_seconds": video.duration_seconds,
        "view_count": video.view_count,
        "like_count": video.like_count,
        "category": video.category,
        "difficulty": video.difficulty,
        "seo_description": video.seo_description,
        "tags": video.tags,
    }


def api_videos_list(request):
    page_num = request.GET.get("page", "1")
    queryset = Video.objects.filter(is_active=True).order_by("-published_at")
    paginator = Paginator(queryset, 12)
    page = paginator.get_page(page_num)
    return JsonResponse(
        {
            "count": paginator.count,
            "num_pages": paginator.num_pages,
            "page": page.number,
            "results": [_serialize_video(video) for video in page.object_list],
        }
    )


def api_search(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"error": "q query parameter is required."}, status=400)

    queryset = Video.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query), is_active=True
    ).order_by("-published_at")[:20]
    return JsonResponse({"query": query, "results": [_serialize_video(video) for video in queryset]})
