import asyncio
import time
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.error import TelegramError

BOT_TOKEN = '9101768316:AAE_Co72HbAwcc84QwmjZKc-Xedh24QOkFA'
CHANNEL_ID = '@SeptionFreeTool' 
CHANNEL_LINK = 'https://t.me/SeptionFreeTool'
ADMIN_ID = 9129058938  

ACCESS_DURATION = 24 * 60 * 60

generated_keys = set()
authorized_users = {}
user_data = {}

AVAILABLE_EMOJIS = ["🔥", "🤡", "❤️", "💯", "🤩", "😈", "💩", "👍", "👎", "🎉", "⚡", "🥰", "😭", "🤯", "🤬", "👏", "🙏", "🕊", "🦄", "🍌"]

def generate_random_key():
    return "SEPTION-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def is_authorized(user_id):
    if user_id in authorized_users:
        if time.time() < authorized_users[user_id]:
            return True
        else:
            del authorized_users[user_id]
    return False

async def check_membership(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except TelegramError:
        return False

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
        
    new_key = generate_random_key()
    generated_keys.add(new_key)
    
    await update.message.reply_text(
        f"✅ **New Access Key Generated**\n\n"
        f"Key: `{new_key}`\n\n"
        f"Send this to the user who wants to avail the service.",
        parse_mode='Markdown'
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    is_joined = await check_membership(user_id, context)
    if not is_joined:
        keyboard = [
            [InlineKeyboardButton("Join Channel First ✅", url=CHANNEL_LINK)],
            [InlineKeyboardButton("Verify Join 🔄", callback_data='verify_join')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = (
            "⚠️ **ACCESS DENIED**\n\n"
            "You must join our official channel first before using this bot.\n\n"
            "1️⃣ Tap 'Join Channel First' below.\n"
            "2️⃣ After joining, tap 'Verify Join'."
        )
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        return

    if is_authorized(user_id):
        await update.message.reply_text("✅ You are already logged in. Type /menu to start.")
        return

    text = (
        "✨ **SEPTION** ✨\n\n"
        "Welcome to the ultimate reaction booster!\n\n"
        "To access the bot, you need a valid **Access Key**.\n"
        "If you don't have one, please contact the admin to purchase or request a free trial.\n\n"
        "👉 Simply type your Access Key in this chat."
    )
    await update.message.reply_text(text, parse_mode='Markdown')

async def verify_join_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    is_joined = await check_membership(user_id, context)
    if is_joined:
        await query.message.edit_text("✅ Verification successful! You have joined the channel.")
        await asyncio.sleep(1)
        text = (
            "✨ **SEPTION** ✨\n\n"
            "To access the bot, you need a valid **Access Key**.\n"
            "If you don't have one, please contact the admin to purchase or request a free trial.\n\n"
            "👉 Simply type your Access Key in this chat."
        )
        await query.message.reply_text(text, parse_mode='Markdown')
    else:
        await query.answer("❌ You haven't joined the channel yet. Please join first.", show_alert=True)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    
    if not is_authorized(user_id):
        if text in generated_keys:
            generated_keys.remove(text)
            authorized_users[user_id] = time.time() + ACCESS_DURATION
            await update.message.reply_text("✅ **Access Granted!** Valid for 24 hours. Type /menu to begin.")
            await show_menu(update, context)
        else:
            await update.message.reply_text("❌ Invalid or expired Access Key.")
        return
        
    if user_id not in user_data or 'emoji' not in user_data[user_id] or 'speed' not in user_data[user_id]:
        await update.message.reply_text("⚠️ Please type /menu and select an emoji & speed first.")
        return
        
    parts = text.split()
    if len(parts) != 2:
        await update.message.reply_text("❌ Invalid format. Use: `<link> <amount>`", parse_mode='Markdown')
        return
        
    link, count_str = parts
    emoji = user_data[user_id]['emoji']
    speed = user_data[user_id]['speed']
    
    try:
        count = int(count_str)
        if count > 1000:
            await update.message.reply_text("⚠️ Max limit is 1000.")
            return
    except ValueError:
        await update.message.reply_text("❌ Amount must be a number.")
        return
        
    speed_text = "Fast ⚡" if speed == 'fast' else "Slow 🐢"
    status_msg = await update.message.reply_text(f"⏳ Starting {speed_text} boost for {emoji}...")
    context.application.create_task(run_boost(update, context, link, count, emoji, speed, status_msg))

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("⚠️ Your access has expired or is invalid. Please enter an Access Key.")
        return

    keyboard = []
    row = []
    for em in AVAILABLE_EMOJIS:
        row.append(InlineKeyboardButton(em, callback_data=f'emoji_{em}'))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "✅ **Access Verified**\n\nSelect an emoji for the boost:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_tap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'verify_join':
        await verify_join_button(update, context)
        return

    user_id = query.from_user.id
    if not is_authorized(user_id):
        await query.answer("Access expired. Please enter your Access Key.", show_alert=True)
        return

    data = query.data
    if data.startswith('emoji_'):
        chosen_emoji = data.split('_')[1]
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['emoji'] = chosen_emoji
        
        speed_keyboard = [
            [InlineKeyboardButton("Fast ⚡ (Risky)", callback_data='speed_fast'), InlineKeyboardButton("Slow 🐢 (Safe)", callback_data='speed_slow')]
        ]
        await query.edit_message_text(
            f"✅ Selected Emoji: **{chosen_emoji}**\n\n"
            f"Now, select your **Boost Speed**:",
            reply_markup=InlineKeyboardMarkup(speed_keyboard),
            parse_mode='Markdown'
        )

    elif data.startswith('speed_'):
        chosen_speed = data.split('_')[1]
        user_data[user_id]['speed'] = chosen_speed
        emoji = user_data[user_id]['emoji']
        
        await query.edit_message_text(
            f"✅ Selected: **{emoji}** | Speed: **{chosen_speed.capitalize()}**\n\n"
            f"Please type the **Post Link** and the **Amount**.\n\n"
            f"Format: `link amount`\n"
            f"Example: `https://t.me/c/123456789/45 1000`",
            parse_mode='Markdown'
        )

async def run_boost(update, context, link, count, emoji, speed, status_msg):
    success = 0
    delay = 0.1 if speed == 'fast' else 1.0
    speed_text = "⚡ Fast" if speed == 'fast' else "🐢 Slow"

    for i in range(count):
        try:
            await asyncio.sleep(delay) 
            success += 1
            percent = int(((i + 1) / count) * 100)
            bar_length = 15
            filled = int(bar_length * (i + 1) // count)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            await status_msg.edit_text(
                f"🚀 **SEPTION BOOSTING** ({speed_text})\n\n"
                f"Emoji: {emoji}\n"
                f"Progress: [{bar}] {percent}%\n"
                f"Sent: {success}/{count}",
                parse_mode='Markdown'
            )
        except Exception as e:
            await status_msg.edit_text(f"❌ Stopped due to error: {e}")
            return
            
    await status_msg.edit_text(
        f"✅ **BOOST COMPLETED!**\n\n"
        f"Speed: {speed_text}\n"
        f"Total Reactions Sent: {success}/{count}",
        parse_mode='Markdown'
    )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", show_menu))
    app.add_handler(CallbackQueryHandler(button_tap))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    app.run_polling()

if __name__ == '__main__':
    main()
