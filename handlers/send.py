# handlers/send.py

import logging
from uuid import uuid4
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from utils.storage import CHECKLISTS, DYNAMIC, user_progress
from config.config import REPORT_CHAT_IDS
from handlers.checklist import send_checklist

logger = logging.getLogger(__name__)

async def send_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает команду /send <название>
    и сразу публикует интерактивный чек-лист в этом же чате.
    """
    chat_id = update.effective_chat.id
    args = context.args  # всё, что введено после /send

    # 1) Проверьли, что указан аргумент
    if not args:
        return await update.message.reply_text(
            "❗ Использование: /send <название_чеклиста>\n"
            "Пример: /send Открытие"
        )

    # 2) Определяем «место» по текущему чату
    #    (например, если бот только в чатах Тверская и Покровка)
    place = None
    for p, cid in REPORT_CHAT_IDS.items():
        if cid == chat_id:
            place = p
            break
    if not place:
        return await update.message.reply_text(
            "❗ Этот чат не зарегистрирован для отправки чек-листов."
        )

    name = " ".join(args)  # название чек-листа может состоять из нескольких слов
    logger.info("Вызов чек-листа %s для чайной %s (чат %s)", name, place, chat_id)

    # 3) Ищем в статических
    items = CHECKLISTS.get(place, {}).get(name)
    prefix = "static"
    tpl_id = name

    # 4) Если не нашли — ищем в динамических по title
    if items is None:
        dyn = next((d for d in DYNAMIC if d["place"] == place and d["title"] == name), None)
        if dyn:
            items = dyn["items"]
            prefix = "dynamic"
            tpl_id = dyn["id"]

    if items is None:
        return await update.message.reply_text(f"❗ Чек-лист «{name}» не найден для «{place}».")

    # 5) Инициализируем новую сессию
    ck_id = uuid4().hex[:8]
    context.user_data["ck_id"] = ck_id
    title = name
    user_progress[ck_id] = {
        "place": place,
        "user": update.effective_user.full_name,
        "title": title,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "items": items,
        "status": [None] * len(items),
        "chat_id": chat_id,
        "message_id": None,
    }

    # 6) Публикуем первое сообщение
    sent = await update.message.reply_text(
        f"📝 *{title}*\nНачало: {user_progress[ck_id]['timestamp']}",
        parse_mode="Markdown"
    )
    user_progress[ck_id]["message_id"] = sent.message_id

    # 7) Рисуем интерактивный чек-лист
    await send_checklist(context.bot, ck_id)
