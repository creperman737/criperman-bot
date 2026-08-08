import asyncio
import logging
import os
import random
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command

# =========================================================
# CONFIG
# =========================================================

TOKEN = os.getenv("8649569111:AAFcgv4xxIv1y3AK76ntuP__g1FAl8v2fkc")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable topilmadi!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# Shu yerga guruh username yoki ID yoz
GROUP_ID = "@criperman_chat"

DB_NAME = "criperman_bot.db"


# =========================================================
# DATABASE
# =========================================================

db = sqlite3.connect(DB_NAME)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS birthdays (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    birthday TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS invites (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    count INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS groups (
    chat_id TEXT PRIMARY KEY
)
""")

db.commit()


# =========================================================
# CHANNELS
# =========================================================

MY_CHANNELS = [
    "💻 Dasturlash: https://www.youtube.com/@criperman_coding",
    "👨‍👩‍👧‍👦 Asosiy kanal: https://www.youtube.com/@criperman_family",
    "🎮 O'yinlar: https://www.youtube.com/@criperman_games",
    "🔥 Minecraft: https://www.youtube.com/@Crimson_criperman"
]


# =========================================================
# SPLASH TEXTS
# =========================================================

SPLASH_TEXTS = [
    "💻 Kod yozish — bu san'at!",
    "🚀 Har bir kichik qadam katta maqsadga olib boradi.",
    "💡 Yangi g'oyalarni sinab ko'rishdan qo'rqmang!",
    "⚡ Xatolar — tajriba.",
    "🎮 Bugun Minecraft'da nima quramiz?",
    "⛏️ Olmos qazish vaqti keldi!",
    "🧱 Har bir katta qurilish bitta blokdan boshlanadi.",
    "🐉 Ender Dragon'ni yengishga tayyormisiz?",
    "🔥 Redstone bilan hammasini avtomatlashtiring!",
    "🏆 Bugungi reja: yangi rekord!",
    "⭐ Maqsad sari olg'a!",
    "🌟 Bugun yangi narsa o'rganing.",
    "🤖 Bot ishlayapti. Demak, hammasi nazorat ostida!",
    "🍕 Pitsa + kod = yaxshi kun.",
    "🚀 Serverlar qiziyapti!",
    "🐱 Mushuk klaviaturaga chiqib ketmasin!",
    "💚 Never Give Up!"
]


# =========================================================
# BAD WORDS
# =========================================================

BAD_WORDS = [
    "ahmoq",
    "axmoq",
    "dalbayob",
    "dapa",
    "dappa",
    "jinni",
    "jalab",
    "lox",
    "tentak",
    "yban",
    "yiban",
    "gandon",
    "гандон",
    "гей",
    "далбаеб",
    "далбаёб",
    "ебан",
    "ебать",
    "жалаб",
    "лохсан",
    "пидр",
    "спам",
    "сука",
    "сикай",
    "тупой",
    "хакерлик",
    "хароми",
    "чит борми",
    ".onion",
    "18+",
    "porno",
    "sex"
]


# =========================================================
# HELPERS
# =========================================================

def is_admin(message: types.Message) -> bool:
    member = asyncio.run_coroutine_threadsafe(
        message.chat.get_member(message.from_user.id),
        asyncio.get_running_loop()
    )

    try:
        result = member.result()
        return result.status in ("administrator", "creator")
    except Exception:
        return False


def save_group(chat_id):
    cursor.execute(
        "INSERT OR IGNORE INTO groups(chat_id) VALUES (?)",
        (str(chat_id),)
    )
    db.commit()


def normalize(text):
    return (
        text.lower()
        .replace(" ", "")
        .replace("*", "")
        .replace("_", "")
        .replace(".", "")
        .replace("-", "")
    )


# =========================================================
# START
# =========================================================

@dp.message(Command("start"))
async def start_command(message: types.Message):
    save_group(message.chat.id)

    await message.answer(
        "🤖 <b>Criperman Bot</b>ga xush kelibsiz!\n\n"
        "👋 Welcome\n"
        "🎂 Birthday\n"
        "🏆 /top\n"
        "👥 /count\n"
        "🎮 Minecraft\n"
        "📺 YouTube\n\n"
        "ℹ️ /info",
        parse_mode="HTML"
    )


# =========================================================
# WELCOME
# =========================================================

@dp.message(F.new_chat_members)
async def welcome_new_members(message: types.Message):

    save_group(message.chat.id)

    for member in message.new_chat_members:

        if member.is_bot:
            # Begona botni chiqarish
            if member.id != bot.id:
                try:
                    await bot.ban_chat_member(
                        message.chat.id,
                        member.id
                    )

                    await message.answer(
                        f"🤖 {member.full_name} bot edi.\n"
                        f"🛡 Guruhga begona bot kiritilmaydi."
                    )

                except Exception as e:
                    logging.error(f"Botni chiqarishda xato: {e}")

            continue

        username = (
            f"@{member.username}"
            if member.username
            else member.full_name
        )

        welcome_messages = [
            f"👋 Xush kelibsiz, {username}!",
            f"🎉 {username} guruhimizga qo'shildi!",
            f"💚 Xush kelibsiz, {username}! Never Give Up!",
            f"🎮 {username}, Minecraft chatimizga xush kelibsiz!",
            f"🔥 {username} ham bizga qo'shildi!"
        ]

        await message.answer(
            random.choice(welcome_messages)
        )

        # Kimdir odam qo'shgan bo'lsa hisoblash
        inviter = message.from_user

        if inviter and inviter.id != member.id:

            cursor.execute(
                "SELECT count FROM invites WHERE user_id=?",
                (inviter.id,)
            )

            row = cursor.fetchone()

            new_count = (row[0] if row else 0) + 1

            cursor.execute("""
                INSERT OR REPLACE INTO invites
                (user_id, username, count)
                VALUES (?, ?, ?)
            """, (
                inviter.id,
                inviter.username or inviter.full_name,
                new_count
            ))

            db.commit()


# =========================================================
# BIRTHDAY
# =========================================================

@dp.message(Command("birthday"))
async def birthday_command(message: types.Message):

    args = message.text.split()

    if len(args) != 2:
        await message.answer(
            "🎂 Tug'ilgan kuningizni kiriting:\n\n"
            "<code>/birthday 15.08</code>",
            parse_mode="HTML"
        )
        return

    birthday = args[1]

    try:
        datetime.strptime(birthday, "%d.%m")
    except ValueError:
        await message.answer(
            "❌ Format noto'g'ri!\n"
            "Masalan: <code>/birthday 15.08</code>",
            parse_mode="HTML"
        )
        return

    user = message.from_user

    cursor.execute("""
        INSERT OR REPLACE INTO birthdays
        (user_id, username, birthday)
        VALUES (?, ?, ?)
    """, (
        user.id,
        user.username or user.full_name,
        birthday
    ))

    db.commit()

    await message.answer(
        f"🎂 Tug'ilgan kuningiz <b>{birthday}</b> sifatida saqlandi!\n"
        f"Bot o'sha kuni sizni tabriklaydi 🎉",
        parse_mode="HTML"
    )


# =========================================================
# BIRTHDAY CHECKER
# =========================================================

async def birthday_checker():

    while True:

        today = datetime.now().strftime("%d.%m")

        cursor.execute("""
            SELECT user_id, username
            FROM birthdays
            WHERE birthday=?
        """, (today,))

        birthdays = cursor.fetchall()

        for user_id, username in birthdays:

            try:

                mention = f"@{username}" if username else "🎉 Tug'ilgan kun egasi"

                text = (
                    f"🎉🎂 <b>HAPPY BIRTHDAY!</b> 🎂🎉\n\n"
                    f"🥳 {mention}\n\n"
                    f"🎈 Tug'ilgan kuningiz muborak bo'lsin!\n"
                    f"🎉 Happy Birthday to You!\n"
                    f"🇯🇵 お誕生日おめでとう！\n"
                    f"🇷🇺 С днём рождения!\n\n"
                    f"💚 Sizga baxt, omad va katta zafarlar tilaymiz!\n"
                    f"🚀 Never Give Up!"
                )

                await bot.send_message(
                    GROUP_ID,
                    text,
                    parse_mode="HTML"
                )

            except Exception as e:
                logging.error(
                    f"Birthday xatosi: {e}"
                )

        # Keyingi tekshiruv 1 soatdan keyin
        await asyncio.sleep(3600)


# =========================================================
# TOP
# =========================================================

@dp.message(Command("top"))
async def top_command(message: types.Message):

    cursor.execute("""
        SELECT username, count
        FROM invites
        ORDER BY count DESC
        LIMIT 10
    """)

    users = cursor.fetchall()

    if not users:
        await message.answer(
            "🏆 Hali hech kim odam qo'shmagan."
        )
        return

    text = "🏆 <b>TOP 10 — ENG KO'P ODAM QO'SHGANLAR</b>\n\n"

    medals = ["🥇", "🥈", "🥉"]

    for index, (username, count) in enumerate(users, 1):

        medal = medals[index - 1] if index <= 3 else f"{index}."

        text += (
            f"{medal} {username} — "
            f"<b>{count}</b> 👥\n"
        )

    await message.answer(
        text,
        parse_mode="HTML"
    )


# =========================================================
# COUNT
# =========================================================

@dp.message(Command("count"))
async def count_command(message: types.Message):

    user = message.from_user

    cursor.execute(
        "SELECT count FROM invites WHERE user_id=?",
        (user.id,)
    )

    row = cursor.fetchone()

    count = row[0] if row else 0

    await message.answer(
        f"👥 Siz qo'shgan odamlar soni: <b>{count}</b>",
        parse_mode="HTML"
    )


# =========================================================
# INFO
# =========================================================

@dp.message(Command("info"))
async def info_command(message: types.Message):

    await message.answer(
        "🤖 <b>Criperman Bot</b>\n\n"
        "👋 Welcome system\n"
        "🎂 Birthday system\n"
        "🏆 TOP system\n"
        "📊 Invite counter\n"
        "🛡 Anti-spam\n"
        "🤖 Anti-bot\n"
        "📺 YouTube\n"
        "🎮 Minecraft\n\n"
        "💚 Criperman\n"
        "🚀 Never Give Up!",
        parse_mode="HTML"
    )


# =========================================================
# SALOM
# =========================================================

@dp.message(F.text)
async def chat_listener(message: types.Message):

    text = message.text.lower()

    # Admin bo'lsa filtrga tushmaydi
    try:
        if message.from_user is not None:
            member = await message.chat.get_member(message.from_user.id)
            if member.status in (
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.CREATOR,
            ):
                return
    except Exception:
        pass

    # Salom
    if "salom" in text:

        await message.reply(
            "👀 Criperman sizni doim eshitadi, "
            "bemalol gapiravering! 💻😎"
        )

        return

    # Bad words
    clean_text = normalize(text)

    for word in BAD_WORDS:

        clean_word = normalize(word)

        if word in text or clean_word in clean_text:

            try:

                await message.delete()

                await message.answer(
                    f"🚫 {message.from_user.mention_html()}, "
                    f"bu guruhda bunday kontent taqiqlangan!",
                    parse_mode="HTML"
                )

            except Exception as e:
                logging.error(
                    f"Message delete xatosi: {e}"
                )

            return


# =========================================================
# 3 KUNLIK MESSAGE
# =========================================================

async def three_day_scheduler():

    while True:

        await asyncio.sleep(259200)  # 3 kun

        text = random.choice(SPLASH_TEXTS)

        try:

            await bot.send_message(
                GROUP_ID,
                f"🌟 <b>Criperman Chat</b>\n\n{text}",
                parse_mode="HTML"
            )

            # YouTube tavsiyasi
            await bot.send_message(
                GROUP_ID,
                "📺 <b>Criperman kanallari:</b>\n\n"
                + "\n".join(MY_CHANNELS),
                parse_mode="HTML",
                disable_web_page_preview=True
            )

        except Exception as e:

            logging.error(
                f"3 kunlik scheduler xatosi: {e}"
            )


# =========================================================
# STARTUP
# =========================================================

async def on_startup():

    asyncio.create_task(
        birthday_checker()
    )

    asyncio.create_task(
        three_day_scheduler()
    )

    logging.info(
        "🤖 Criperman Bot ishga tushdi!"
    )


# =========================================================
# MAIN
# =========================================================

async def main():

    await on_startup()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
