from django.conf import settings

from bot.models import BotNotification
from videos.models import SpiritPin, UserProfile
from videos.services.spiritual import build_spirit_cards, card_hash


def spirit_panel(request):
    refresh_requested = request.GET.get("spirit_refresh") == "1"
    cards = build_spirit_cards(target=5, use_cache=not refresh_requested)
    for card in cards:
        card["card_hash"] = card_hash(card)

    pinned_hashes = set()
    pinned_cards = []
    if getattr(request, "user", None) and request.user.is_authenticated:
        pins = SpiritPin.objects.filter(user=request.user)
        pinned_cards = [
            {
                "kind": p.kind,
                "title": p.title,
                "lines": [p.line_text],
                "source": p.source,
                "card_hash": p.card_hash,
            }
            for p in pins
        ]
        pinned_hashes = {p.card_hash for p in pins}
        cards = [c for c in cards if c["card_hash"] not in pinned_hashes]
    return {"spirit_cards": cards, "spirit_pinned_cards": pinned_cards, "spirit_pinned_hashes": pinned_hashes}


def branding(request):
    can_moderate = False
    if getattr(request, "user", None) and request.user.is_authenticated:
        profile = UserProfile.objects.filter(user=request.user).only("role").first()
        role = profile.role if profile else UserProfile.ROLE_USER
        can_moderate = request.user.is_superuser or role in (UserProfile.ROLE_ADMIN, UserProfile.ROLE_MODERATOR)
    recent_notifications = list(BotNotification.objects.all()[:5])
    return {
        "platform_name": getattr(settings, "SITE_NAME", "نور الدعوة"),
        "can_moderate": can_moderate,
        "recent_bot_notifications": recent_notifications,
    }
