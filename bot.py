import os
import re
import random
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

# ==========================================
# FILE PATHS AND CONFIGURATION
# ==========================================

BAD_WORDS_FILE = os.path.join(os.path.dirname(__file__), "bad_words.txt")
WARNING_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "warning_word.jpg")
HELLO_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "hello.jpg")

DEFAULT_BAD_WORDS = [
    "ahmoq", "zb", "axmoq", "dalbayob", "poxoy", "dnx", "ph", "dapa", "dappa", 
    "jinni", "jalab", "lox", "tentak", "yban", "yiban", "gandon", "гандон", 
    "гей", "далбаеб", "далбаёб", "ебан", "ебать", "жалаб", "лохсан", "пидр", 
    "спам", "сука", "сикай", "тупой", "хакерлик", "хароми", "чит борми", 
    ".onion", "18+", "porno", "sex", "fock", "f*ck", "f u c k", "kot", "ko't", 
    "neger", "https://youtube.com/@artijon", "https://t.me/artijonuzb", "porn.hub", "boqbek",
]

MANUAL_LINK_BLOCKED_USERS = {"5144283333"}

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def is_manual_link_blocked_user(message: types.Message) -> bool:
    if not message.from_user:
        return True
    username = (message.from_user.username or "").strip().lower()
    user_id = str(message.from_user.id)
    candidates = {user_id, username, f"@{username}"}
    normalized = {item.strip().lower() for item in MANUAL_LINK_BLOCKED_USERS if item and item.strip()}
    return bool(candidates & normalized)

