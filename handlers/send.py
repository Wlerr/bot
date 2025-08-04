# handlers/send.py

import json
from uuid import uuid4
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from utils.storage import CHECKLISTS, DYNAMIC, user_progress
from config.config import REPORT_CHAT_IDS, DYNAMIC_FILE
from handlers.checklist import send_checklist

async def send_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /send <название_чеклиста>
    Ищет шаблон в статических и динамических чек-листах для текущего чата,
    публикует его один раз и делает одноразовый динамический чек-лист недоступным.
    """
    chat_id = update.effective_chat.id
    args = context.args  # список слов после команды

    # 1) Проверка: указан ли аргумент
    if not args:
        return await update.message.reply_text(
            "❗ Использование: /send <название_чеклиста>\n"
            "Пример: /send Открытие"
        )

    # 2) Определяем, для какой «чайной» этот чат
    place = None
    for p, cid in REPORT_CHAT_IDS.items():
        if cid == chat_id:
            place = p
            break
    if not place:
        return await update.message.reply_text(
            "❗ Этот чат не зарегистрирован для отправки чек-листов."
        )

    # 3) Собираем полное название чек-листа
    title = " ".join(args)

    # 4) Ищем в статических шаблонах
    items = CHECKLISTS.get(place, {}).get(title)
    prefix = "static"
    tpl_id = title

    # 5) Если не нашли — ищем в динамических по title
    if items is None:
        dyn = next(
            (d for d in DYNAMIC if d["place"] == place and d["title"] == title),
            None
        )
        if dyn:
            items = dyn["items"]
            prefix = "dynamic"
            tpl_id = dyn["id"]

            # 5a) Если это одноразовый динамический чек-лист — удаляем его
            if dyn.get("one_time"):
                DYNAMIC.remove(dyn)
                with open(DYNAMIC_FILE, "w", encoding="utf-8") as f:
                    json.dump(DYNAMIC, f, ensure_ascii=False, indent=2)

    # 6) Если всё ещё не найден — сообщаем об ошибке
    if items is None:
        return await update.message.reply_text(
            f"❗ Чек-лист «{title}» не найден для «{place}»."
        )

    # 7) Инициализируем новую сессию чек-листа
    ck_id = uuid4().hex[:8]
    context.user_data["ck_id"] = ck_id
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_progress[ck_id] = {
        "place": place,
        "user": update.effective_user.full_name,
        "title": title,
        "timestamp": timestamp,
        "items": items,
        "status": [None] * len(items),
        "chat_id": chat_id,
        "message_id": None,
    }

    # 8) Публикуем вступительное сообщение
    intro = (
        f"🟢 Чек-лист *{title}* запущен!\n"
        f"Начало: {user_progress[ck_id]['timestamp']}\n\n"
        """"
Нажимая, отмечайте 🍃 то, что выполнено без вопросов.

Второе нажатие проставит статус проблемы/неисправности ⚠️.

Третьим нажатием установите отметку ⁉️, если есть вопросы или что-то мешает выполнению.

Четвёртое нажатие вернёт пункт в состояние «не отмечено».

После прохождения чек-листа отправьте его, нажав кнопку «📤 Отправить отчёт» в конце списка.
"""
    )
    sent = await update.message.reply_text(intro, parse_mode="Markdown")
    user_progress[ck_id]["message_id"] = sent.message_id

    # 9) Рисуем интерактивный чек-лист (кнопки)
    await send_checklist(context.bot, ck_id)


# Регистрируем хендлер в bot.py так:
# app.add_handler(CommandHandler("send", send_handler))
