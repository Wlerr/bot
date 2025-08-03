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

from config.config import ADMIN_CHAT_ID, DYNAMIC_FILE, REPORT_CHAT_IDS
from utils.storage import CHECKLISTS, DYNAMIC, user_progress
from handlers.checklist import send_checklist

# Состояния для создания
ASK_PLACE, ASK_TITLE, ASK_ITEMS, CONFIRM = range(4)

# Telegram user_id админов, которым разрешено создавать чек-листы
ADMINS = {512193226, 987654321}  # <-- замените на реальные ID руководителей


async def newchecklist_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1) Только в вашем админ-чате
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return

    # 2) Только определённые пользователи
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("❌ У вас нет прав создавать чек-листы.")
        return ConversationHandler.END

    # 3) Начинаем диалог: выбор чайной
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
    # И здесь проверяем админ-чат и права ещё раз (на всякий случай)
    if update.effective_chat.id != ADMIN_CHAT_ID or update.effective_user.id not in ADMINS:
        return ConversationHandler.END

    context.user_data["place"] = update.callback_query.data
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("✏️ Введите название чек-листа:")
    return ASK_TITLE


async def ask_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверка прав
    if update.effective_chat.id != ADMIN_CHAT_ID or update.effective_user.id not in ADMINS:
        return ConversationHandler.END

    context.user_data["title"] = update.message.text.strip()
    await update.message.reply_text(
        "🗒 Теперь введите пункты через новую строку.\n"
        "Пример:\nПункт 1\nПункт 2\n…"
    )
    return ASK_ITEMS


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверка прав
    if update.effective_chat.id != ADMIN_CHAT_ID or update.effective_user.id not in ADMINS:
        return ConversationHandler.END

    items = [line.strip() for line in update.message.text.splitlines() if line.strip()]
    context.user_data["items"] = items

    preview = "\n".join(f"– {i}" for i in items)
    await update.message.reply_text(
        f"Сохраним чек-лист «{context.user_data['title']}» для "
        f"{context.user_data['place']}:\n\n{preview}\n\n"
        "Подтвердите /yes или отмените /no",
        parse_mode="Markdown"
    )
    return CONFIRM


async def save_dynamic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем право на сохранение
    if update.effective_chat.id != ADMIN_CHAT_ID or update.effective_user.id not in ADMINS:
        return ConversationHandler.END

    if update.message.text.strip().lower() != "/yes":
        await update.message.reply_text("❌ Отмена.")
        return ConversationHandler.END

    new_id = uuid4().hex[:8]
    entry = {
        "id":    new_id,
        "place": context.user_data["place"],
        "title": context.user_data["title"],
        "items": context.user_data["items"],
    }
    DYNAMIC.append(entry)
    with open(DYNAMIC_FILE, "w", encoding="utf-8") as f:
        json.dump(DYNAMIC, f, ensure_ascii=False, indent=2)

    await update.message.reply_text(f"✅ Шаблон сохранён! Его ID: `{new_id}`", parse_mode="Markdown")
    return ConversationHandler.END


async def publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Тоже проверяем права и чат
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("❌ У вас нет прав.")
        return

    parts = update.message.text.split()
    if len(parts) != 2:
        return await update.message.reply_text("Использование: /publish <ID>")

    tpl = next((d for d in DYNAMIC if d["id"] == parts[1]), None)
    if not tpl:
        return await update.message.reply_text("❌ Шаблон не найден.")

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

    sent = await update.message.reply_text(f"📝 *{tpl['title']}*", parse_mode="Markdown")
    user_progress[ck_id]["message_id"] = sent.message_id
    await send_checklist(context.bot, ck_id)


conv = ConversationHandler(
    entry_points=[CommandHandler("newchecklist", newchecklist_start)],
    states={
        ASK_PLACE: [CallbackQueryHandler(ask_title)],
        ASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_items)],
        ASK_ITEMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
        CONFIRM:  [MessageHandler(filters.Regex("^(?:/yes|/no)$"), save_dynamic)],
    },
    fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    allow_reentry=True
)
