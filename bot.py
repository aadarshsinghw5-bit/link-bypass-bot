import asyncio
import os
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from database import Database
from bypass import SafeRedirectResolver

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
PORT = int(os.getenv("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")
if not OWNER_ID:
    raise RuntimeError("OWNER_ID is missing")

db = Database()
resolver = SafeRedirectResolver()
URL_REGEX = re.compile(r"https?://[^\s<>\"]+", re.IGNORECASE)


def extract_url(text: str):
    if not text:
        return None
    match = URL_REGEX.search(text)
    return match.group(0).rstrip(".,!?)]}") if match else None


def is_admin(user_id: int):
    return user_id == OWNER_ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message:
        return
    db.add_user(user)
    if db.is_banned(user.id):
        await update.message.reply_text("🚫 You are banned from using this bot.")
        return
    await update.message.reply_text(
        "ʜɪ ᴛʜᴇʀᴇ! 👋\n\n"
        "🔗 Send me a shortened/public redirect link "
        "and I'll try to resolve its final destination.\n\n"
        "⚡ Fast • Simple • Automatic"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 <b>How to use</b>\n\n"
        "Just send me a URL and I'll try to resolve ordinary HTTP redirects.\n\n"
        "⚠️ Links requiring CAPTCHA, login, anti-bot challenges, or "
        "other access controls are not bypassed.",
        parse_mode=ParseMode.HTML,
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not is_admin(user.id):
        return
    await update.message.reply_text(
        f"📊 <b>Users:</b> <code>{db.user_count()}</code>",
        parse_mode=ParseMode.HTML,
    )


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not is_admin(user.id):
        return
    if not context.args:
        await update.message.reply_text("Usage:\n<code>/ban USER_ID</code>", parse_mode=ParseMode.HTML)
        return
    try:
        target = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")
        return
    db.ban_user(target)
    await update.message.reply_text(f"🚫 User <code>{target}</code> banned.", parse_mode=ParseMode.HTML)


async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not is_admin(user.id):
        return
    if not context.args:
        await update.message.reply_text("Usage:\n<code>/unban USER_ID</code>", parse_mode=ParseMode.HTML)
        return
    try:
        target = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")
        return
    db.unban_user(target)
    await update.message.reply_text(f"✅ User <code>{target}</code> unbanned.", parse_mode=ParseMode.HTML)


async def resolve_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    if not user or not message:
        return

    db.add_user(user)
    if db.is_banned(user.id):
        await message.reply_text("🚫 You are banned from using this bot.")
        return

    url = extract_url(message.text or message.caption)
    if not url:
        await message.reply_text("❌ Please send a valid HTTP/HTTPS link.")
        return

    status = await message.reply_text("🔄 <b>Processing your link...</b>", parse_mode=ParseMode.HTML)

    try:
        final_url = await resolver.resolve(url)
        if final_url == url:
            text = f"ℹ️ No redirect detected.\n\n🔗 <b>Link:</b>\n{final_url}"
        else:
            text = (
                "✅ <b>Destination found!</b>\n\n"
                f"🔗 <b>Original:</b>\n{url}\n\n"
                f"🎯 <b>Destination:</b>\n{final_url}"
            )
        await status.edit_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as exc:
        print("Resolver error:", repr(exc))
        await status.edit_text(
            "❌ <b>Unable to resolve this link.</b>\n\n"
            "The website may require JavaScript, authentication, CAPTCHA, "
            "anti-bot protection, or another unsupported mechanism.",
            parse_mode=ParseMode.HTML,
        )


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'{"status":"ok","service":"link-bypass-bot"}'
        self.send_response(200 if self.path in ("/", "/health") else 404)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.path in ("/", "/health"):
            self.wfile.write(body)

    def log_message(self, format, *args):
        return


def run_health_server():
    HTTPServer(("0.0.0.0", PORT), HealthHandler).serve_forever()


def main():
    threading.Thread(target=run_health_server, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, resolve_link))
    app.add_handler(MessageHandler(filters.CAPTION, resolve_link))

    print("🤖 Bot started.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
