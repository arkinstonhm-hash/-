import os
import logging
import asyncio

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from shazamio import Shazam
import yt_dlp

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ⚠️ Tokeningizni shu yerga yozing (yoki BOT_TOKEN nomli environment variable orqali bering)
BOT_TOKEN = os.getenv("BOT_TOKEN", "TOKENINGIZNI_BU_YERGA_QOYING")

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom! 🎵\n\n"
        "Men bunday ishlayman:\n"
        "1️⃣ Menga qo'shiqning nomini yozing — YouTube'dan topib, audio qilib yuboraman.\n"
        "2️⃣ Yoki menga ovozli xabar / audio / video yuboring — Shazam orqali qo'shiqni "
        "aniqlab, keyin YouTube'dan yuklab beraman.\n\n"
        "Sinab ko'ring! 🚀"
    )


def search_and_download_youtube(query: str) -> str:
    """YouTube'da qidiradi, birinchi natijani mp3 qilib yuklaydi va fayl yo'lini qaytaradi."""
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "default_search": "ytsearch1",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        if "entries" in info:
            info = info["entries"][0]
        filename = ydl.prepare_filename(info)
        base, _ = os.path.splitext(filename)
        return base + ".mp3"


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    status = await update.message.reply_text(f"🔎 Qidirilmoqda: {query}")
    path = None
    try:
        loop = asyncio.get_event_loop()
        path = await loop.run_in_executor(None, search_and_download_youtube, query)
        with open(path, "rb") as audio_file:
            await update.message.reply_audio(audio=audio_file, title=query)
    except Exception as e:
        logger.exception(e)
        await update.message.reply_text("Kechirasiz, topilmadi yoki xatolik yuz berdi. 😔")
    finally:
        await status.delete()
        if path and os.path.exists(path):
            os.remove(path)


async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ovozli xabar / audio / video / video-note -> Shazam orqali aniqlash."""
    status = await update.message.reply_text("🎧 Musiqa aniqlanmoqda...")

    tg_file = None
    if update.message.voice:
        tg_file = await update.message.voice.get_file()
    elif update.message.audio:
        tg_file = await update.message.audio.get_file()
    elif update.message.video:
        tg_file = await update.message.video.get_file()
    elif update.message.video_note:
        tg_file = await update.message.video_note.get_file()

    if not tg_file:
        await status.edit_text("Iltimos, audio, video yoki ovozli xabar yuboring.")
        return

    local_path = os.path.join(DOWNLOAD_DIR, f"input_{update.message.message_id}")
    await tg_file.download_to_drive(local_path)

    yt_path = None
    try:
        shazam = Shazam()
        result = await shazam.recognize(local_path)
        track = result.get("track")

        if not track:
            await status.edit_text(
                "Musiqani aniqlay olmadim 😔 Boshqa audio yuboring yoki qo'shiq nomini yozing."
            )
            return

        title = track.get("title", "Noma'lum")
        subtitle = track.get("subtitle", "")
        query = f"{subtitle} {title}".strip()

        await status.edit_text(f"✅ Topildi: {subtitle} - {title}\n⬇️ YouTube'dan yuklanmoqda...")

        loop = asyncio.get_event_loop()
        yt_path = await loop.run_in_executor(None, search_and_download_youtube, query)

        with open(yt_path, "rb") as audio_file:
            await update.message.reply_audio(audio=audio_file, title=title, performer=subtitle)

        await status.delete()
    except Exception as e:
        logger.exception(e)
        await status.edit_text("Xatolik yuz berdi, qaytadan urinib ko'ring.")
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)
        if yt_path and os.path.exists(yt_path):
            os.remove(yt_path)


def main():
    if BOT_TOKEN == "TOKENINGIZNI_BU_YERGA_QOYING":
        raise RuntimeError(
            "Iltimos, bot.py faylida BOT_TOKEN qiymatini o'z tokeningizga almashtiring "
            "yoki BOT_TOKEN environment variable orqali bering."
        )

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(
            filters.VOICE | filters.AUDIO | filters.VIDEO | filters.VIDEO_NOTE,
            handle_media,
        )
    )
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
