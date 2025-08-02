# bot.py

import logging
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
)

from config.config import TOKEN, LOG_FILE, LOG_LEVEL
from handlers.start import start_command
from handlers.menu import start_command, place_handler, checklist_handler, back_to_main
from handlers.checklist import toggle_handler
from handlers.report import report_handler
from handlers.admin import conv, publish  # импорт админского ConversationHandler и /publish

app = Application.builder().token(TOKEN).build()

# Настройка логирования
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    # Создаём приложение
    app = Application.builder().token(TOKEN).build()

    # --- Регистрируем админские хендлеры ---
    app.add_handler(conv)                         # ConversationHandler для /newchecklist
    app.add_handler(CommandHandler("publish", publish))

    # --- Регистрируем пользовательские хендлеры ---
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(place_handler, pattern="^place\\|"))
    app.add_handler(CallbackQueryHandler(checklist_handler, pattern="^(?:static|dynamic)\\|"))
    app.add_handler(CallbackQueryHandler(back_to_main,      pattern="^back\\|main$"))
    app.add_handler(CallbackQueryHandler(toggle_handler, pattern="^toggle\\|"))
    app.add_handler(CallbackQueryHandler(report_handler, pattern="^report\\|"))


    logger.info("Бот запущен")
    # Запускаем polling
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
