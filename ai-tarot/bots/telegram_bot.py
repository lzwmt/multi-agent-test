#!/usr/bin/env python3
"""
AI Tarot Telegram Bot

A Telegram bot for AI-powered tarot readings.
Uses python-telegram-bot (async) and httpx for API calls.
"""

import os
import logging
from typing import Optional
from datetime import datetime

import httpx
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode

# ─── Configuration ───────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TAROT_API_URL = os.environ.get("TAROT_API_URL", "http://localhost:18899")

# Conversation states
CHOOSING_SPREAD, ASKING_QUESTION, CHOOSING_PERSONA = range(3)

# User session data storage
user_sessions: dict[int, dict] = {}

# Logger
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ─── API Helpers ─────────────────────────────────────────────────────────────
async def api_get(path: str) -> Optional[dict | list]:
    """GET request to the tarot backend API."""
    url = f"{TAROT_API_URL.rstrip('/')}{path}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        logger.error("API GET %s → %s", url, e.response.status_code)
    except Exception as e:
        logger.error("API GET %s error: %s", url, e)
    return None


async def api_post(path: str, payload: dict) -> Optional[dict]:
    """POST request to the tarot backend API."""
    url = f"{TAROT_API_URL.rstrip('/')}{path}"
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        logger.error("API POST %s → %s", url, e.response.status_code)
    except Exception as e:
        logger.error("API POST %s error: %s", url, e)
    return None


# ─── Formatting Helpers ─────────────────────────────────────────────────────
def format_reading(result: dict) -> str:
    """Format a divination result into a beautiful Markdown message."""
    lines: list[str] = []

    # Card details
    cards = result.get("cards", [])
    spread_name = result.get("spread_name", "塔罗牌阵")
    lines.append(f"🔮 *{spread_name}*\n")

    if cards:
        lines.append("🃏 *牌面信息*\n")
        for i, card in enumerate(cards, 1):
            name = card.get("name", "未知牌")
            name_en = card.get("name_en", "")
            orientation = card.get("orientation", "upright")
            position = card.get("position", "")

            # Orientation symbol
            if orientation.lower() in ("reversed", "inverted", "逆位", "reverse"):
                orient_display = "逆位↓"
                orient_emoji = "🔽"
            else:
                orient_display = "正位↑"
                orient_emoji = "🔼"

            pos_label = f" ({position})" if position else ""
            lines.append(f"{orient_emoji} *{i}. {name}*{pos_label}")
            if name_en:
                lines.append(f"   _{name_en}_")
            lines.append(f"   ➡️ {orient_display}\n")

    # AI reading
    reading = result.get("reading") or result.get("ai_reading") or result.get("interpretation", "")
    if reading:
        lines.append("✨ *AI 解读*\n")
        lines.append(reading.strip())

    # Overall advice
    advice = result.get("advice", "")
    if advice:
        lines.append(f"\n💡 *建议*\n{advice.strip()}")

    return "\n".join(lines)


def format_list(items: list[dict], key_name: str, display_field: str = "name") -> str:
    """Format a list of API items for display."""
    if not items:
        return "暂无数据"
    lines = []
    for item in items:
        name = item.get(display_field, "未知")
        desc = item.get("description", "")
        if desc:
            lines.append(f"• *{name}* — {desc}")
        else:
            lines.append(f"• *{name}*")
    return "\n".join(lines)


