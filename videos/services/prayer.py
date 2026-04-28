from __future__ import annotations

import logging

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

ALADHAN_TIMINGS_URL = "https://api.aladhan.com/v1/timingsByCity"
PRAYER_ROWS_AR = (
    ("Fajr", "الفجر"),
    ("Sunrise", "الشروق"),
    ("Dhuhr", "الظهر"),
    ("Asr", "العصر"),
    ("Maghrib", "المغرب"),
    ("Isha", "العشاء"),
)


def _method_for_country(country: str) -> int:
    return 5 if (country or "").strip().lower() in ("egypt", "eg", "مصر") else 3


def _fetch_uncached(city: str, country: str) -> dict | None:
    try:
        response = requests.get(
            ALADHAN_TIMINGS_URL,
            params={"city": city, "country": country, "method": _method_for_country(country)},
            timeout=10,
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        payload = response.json().get("data") or {}
        timings = payload.get("timings") or {}
        date_info = payload.get("date") or {}
        hijri = (date_info.get("hijri") or {}).get("date", "")
        gregorian = (date_info.get("gregorian") or {}).get("readable", "")
        rows = [{"label": label, "time": timings.get(key)} for key, label in PRAYER_ROWS_AR if timings.get(key)]
        return {"rows": rows, "hijri": hijri, "gregorian": gregorian, "city": city, "country": country}
    except Exception as exc:
        logger.warning("Prayer timings fetch failed: %s", exc)
        return None


def fetch_prayer_timings_cached() -> dict | None:
    city = getattr(settings, "PRAYER_CITY", "Cairo")
    country = getattr(settings, "PRAYER_COUNTRY", "Egypt")
    ttl = max(60, int(getattr(settings, "PRAYER_CACHE_SECONDS", 900)))
    cache_key = f"prayer_{city}_{country}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    data = _fetch_uncached(city, country)
    cache.set(cache_key, data, ttl)
    return data
