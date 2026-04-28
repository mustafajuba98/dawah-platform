from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.core import signing
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.html import escape
from django.utils.text import slugify

from videos.forms import MosqueLessonForm, RegistrationForm, TodoItemForm
from videos.models import (
    EmailVerificationPending,
    Favorite,
    MosqueLesson,
    Playlist,
    Post,
    PostComment,
    PostLike,
    SpiritPin,
    TodoItem,
    UserProfile,
    Video,
    VideoPlaylist,
)
from videos.services.email_delivery import send_registration_verification_email
from videos.services.prayer import fetch_prayer_timings_cached
from videos.services.spiritual import build_spirit_cards
from bot.models import BotNotification


def _ordered_lessons(queryset):
    lessons = list(queryset)

    def lesson_sort_key(lesson):
        weekly_bucket = 0 if lesson.is_weekly else 1
        weekday = lesson.weekday if lesson.weekday is not None else 99
        one_time_date = lesson.one_time_date.isoformat() if lesson.one_time_date else "9999-99-99"
        time_val = lesson.lesson_time.isoformat() if lesson.lesson_time else "99:99:99"
        return (weekly_bucket, weekday, one_time_date, time_val, lesson.mosque_name.lower())

    lessons.sort(key=lesson_sort_key)
    return lessons


def home(request):
    featured_ids = cache.get("home_featured_ids")
    if featured_ids is None:
        featured_ids = list(
            Video.objects.filter(is_active=True, is_featured=True).order_by("-published_at").values_list("id", flat=True)[:12]
        )
        cache.set("home_featured_ids", featured_ids, 300)
    featured_map = {v.id: v for v in Video.objects.filter(id__in=featured_ids)}
    featured_videos = [featured_map[i] for i in featured_ids if i in featured_map]
    if not featured_videos:
        featured_videos = list(Video.objects.filter(is_active=True).order_by("-view_count", "-published_at")[:8])

    recent_ids = cache.get("home_recent_ids")
    if recent_ids is None:
        recent_ids = list(Video.objects.filter(is_active=True).order_by("-published_at").values_list("id", flat=True)[:12])
        cache.set("home_recent_ids", recent_ids, 300)
    recent_map = {v.id: v for v in Video.objects.filter(id__in=recent_ids)}
    recent_videos = [recent_map[i] for i in recent_ids if i in recent_map]
    categories = Video.CATEGORY_CHOICES
    spirit_cards = build_spirit_cards(target=6)
    prayer = fetch_prayer_timings_cached()
    return render(
        request,
        "videos/home.html",
        {
            "featured_videos": featured_videos,
            "recent_videos": recent_videos,
            "categories": categories,
            "spirit_cards": spirit_cards,
            "prayer": prayer,
            "prayer_place": "القاهرة، مصر",
            "telegram_channel_url": "https://t.me/omar_elarby",
            "telegram_bot_url": "http://t.me/Omar_ebnel_araby_bot",
            "whatsapp_group_url": "https://chat.whatsapp.com/Ift7nI5qurWE0sX1rgfs0n?mode=ems_copy_t",
            "landing_notifications": BotNotification.objects.all()[:3],
            "lesson_announcements": _ordered_lessons(MosqueLesson.objects.filter(is_active=True)[:8]),
            "weekday_choices": MosqueLesson.WEEKDAY_CHOICES,
        },
    )


def bot_notifications(request):
    notifications = BotNotification.objects.all().order_by("-sent_at")
    page_obj = Paginator(notifications, 20).get_page(request.GET.get("page"))
    return render(request, "videos/bot_notifications.html", {"page_obj": page_obj})


