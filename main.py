import logging
import sys

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from config import BOT_TOKEN
from handlers import start, button_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("Lutfen config.py dosyasindaki BOT_TOKEN degiskenine bot token'inizi girin!")
        print("HATA: config.py dosyasindaki BOT_TOKEN degiskenini duzenleyin!")
        print("  1. Telegram'da @BotFather ile bot olusturun")
        print("  2. Aldiginiz token'i config.py icine yazin")
        print("  3. Tekrar calistirin: python main.py")
        sys.exit(1)

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("BetAnaliz Bot baslatiliyor...")
    print("Bot basariyla baslatildi! Telegram'da botunuzu test edin.")
    print("Botu durdurmak icin Ctrl+C'ye basin.")

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
