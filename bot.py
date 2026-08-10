import asyncio
import logging
import os
import random
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command

# =========================================================
# CONFIG
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable topilmadi!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# O'zbekiston vaqti
UZ_TZ = ZoneInfo("Asia/Tashkent")

DB_NAME = "criperman_bot.db"

# Donate linking
DONATE_LINK = "SENING_DONATE_LINKING"

# =========================================================
# DATABASE
# =========================================================

db = sqlite3.connect(DB_NAME, check_same_thread=False)
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

# Birthday dublikatlarini oldini olish
cursor.execute("""
CREATE TABLE IF NOT EXISTS birthday_sent (
    user_id INTEGER,
    year INTEGER,
    PRIMARY KEY (user_id, year)
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
    "sex",
    "fock",
    "f*ck",
    "f u c k",
    "f u c k",
    "kot",
    "ko't",
    "neger"
]


# =========================================================
# HELPERS
# =========================================================

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


def get_saved_groups():
    cursor.execute("SELECT chat_id FROM groups")
    return [row[0] for row in cursor.fetchall()]


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
        "🎁 /danat\n"
        "ℹ️ /info\n"
        "📖 /help\n\n"
        "💚 Never Give Up!",
        parse_mode="HTML"
    )


# =========================================================
# HELP
# =========================================================

@dp.message(Command("help"))
async def help_command(message: types.Message):

    await message.answer(
        "📖 <b>Criperman Bot buyruqlari</b>\n\n"
        "🎂 /birthday 15.08 — tug'ilgan kunni saqlash\n"
        "🎈 /mybirthday — tug'ilgan kuningizni ko'rish\n"
        "🗑️ /delbirthday — tug'ilgan kunni o'chirish\n"
        "🏆 /top — TOP 10 odam qo'shganlar\n"
        "👥 /count — nechta odam qo'shganingizni ko'rish\n"
        "🎁 /danat — donate qilish\n"
        "📺 /channels — Criperman kanallari\n"
        "🆔 /id — Telegram ID\n"
        "📊 /stats — guruh statistikasi\n"
        "ℹ️ /info — bot haqida\n"
        "📖 /help — buyruqlar ro'yxati",
        parse_mode="HTML"
    )


# =========================================================
# ID
# =========================================================

@dp.message(Command("id"))
async def id_command(message: types.Message):

    await message.answer(
        f"🆔 Sizning Telegram ID'ingiz:\n"
        f"<code>{message.from_user.id}</code>",
        parse_mode="HTML"
    )


# =========================================================
# DONATE
# =========================================================

@dp.message(Command("danat"))
async def danat_command(message: types.Message):

    await message.answer(
        "💸 <b>Criperman'ni qo'llab-quvvatlash!</b>\n\n"
        "🎁 Agar xohlasangiz, donate yuborishingiz mumkin.\n\n"
        f"👉 <a href=\"{DONATE_LINK}\">💰 Donate qilish</a>",
        parse_mode="HTML"
    )


# =========================================================
# CHANNELS
# =========================================================

@dp.message(Command("channels"))
async def channels_command(message: types.Message):

    await message.answer(
        "📺 <b>Criperman kanallari:</b>\n\n"
        + "\n".join(MY_CHANNELS),
        parse_mode="HTML",
        disable_web_page_preview=True
    )


# =========================================================
# WELCOME
# =========================================================

@dp.message(F.new_chat_members)
async def welcome_new_members(message: types.Message):

    save_group(message.chat.id)

    for member in message.new_chat_members:

        # Begona bot
        if member.is_bot:

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
                    logging.error(
                        f"Botni chiqarishda xato: {e}"
                    )

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
# BIRTHDAY SET
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
        f"🎂 Tug'ilgan kuningiz "
        f"<b>{birthday}</b> sifatida saqlandi!\n\n"
        f"🎉 Bot o'sha kuni sizni tabriklaydi!",
        parse_mode="HTML"
    )


# =========================================================
# MY BIRTHDAY
# =========================================================

@dp.message(Command("mybirthday"))
async def mybirthday_command(message: types.Message):

    cursor.execute(
        "SELECT birthday FROM birthdays WHERE user_id=?",
        (message.from_user.id,)
    )

    row = cursor.fetchone()

    if not row:

        await message.answer(
            "🎂 Siz hali tug'ilgan kuningizni saqlamagansiz.\n\n"
            "Masalan:\n"
            "<code>/birthday 15.08 yani kun.oy</code>",
            parse_mode="HTML"
        )

        return

    await message.answer(
        f"🎂 Sizning tug'ilgan kuningiz: "
        f"<b>{row[0]}</b>",
        parse_mode="HTML"
    )


# =========================================================
# DELETE BIRTHDAY
# =========================================================

@dp.message(Command("delbirthday"))
async def delbirthday_command(message: types.Message):

    cursor.execute(
        "DELETE FROM birthdays WHERE user_id=?",
        (message.from_user.id,)
    )

    db.commit()

    await message.answer(
        "🗑️ Tug'ilgan kuningiz botdan o'chirildi."
    )


# =========================================================
# BIRTHDAY CHECKER
# =========================================================

async def birthday_checker():

    last_checked_date = None

    while True:

        now = datetime.now(UZ_TZ)
        today = now.strftime("%d.%m")

        # Bir kun ichida qayta tekshirib yubormaslik
        if today != last_checked_date:

            cursor.execute("""
                SELECT user_id, username, birthday
                FROM birthdays
                WHERE birthday=?
            """, (today,))

            birthdays = cursor.fetchall()

            for user_id, username, birthday in birthdays:

                current_year = now.year

                # Shu yil tabriklanganmi?
                cursor.execute("""
                    SELECT 1
                    FROM birthday_sent
                    WHERE user_id=? AND year=?
                """, (
                    user_id,
                    current_year
                ))

                already_sent = cursor.fetchone()

                if already_sent:
                    continue

                try:

                    if username and not username.startswith("@"):
                        mention = f"@{username}"
                    elif username:
                        mention = username
                    else:
                        mention = "🎉 Tug'ilgan kun egasi"

                    text = (
                        f"🎉🎂 <b>HAPPY BIRTHDAY!</b> 🎂🎉\n\n"
                        f"🥳 {mention}\n\n"
                        f"🎈 Tug'ilgan kuningiz muborak bo'lsin!\n"
                        f"🇬🇧 Happy Birthday to You!\n"
                        f"🇯🇵 お誕生日おめでとう！\n"
                        f"🇷🇺 С днём рождения!\n\n"
                        f"💚 Sizga baxt, omad va katta zafarlar tilaymiz!\n"
                        f"🚀 Never Give Up!"
                    )

                    # Barcha saqlangan guruhlarga yuborish
                    groups = get_saved_groups()

                    for group_id in groups:

                        try:

                            await bot.send_message(
                                int(group_id),
                                text,
                                parse_mode="HTML"
                            )

                        except Exception as e:

                            logging.error(
                                f"Birthday {group_id} xatosi: {e}"
                            )

                    # Tabrik yuborildi deb saqlash
                    cursor.execute("""
                        INSERT OR IGNORE INTO birthday_sent
                        (user_id, year)
                        VALUES (?, ?)
                    """, (
                        user_id,
                        current_year
                    ))

                    db.commit()

                except Exception as e:

                    logging.error(
                        f"Birthday xatosi: {e}"
                    )

            last_checked_date = today

        # Har 1 daqiqada Toshkent vaqtini tekshiradi
        await asyncio.sleep(60)


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

    text = (
        "🏆 <b>TOP 10 — ENG KO'P ODAM QO'SHGANLAR</b>\n\n"
    )

    medals = ["🥇", "🥈", "🥉"]

    for index, (username, count) in enumerate(users, 1):

        medal = (
            medals[index - 1]
            if index <= 3
            else f"{index}."
        )

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

    cursor.execute(
        "SELECT count FROM invites WHERE user_id=?",
        (message.from_user.id,)
    )

    row = cursor.fetchone()

    count = row[0] if row else 0

    await message.answer(
        f"👥 Siz qo'shgan odamlar soni: "
        f"<b>{count}</b>",
        parse_mode="HTML"
    )


# =========================================================
# STATS
# =========================================================

@dp.message(Command("stats"))
async def stats_command(message: types.Message):

    cursor.execute(
        "SELECT COUNT(*) FROM birthdays"
    )

    birthday_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM invites"
    )

    invite_users = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM groups"
    )

    group_count = cursor.fetchone()[0]

    await message.answer(
        "📊 <b>Criperman Bot statistikasi</b>\n\n"
        f"👥 Guruhlar: <b>{group_count}</b>\n"
        f"🎂 Birthday saqlaganlar: <b>{birthday_count}</b>\n"
        f"🏆 Invite statistikasi: <b>{invite_users}</b>",
        parse_mode="HTML"
    )


# =========================================================
# INFO
# =========================================================

@dp.message(Command("info"))
async def info_command(message: types.Message):

    await message.answer(
        "🤖 <b>Criperman Bot</b>\n\n"
        "👋 odam qoshilsa hush kelibsiz deydi\n"
        "🎂 /birthday 00.00 kun/oy kiritsayiz tugulgan kunda tabriklaydi\n"
        "🏆 kim ko'p odam qo'shgan top 10ta odamni korsatadi\n"
        "📊 Invite counter\n"
        "🛡 Anti-spam\n"
        "🤖 Anti-bot\n"
        "📺 YouTube\n"
        "🎁 Donate\n\n"
        "💚 Criperman\n"
        "🚀 Never Give Up!",
        parse_mode="HTML"
    )


# =========================================================
# SALOM + BAD WORD FILTER
# =========================================================

@dp.message(F.text)
async def chat_listener(message: types.Message):

    text = message.text.lower()

    # Avval taqiqlangan so'zlarni tekshirish.
    # Adminlar ham bundan mustasno emas.
    clean_text = normalize(text)

    for word in BAD_WORDS:

        clean_word = normalize(word)

        if word in text or clean_word in clean_text:

            try:

                await message.delete()

                await message.answer(
                    "🚫 Bu guruhda bunday so'z "
                    "taqiqlangan!",
                    parse_mode="HTML"
                )

            except Exception as e:

                logging.error(
                    f"Message delete xatosi: {e}"
                )

            return

    # Salom funksiyasi adminlarda ham ishlaydi
    if "salom" in text:

        await message.reply(
            "👀 <b>Criperman sizni doim eshitadi, "
            "bemalol gapiravering!</b> 💻😎",
            parse_mode="HTML"
        )

        return


# =========================================================
# DAILY SPLASH + AD
# =========================================================

async def daily_scheduler():

    last_sent_date = None

    while True:

        now = datetime.now(UZ_TZ)

        # Har kuni soat 20:00
        if now.hour == 20 and now.minute == 0:

            current_date = now.strftime("%Y-%m-%d")

            if current_date != last_sent_date:

                text = random.choice(SPLASH_TEXTS)

                groups = get_saved_groups()

                for group_id in groups:

                    try:

                        chat_id = int(group_id)

                        # Splash
                        await bot.send_message(
                            chat_id,
                            f"🌟 <b>Criperman Chat</b>\n\n"
                            f"{text}",
                            parse_mode="HTML"
                        )

                        # Reklama
                        await bot.send_message(
                            chat_id,
                            "📺 <b>Criperman kanallari:</b>\n\n"
                            + "\n".join(MY_CHANNELS),
                            parse_mode="HTML",
                            disable_web_page_preview=True
                        )

                    except Exception as e:

                        logging.error(
                            f"Daily scheduler {group_id} xatosi: {e}"
                        )

                last_sent_date = current_date

        await asyncio.sleep(30)


# =========================================================
# STARTUP
# =========================================================

async def on_startup():

    asyncio.create_task(
        birthday_checker()
    )

    asyncio.create_task(
        daily_scheduler()
    )

    logging.info(
        "🤖 Criperman Bot ishga tushdi!"
    )


# =========================================================
# MAIN
# =========================================================

async def main():

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    await on_startup()

    await dp.start_polling(bot)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    asyncio.run(main())