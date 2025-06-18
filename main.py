from telegram.ext import Application, CommandHandler
import os

async def start(update, context):
    await update.message.reply_text("👋 Бот Stargram активирован! Он работает только для передачи данных сайту.")

def main():
    app = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == '__main__':
    main()