def mosque_lessons(request):
    lessons_qs = MosqueLesson.objects.select_related("created_by").all()
    can_moderate = _can_moderate(request.user)
    editing_lesson = None

    if request.method == "POST":
        if not can_moderate:
            return HttpResponseForbidden("Forbidden")

        action = request.POST.get("action", "save")
        lesson_id = request.POST.get("lesson_id", "").strip()

        if action == "delete" and lesson_id:
            lesson = get_object_or_404(MosqueLesson, id=lesson_id)
            lesson.delete()
            messages.success(request, "تم حذف تنبيه الدرس.")
            return redirect("mosque_lessons")

        instance = MosqueLesson.objects.filter(id=lesson_id).first() if lesson_id else None
        form = MosqueLessonForm(request.POST, instance=instance)
        if form.is_valid():
            lesson = form.save(commit=False)
            if lesson.created_by_id is None:
                lesson.created_by = request.user
            lesson.save()
            messages.success(request, "تم حفظ تنبيه الدرس بنجاح.")
            return redirect("mosque_lessons")
        editing_lesson = instance
    else:
        edit_id = request.GET.get("edit", "").strip()
        if can_moderate and edit_id:
            editing_lesson = MosqueLesson.objects.filter(id=edit_id).first()
        form = MosqueLessonForm(instance=editing_lesson) if can_moderate else None

    return render(
        request,
        "videos/mosque_lessons.html",
        {
            "lessons": _ordered_lessons(lessons_qs),
            "can_manage_lessons": can_moderate,
            "form": form,
            "editing_lesson": editing_lesson,
            "weekday_choices": MosqueLesson.WEEKDAY_CHOICES,
        },
    )


@login_required
def my_todos(request):
    form = TodoItemForm()
    if request.method == "POST":
        action = request.POST.get("action", "add")
        todo_id = request.POST.get("todo_id", "").strip()

        if action == "add":
            form = TodoItemForm(request.POST)
            if form.is_valid():
                todo = form.save(commit=False)
                todo.user = request.user
                todo.save()
                messages.success(request, "تمت إضافة المهمة.")
                return redirect("my_todos")
        elif action == "toggle" and todo_id:
            todo = get_object_or_404(TodoItem, id=todo_id, user=request.user)
            todo.is_done = not todo.is_done
            todo.save(update_fields=["is_done", "updated_at"])
            messages.success(request, "تم تحديث حالة المهمة.")
            return redirect("my_todos")
        elif action == "delete" and todo_id:
            todo = get_object_or_404(TodoItem, id=todo_id, user=request.user)
            todo.delete()
            messages.success(request, "تم حذف المهمة.")
            return redirect("my_todos")
    else:
        form = TodoItemForm()

    todos = TodoItem.objects.filter(user=request.user).order_by("is_done", "due_at", "-created_at")
    return render(request, "videos/my_todos.html", {"form": form, "todos": todos})


