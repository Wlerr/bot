# handlers/menu.py

import logging
from uuid import uuid4
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from utils.storage import CHECKLISTS, DYNAMIC, user_progress
from config.config import REPORT_CHAT_IDS
from handlers.checklist import send_checklist

logger = logging.getLogger(__name__)

# --- Шаг 1: Старт (команда /start) ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает кнопки с выбором чайной.
    """
    keyboard = [
        [InlineKeyboardButton(place, callback_data=f"place|{place}")]
        for place in CHECKLISTS.keys()
    ]
    await update.message.reply_text(
        "👋 *Выберите чайную:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# --- Шаг 2: Пользователь нажал на «place|<place>» ---
async def place_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Получает callback_data="place|<place>",
    сохраняет его и показывает реальные чек-листы.
    """
    query = update.callback_query
    await query.answer()

    # Разбираем место и сохраняем
    _, place = query.data.split("|", 1)
    context.user_data["place"] = place

    # Собираем списки
    static_names = list(CHECKLISTS.get(place, {}).keys())
    dynamic_items = [d for d in DYNAMIC if d["place"] == place]

    # Строим клавиатуру: статические
    keyboard = []
    for name in static_names:
        keyboard.append([
            InlineKeyboardButton(name, callback_data=f"static|{place}|{name}")
        ])
    # и динамические
    for tpl in dynamic_items:
        keyboard.append([
            InlineKeyboardButton(tpl["title"], callback_data=f"dynamic|{place}|{tpl['id']}")
        ])
    # кнопка Назад к выбору места (опционально)
    keyboard.append([
        InlineKeyboardButton("← Назад", callback_data="back|main")
    ])

    # Отправляем/редактируем сообщение
    await query.edit_message_text(
        f"🏠 *Чек-листы для* _{place}_:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# --- Шаг 3: Пользователь нажал на «static|…» или «dynamic|…» ---
async def checklist_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()


    # Лог для отладки: какая data приходит от кнопки
    logger.info("checklist_handler called with data=%s", query.data)


    # Разбираем callback_data
    try:
        prefix, place, ident = query.data.split("|", 2)
    except ValueError:
        await query.edit_message_text("❗ Некорректный формат данных.")
        return

    # Получаем пункты чек-листа
    if prefix == "static":
        items = CHECKLISTS.get(place, {}).get(ident)
        title = ident  # просто имя шаблона — идентификатор
    else:  # dynamic
        tpl = next((d for d in DYNAMIC if d["id"] == ident and d["place"] == place), None)
        if not tpl:
            await query.edit_message_text("❗ Динамический чек-лист не найден.")
            return
        items = tpl["items"] 
        title = tpl["title"]

    if not items:
        await query.edit_message_text("❗ Чек-лист не найден.")
        return



    # Создаём уникальный ID сессии и сохраняем прогресс
    from uuid import uuid4
    from datetime import datetime
    ck_id = uuid4().hex[:8]

    context.user_data["ck_id"] = ck_id
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    chat_id = REPORT_CHAT_IDS.get(place)

    """

    user_progress[ck_id] = {
        "place": place,
        "user": query.from_user.full_name,
        "title": title,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "items": items,
        "status": [None] * len(items),
        "chat_id": REPORT_CHAT_IDS.get(place),
        "message_id": None,
    }

    # Информируем пользователя и публикуем в чат чайной
    await query.edit_message_text("⏳ Отправка чек-листа…")
    sent = await context.bot.send_message(
        chat_id=user_progress[ck_id]["chat_id"],
        text=f"📝 *{title}*\nНачато: {user_progress[ck_id]['timestamp']}",
        parse_mode="Markdown"
    )
    user_progress[ck_id]["message_id"] = sent.message_id

    # Рисуем интерактивный чек-лист
    await send_checklist(context.bot, ck_id)


# --- Шаг 4: Назад к выбору чайной ---
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start_command(update, context)  # просто заново вызывает старт
