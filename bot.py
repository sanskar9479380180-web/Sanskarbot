import os
import sqlite3
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = 8468468528

FORCE_CHANNELS = [
    {"name": "📁 ꜰʀᴇᴇ ꜰɪʟᴇꜱ 1", "id": -1003967488577, "url": "https://t.me/+OTdUhcRbnVU5MzA1"},
    {"name": "📁 ꜰʀᴇᴇ ꜰɪʟᴇꜱ 2", "id": -1003992590332, "url": "https://t.me/+YAKn7VX2SkBkMjc1"},
    {"name": "📁 ꜰʀᴇᴇ ꜰɪʟᴇꜱ 3", "id": -1004334984541, "url": "https://t.me/+4ltNAkvNeOAyNDFl"},
]

WELCOME_TEXT = (
    "ʜᴇʏ *ꜱᴀɴꜱᴋᴀʀ* ʜᴇʀᴇ!! 🔥\n"
    "━━━━━━━━━━━━━━━━━━\n\n"
    "ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ *ꜱᴀɴꜱᴋᴀʀ ꜰɪʟᴇ'ꜱ* ⚡\n\n"
    "📌 ᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴀʟʟ ᴍʏ ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟꜱ\n"
    "✅ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴠᴇʀɪꜰʏ\n\n"
    "━━━━━━━━━━━━━━━━━━"
)

