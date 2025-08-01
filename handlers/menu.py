# handlers/menu.py

import json
from uuid import uuid4
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.storage import CHECKLISTS, user_progress
from config.config import REPORT_CHAT_IDS
from handlers.checklist import send_checklist

async def place_handler(update: "telegram.Update", context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик callback_data="place|<Название>"
    Сохраняет выбранную чайную в context.user_data и предлагает выбрать чек-лист.
    """
    query = update.callback_query
    await query.answer()

    # получаем название чайной
    place = query.data.split("|", 1)[1]
    context.user_data["place"] = place

    # строим кнопки с именами чек-листов для выбранной чайной
    keyboard = [
        [InlineKeyboardButton(cl_name, callback_data=f"checklist|{cl_name}")]
        for cl_name in CHECKLISTS[place].keys()
    ]

    await query.edit_message_text(
        text=f"🏠 Вы выбрали чайную *{place}*. Выберите чек-лист:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def checklist_handler(update: "telegram.Update", context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик callback_data="checklist|<Имя чек-листа>"
    Инициализирует сессию, публикует интерактивный чек-лист в общем чате,
    сохраняет chat_id и message_id и запускает отрисовку.
    """
    query = update.callback_query
    await query.answer()

    place = context.user_data.get("place")
    checklist_name = query.data.split("|", 1)[1]
    if place is None:
        # На всякий случай — если place потерялся
        await query.edit_message_text("❗ Сначала выберите чайную командой /start")
        return

    # создаём короткий уникальный ID сессии
    ck_id = uuid4().hex[:8]
    context.user_data["checklist_id"] = ck_id

    # инициализируем прогресс: список пунктов + статусы (None / "done" / "skipped" / "ignored")
    items = CHECKLISTS[place][checklist_name]
    user_progress[ck_id] = {
        "place": place,
        "user": query.from_user.full_name,
        "title": f"{place} — {checklist_name}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "items": items,
        "status": [None] * len(items),
        # определяем, куда публиковать чек-лист
        "chat_id": REPORT_CHAT_IDS.get(place),
        "message_id": None,
    }

    # 1) сообщаем пользователю в ЛС, что чек-лист создаётся
    await query.edit_message_text(
        text="⏳ Ваш чек-лист сохраняется и вскоре появится в общем чате..."
    )

    # 2) публикуем первое сообщение в групповом чате и запоминаем его message_id
    chat_id = user_progress[ck_id]["chat_id"]
    sent = await context.bot.send_message(
        chat_id=chat_id,
        text=f"📝 *{user_progress[ck_id]['title']}*\nНачато: {user_progress[ck_id]['timestamp']}\n\n(загружается…)",
        parse_mode="Markdown"
    )
    user_progress[ck_id]["message_id"] = sent.message_id

    # 3) сразу отрисовываем интерактивный чек-лист в том же сообщении
    await send_checklist(context.bot, ck_id)
