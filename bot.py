import logging
import threading
import asyncio
import os
import time
from datetime import datetime
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import cloudscraper  # Import the fix for Cloudflare

# ==================== WEB SERVER (KEEP ALIVE) ====================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running on Render!"

def run_web_server():
    # Render assigns a port automatically via environment variable
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def start_web_server():
    t = threading.Thread(target=run_web_server, daemon=True)
    t.start()

# ==================== CONFIGURATION ====================

API_BASE = "https://anishexploits.site/api/api.php?key=exploits&num="
BOT_TOKEN = "8372266918:AAFOsz7LZc9d20dNeZCSwza5N_nDCHE2iA8"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Referer": "https://oliver-exploits.vercel.app/"
}

# ==================== BOT SETUP ====================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "👋 *WELCOME TO OLIVER EXPLOITS*\n\n" \
                   "🛡️ *Cybersecurity Data Scanner*\n" \
                   "Click the button below to start."
    
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
    
    # Use asyncio.sleep to simulate processing and avoid blocking
    await asyncio.sleep(1)  
    
    result = await search_number_api(number)  
    
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=processing_msg.message_id)  
    await update.message.reply_text(result, parse_mode='Markdown')

# ==================== API LOGIC (FIXED) ====================

async def search_number_api(number):
    url = f"{API_BASE}{number}"
    
    try:
        # Use cloudscraper to bypass Cloudflare protection on the API
        scraper = cloudscraper.create_scraper()
        
        loop = asyncio.get_event_loop()
        # Run scraper in executor to prevent blocking the bot
        response = await loop.run_in_executor(None, lambda: scraper.get(url, headers=HEADERS, timeout=30))
        
        if response.status_code != 200:
            logging.error(f"API Error: {response.status_code} - {response.text}")
            return f"❌ *SERVER ERROR*: The API rejected the request ({response.status_code})."
        
        try:
            data = response.json()
        except:
            return "❌ *DATA ERROR*: Invalid JSON received from API."
        
        if isinstance(data, dict) and data.get('success') is False:
             return f"⚠️ *API KEY ERROR*: {data.get('msg', 'Invalid Key or Quota Over')}"

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_data, record_count = extract_user_data(data)
        
        if user_data:
            return format_cybersecurity_report(user_data, number, record_count, current_time)
        else:
            return "⚠️ *NO DATA FOUND*: Number not in database."
            
    except Exception as e:
        logging.error(f"System Error: {e}")
        return "❌ *SYSTEM ERROR*: Connection failed. Try again later."

def extract_user_data(data):
    user_data = None
    record_count = 0
    
    if isinstance(data, dict) and data.get('success') and data.get('result'):
        results = data.get('result', [])
        if results:
            user_data = results[0]
            record_count = len(results)
    elif isinstance(data, dict) and (data.get('mobile') or data.get('name')):
        user_data = data
        record_count = 1
    elif isinstance(data, list) and len(data) > 0:
        user_data = data[0]
        record_count = len(data)
    elif isinstance(data, dict) and data.get('status') == 'success':
        user_data = data.get('data', {})
        record_count = 1
    
    return user_data, record_count

def format_cybersecurity_report(user_data, number, record_count, current_time):
    phone = user_data.get('mobile', number)
    alt = user_data.get('alt_mobile', None)
    email = user_data.get('email', None)
    aadhar = user_data.get('id_number') or user_data.get('aadhar') or user_data.get('uid')
    name = user_data.get('name', 'Unknown')
    father = user_data.get('father_name', 'Not Available')
    address = user_data.get('address', '')
    circle = user_data.get('circle', 'Unknown')
    
    if address:
        address = address.replace('!', ' ').replace('|', ' ').replace('NA', '').replace("l'", "")
        address = ' '.join(address.split())
    else:
        address = "Not Available"

    network = 'Unknown'
    circle_upper = circle.upper() if circle else ""
    if 'JIO' in circle_upper: network = 'JIO 4G/5G'
    elif 'AIRTEL' in circle_upper: network = 'AIRTEL'
    elif 'VI' in circle_upper or 'VODAFONE' in circle_upper: network = 'VI (Vodafone-Idea)'
    elif 'BSNL' in circle_upper: network = 'BSNL'
    
    score = 0
    if name and name != 'Unknown': score += 1
    if father and father != 'Not Available': score += 1
    if address and address != 'Not Available': score += 1
    if aadhar: score += 2
    if alt: score += 1
    
    if score >= 4: risk_emoji, exposure = "🔴", "CRITICAL"
    elif score >= 2: risk_emoji, exposure = "🟠", "HIGH"
    else: risk_emoji, exposure = "🟡", "MODERATE"

    report = f"🛡️ *OLIVER EXPLOITS INTELLIGENCE* 🛡️\n\n"
    report += f"👤 *TARGET PROFILE*\n├ Name: `{name}`\n├ Father: `{father}`\n└ Circle: {circle}\n\n"
    report += f"📞 *CONTACT VECTORS*\n├ Mobile: `+91-{phone}`\n"
    if alt: report += f"├ Alt Num: `{alt}`\n"
    if email: report += f"├ Email: `{email}`\n"
    report += f"└ Network: {network}\n\n"
    report += f"📍 *LOCATION*\n├ Address: `{address}`\n└ Country: India 🇮🇳\n\n"
    if aadhar: report += f"🪪 *DOCUMENTS*\n└ Aadhar/ID: `{aadhar}`\n\n"
    report += f"📊 *RISK*: {risk_emoji} {exposure}\n"
    report += f"🔐 _System provided by Oliver Exploits_"

    return report

# ==================== MAIN ====================

if __name__ == "__main__":
    start_web_server()
    print("🚀 Bot Started Successfully")
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling(allowed_updates=Update.ALL_TYPES)
