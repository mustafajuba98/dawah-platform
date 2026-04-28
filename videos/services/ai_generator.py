from __future__ import annotations

import logging
import os
import time

import google.generativeai as genai

logger = logging.getLogger(__name__)


class AIDescriptionGenerator:
    def __init__(self, api_key: str | None = None, requests_per_minute: int = 10) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.requests_per_minute = requests_per_minute
        self.delay_seconds = 60 / max(requests_per_minute, 1)
        self.enabled = bool(self.api_key)

        if self.enabled:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.model = None

    def _generate(self, prompt: str, max_chars: int = 700) -> str:
        if not self.enabled or not self.model:
            return ""
        try:
            response = self.model.generate_content(prompt)
            text = (response.text or "").strip()
            if not text:
                return ""
            return text[:max_chars]
        except Exception as exc:
            logger.warning("Gemini generation failed: %s", exc)
            return ""
        finally:
            time.sleep(self.delay_seconds)

    def generate_seo_description(self, video) -> str:
        prompt = (
            "اكتب وصف SEO باللغة العربية لفيديو يوتيوب إسلامي بين 200 و300 حرف. "
            "اذكر الكلمات المفتاحية المناسبة بشكل طبيعي دون مبالغة.\n\n"
            f"العنوان: {video.title}\n"
            f"الوصف: {video.description[:1200]}"
        )
        return self._generate(prompt, max_chars=320)

    def generate_summary(self, video) -> str:
        prompt = (
            "اكتب ملخصًا عربيًا من 3 إلى 5 نقاط مختصرة لفيديو دعوي. "
            "استخدم صياغة واضحة ومباشرة.\n\n"
            f"العنوان: {video.title}\n"
            f"الوصف: {video.description[:1200]}"
        )
        return self._generate(prompt, max_chars=900)

    def generate_tags(self, video) -> str:
        prompt = (
            "استخرج 10 إلى 15 وسمًا مناسبًا (عربي/إنجليزي) مفصولة بفواصل "
            "لفيديو يوتيوب إسلامي.\n\n"
            f"العنوان: {video.title}\n"
            f"الوصف: {video.description[:1200]}"
        )
        return self._generate(prompt, max_chars=300)

    def bulk_generate(self, queryset) -> int:
        if not self.enabled:
            return 0
        processed = 0
        for video in queryset:
            if video.seo_description:
                continue
            video.seo_description = self.generate_seo_description(video)
            video.ai_summary = video.ai_summary or self.generate_summary(video)
            video.tags = video.tags or self.generate_tags(video)
            video.save(update_fields=["seo_description", "ai_summary", "tags", "updated_at"])
            processed += 1
        return processed
