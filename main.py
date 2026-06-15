import os
import tempfile
from dotenv import load_dotenv
from groq import Groq
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Load environment variables
load_dotenv(override=True)

# ----------------------------------------------------------------------
# Initialization & Configuration
# ----------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set in environment")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set in environment")

groq_client = Groq(api_key=GROQ_API_KEY)

# Load allowlist
_raw_ids = os.getenv("ALLOWED_TELEGRAM_IDS", "")
ALLOWED_TELEGRAM_IDS: set[int] = {
    int(uid.strip()) for uid in _raw_ids.split(",") if uid.strip()
}


def is_authorized(user_id: int) -> bool:
    """Check if the user is in the strict whitelist."""
    return user_id in ALLOWED_TELEGRAM_IDS


# ----------------------------------------------------------------------
# Core Message Handler
# ----------------------------------------------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stateless handler for all incoming Telegram messages."""
    if not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id

    # 1. Strict Whitelist: Silently ignore unauthorized users
    if not is_authorized(user_id):
        return

    # 2. Input Filtering: Require voice or audio
    audio_attachment = update.message.voice or update.message.audio

    if not audio_attachment:
        # Authorized user sent a text, image, sticker, etc.
        await update.message.reply_text("Only audio messages are allowed")
        return

    # 3. Send "Transcribing..." placeholder message
    status_message = await update.message.reply_text("Transcribing... ⏳")

    # 4. Temporary File Handling & Transcription
    temp_file_path = ""
    try:
        # Create a physical temporary file.
        ext = ".ogg" if update.message.voice else ".mp3"
        fd, temp_file_path = tempfile.mkstemp(suffix=ext)
        os.close(fd)

        # Download directly to the local disk
        telegram_file = await context.bot.get_file(audio_attachment.file_id)
        await telegram_file.download_to_drive(custom_path=temp_file_path)

        # Send to Groq API
        with open(temp_file_path, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=(os.path.basename(temp_file_path), audio_file.read()),
                model="whisper-large-v3-turbo",
            )

        # 5. Output Formatting: Raw transcription, no filler
        transcribed_text = (
            transcription.text.strip()
            if hasattr(transcription, "text")
            else str(transcription).strip()
        )

        if transcribed_text:
            # Edit the placeholder message with the final text
            await status_message.edit_text(transcribed_text)
        else:
            # If the audio was completely silent, delete the placeholder
            await status_message.delete()

    except Exception as e:
        print(f"Transcription error for user {user_id}: {e}")
        # If an error occurs, delete the placeholder so it doesn't stay stuck forever
        try:
            await status_message.delete()
        except Exception as delete_error:
            print(f"Could not delete status message: {delete_error}")

    finally:
        # 6. CRITICAL: Guarantee local disk cleanup
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError as e:
                print(f"Failed to delete temporary file {temp_file_path}: {e}")


# ----------------------------------------------------------------------
# Application Entry Point
# ----------------------------------------------------------------------
def main():
    print("🚀 Starting Dumb Transcriber Bot...")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(MessageHandler(filters.ALL, handle_message))

    # Run polling
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
