from __future__ import annotations

import logging
import secrets
import hashlib

import requests

logger = logging.getLogger(__name__)

ALQURAN_RANDOM_AYAH = "https://api.alquran.cloud/v1/ayah/random"
HADITH_API_BASE = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions"
HADITH_BOOKS_MAX = (("ara-bukhari", 7563), ("ara-muslim", 7000))

STATIC_ADHKAR = [
    {"kind": "ذكر", "title": "كفارة المجلس", "lines": ["سبحانك اللهم وبحمدك، أشهد أن لا إله إلا أنت، أستغفرك وأتوب إليك."], "source": "ثبت في الصحيحين."},
    {"kind": "ذكر", "title": "ذكر بعد الصلاة", "lines": ["سبحان الله والحمد لله والله أكبر ثلاثاً وثلاثين."], "source": "من السنة النبوية."},
    {"kind": "ذكر", "title": "عند الكرب", "lines": ["لا إله إلا أنت سبحانك إني كنت من الظالمين."], "source": "دعاء ذي النون عليه السلام."},
]


def _fetch_random_hadith() -> dict | None:
    rng = secrets.SystemRandom()
    for _ in range(4):
        book, mx = rng.choice(HADITH_BOOKS_MAX)
        num = rng.randint(1, mx)
        try:
            response = requests.get(f"{HADITH_API_BASE}/{book}/{num}.json", timeout=10)
            if response.status_code != 200:
                continue
            data = response.json()
            hadiths = data.get("hadiths") or []
            if not hadiths:
                continue
            text = (hadiths[0].get("text") or "").strip()
            if len(text) < 20:
                continue
            source = "صحيح البخاري" if "bukhari" in book else "صحيح مسلم"
            return {"kind": "حديث", "title": f"{source}", "lines": [text], "source": "نص عبر hadith-api."}
        except Exception as exc:
            logger.debug("Hadith fetch failed: %s", exc)
    return None


def _fetch_random_ayah() -> dict | None:
    try:
        response = requests.get(ALQURAN_RANDOM_AYAH, timeout=8)
        response.raise_for_status()
        data = response.json().get("data") or {}
        text = (data.get("text") or "").strip()
        if not text:
            return None
        surah = data.get("surah") or {}
        name = surah.get("name", "") if isinstance(surah, dict) else ""
        return {"kind": "آية", "title": f"سورة {name}" if name else "من القرآن الكريم", "lines": [text], "source": "api.alquran.cloud"}
    except Exception as exc:
        logger.debug("Ayah fetch failed: %s", exc)
    return None


def build_spirit_cards(target: int = 6, use_cache: bool = True) -> list[dict]:
    if use_cache:
        from django.core.cache import cache

        key = f"spirit_cards_{target}"
        cached = cache.get(key)
        if cached:
            return cached

    cards: list[dict] = []
    hadith = _fetch_random_hadith()
    if hadith:
        cards.append(hadith)
    ayah = _fetch_random_ayah()
    if ayah:
        cards.append(ayah)
    pool = list(STATIC_ADHKAR)
    secrets.SystemRandom().shuffle(pool)
    cards.extend(pool[: max(0, target - len(cards))])
    secrets.SystemRandom().shuffle(cards)
    result = cards[:target]
    if use_cache:
        from django.core.cache import cache

        cache.set(f"spirit_cards_{target}", result, 300)
    return result


def card_hash(card: dict) -> str:
    base = f"{card.get('kind','')}|{card.get('title','')}|{' '.join(card.get('lines') or [])}|{card.get('source','')}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()
