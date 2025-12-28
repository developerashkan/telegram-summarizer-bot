import os
import logging
from typing import List
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_SUM_BOT_TOKEN")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION")

# ✅ Correct env checks
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_SUM_BOT_TOKEN not set")
if not AZURE_OPENAI_API_KEY:
    raise RuntimeError("AZURE_OPENAI_API_KEY not set")
if not AZURE_OPENAI_ENDPOINT:
    raise RuntimeError("AZURE_OPENAI_ENDPOINT not set")
if not AZURE_OPENAI_API_VERSION:
    raise RuntimeError("AZURE_OPENAI_API_VERSION not set")

# ✅ Correct Azure client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=AZURE_OPENAI_API_VERSION,
)

# ⚠️ MUST be Azure DEPLOYMENT NAME
MODEL = "gpt-4.1"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

chat_history = {}


def store_message(chat_id: int, data: dict):
    chat_history.setdefault(chat_id, []).append(data)
    chat_history[chat_id] = chat_history[chat_id][-200:]


def get_recent_messages(chat_id: int, count: int = 50) -> List[dict]:
    return chat_history.get(chat_id, [])[-count:]


def clear_chat_history(chat_id: int):
    chat_history.pop(chat_id, None)


def summarize_chat(messages: List[dict], chat_name: str) -> str:
    if not messages:
        return "No messages found."

    lines = [f"{m['sender']}: {m['text']}" for m in messages if m.get("text")]
    if not lines:
        return "No text messages."

    chat_text = "\n".join(lines)

    system_prompt = (
        "You are a professional Telegram chat summarizer.\n"
        "Summarize strictly in Persian.\n"
        "Tone: informal and friendly.\n"
        "No emojis. No formatting.\n"
        "Mention different opinions if any.\n"
        "Mention decisions if any.\n"
    )

    user_prompt = (
        f"Chat name: {chat_name}\n"
        f"Messages: {len(messages)}\n\n"
        f"{chat_text[:6000]}\n\n"
        "Persian summary:"
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=1500,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Summarization error: {e}")
        return "Failed to summarize."


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello!\n"
        "I summarize Telegram chats.\n\n"
        "Commands:\n"
        "/summarize\n"
        "/summarize 100\n"
        "/clear\n"
        "/stats"
    )


async def summarize_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_name = update.effective_chat.title or update.effective_chat.first_name or "Chat"

    count = 50
    if context.args:
        try:
            count = max(10, min(200, int(context.args[0])))
        except ValueError:
            await update.message.reply_text("Invalid number.")
            return

    messages = get_recent_messages(chat_id, count)
    if len(messages) < 5:
        await update.message.reply_text("Not enough messages.")
        return

    processing = await update.message.reply_text(f"Summarizing {len(messages)} messages...")
    summary = summarize_chat(messages, chat_name)
    await processing.delete()

    text = f"Summary ({len(messages)} messages):\n\n{summary}"
    for i in range(0, len(text), 4096):
        await update.message.reply_text(text[i:i + 4096])


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_chat_history(update.effective_chat.id)
    await update.message.reply_text("Chat history cleared.")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    messages = chat_history.get(chat_id, [])

    users = {}
    for m in messages:
        users[m["sender"]] = users.get(m["sender"], 0) + 1

    active = max(users.items(), key=lambda x: x[1])[0] if users else "None"

    await update.message.reply_text(
        f"Messages: {len(messages)}\n"
        f"Users: {len(users)}\n"
        f"Most active: {active}"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.is_bot:
        return

    store_message(
        update.effective_chat.id,
        {
            "sender": update.message.from_user.first_name or "User",
            "text": update.message.text or update.message.caption or "",
            "timestamp": update.message.date.isoformat(),
        }
    )


def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("summarize", summarize_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(MessageHandler(filters.TEXT | filters.CAPTION, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()
