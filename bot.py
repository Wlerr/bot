# bot.py

import logging
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
)

from config.config import TOKEN, LOG_FILE, LOG_LEVEL
from handlers.start import start_command
from handlers.menu import (
    start_command as menu_start,  # если в menu.py start_command дублируется
    place_handler,
    checklist_handler,
    back_to_main,
)
from handlers.checklist import toggle_handler
from handlers.report import report_handler
from handlers.send import send_handler  # новый хендлер для /send
from handlers.admin import conv, publish  # админский ConversationHandler и /publish

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
    # 1) Создаём приложение
    app = Application.builder().token(TOKEN).build()

    # --- Админские хендлеры ---
    app.add_handler(conv)                        # /newchecklist через ConversationHandler
    app.add_handler(CommandHandler("publish", publish))

    # --- Пользовательские хендлеры ---
    # замена /start на меню выбора чайной
    app.add_handler(CommandHandler("start", start_command))

    # /send <название> — сразу публикует чек-лист в этом чате
    app.add_handler(CommandHandler("send", send_handler))

    # выбор чайной из меню (callback_data="place|<place>")
    app.add_handler(CallbackQueryHandler(place_handler, pattern="^place\\|"))

    # выбор конкретного чек-листа (static|… или dynamic|…)
    app.add_handler(CallbackQueryHandler(checklist_handler, pattern="^(?:static|dynamic)\\|"))

    # кнопка «← Назад» возвращает к выбору чайной
    app.add_handler(CallbackQueryHandler(back_to_main, pattern="^back\\|main$"))

    # переключение статусов пунктов
    app.add_handler(CallbackQueryHandler(toggle_handler, pattern="^toggle\\|"))

    # отправка финального отчёта
    app.add_handler(CallbackQueryHandler(report_handler, pattern="^report\\|"))

    logger.info("Бот запущен")
    # 2) Запускаем polling, сбрасывая старые updates
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
