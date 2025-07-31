# utils/storage.py

import json
from uuid import uuid4
from datetime import datetime
from config.config import CHECKLISTS_FILE

# Загружаем все чек-листы
with open(CHECKLISTS_FILE, encoding="utf-8") as f:
    CHECKLISTS = json.load(f)

# Здесь будем хранить прогресс в памяти
user_progress = {}
