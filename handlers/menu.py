# handlers/menu.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.storage import CHECKLISTS
from utils.storage import user_progress
from uuid import uuid4
from datetime import datetime

async def place_handler(update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик callback_data="place|<Название>"
    Сохраняет выбранную чайную и предлагает выбрать чек-лист открытия/закрытия.
    """
    query = update.callback_query
    await query.answer()
    place = query.data.split("|")[1]
    # Сохраняем выбор в user_data
    context.user_data["place"] = place

    # Формируем кнопки для чек-листов этой чайной
    buttons = [
        [InlineKeyboardButton(name, callback_data=f"checklist|{name}")]
        for name in CHECKLISTS[place].keys()
    ]
    await query.edit_message_text(
        text=f"🏠 Вы выбрали чайную *{place}*. Выбери чек-лист:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def checklist_handler(update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик callback_data="checklist|<Название>"
    Генерирует уникальный ID запущенного чек-листа и сохраняет initial state.
    """
   

    query = update.callback_query
    await query.answer()

    checklist_name = query.data.split("|")[1]
    place = context.user_data.get("place")
    checklist_id = str(uuid4())
    context.user_data["checklist_id"] = checklist_id

    # handlers/menu.py (часть checklist_handler)

    items = CHECKLISTS[place][checklist_name]
    # инициализируем как списки
    user_progress[checklist_id] = {
        "place": place,       
        "chat_id": query.message.chat.id,
        "user": query.from_user.full_name,
        "title": f"{place} — {checklist_name}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "items": items,             # список текстов
        "status": [False] * len(items)  # параллельный список статусов
    }


    # Дальше отдадим на отрисовку
    from handlers.checklist import send_checklist
    await send_checklist(query, checklist_id)
