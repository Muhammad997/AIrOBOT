
import os, sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from google import genai

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

db = sqlite3.connect("husnanai.db", check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT)")

SYSTEM = """
Kamu adalah HusnanAi.
X: @husnan97
Telegram: @Qomaroen
Instagram: @husnan.eth
Jawab dalam bahasa Indonesia.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    db.execute("INSERT OR REPLACE INTO users(id,username) VALUES(?,?)",(u.id,u.username))
    db.commit()
    await update.message.reply_text("Halo, saya HusnanAi. Gunakan /about untuk info bot.")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 HusnanAi\nX: @husnan97\nTelegram: @Qomaroen\nInstagram: @husnan.eth")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{SYSTEM}\n\nPengguna: {text}"
    )
    await update.message.reply_text(response.text)

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("about", about))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
app.run_polling()


# HusnanAi V3 patch