def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_active = False
            user.save(update_fields=["is_active"])
            UserProfile.objects.update_or_create(user=user, defaults={"role": UserProfile.ROLE_USER})

            signer = signing.TimestampSigner(salt="register-email")
            token = signer.sign(str(user.pk))
            expires_at = timezone.now() + timedelta(hours=24)
            EmailVerificationPending.objects.update_or_create(
                user=user,
                defaults={"token": token, "expires_at": expires_at},
            )
            verify_url = f"{request.scheme}://{request.get_host()}/verify-email/?token={token}"
            site_name = getattr(settings, "SITE_NAME", "نور الدعوة")
            html_body = (
                "<html><body dir='rtl'>"
                f"<p>مرحبًا بك في {escape(site_name)}.</p>"
                "<p>اضغط الرابط التالي لتأكيد بريدك الإلكتروني:</p>"
                f"<p><a href='{escape(verify_url)}'>{escape(verify_url)}</a></p>"
                "</body></html>"
            )
            text_body = f"رابط تأكيد الحساب: {verify_url}"
            send_registration_verification_email(
                to_email=user.email,
                subject=f"{site_name} - تأكيد البريد الإلكتروني",
                html_body=html_body,
                text_body=text_body,
            )
            messages.success(request, "تم إنشاء الحساب. تم إرسال رابط التأكيد إلى بريدك الإلكتروني.")
            return redirect("login")
    else:
        form = RegistrationForm()
    return render(request, "videos/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "بيانات الدخول غير صحيحة.")
        elif not user.is_active:
            messages.error(request, "هذا الحساب موقوف أو غير مفعل.")
        else:
            login(request, user)
            return redirect("home")
    return render(request, "videos/login.html")


def verify_email(request):
    token = request.GET.get("token", "")
    if not token:
        messages.error(request, "رابط التأكيد غير صالح.")
        return redirect("login")

    try:
        signer = signing.TimestampSigner(salt="register-email")
        unsigned = signer.unsign(token, max_age=60 * 60 * 24)
        user = User.objects.get(pk=int(unsigned))
    except Exception:
        messages.error(request, "رابط التأكيد غير صالح أو منتهي الصلاحية.")
        return redirect("login")

    pending = EmailVerificationPending.objects.filter(user=user, token=token).first()
    if not pending or pending.expires_at < timezone.now():
        messages.error(request, "طلب التفعيل غير موجود أو منتهي.")
        return redirect("login")

    user.is_active = True
    user.save(update_fields=["is_active"])
    pending.delete()
    messages.success(request, "تم تأكيد البريد الإلكتروني بنجاح. يمكنك تسجيل الدخول الآن.")
    return redirect("login")


def logout_view(request):
    logout(request)
    return redirect("home")


def search(request):
    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "newest")
    playlist_id = request.GET.get("playlist", "").strip()
    content_type = request.GET.get("content_type", "").strip()

    queryset = Video.objects.filter(is_active=True)
    if query:
        queryset = queryset.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if playlist_id:
        queryset = queryset.filter(playlist_links__playlist__playlist_id=playlist_id)
    if content_type == "shorts":
        queryset = queryset.filter(duration_seconds__lte=180)
    elif content_type == "podcasts":
        queryset = queryset.filter(
            Q(title__icontains="podcast")
            | Q(title__icontains="بودكاست")
            | Q(description__icontains="podcast")
            | Q(description__icontains="بودكاست")
            | Q(playlist_links__playlist__title__icontains="podcast")
            | Q(playlist_links__playlist__title__icontains="بودكاست")
        )
    elif content_type == "videos":
        queryset = queryset.filter(duration_seconds__gt=180)

    selected_newest = sort == "newest"
    selected_most_viewed = sort == "most_viewed"
    selected_shorts = content_type == "shorts"
    if selected_most_viewed:
        queryset = queryset.order_by("-view_count", "-published_at")
    else:
        queryset = queryset.order_by("-published_at")
    queryset = queryset.distinct()

    page_num = int(request.GET.get("page", "1") or "1")
    cache_key = f"search:{query}:{playlist_id}:{content_type}:{sort}:p{page_num}"
    cached_page_ids = cache.get(cache_key)
    if cached_page_ids is None:
        paginator = Paginator(queryset, 24)
        page_obj = paginator.get_page(page_num)
        cached_page_ids = list(page_obj.object_list.values_list("id", flat=True))
        cache.set(cache_key, cached_page_ids, 300)
    else:
        paginator = Paginator(queryset, 24)
        page_obj = paginator.get_page(page_num)
        page_obj.object_list = Video.objects.filter(id__in=cached_page_ids)

    playlists = (
        Playlist.objects.filter(is_active=True, video_links__video__is_active=True)
        .distinct()
        .order_by("title")
        .values_list("playlist_id", "title")
    )
    content_type_choices = [
        ("videos", "فيديوهات طويلة"),
        ("shorts", "Shorts"),
        ("podcasts", "Podcasts"),
    ]
    return render(
        request,
        "videos/search.html",
        {
            "page_obj": page_obj,
            "query": query,
            "selected_sort": sort,
            "selected_newest": selected_newest,
            "selected_most_viewed": selected_most_viewed,
            "selected_shorts": selected_shorts,
            "selected_playlist": playlist_id,
            "selected_content_type": content_type,
            "playlists": playlists,
            "content_type_choices": content_type_choices,
        },
    )


