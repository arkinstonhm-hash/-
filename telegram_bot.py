import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot tokenini va parolni belgilash
BOT_TOKEN = '8108986276:AAHHgfWZBw2euWTXPXcOnSqd97HsKYYQ1hc'
PASSWORD = '1991200020071227'  # Parolni o'rnating
BOT_CREATED_TIME = datetime.now()

# Kanallar ro'yxati
CHANNELS = [
    {
        'name': 'Godzilla DM',
        'url': 'https://t.me/GodzillaDM_MMAB'
    },
    {
        'name': 'Bulls Capital TR',
        'url': 'https://t.me/BullsCapitalTR'
    },
    {
        'name': 'Group Chat',
        'url': 'https://t.me/+9fpOyJaHP_5iMjgy'
    }
]

# Foydalanuvchi holatini saqlash
user_authenticated = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start komandasini handle qilish"""
    user_id = update.effective_user.id
    
    if user_authenticated.get(user_id):
        await send_channels(update, context)
    else:
        await update.message.reply_text(
            "👋 Assalomu alaikum! Bot ishga tushdi.\n\n"
            "🔐 Iltimos, parolni kiriting:"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchi xabarlarini handle qilish"""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    if not user_authenticated.get(user_id):
        # Parol tekshirish
        if message_text == PASSWORD:
            user_authenticated[user_id] = True
            await update.message.reply_text("✅ Parol to'g'ri! Kanallar yuborilmoqda...")
            await send_channels(update, context)
        else:
            await update.message.reply_text("❌ Parol noto'g'ri! Qayta urinib ko'ring:")
    else:
        await update.message.reply_text(
            "ℹ️ Siz allaqachon autentifikatsiya qilib bo'lgansiz.\n"
            "/start komandasidan foydalaning"
        )


async def send_channels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kanallarni knopkali qilib yuborish"""
    
    # Har bir kanal uchun alohida xabar yuborish
    for i, channel in enumerate(CHANNELS, 1):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"➡️ {channel['name']} ga o'tish",
                url=channel['url']
            )]
        ])
        
        await update.effective_chat.send_message(
            f"📱 **{i}. {channel['name']}**\n\n"
            f"Kanalni ochish uchun quyidagi knopkani bosing:",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    # Bot yaratilish vaqti haqida xabar
    created_time_str = BOT_CREATED_TIME.strftime("%Y-%m-%d %H:%M:%S")
    await update.effective_chat.send_message(
        f"⏰ **Bot Haqida Ma'lumot**\n\n"
        f"🤖 Bot yaratilgan vaqt: `{created_time_str}`\n"
        f"✅ Barcha kanallar sizga yuborildi!",
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Yordam buyrugi"""
    await update.message.reply_text(
        "📋 **Bot Buyruqlari:**\n\n"
        "/start - Botni ishga tushirish\n"
        "/help - Yordam ko'rsatish\n\n"
        "🔐 Parolni kiritib, kanallarni ochishingiz mumkin.",
        parse_mode='Markdown'
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xatolarni handle qilish"""
    logger.warning(f'Update "{update}" created error "{context.error}"')


def main() -> None:
    """Bot Application yaratish va ishga tushirish"""
    
    # Application yaratish
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Komandalarni qo'shish
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Xabar handlerini qo'shish
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Error handler qo'shish
    application.add_error_handler(error_handler)
    
    # Botni ishga tushirish
    print("🤖 Bot ishga tushmoqda...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
