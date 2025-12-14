import requests
import json
import logging
import time
import threading
from datetime import datetime
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os

# ==================== WEB SERVER (KEEP ALIVE) ====================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def start_web_server():
    t = threading.Thread(target=run_web_server)
    t.start()

# ==================== CONFIGURATION ====================

API_BASE = "https://anishexploits.site/api/api.php?key=exploits&num="
# REPLACE THIS WITH YOUR NEW TOKEN
BOT_TOKEN = "YOUR_NEW_TOKEN_HERE" 

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Termux) Gecko/117.0 Firefox/117.0",
    "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8",
    "Referer": "https://oliver-exploits.vercel.app/",
    "Connection": "keep-alive"
}

# ==================== BOT SETUP ====================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==================== WELCOME MESSAGE ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "👋 *WELCOME TO OLIVER EXPLOITS*\n\n" 
    
    keyboard = [[KeyboardButton("📞 ENTER NUMBER")]]  
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)  
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

# ==================== HANDLE BUTTON CLICK ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "📞 ENTER NUMBER":
        await update.message.reply_text("📤 *Send Your 10-digit Number Without +91:*", parse_mode='Markdown')  
    else:  
        await process_number(update, context)

# ==================== PROCESS NUMBER ====================

async def process_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.message.text.strip()
    
    if not number.isdigit() or len(number) != 10:  
        await update.message.reply_text("❌ *INVALID INPUT*\nPlease send 10-digit number only.", parse_mode='Markdown')  
        return  
    
    processing_msg = await update.message.reply_text("🔍 *Scanning Database...*", parse_mode='Markdown')  
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")  
    time.sleep(2)  
    
    result = await search_number_api(number)  
    
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=processing_msg.message_id)  
    
    await update.message.reply_text(result, parse_mode='Markdown')

# ==================== API CALL FUNCTION ====================

async def search_number_api(number):
    url = f"{API_BASE}{number}"
    
    try:  
        response = requests.get(url, headers=HEADERS, timeout=30)
        
        if response.status_code != 200:  
            return "❌ DATABASE ERROR: Server connection failed."
        
        try:
            data = response.json()
        except:
            return "❌ DATA ERROR: Invalid response format."
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_data, record_count = extract_user_data(data)
        
        if user_data:
            return format_cybersecurity_report(user_data, number, record_count, current_time)
        else:
            return "⚠️ NO INFORMATION FOUND"
        
    except Exception as e:  
        return "❌ SYSTEM ERROR"

# ==================== DATA EXTRACTION ====================

def extract_user_data(data):
    user_data = None
    record_count = 1
    
    if isinstance(data, dict) and data.get('success') and data.get('result'):
        results = data.get('result', [])
        if results:
            user_data = results[0]
            record_count = len(results)
    elif isinstance(data, dict) and (data.get('mobile') or data.get('name')):
        user_data = data
    elif isinstance(data, list) and len(data) > 0:
        user_data = data[0]
        record_count = len(data)
    elif isinstance(data, dict) and data.get('status') == 'success':
        user_data = data.get('data', {})
    
    return user_data, record_count

# ==================== REPORT FORMATTING ====================

def format_cybersecurity_report(user_data, number, record_count, current_time):
    phone = user_data.get('mobile', number)
    alt = user_data.get('alt_mobile')
    aadhar = user_data.get('id_number', user_data.get('aadhar'))
    name = user_data.get('name', 'None')
    father = user_data.get('father_name', 'None')
    address = user_data.get('address', '')
    circle = user_data.get('circle', '')
    
    if address:
        address = address.replace('!', ' ').replace('|', ' ').replace('NA', '').replace('l\'', '')
        address = ' '.join(address.split())
    
    report = "🛡️ OLIVER EXPLOITS REPORT 🛡️\n\n"
    report += f"👤 Name: {name}\n"
    report += f"👨‍👦 Father: {father}\n"
    report += f"📞 Mobile: {phone}\n"
    report += f"📍 Circle: {circle}\n"
    if address: report += f"🏠 Address: {address}\n"
    if aadhar: report += f"🪪 Aadhar: {aadhar}\n"
    report += f"📡 Network: {circle}\n\n"
    report += "🔐 END OF REPORT"
    
    return report

# ==================== MAIN FUNCTION ====================

if __name__ == "__main__":
    # Start the web server in a separate thread
    start_web_server()
    
    print("🤖 Bot Starting...")
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Run the bot
    application.run_polling()