# ─── Command Handlers ────────────────────────────────────────────────────────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — send welcome message with inline keyboard."""
    welcome = (
        "🌙 *欢迎来到 AI 塔罗* 🌙\n\n"
        "我是你的 AI 塔罗占卜师，可以为你进行智能塔罗牌占卜。\n\n"
        "🔮 *使用方法：*\n"
        "• 发送 /draw 开始一次新的占卜\n"
        "• 发送 /spreads 查看可用牌阵\n"
        "• 发送 /personas 查看可用角色\n"
        "• 发送 /help 获取帮助\n\n"
        "点击下方按钮开始你的塔罗之旅 👇"
    )

    keyboard = [
        [InlineKeyboardButton("🔮 开始占卜", callback_data="start_draw")],
        [InlineKeyboardButton("📋 查看牌阵", callback_data="list_spreads"),
         InlineKeyboardButton("🎭 查看角色", callback_data="list_personas")],
        [InlineKeyboardButton("❓ 帮助", callback_data="show_help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help — show available commands."""
    help_text = (
        "📖 *AI 塔罗 — 帮助*\n\n"
        "*可用命令：*\n"
        "• /start — 重启机器人\n"
        "• /draw — 开始一次新的塔罗占卜\n"
        "• /spreads — 查看所有可用牌阵\n"
        "• /personas — 查看所有可用角色\n"
        "• /help — 显示此帮助信息\n"
        "• /cancel — 取消当前占卜\n\n"
        "*占卜流程：*\n"
        "1️⃣ 选择牌阵（单牌、三牌、凯尔特十字等）\n"
        "2️⃣ 输入你想占卜的问题\n"
        "3️⃣ 选择解读角色（如：温柔姐姐、理性分析师等）\n"
        "4️⃣ 获取 AI 生成的塔罗解读\n\n"
        "祝你占卜愉快！✨"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def spreads_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /spreads — list available spreads from API."""
    data = await api_get("/api/divination/spreads")
    if data is None:
        await update.message.reply_text("⚠️ 无法获取牌阵列表，请稍后再试。")
        return

    items = data if isinstance(data, list) else data.get("spreads", data.get("results", []))
    text = f"📋 *可用牌阵*\n\n{format_list(items, 'spread')}"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def personas_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /personas — list available personas from API."""
    data = await api_get("/api/divination/personas")
    if data is None:
        await update.message.reply_text("⚠️ 无法获取角色列表，请稍后再试。")
        return

    items = data if isinstance(data, list) else data.get("personas", data.get("results", []))
    text = f"🎭 *可用角色*\n\n{format_list(items, 'persona')}"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ─── Callback Query Handler (inline buttons) ────────────────────────────────
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
    """Handle inline keyboard button presses."""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "start_draw":
        return await _start_draw_flow(query, context)

    if data == "list_spreads":
        api_data = await api_get("/api/divination/spreads")
        if api_data is None:
            await query.edit_message_text("⚠️ 无法获取牌阵列表，请稍后再试。")
            return ConversationHandler.END
        items = api_data if isinstance(api_data, list) else api_data.get("spreads", api_data.get("results", []))
        text = f"📋 *可用牌阵*\n\n{format_list(items, 'spread')}"
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END

    if data == "list_personas":
        api_data = await api_get("/api/divination/personas")
        if api_data is None:
            await query.edit_message_text("⚠️ 无法获取角色列表，请稍后再试。")
            return ConversationHandler.END
        items = api_data if isinstance(api_data, list) else api_data.get("personas", api_data.get("results", []))
        text = f"🎭 *可用角色*\n\n{format_list(items, 'persona')}"
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END

    if data == "show_help":
        help_text = (
            "📖 *AI 塔罗 — 帮助*\n\n"
            "• /draw — 开始占卜\n"
            "• /spreads — 查看牌阵\n"
            "• /personas — 查看角色\n"
            "• /cancel — 取消当前占卜"
        )
        await query.edit_message_text(help_text, parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END

    if data.startswith("spread_"):
        spread_id = data.replace("spread_", "", 1)
        user_id = query.from_user.id
        user_sessions.setdefault(user_id, {})["spread_id"] = spread_id

        await query.edit_message_text(
            "🤔 *请输入你的问题：*\n\n"
            "比如：最近的事业运势如何？我和 TA 的感情走向？",
            parse_mode=ParseMode.MARKDOWN,
        )
        return ASKING_QUESTION

    if data.startswith("persona_"):
        persona_id = data.replace("persona_", "", 1)
        user_id = query.from_user.id
        user_sessions.setdefault(user_id, {})["persona_id"] = persona_id

        session = user_sessions[user_id]
        # Show loading message
        await query.edit_message_text("🔮 *正在为您占卜...* 请稍候 ✨", parse_mode=ParseMode.MARKDOWN)

        # Call divination API
        payload = {
            "spread_id": session.get("spread_id"),
            "question": session.get("question", ""),
            "persona_id": persona_id,
        }
        result = await api_post("/api/divination/", payload)

        if result is None:
            await query.edit_message_text(
                "⚠️ 占卜失败，请稍后再试。\n如果问题持续，请联系管理员。",
                parse_mode=ParseMode.MARKDOWN,
            )
            return ConversationHandler.END

        reading_text = format_reading(result)

        # Telegram message length limit is 4096
        if len(reading_text) > 4000:
            # Split into parts
            parts = []
            while reading_text:
                if len(reading_text) <= 4000:
                    parts.append(reading_text)
                    break
                # Find a good break point
                idx = reading_text.rfind("\n", 0, 4000)
                if idx == -1:
                    idx = 4000
                parts.append(reading_text[:idx])
                reading_text = reading_text[idx:].lstrip("\n")

            for part in parts:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=part,
                    parse_mode=ParseMode.MARKDOWN,
                )
        else:
            await query.edit_message_text(reading_text, parse_mode=ParseMode.MARKDOWN)

        # Clean up session
        user_sessions.pop(user_id, None)
        return ConversationHandler.END

    return ConversationHandler.END


# ─── Draw Flow ───────────────────────────────────────────────────────────────
async def _start_draw_flow(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Initiate the draw flow: fetch spreads and show inline keyboard."""
    data = await api_get("/api/divination/spreads")
    if data is None:
        await query.edit_message_text("⚠️ 无法获取牌阵列表，请稍后再试。")
        return ConversationHandler.END

    items = data if isinstance(data, list) else data.get("spreads", data.get("results", []))
    if not items:
        await query.edit_message_text("⚠️ 暂无可用牌阵。")
        return ConversationHandler.END

    keyboard = []
    for item in items:
        sid = item.get("id", item.get("name", ""))
        name = item.get("name", "未知牌阵")
        desc = item.get("description", "")
        label = f"{name}" + (f" — {desc}" if desc else "")
        keyboard.append([InlineKeyboardButton(label, callback_data=f"spread_{sid}")])

    await query.edit_message_text(
        "🎴 *请选择牌阵：*\n\n点击下方按钮选择你想使用的牌阵 👇",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSING_SPREAD


async def draw_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /draw command — start the reading flow."""
    return await _start_draw_flow_message(update, context)


async def _start_draw_flow_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Initiate the draw flow from a message (not callback)."""
    data = await api_get("/api/divination/spreads")
    if data is None:
        await update.message.reply_text("⚠️ 无法获取牌阵列表，请稍后再试。")
        return ConversationHandler.END

    items = data if isinstance(data, list) else data.get("spreads", data.get("results", []))
    if not items:
        await update.message.reply_text("⚠️ 暂无可用牌阵。")
        return ConversationHandler.END

    keyboard = []
    for item in items:
        sid = item.get("id", item.get("name", ""))
        name = item.get("name", "未知牌阵")
        desc = item.get("description", "")
        label = f"{name}" + (f" — {desc}" if desc else "")
        keyboard.append([InlineKeyboardButton(label, callback_data=f"spread_{sid}")])

    await update.message.reply_text(
        "🎴 *请选择牌阵：*\n\n点击下方按钮选择你想使用的牌阵 👇",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSING_SPREAD


# ─── Question Handler ────────────────────────────────────────────────────────
async def receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive the user's question and show persona selection."""
    user_id = update.effective_user.id
    question = update.message.text.strip()

    if not question:
        await update.message.reply_text("❓ 请输入你的问题，不能为空哦。")
        return ASKING_QUESTION

    user_sessions.setdefault(user_id, {})["question"] = question

    # Fetch personas
    data = await api_get("/api/divination/personas")
    if data is None:
        await update.message.reply_text("⚠️ 无法获取角色列表，请稍后再试。")
        return ConversationHandler.END

    items = data if isinstance(data, list) else data.get("personas", data.get("results", []))
    if not items:
        await update.message.reply_text("⚠️ 暂无可用角色。")
        return ConversationHandler.END

    keyboard = []
    for item in items:
        pid = item.get("id", item.get("name", ""))
        name = item.get("name", "未知角色")
        desc = item.get("description", "")
        label = f"{name}" + (f" — {desc}" if desc else "")
        keyboard.append([InlineKeyboardButton(label, callback_data=f"persona_{pid}")])

    await update.message.reply_text(
        f"✅ *你的问题：* _{question}_\n\n"
        "🎭 *请选择解读角色：*\n\n点击下方按钮选择 👇",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSING_PERSONA


# ─── Cancel Handler ──────────────────────────────────────────────────────────
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current conversation."""
    user_id = update.effective_user.id
    user_sessions.pop(user_id, None)
    await update.message.reply_text("❌ 占卜已取消。随时发送 /draw 重新开始。")
    return ConversationHandler.END


# ─── Fallback Handler ────────────────────────────────────────────────────────
async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle unexpected messages during conversation."""
    await update.message.reply_text(
        "🤔 我不太理解你的意思。\n"
        "• 发送 /draw 开始占卜\n"
        "• 发送 /cancel 取消当前操作\n"
        "• 发送 /help 查看帮助"
    )
    return ConversationHandler.END


# ─── Main ────────────────────────────────────────────────────────────────────
def main() -> None:
    """Entry point — set up and run the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set!")
        raise SystemExit("Error: TELEGRAM_BOT_TOKEN not set. Please set it before running.")

    logger.info("Starting AI Tarot Telegram Bot...")
    logger.info("Backend API URL: %s", TAROT_API_URL)

    # Build the application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Conversation handler for the draw flow
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("draw", draw_command),
            CallbackQueryHandler(button_callback, pattern="^start_draw$"),
        ],
        states={
            CHOOSING_SPREAD: [
                CallbackQueryHandler(button_callback, pattern="^spread_"),
                CallbackQueryHandler(button_callback, pattern="^list_"),
            ],
            ASKING_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_question),
            ],
            CHOOSING_PERSONA: [
                CallbackQueryHandler(button_callback, pattern="^persona_"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.ALL, fallback),
        ],
        per_message=False,
    )

    # Register handlers (order matters!)
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("spreads", spreads_command))
    application.add_handler(CommandHandler("personas", personas_command))
    application.add_handler(CommandHandler("cancel", cancel))

    # Catch-all callback for non-conversation buttons
    application.add_handler(CallbackQueryHandler(button_callback))

    # Set bot commands for Telegram's command menu
    async def post_init(app: Application) -> None:
        await app.bot.set_my_commands([
            BotCommand("start", "重启机器人"),
            BotCommand("draw", "开始塔罗占卜"),
            BotCommand("spreads", "查看可用牌阵"),
            BotCommand("personas", "查看可用角色"),
            BotCommand("help", "获取帮助"),
            BotCommand("cancel", "取消当前占卜"),
        ])

    application.post_init = post_init

    # Run the bot
    logger.info("Bot is polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
