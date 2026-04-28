from __future__ import annotations

import os
import random

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from bot.models import TelegramSubscriber
from videos.models import Video


def _video_url(video: Video) -> str:
    return f"https://www.youtube.com/watch?v={video.video_id}"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    TelegramSubscriber.objects.update_or_create(
        chat_id=chat_id,
        defaults={"username": user.username or "", "first_name": user.first_name or "", "is_active": True},
    )
    await update.message.reply_text("مرحبًا بك في بوت منصة الدعوة. اكتب /help لعرض الأوامر.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/search <keyword>\n/category\n/daily\n/random\n/help")


async def random_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    videos = list(Video.objects.filter(is_active=True)[:1000])
    if not videos:
        await update.message.reply_text("لا يوجد فيديوهات حالياً.")
        return
    video = random.choice(videos)
    await update.message.reply_text(f"{video.title}\n{_video_url(video)}")


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = " ".join(context.args).strip()
    if not keyword:
        await update.message.reply_text("اكتب كلمة البحث بعد الأمر. مثال: /search عقيدة")
        return
    results = Video.objects.filter(title__icontains=keyword, is_active=True).order_by("-published_at")[:5]
    if not results:
        await update.message.reply_text("لا توجد نتائج.")
        return
    message = "\n\n".join([f"{video.title}\n{_video_url(video)}" for video in results])
    await update.message.reply_text(message)


async def category_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton(label, callback_data=f"cat:{key}")]
        for key, label in Video.CATEGORY_CHOICES
    ]
    await update.message.reply_text("اختر التصنيف:", reply_markup=InlineKeyboardMarkup(buttons))


async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    payload = query.data.split(":", 1)
    if len(payload) != 2:
        return
    category = payload[1]
    videos = Video.objects.filter(category=category, is_active=True).order_by("-published_at")[:5]
    if not videos:
        await query.edit_message_text("لا توجد فيديوهات لهذا التصنيف.")
        return
    text = "\n\n".join([f"{v.title}\n{_video_url(v)}" for v in videos])
    await query.edit_message_text(text)


async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subscriber, _ = TelegramSubscriber.objects.get_or_create(chat_id=update.effective_chat.id)
    subscriber.is_active = not subscriber.is_active
    subscriber.save(update_fields=["is_active", "last_active"])
    status = "مفعل" if subscriber.is_active else "موقوف"
    await update.message.reply_text(f"الاشتراك اليومي الآن: {status}")


def build_application() -> Application:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN missing.")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("random", random_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("category", category_command))
    app.add_handler(CommandHandler("daily", daily_command))
    app.add_handler(CallbackQueryHandler(category_callback, pattern=r"^cat:"))
    return app
