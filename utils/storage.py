import json
from pathlib import Path
from config.config import CHECKLISTS_FILE, DYNAMIC_FILE

BASE = Path(__file__).resolve().parent.parent

# 1) Статические шаблоны
with open(BASE / CHECKLISTS_FILE, encoding="utf-8") as f:
    CHECKLISTS = json.load(f)

# 2) Динамические шаблоны
with open(BASE / DYNAMIC_FILE, encoding="utf-8") as f:
    DYNAMIC = json.load(f)

# 3) Состояния запущенных чек-листов
user_progress = {}