def category_list(request, slug):
    videos = Video.objects.filter(is_active=True, category=slug).order_by("-published_at")
    page_obj = Paginator(videos, 12).get_page(request.GET.get("page"))
    category_name = dict(Video.CATEGORY_CHOICES).get(slug, slug)
    return render(
        request,
        "videos/category.html",
        {"page_obj": page_obj, "category_slug": slug, "category_name": category_name},
    )


def video_detail(request, video_id):
    video = get_object_or_404(Video, video_id=video_id, is_active=True)
    playlist_id = request.GET.get("playlist", "").strip()
    active_playlist = None
    playlist_navigation = {}
    if playlist_id:
        active_playlist = Playlist.objects.filter(playlist_id=playlist_id, is_active=True).first()
        if active_playlist:
            links = list(
                VideoPlaylist.objects.select_related("video")
                .filter(playlist=active_playlist, video__is_active=True)
                .order_by("position")
            )
            ids = [link.video.video_id for link in links]
            if video.video_id in ids:
                idx = ids.index(video.video_id)
                playlist_navigation = {
                    "youtube_playlist_url": f"https://www.youtube.com/watch?v={video.video_id}&list={active_playlist.playlist_id}",
                    "playlist_url": f"/playlist/{active_playlist.playlist_id}/",
                    "playlist_title": active_playlist.title,
                    "prev_video_id": ids[idx - 1] if idx > 0 else "",
                    "next_video_id": ids[idx + 1] if idx < len(ids) - 1 else "",
                    "playlist_id": active_playlist.playlist_id,
                }
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, video=video).exists()
    related = Video.objects.filter(
        is_active=True,
        category=video.category,
    ).exclude(pk=video.pk)[:6]
    return render(
        request,
        "videos/detail.html",
        {
            "video": video,
            "related_videos": related,
            "is_favorite": is_favorite,
            "playlist_navigation": playlist_navigation,
            "active_playlist": active_playlist,
        },
    )


def playlist_detail(request, playlist_id):
    playlist = get_object_or_404(Playlist, playlist_id=playlist_id, is_active=True)
    links = VideoPlaylist.objects.select_related("video").filter(playlist=playlist).order_by("position")
    videos = [link.video for link in links if link.video.is_active]
    return render(request, "videos/playlist.html", {"playlist": playlist, "videos": videos})


def _get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={"role": UserProfile.ROLE_USER})
    return profile


def _can_moderate(user):
    if not user.is_authenticated:
        return False
    profile = _get_or_create_profile(user)
    return user.is_superuser or profile.role in (UserProfile.ROLE_ADMIN, UserProfile.ROLE_MODERATOR)


def _is_admin(user):
    if not user.is_authenticated:
        return False
    profile = _get_or_create_profile(user)
    return user.is_superuser or profile.role == UserProfile.ROLE_ADMIN


def posts_list(request):
    query = request.GET.get("q", "").strip()
    author = request.GET.get("author", "").strip()
    posts_qs = Post.objects.filter(is_published=True).select_related("author").order_by("-created_at")
    if query:
        posts_qs = posts_qs.filter(Q(title__icontains=query) | Q(content__icontains=query))
    if author:
        posts_qs = posts_qs.filter(author__username__icontains=author)
    page_obj = Paginator(posts_qs, 6).get_page(request.GET.get("page"))
    context = {
        "posts": page_obj,
        "can_publish": _is_admin(request.user),
        "page_obj": page_obj,
        "query": query,
        "author_filter": author,
    }
    if request.GET.get("partial") == "1":
        return render(request, "videos/_posts_rows.html", context)
    return render(request, "videos/posts_list.html", context)