DB = "/tmp/sanskarfiles.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, verified INTEGER DEFAULT 0)")
    c.execute("CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, file_id TEXT, size TEXT, uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    c.execute("CREATE TABLE IF NOT EXISTS pending_upload (admin_id INTEGER PRIMARY KEY, name TEXT)")
    conn.commit()
    conn.close()

def add_user(uid, un, fn):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (id, username, first_name) VALUES (?, ?, ?)", (uid, un, fn))
    conn.commit()
    conn.close()

def is_verified(uid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT verified FROM users WHERE id = ?", (uid,))
    r = c.fetchone()
    conn.close()
    return r and r[0] == 1

def set_verified(uid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE users SET verified = 1 WHERE id = ?", (uid,))
    conn.commit()
    conn.close()

def add_file(name, file_id, size):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO files (name, file_id, size) VALUES (?, ?, ?)", (name, file_id, size))
    conn.commit()
    conn.close()

def get_all_files():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, name, size FROM files ORDER BY id DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()
    return rows

def get_file(fid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT name, file_id, size FROM files WHERE id = ?", (fid,))
    row = c.fetchone()
    conn.close()
    return row

def delete_file(fid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM files WHERE id = ?", (fid,))
    conn.commit()
    conn.close()

def set_pending(admin_id, name):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO pending_upload (admin_id, name) VALUES (?, ?)", (admin_id, name))
    conn.commit()
    conn.close()

def get_pending(admin_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT name FROM pending_upload WHERE admin_id = ?", (admin_id,))
    row = c.fetchone()
    conn.close()
    return row

def clear_pending(admin_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM pending_upload WHERE admin_id = ?", (admin_id,))
    conn.commit()
    conn.close()

def total_files():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM files")
    n = c.fetchone()[0]
    conn.close()
    return n

async def check_join(ctx, uid):
    nj = []
    for ch in FORCE_CHANNELS:
        try:
            m = await ctx.bot.get_chat_member(ch["id"], uid)
            if m.status in ["left", "kicked"]:
                nj.append(ch)
        except:
            continue
    return nj

def join_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(FORCE_CHANNELS[0]["name"], url=FORCE_CHANNELS[0]["url"]),
         InlineKeyboardButton(FORCE_CHANNELS[1]["name"], url=FORCE_CHANNELS[1]["url"])],
        [InlineKeyboardButton(FORCE_CHANNELS[2]["name"], url=FORCE_CHANNELS[2]["url"]),
         InlineKeyboardButton("✅ ᴠᴇʀɪꜰʏ", callback_data="verify")],
    ])

def files_kb():
    files = get_all_files()
    if not files:
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔄 ʀᴇꜰʀᴇꜱʜ", callback_data="files")]])
    kb = []
    for f in files[:20]:
        kb.append([InlineKeyboardButton(f"📄 {f[1]} ({f[2]})", callback_data=f"get_{f[0]}")])
    kb.append([InlineKeyboardButton("🔄 ʀᴇꜰʀᴇꜱʜ", callback_data="files")])
    return InlineKeyboardMarkup(kb)

def files_text():
    return (
        "📁 *ꜱᴀɴꜱᴋᴀʀ ꜰɪʟᴇ'ꜱ*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 ᴛᴏᴛᴀʟ ꜰɪʟᴇꜱ: `{total_files()}`\n\n"
        "👇 ᴄʟɪᴄᴋ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ:"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    add_user(u.id, u.username, u.first_name)
    if is_verified(u.id):
        await update.message.reply_text(files_text(), parse_mode="Markdown", reply_markup=files_kb())
    else:
        await update.message.reply_text(WELCOME_TEXT, parse_mode="Markdown", reply_markup=join_kb())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    u = q.from_user
    if q.data == "verify":
        nj = await check_join(context, u.id)
        if nj:
            names = ", ".join([c["name"] for c in nj])
            await q.edit_message_text(f"⚠️ Pehle yeh channels join karo:\n{names}", reply_markup=join_kb())
        else:
            set_verified(u.id)
            await q.edit_message_text(files_text(), parse_mode="Markdown", reply_markup=files_kb())
    elif q.data == "files":
        await q.edit_message_text(files_text(), parse_mode="Markdown", reply_markup=files_kb())
    elif q.data.startswith("get_"):
        fid = int(q.data[4:])
        f = get_file(fid)
        if not f:
            await q.answer("❌ File not found", show_alert=True)
            return
        name, file_id, size = f
        try:
            await context.bot.send_document(chat_id=u.id, document=file_id,
                                            caption=f"📄 *{name}*\n📦 {size}\n\n📁 *ꜱᴀɴꜱᴋᴀʀ ꜰɪʟᴇ'ꜱ*",
                                            parse_mode="Markdown")
            await q.answer("✅ Sent!")
        except Exception as e:
            await q.answer(f"❌ Error: {e}", show_alert=True)

async def addfile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: `/addfile <name>`", parse_mode="Markdown")
        return
    name = " ".join(context.args)
    set_pending(update.effective_user.id, name)
    await update.message.reply_text(f"✅ Setup OK\n📄 `{name}`\n\n👇 Ab file bhej", parse_mode="Markdown")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    doc = update.message.document
    file_id = doc.file_id
    pending = get_pending(update.effective_user.id)
    if pending:
        name = pending[0]
        clear_pending(update.effective_user.id)
    else:
        name = doc.file_name or "File"
    size_bytes = doc.file_size or 0
    size = f"{size_bytes / 1024:.1f} KB" if size_bytes < 1024*1024 else f"{size_bytes / (1024*1024):.1f} MB"
    add_file(name, file_id, size)
    await update.message.reply_text(f"✅ File added!\n📄 {name}\n📦 {size}\n\n📁 Total: `{total_files()}`", parse_mode="Markdown")

async def listfiles_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    files = get_all_files()
    if not files:
        await update.message.reply_text("❌ No files.")
        return
    text = f"📁 *Total: {total_files()}*\n\n"
    for f in files:
        text += f"`{f[0]}` | {f[1]} | {f[2]}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def delfile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        return
    try:
        delete_file(int(context.args[0]))
        await update.message.reply_text(f"✅ Deleted #{context.args[0]}")
    except:
        await update.message.reply_text("❌ Invalid ID")

async def stats_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    t = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE verified = 1")
    v = c.fetchone()[0]
    conn.close()
    await update.message.reply_text(f"📊 Users: {t}\n✅ Verified: {v}\n📁 Files: {total_files()}")

async def broadcast_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        return
    msg = " ".join(context.args)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id FROM users")
    us = c.fetchall()
    conn.close()
    s = 0
    for u in us:
        try:
            await context.bot.send_message(u[0], msg)
            s += 1
        except:
            pass
    await update.message.reply_text(f"✅ Sent to {s}")

async def files_cmd(update, context):
    if not is_verified(update.effective_user.id):
        await update.message.reply_text("❌ Join channels first.", reply_markup=join_kb())
        return
    await update.message.reply_text(files_text(), parse_mode="Markdown", reply_markup=files_kb())

async def run_bot():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("files", files_cmd))
    app.add_handler(CommandHandler("addfile", addfile_cmd))
    app.add_handler(CommandHandler("listfiles", listfiles_cmd))
    app.add_handler(CommandHandler("delfile", delfile_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(button))
    print("Sanskar File's bot chal raha hai...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(run_bot())
