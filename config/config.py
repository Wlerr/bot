# config/config.py

import os
import logging
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Этот относительный путь к JSON
CHECKLISTS_FILE = "checklists.json"
DYNAMIC_FILE    = os.path.join(BASE_DIR, "dynamic.json") 

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Токен бота (возьми у BotFather и вставь сюда или лучше — через переменную окружения)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Пути к файлам
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKLISTS_FILE = os.path.join(BASE_DIR, "checklists.json")
DATA_FILE = os.path.join(BASE_DIR, "data", "progress.json")

# Логирование
LOG_FILE = os.path.join(BASE_DIR, "logs", "bot.log")
LOG_LEVEL = "INFO"


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "ВАШ_ТОКЕН")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKLISTS_FILE = os.path.join(BASE_DIR, "checklists.json")
DATA_FILE = os.path.join(BASE_DIR, "data", "progress.json")

LOG_FILE = os.path.join(BASE_DIR, "logs", "bot.log")
LOG_LEVEL = "INFO"

# ID чатов (групп) для отчётов по каждой чайной
REPORT_CHAT_IDS = {
    "Тверская": -1002840146051,   # замените на настоящий ID
    "Покровка": -4968880134
}

# **Добавляем ID админского чата** (скопируйте реальное число из /getchat)
ADMIN_CHAT_ID = -4952000366