def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, is_published=True)
    replies_prefetch = Prefetch(
        "replies",
        queryset=PostComment.objects.filter(status=PostComment.STATUS_APPROVED).select_related("author").order_by("created_at"),
    )
    comments_qs = (
        post.comments.filter(status=PostComment.STATUS_APPROVED, parent__isnull=True)
        .select_related("author")
        .prefetch_related(replies_prefetch)
        .order_by("-created_at")
    )
    comments_page = Paginator(comments_qs, 10).get_page(request.GET.get("cpage"))
    can_comment = request.user.is_authenticated and _get_or_create_profile(request.user).can_comment
    is_liked = request.user.is_authenticated and PostLike.objects.filter(post=post, user=request.user).exists()
    return render(
        request,
        "videos/post_detail.html",
        {
            "post": post,
            "comments": comments_page,
            "can_comment": can_comment,
            "can_moderate": _can_moderate(request.user),
            "comments_page": comments_page,
            "is_liked": is_liked,
        },
    )


@login_required
def post_like_toggle(request, slug):
    post = get_object_or_404(Post, slug=slug, is_published=True)
    like, created = PostLike.objects.get_or_create(post=post, user=request.user)
    if not created:
        like.delete()
    return redirect("post_detail", slug=slug)


@login_required
def add_post_comment(request, slug):
    if request.method != "POST":
        return redirect("post_detail", slug=slug)
    post = get_object_or_404(Post, slug=slug, is_published=True)
    profile = _get_or_create_profile(request.user)
    if not profile.can_comment and not _can_moderate(request.user):
        messages.error(request, "تم تقييد حسابك من التعليق.")
        return redirect("post_detail", slug=slug)
    content = request.POST.get("content", "").strip()
    parent_id = request.POST.get("parent_id", "").strip()
    if not content:
        messages.error(request, "لا يمكن إضافة تعليق فارغ.")
        return redirect("post_detail", slug=slug)
    parent = None
    if parent_id:
        parent = post.comments.filter(id=parent_id).first()
    status = PostComment.STATUS_APPROVED if _can_moderate(request.user) else PostComment.STATUS_PENDING
    PostComment.objects.create(post=post, author=request.user, parent=parent, content=content, status=status)
    messages.success(request, "تم إرسال التعليق للمراجعة." if status == PostComment.STATUS_PENDING else "تم نشر التعليق.")
    return redirect("post_detail", slug=slug)


@login_required
def moderate_comment(request, comment_id, action):
    if not _can_moderate(request.user):
        return HttpResponseForbidden("Forbidden")
    comment = get_object_or_404(PostComment, id=comment_id)
    if action == "approve":
        comment.status = PostComment.STATUS_APPROVED
    elif action == "reject":
        comment.status = PostComment.STATUS_REJECTED
    comment.reviewed_by = request.user
    comment.save(update_fields=["status", "reviewed_by"])
    return redirect("pending_comments")


@login_required
def pending_comments(request):
    if not _can_moderate(request.user):
        return HttpResponseForbidden("Forbidden")
    pending_qs = PostComment.objects.filter(status=PostComment.STATUS_PENDING).select_related("author", "post").order_by("created_at")
    page_obj = Paginator(pending_qs, 20).get_page(request.GET.get("page"))
    return render(request, "videos/pending_comments.html", {"page_obj": page_obj})


@login_required
def create_post(request):
    if not _is_admin(request.user):
        return HttpResponseForbidden("Forbidden")
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        if title and content:
            base_slug = slugify(title) or "post"
            slug = base_slug
            idx = 2
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{idx}"
                idx += 1
            Post.objects.create(title=title, content=content, slug=slug, author=request.user, is_published=True)
            messages.success(request, "تم نشر المقال.")
            return redirect("posts_list")
        messages.error(request, "العنوان والمحتوى مطلوبان.")
    return render(request, "videos/post_create.html")


