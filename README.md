# Telegram Chat Summarizer Bot

A Telegram bot that summarizes chat messages in **Persian** using Azure OpenAI GPT-4.1.

The bot collects messages from a chat and generates a concise summary in **informal Persian**, mentioning opinions and decisions.

---

## Features

- Summarizes recent Telegram chat messages in **Persian**.
- Keeps track of chat history (up to 200 messages per chat).
- Commands supported:
  - `/start` – Show welcome message and usage instructions.
  - `/summarize [count]` – Summarize the last `count` messages (default: 50, max: 200).
  - `/clear` – Clear chat history.
  - `/stats` – Show statistics: total messages, users, and most active user.
- Ignores bot messages automatically.
- Friendly, informal tone without emojis or formatting.

---

## Requirements

- Python 3.10+
- Packages:
```bash
pip install python-telegram-bot==20.5 openai

Set the .env like this:

AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_VERSION=2025-04-01-preview
TELEGRAM_SUM_BOT_TOKEN=your_telegram_bot_key_here
