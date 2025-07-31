# bot.py

import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config.config import TOKEN, LOG_FILE, LOG_LEVEL

# 1) Настроим логирование в файл и в консоль
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 2) Импортируем наши обработчики
#    (файлы создадим далее в папке handlers/)
from handlers.start import start_command
from handlers.menu import place_handler, checklist_handler
from handlers.checklist import toggle_handler, send_checklist
from handlers.report import report_handler

def main():
    # 3) Создаём приложение (обёртку над ботом)
    app = Application.builder().token(TOKEN).build()

    # 4) Регистрируем команду /start
    app.add_handler(CommandHandler("start", start_command))

    # 5) Регистрируем общий обработчик нажатий на inline-кнопки
    #    Обратите внимание на шаблоны `pattern` для маршрутизации
    app.add_handler(CallbackQueryHandler(place_handler, pattern="^place\\|"))
    app.add_handler(CallbackQueryHandler(checklist_handler, pattern="^checklist\\|"))
    app.add_handler(CallbackQueryHandler(toggle_handler, pattern="^toggle\\|"))
    app.add_handler(CallbackQueryHandler(report_handler, pattern="^report\\|"))

    # 6) Запуск поллинга (бот начинает получать обновления)
    logger.info("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
