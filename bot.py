import os
import sqlite3
import time
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from google import genai

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

# ==========================
# DATABASE
# ==========================

db = sqlite3.connect("husnanai.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    username TEXT,
    total_messages INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS memory(
    user_id INTEGER,
    role TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

db.commit()

# ==========================
# SYSTEM PROMPT
# ==========================

SYSTEM = """
Kamu adalah HusnanAi V4.

Owner:
X: @husnan97
Telegram: @Qomaroen
Instagram: @husnan.eth

Karakter:
- Ramah
- Santai
- Lucu jika diperlukan
- Ahli Crypto
- Ahli Telegram Bot
- Ahli Python

Jawab menggunakan bahasa Indonesia.
"""

# ==========================
# MEMORY FUNCTIONS
# ==========================

def save_memory(user_id, role, content):
    cursor.execute(
        "INSERT INTO memory(user_id,role,content) VALUES(?,?,?)",
        (user_id, role, content)
    )
    db.commit()

def get_memory(user_id, limit=10):
    cursor.execute("""
        SELECT role,content
        FROM memory
        WHERE user_id=?
        ORDER BY rowid DESC
        LIMIT ?
    """, (user_id, limit))

    rows = cursor.fetchall()

    history = ""

    for role, content in reversed(rows):
        history += f"{role}: {content}\n"

    return history

# ==========================
# COMMANDS
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    cursor.execute("""
    INSERT OR REPLACE INTO users(id,username)
    VALUES(?,?)
    """, (user.id, user.username))

    db.commit()

    await update.message.reply_text(
        f"👋 Halo {user.first_name}\n\n"
        "Saya HusnanAi V4.\n"
        "Ketik apa saja untuk mulai ngobrol."
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """
🤖 HusnanAi V4

X : @husnan97
Telegram : @Qomaroen
Instagram : @husnan.eth

Powered by Gemini AI
        """
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total_messages) FROM users")
    total_messages = cursor.fetchone()[0] or 0

    await update.message.reply_text(
        f"""
📊 Statistik

👥 Users : {total_users}
💬 Messages : {total_messages}
        """
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    cursor.execute(
        "DELETE FROM memory WHERE user_id=?",
        (uid,)
    )

    db.commit()

    await update.message.reply_text(
        "🧠 Memori percakapan berhasil dihapus."
    )

# ==========================
# CHAT
# ==========================

user_cooldown = {}

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    uid = user.id

    text = update.message.text

    # Anti spam
    now = time.time()

    if uid in user_cooldown:
        if now - user_cooldown[uid] < 1:
            return

    user_cooldown[uid] = now

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    save_memory(uid, "user", text)

    history = get_memory(uid)

    prompt = f"""
{SYSTEM}

Riwayat Percakapan:
{history}

User: {text}
"""

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        answer = response.text

        save_memory(uid, "assistant", answer)

        cursor.execute("""
        UPDATE users
        SET total_messages = total_messages + 1
        WHERE id=?
        """, (uid,))
        db.commit()

        if len(answer) > 4096:
            for i in range(0, len(answer), 4000):
                await update.message.reply_text(answer[i:i+4000])
        else:
            await update.message.reply_text(answer)

    except Exception as e:
        await update.message.reply_text(
            f"❌ Error:\n{str(e)}"
        )

# ==========================
# ERROR HANDLER
# ==========================

async def error_handler(update, context):
    print("ERROR:", context.error)

# ==========================
# APP
# ==========================

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("about", about))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("reset", reset))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        chat
    )
)

app.add_error_handler(error_handler)

print("✅ HusnanAi V4 Online")

app.run_polling()