@login_required
def users_moderation(request):
    if not _can_moderate(request.user):
        return HttpResponseForbidden("Forbidden")
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        action = request.POST.get("action")
        target = get_object_or_404(User, id=user_id)
        profile = _get_or_create_profile(target)
        if action == "ban":
            target.is_active = False
            target.save(update_fields=["is_active"])
            profile.is_banned = True
            profile.save(update_fields=["is_banned"])
        elif action == "unban":
            target.is_active = True
            target.save(update_fields=["is_active"])
            profile.is_banned = False
            profile.save(update_fields=["is_banned"])
        elif action == "block_comments":
            profile.can_comment = False
            profile.save(update_fields=["can_comment"])
        elif action == "allow_comments":
            profile.can_comment = True
            profile.save(update_fields=["can_comment"])
        elif action == "make_moderator":
            profile.role = UserProfile.ROLE_MODERATOR
            profile.save(update_fields=["role"])
        elif action == "make_user":
            profile.role = UserProfile.ROLE_USER
            profile.save(update_fields=["role"])
    query = request.GET.get("q", "").strip()
    role_filter = request.GET.get("role", "").strip()
    status_filter = request.GET.get("status", "").strip()

    users = User.objects.all().order_by("-date_joined")
    if query:
        users = users.filter(Q(username__icontains=query) | Q(email__icontains=query))
    profiles = {p.user_id: p for p in UserProfile.objects.filter(user__in=users)}
    user_rows = []
    for u in users:
        p = profiles.get(u.id)
        role = p.role if p else UserProfile.ROLE_USER
        if role_filter and role != role_filter:
            continue
        if status_filter == "active" and not u.is_active:
            continue
        if status_filter == "banned" and u.is_active:
            continue
        user_rows.append({"user": u, "profile": p})
    page_obj = Paginator(user_rows, 20).get_page(request.GET.get("page"))
    return render(
        request,
        "videos/users_moderation.html",
        {
            "user_rows": page_obj,
            "page_obj": page_obj,
            "query": query,
            "selected_role": role_filter,
            "selected_status": status_filter,
            "role_choices": UserProfile.ROLE_CHOICES,
        },
    )


@login_required
def toggle_favorite(request, video_id):
    if request.method != "POST":
        return redirect("video_detail", video_id=video_id)
    video = get_object_or_404(Video, video_id=video_id, is_active=True)
    favorite, created = Favorite.objects.get_or_create(user=request.user, video=video)
    if not created:
        favorite.delete()
        messages.info(request, "تمت إزالة الفيديو من المفضلة.")
    else:
        messages.success(request, "تمت إضافة الفيديو إلى المفضلة.")
    return redirect("video_detail", video_id=video_id)


@login_required
def my_favorites(request):
    favorites = (
        Favorite.objects.select_related("video")
        .filter(user=request.user, video__is_active=True)
        .order_by("-created_at")
    )
    return render(request, "videos/favorites.html", {"favorites": favorites})


@login_required
def toggle_spirit_pin(request):
    if request.method != "POST":
        return redirect("home")
    card_hash = request.POST.get("card_hash", "").strip()
    kind = request.POST.get("kind", "").strip()
    title = request.POST.get("title", "").strip()
    line_text = request.POST.get("line_text", "").strip()
    source = request.POST.get("source", "").strip()
    if not card_hash or not line_text:
        messages.error(request, "بيانات الذكر غير مكتملة.")
        ref = request.META.get("HTTP_REFERER", "/")
        return redirect(f"{ref}{'&' if '?' in ref else '?'}spirit=open")
    pin, created = SpiritPin.objects.get_or_create(
        user=request.user,
        card_hash=card_hash,
        defaults={"kind": kind, "title": title, "line_text": line_text, "source": source},
    )
    if not created:
        pin.delete()
        messages.info(request, "تم إلغاء التثبيت.")
    else:
        messages.success(request, "تم تثبيت العنصر.")
    ref = request.META.get("HTTP_REFERER", "/")
    return redirect(f"{ref}{'&' if '?' in ref else '?'}spirit=open")
