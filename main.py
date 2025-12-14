import requests
import logging
import threading
import asyncio
import os
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==================== WEB SERVER (KEEP ALIVE) ====================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def start_web_server():
    # daemon=True ensures that if the Bot crashes, the Web Server dies too
    # so Render can restart the whole app.
    t = threading.Thread(target=run_web_server, daemon=True)
    t.start()

# ==================== CONFIGURATION ====================

API_BASE = "https://anishexploits.site/api/api.php?key=exploits&num="

# ⚠️ PASTE YOUR NEW TOKEN INSIDE THE QUOTES BELOW ⚠️
BOT_TOKEN = "8372266918:AAFOsz7LZc9d20dNeZCSwza5N_nDCHE2iA8" 

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Termux) Gecko/117.0 Firefox/117.0",
    "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8",
    "Referer": "https://oliver-exploits.vercel.app/",
    "Connection": "keep-alive"
}

# ==================== BOT SETUP ====================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "👋 *WELCOME TO OLIVER EXPLOITS*"
    keyboard = [[KeyboardButton("📞 ENTER NUMBER")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📞 ENTER NUMBER":
        await update.message.reply_text("📤 *Send Your 10-digit Number Without +91:*", parse_mode='Markdown')
    else:
        await process_number(update, context)

async def process_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.message.text.strip()
    
    if not number.isdigit() or len(number) != 10:
        await update.message.reply_text("❌ *INVALID INPUT*\nPlease send 10-digit number only.", parse_mode='Markdown')
        return
    
    processing_msg = await update.message.reply_text("🔍 *Scanning Database...*", parse_mode='Markdown')
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # FIXED: Use asyncio.sleep instead of time.sleep to prevent freezing
    await asyncio.sleep(2)
    
    result = await search_number_api(number)
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=processing_msg.message_id)
    await update.message.reply_text(result, parse_mode='Markdown')

async def search_number_api(number):
    url = f"{API_BASE}{number}"
    try:
        # Running blocking request in executor to prevent lag
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: requests.get(url, headers=HEADERS, timeout=30))
        
        if response.status_code != 200: return "❌ DATABASE ERROR"
        try: data = response.json()
        except: return "❌ DATA ERROR"
        
        user_data, record_count = extract_user_data(data)
        if user_data:
            return format_report(user_data, number)
        else:
            return "⚠️ NO INFORMATION FOUND"
    except Exception as e:
        return "❌ SYSTEM ERROR"

def extract_user_data(data):
    user_data = None
    if isinstance(data, dict) and data.get('success') and data.get('result'):
        results = data.get('result', [])
        if results: user_data = results[0]
    elif isinstance(data, dict) and (data.get('mobile') or data.get('name')):
        user_data = data
    elif isinstance(data, list) and len(data) > 0:
        user_data = data[0]
    return user_data, 1

def format_report(user_data, number):
    phone = user_data.get('mobile', number)
    name = user_data.get('name', 'None')
    father = user_data.get('father_name', 'None')
    address = user_data.get('address', 'None')
    
    return f"🛡️ *OLIVER REPORT*\n\n👤 Name: {name}\n👨‍👦 Father: {father}\n📞 Mobile: {phone}\n🏠 Address: {address}\n\n🔐 END REPORT"

if __name__ == "__main__":
    start_web_server()
    print("🚀 Bot is starting...")
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()
