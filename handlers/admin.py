# handlers/admin.py

import json
import re
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

# ConversationHandler состояния
ASK_PLACE, ASK_TITLE, ASK_ITEMS, ASK_ONE_TIME, CONFIRM = range(5)

# Список Telegram user_id админов
ADMINS = {512193226, 987654321}  # замените на реальные ID


# === Шаг 1: Запуск создания чек-листа ===
async def newchecklist_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return

    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("❌ У вас нет прав создавать чек-листы.")
        return ConversationHandler.END

    # Предлагаем выбор чайной
    keyboard = [
        [InlineKeyboardButton(place, callback_data=place)]
        for place in CHECKLISTS.keys()
    ]
    await update.message.reply_text(
        "🛠 Для какой чайной создаём новый чек-лист?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ASK_PLACE


# === Шаг 2: Ввод названия чек-листа ===
async def ask_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID or update.effective_user.id not in ADMINS:
        return ConversationHandler.END

    context.user_data["place"] = update.callback_query.data
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("✏️ Введите название чек-листа:")
    return ASK_TITLE


# === Шаг 3: Ввод пунктов чек-листа ===
async def ask_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID or update.effective_user.id not in ADMINS:
        return ConversationHandler.END

    context.user_data["title"] = update.message.text.strip()
    await update.message.reply_text(
        "🗒 Теперь введите пункты через новую строку.\n"
        "Пример:\nПункт 1\nПункт 2\n…"
    )
    return ASK_ITEMS


# === Шаг 4: Уточнение — одноразовый ли чек-лист ===
async def ask_one_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID or update.effective_user.id not in ADMINS:
        return ConversationHandler.END

    items = [line.strip() for line in update.message.text.splitlines() if line.strip()]
    if not items:
        await update.message.reply_text("❌ Нет валидных пунктов.")
        return ConversationHandler.END

    context.user_data["items"] = items

    preview = "\n".join(f"– {item}" for item in items)
    await update.message.reply_text(
        f"✅ Чек-лист:\n*{context.user_data['title']}*\n\n{preview}\n\n"
        "Этот чек-лист должен быть одноразовым? Напишите `yes` или `no`.",
        parse_mode="Markdown"
    )
    return ASK_ONE_TIME


# === Шаг 5: Подтверждение создания ===
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID or update.effective_user.id not in ADMINS:
        return ConversationHandler.END

    response = update.message.text.strip().lower()
    if response not in ("yes", "no"):
        await update.message.reply_text("❗ Пожалуйста, ответьте 'yes' или 'no'.")
        return ASK_ONE_TIME

    context.user_data["one_time"] = (response == "yes")

    preview = "\n".join(f"– {item}" for item in context.user_data["items"])
    await update.message.reply_text(
        f"💾 Сохраняем чек-лист *{context.user_data['title']}* "
        f"для {context.user_data['place']}?\n"
        f"Одноразовый: {'Да' if context.user_data['one_time'] else 'Нет'}\n\n"
        f"{preview}\n\n"
        "Подтвердите командой /yes или отмените /no",
        parse_mode="Markdown"
    )
    return CONFIRM


# === Финальный шаг: Сохранение чек-листа ===
async def save_dynamic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID or update.effective_user.id not in ADMINS:
        return ConversationHandler.END

    if update.message.text.strip().lower() != "/yes":
        await update.message.reply_text("❌ Отмена.")
        return ConversationHandler.END

    new_id = uuid4().hex[:8]
    entry = {
        "id": new_id,
        "place": context.user_data["place"],
        "title": context.user_data["title"],
        "items": context.user_data["items"],
        "one_time": context.user_data.get("one_time", False)
    }
    DYNAMIC.append(entry)

    with open(DYNAMIC_FILE, "w", encoding="utf-8") as f:
        json.dump(DYNAMIC, f, ensure_ascii=False, indent=2)

    await update.message.reply_text(f"✅ Чек-лист сохранён! Его ID: `{new_id}`", parse_mode="Markdown")
    return ConversationHandler.END


# === Команда публикации чек-листа по ID ===
async def publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID or update.effective_user.id not in ADMINS:
        await update.message.reply_text("❌ У вас нет прав.")
        return

    parts = update.message.text.strip().split()
    if len(parts) != 2:
        return await update.message.reply_text("Использование: /publish <ID>")

    tpl_id = parts[1]
    tpl = next((d for d in DYNAMIC if d["id"] == tpl_id), None)

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


# === ConversationHandler ===
conv = ConversationHandler(
    entry_points=[CommandHandler("newchecklist", newchecklist_start)],
    states={
        ASK_PLACE:    [CallbackQueryHandler(ask_title)],
        ASK_TITLE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_items)],
        ASK_ITEMS:    [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_one_time)],
        ASK_ONE_TIME: [MessageHandler(filters.Regex("(?i)^(yes|no)$"), confirm)],
        CONFIRM:      [MessageHandler(filters.Regex("(?i)^/(yes|no)$"), save_dynamic)],
    },
    fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    allow_reentry=True
)
