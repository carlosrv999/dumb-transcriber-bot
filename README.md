# Dumb Transcriber Bot

**Act as an expert Python developer.** Please write a complete Python script for a stateless Telegram bot that transcribes audio messages to text.
**Context & Environment:**

- The project is already initialized using `uv` with **Python 3.14**. Do not provide project setup commands; only provide the required dependencies and the Python code.
- Use `python-dotenv` to load environment variables from a `.env` file.
- Use `python-telegram-bot`.
- No heavy frameworks like LangChain or LangGraph are needed or allowed.

**Core Requirements:**

1. **Stateless Architecture:** The bot must have absolutely zero conversational memory or database storage.
2. **Strict Whitelist:** The bot must only process messages from a predefined list of allowed Telegram User IDs (provided via a comma-separated list in the `ALLOWED_TELEGRAM_IDS` environment variable). Silently ignore messages from unauthorized users.
3. **Input Filtering:** \* The bot must only process Telegram `voice` (voice notes) and `audio` (audio files) message types.

- If an allowed user sends _any_ other type of message (text, image, video, sticker, etc.), the bot must immediately reply with the exact string: _"Only audio messages are allowed"_.

4. **Transcription (Groq API):**

- Download the received audio/voice file temporarily to the local disk.
- Send the audio file to the Groq API using the official Groq Python SDK.
- Model required: `whisper-large-v3-turbo`.
- Configure the API call to auto-detect whether the language is English or Spanish.
- **CRITICAL:** Ensure the temporary local audio file is deleted immediately after the Groq API call completes to prevent disk leaks.

5. **Output Formatting:** The bot's reply must be the _exact_ transcribed text, completely straightforward. Do not add conversational filler, quotation marks, or prefixes. If the audio says "Hello, I am Carlos", the bot must reply strictly with: `Hello, I am Carlos`.
