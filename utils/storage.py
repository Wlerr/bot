# utils/storage.py

import json
from pathlib import Path
from config.config import CHECKLISTS_FILE

# 1) Загружаем шаблоны чек-листов из JSON
#    Path(__file__).parent.parent — это корень проекта
CHECKLISTS_PATH = Path(__file__).resolve().parent.parent / CHECKLISTS_FILE

with open(CHECKLISTS_PATH, encoding="utf-8") as f:
    CHECKLISTS = json.load(f)

# 2) Здесь будут храниться состояния активных чек-листов.
#    Ключ — это ваш ck_id, а значение — словарь с полями:
#      place, user, title, timestamp, items, status, chat_id, message_id
user_progress = {}
