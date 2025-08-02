# handlers/admin.py

import json
from uuid import uuid4
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# Импорты из вашего проекта
from config.config import ADMIN_CHAT_ID, DYNAMIC_FILE, REPORT_CHAT_IDS
from utils.storage import CHECKLISTS, DYNAMIC, user_progress
from handlers.checklist import send_checklist

# Состояния для ConversationHandler
ASK_PLACE, ASK_TITLE, ASK_ITEMS, CONFIRM = range(4)

# Список Telegram user_id пользователей-руководителей
ADMINS = {
    512193226,  # замените на реальные ID ваших администраторов
}


async def newchecklist_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Точка входа для создания нового динамического шаблона.
    Срабатывает на команду /newchecklist, только в админ-чате.
    """
    """
    # 1) Разрешаем только в админском чате
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return
"""

    # 2) Проверяем, что отправитель — в списке ADMINS
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("❌ У вас нет прав для этой команды.")
        return ConversationHandler.END

    # 3) Предлагаем выбрать чайную из статических шаблонов
    keyboard = [
        [InlineKeyboardButton(place, callback_data=place)]
        for place in CHECKLISTS.keys()
    ]
    await update.message.reply_text(
        "🛠 Для какой чайной создаём новый чек-лист?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ASK_PLACE


async def ask_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    После выбора чайной: спрашиваем название нового чек-листа.
    """
    # Сохраняем выбранную чайную
    place = update.callback_query.data
    context.user_data["place"] = place

    # Подтверждаем выбор и просим ввести название
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("✏️ Введите название нового чек-листа:")
    return ASK_TITLE


async def ask_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    После получения названия: спрашиваем пункты.
    """
    # Сохраняем название
    title = update.message.text.strip()
    context.user_data["title"] = title

    # Инструкция по вводу пунктов
    await update.message.reply_text(
        "🗒 Теперь введите пункты через новую строку.\n"
        "Пример:\n"
        "Пункт 1\n"
        "Пункт 2\n"
        "Пункт 3"
    )
    return ASK_ITEMS


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показываем предпросмотр и просим подтвердить сохранение.
    """
    # Разбиваем текст по строкам — получаем список пунктов
    items = [line.strip() for line in update.message.text.splitlines() if line.strip()]
    context.user_data["items"] = items

    # Собираем предпросмотр
    preview = "\n".join(f"– {item}" for item in items)
    await update.message.reply_text(
        f"Сохраняем чек-лист:\n\n"
        f"Название: *{context.user_data['title']}*\n"
        f"Чайная: *{context.user_data['place']}*\n\n"
        f"{preview}\n\n"
        "Подтвердите /yes или отмените /no",
        parse_mode="Markdown"
    )
    return CONFIRM


async def save_dynamic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    При подтверждении сохраняем новый шаблон в dynamic.json.
    """
    text = update.message.text.strip().lower()
    if text != "/yes":
        await update.message.reply_text("❌ Создание шаблона отменено.")
        return ConversationHandler.END

    # Формируем новую запись
    new_id = uuid4().hex[:8]
    entry = {
        "id": new_id,
        "place": context.user_data["place"],
        "title": context.user_data["title"],
        "items": context.user_data["items"],
    }
    DYNAMIC.append(entry)

    # Перезаписываем файл dynamic.json
    with open(DYNAMIC_FILE, "w", encoding="utf-8") as f:
        json.dump(DYNAMIC, f, ensure_ascii=False, indent=2)

    await update.message.reply_text(
        f"✅ Шаблон сохранён! Его ID: `{new_id}`",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /publish <ID> публикует готовый шаблон в соответствующий чат.
    """
    # 1) Проверяем чат и права
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("❌ У вас нет прав.")
        return

    # 2) Разбор команды
    parts = update.message.text.split()
    if len(parts) != 2:
        return await update.message.reply_text("Использование: /publish <ID>")

    tpl = next((d for d in DYNAMIC if d["id"] == parts[1]), None)
    if not tpl:
        return await update.message.reply_text("❌ Шаблон с таким ID не найден.")

    # 3) Инициализация прогресса по аналогии со статическим чек-листом
    ck_id = uuid4().hex[:8]
    user_progress[ck_id] = {
        "place": tpl["place"],
        "user": update.effective_user.full_name,
        "title": tpl["title"],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "items": tpl["items"],
        "status": [None] * len(tpl["items"]),
        "chat_id": REPORT_CHAT_IDS[tpl["place"]],
        "message_id": None
    }

    # 4) Публикуем интерактивный чек-лист
    sent = await update.message.reply_text(
        f"📝 *{tpl['title']}*",
        parse_mode="Markdown"
    )
    user_progress[ck_id]["message_id"] = sent.message_id

    # 5) Отрисовываем кнопки и пункты
    await send_checklist(context.bot, ck_id)


# ConversationHandler для создания шаблона
conv = ConversationHandler(
    entry_points=[CommandHandler("newchecklist", newchecklist_start)],

    states={
        ASK_PLACE: [CallbackQueryHandler(ask_title)],
        ASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_items)],
        ASK_ITEMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
        CONFIRM:  [MessageHandler(filters.Regex("^(?:/yes|/no)$"), save_dynamic)],
    },

    # Команда /cancel в любой момент завершает разговор
    fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],

    allow_reentry=True  # позволяет заново войти в разговор
)