def load_bad_words():
    words = []
    if os.path.exists(BAD_WORDS_FILE):
        try:
            with open(BAD_WORDS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    w = line.strip()
                    if w:
                        words.append(w)
        except Exception as e:
            logging.error(f"bad_words: error reading file: {e}")
            words = DEFAULT_BAD_WORDS.copy()
    else:
        words = DEFAULT_BAD_WORDS.copy()
        try:
            with open(BAD_WORDS_FILE, "w", encoding="utf-8") as f:
                for w in words:
                    f.write(w + "\n")
        except Exception as e:
            logging.error(f"bad_words: error creating file: {e}")

    seen = set()
    dedup = []
    for w in words:
        key = w.lower().strip()
        if key and key not in seen:
            seen.add(key)
            dedup.append(w)
    return dedup

BAD_WORDS = load_bad_words()

def is_bad_word_present(text: str, bad_words: list) -> bool:
    """
    So'zlarni to'liq so'z chegarasi (Regex) bo'yicha tekshirish.
    'yangi', 'mustahkam' kabi toza so'zlar ichidagi harf birikmalarini o'chirmaydi.
    """
    text_lower = text.lower()
    for word in bad_words:
        w_clean = word.strip().lower()
        if not w_clean:
            continue
        
        # Havolalar va domenlar uchun oddiy qidiruv
        if "http" in w_clean or "." in w_clean or "*" in w_clean or " " in w_clean or "+" in w_clean:
            if w_clean in text_lower:
                return True
        else:
            # Alohida so'z ekanligini aniq tekshirish
            pattern = r'(?<!\w)' + re.escape(w_clean) + r'(?!\w)'
            if re.search(pattern, text_lower):
                return True
    return False

# ==========================================
# ELEMENT BATTLE GAME LOGIC
# ==========================================

ELEMENTS = {
    "🔥 Olov": {"beats": ["🌳 Daraxt", "🧊 Muz", "🍃 Bargli"]},
    "💧 Suv": {"beats": ["🔥 Olov", "⏳ Lava", "🪵 Loy"]},
    "⚡ Chaqmoq": {"beats": ["💧 Suv", "⚙️ Metall", "🌩️ Firtina"]},
    "🌪️ Shamol": {"beats": ["🌫️ Tutun", "🔥 Olov", "🍃 Bargli"]},
    "⏳ Lava": {"beats": ["🪨 Tosh", "🧊 Muz", "⚙️ Metall"]},
    "🪨 Tosh": {"beats": ["🔥 Olov", "⚡ Chaqmoq", "🧊 Muz"]},
    "⚙️ Metall": {"beats": ["🪨 Tosh", "🌳 Daraxt", "💎 Kristall"]},
    "💡 Nur": {"beats": ["🌑 Soya", "🌫️ Tutun", "🧊 Muz"]},
    "🌑 Soya": {"beats": ["🌙 Oy", "💎 Kristall", "🧠 Savol"]},
    "🧊 Muz": {"beats": ["💧 Suv", "🍃 Bargli", "🌳 Daraxt"]},
    "🌙 Oy": {"beats": ["💡 Nur", "☀️ Quyosh", "🌟 Yulduz"]},
    "☀️ Quyosh": {"beats": ["🌑 Soya", "🧊 Muz", "🌙 Oy"]},
    "📦 Qum": {"beats": ["🔥 Olov", "💧 Suv", "⚡ Chaqmoq"]},
    "🍃 Bargli": {"beats": ["📦 Qum", "💧 Suv", "🪵 Loy"]},
    "🌳 Daraxt": {"beats": ["📦 Qum", "🪨 Tosh", "🪵 Loy"]},
    "🌫️ Tutun": {"beats": ["💡 Nur", "☀️ Quyosh", "🍃 Bargli"]},
    "💎 Kristall": {"beats": ["💡 Nur", "⚡ Chaqmoq", "🔥 Olov"]},
    "🪵 Loy": {"beats": ["🔥 Olov", "📦 Qum", "💎 Kristall"]},
    "🌩️ Firtina": {"beats": ["🌳 Daraxt", "🌪️ Shamol", "📦 Qum"]},
    "🌟 Yulduz": {"beats": ["🌑 Soya", "🌫️ Tutun", "🌩️ Firtina"]}
}

def create_element_buttons():
    buttons = []
    elements_list = list(ELEMENTS.keys())
    for i in range(0, len(elements_list), 5):
        row = []
        for j in range(5):
            if i + j < len(elements_list):
                element = elements_list[i + j]
                row.append(
                    InlineKeyboardButton(
                        text=element,
                        callback_data=f"battle_idx_{i+j}"
                    )
                )
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ==========================================
# 1. COMMAND HANDLERS (Yuqori ustuvorlik)
# ==========================================

bot = None
dp = None

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable topilmadi!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("battle"))
async def battle_command(message: types.Message):
    keyboard = create_element_buttons()
    await message.answer(
        "🔥 <b>ELEMENT BATTLE</b> 🔥\n\n"
        f"👤 <b>{message.from_user.full_name}</b>, o'z unsuringizni tanlang:\n\n"
        "<i>Har bir unsur boshqasidan quvvatli, boshqasidan zaif.</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.startswith("battle_idx_"))
async def process_battle(query: types.CallbackQuery):
    try:
        elem_idx = int(query.data.replace("battle_idx_", ""))
        user_element = list(ELEMENTS.keys())[elem_idx]
    except Exception:
        await query.answer("❌ Unsur topilmadi!", show_alert=True)
        return

    bot_element = random.choice(list(ELEMENTS.keys()))
    
    if user_element == bot_element:
        result = "🤝 DURANG!"
        result_text = "Ikkalangiz ham bir xil unsur tanladingiz!"
    elif bot_element in ELEMENTS[user_element]["beats"]:
        result = "🏆 SIZ G'ALABA QOZONDINGIZ!"
        result_text = f"<b>{user_element}</b> ➡️ <b>{bot_element}</b>ni mag'lub etdi!"
    else:
        result = "💀 MAG'LUBIYAT!"
        result_text = f"<b>{bot_element}</b> ➡️ <b>{user_element}</b>ni mag'lub etdi!"
    
    result_message = (
        f"⚔️ <b>JANG BOSHLANDI!</b>\n\n"
        f"👤 <b>Siz ({query.from_user.first_name}):</b> {user_element}\n"
        f"🤖 <b>Curina Bot:</b> {bot_element}\n\n"
        f"<b>{user_element} 🆚 {bot_element}</b>\n\n"
        f"<b>{result}</b>\n"
        f"<i>{result_text}</i>\n\n"
        f"<code>/battle</code> - qayta o'ynash uchun"
    )
    
    try:
        await query.message.edit_text(result_message, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Edit message error: {e}")
        await query.message.answer(result_message, parse_mode="HTML")
    
    await query.answer()

@dp.message(Command("start", "help", "info", "text", "savol"))
async def general_commands_handler(message: types.Message, command: CommandObject):
    cmd_name = command.command
    args = command.args or ""
    
    if cmd_name == "start":
        await message.reply("👋 Salom! Men Curina botman. Guruhda tartibni saqlashga yordam beraman.")
    elif cmd_name == "help":
        await message.reply("ℹ️ Bot buyruqlari:\n/battle - Elementlar jangi\n/info - Bot haqida ma'lumot")
    elif cmd_name == "info":
        await message.reply("🤖 <b>Curina Bot</b>\nGuruh xavfsizligi va ko'ngilochar bot.")
    elif cmd_name in ["text", "savol"]:
        if not args:
            await message.reply(f"❓ Yozish usuli: <code>/{cmd_name} savolingiz</code>")
        else:
            await message.reply(f"💡 Savolingiz qabul qilindi: <i>{args}</i>")

# ==========================================
# 2. SALOM LISTENER
# ==========================================

@dp.message(F.text & F.chat.type.in_({"group", "supergroup"}))
async def hello_listener(message: types.Message):
    # Buyruqlarni e'tiborsiz qoldirish
    if message.text.startswith('/'):
        return

    text = message.text.lower().strip()
    hello_keywords = ["salom", "assalomu alaykum", "salom alaykum", "privet", "hello"]
    
    if any(re.search(r'(?<!\w)' + re.escape(kw) + r'(?!\w)', text) for kw in hello_keywords):
        owner_name = "Guruh egasi"

        try:
            admins = await message.chat.get_administrators()
            for admin in admins:
                if admin.status == "creator":
                    owner_name = f"@{admin.user.username}" if admin.user.username else admin.user.full_name
                    break
        except Exception as e:
            logging.error(f"Owner error: {e}")

        user_name = message.from_user.first_name if message.from_user else "Foydalanuvchi"
        hello_responses = [
            f"👀 <b>{owner_name} sizni doim eshitadi, bemalol gapiravering!</b> 💻😎",
            f"👋 Assalomu alaykum, {user_name}! {owner_name} bilan birga sizga ajoyib kayfiyat tilaymiz! ✨",
            f"🎧 {owner_name} quloqda, chatni kuzatib bormoqda... Nima gaplar, {user_name}? 🎮",
            f"🤖 Salom, {user_name}! Men <b>Curina</b>man, {owner_name}ning sodiq yordamchisiman. Xush kelibsiz! ⚡",
            f"🔥 Ooo salom, {user_name}! {owner_name} va men xizmatingizdamiz, bemalol yozing! 🚀"
        ]

        selected_caption = random.choice(hello_responses)

        try:
            if os.path.exists(HELLO_IMAGE_PATH):
                photo = FSInputFile(HELLO_IMAGE_PATH)
                await message.reply_photo(photo=photo, caption=selected_caption, parse_mode="HTML")
            else:
                await message.reply(text=selected_caption, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Hello error: {e}")
            await message.reply(selected_caption, parse_mode="HTML")

# ==========================================
# 3. CHAT LISTENER (Taqiqlangan so'zlar filtri)
# ==========================================

@dp.message(F.text & F.chat.type.in_({"group", "supergroup"}))
async def chat_listener(message: types.Message):
    if message.text.startswith('/'):
        return

    # Taqiqlangan so'zlarni tekshirish
    if is_bad_word_present(message.text, BAD_WORDS):
        try:
            await message.delete()
            user_mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>'
            caption_text = f"⚠️ {user_mention}, iltimos, guruhda taqiqlangan soʻz ishlatmang!"
            
            if os.path.exists(WARNING_IMAGE_PATH):
                photo = FSInputFile(WARNING_IMAGE_PATH)
                await message.answer_photo(photo=photo, caption=caption_text, parse_mode="HTML")
            else:
                await message.answer(text=caption_text, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Message delete error: {e}")

# ==========================================
# BOT STARTUP
# ==========================================

async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
