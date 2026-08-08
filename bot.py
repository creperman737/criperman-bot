import asyncio
import random
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command

# Tokeningiz
TOKEN = "8649569111:AAFcgv4xxIv1y3AK76ntuP__g1FAl8v2fkc"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Loggingni sozlash
logging.basicConfig(level=logging.INFO)

# Kanallaringiz ro'yxati (Bu yerga o'z kanallaringiz havolalarini yozishingiz mumkin)
# Kanallaringiz ro'yxati
MY_CHANNELS = [
    "💻 **Dasturlash kanalim:** [Criperman Coding](https://www.youtube.com/@criperman_coding)",
    "👨‍👩‍👧‍👦 **Assiy kanalim:** [Criperman Family](https://www.youtube.com/@criperman_family)",
    "🎮 **O'yinlar kanalim:** [Criperman Games](https://www.youtube.com/@criperman_games)",
    "🔥 **minecraftga kanalim:** [Crimson Criperman](https://www.youtube.com/@Crimson_criperman)"
]

# Bayramlarni yillarga qarab avtomatik chiqaruvchi funksiya
def get_holidays():
    current_year = datetime.now().year
    return {
        "01-01": f"🎉 **Yangi {current_year}-yilingiz bilan!** Hammaga omad, muvaffaqiyat va yangi zafarlar tilaymiz! 🎄",
        "01-07": f"🎂🎉 **7-yanvar — Guruhimiz asoschisi (criperman)ning Tug'ilgan kunlari muborak bo'lsin!** Sizga sihat-salomatlik, ijodiy muvaffaqiyat va ulkan zafarlar tilaymiz! 🚀🎁",
        "01-14": f"🎖 **14-yanvar – Vatan himoyachilari kuni muborak bo'lsin!** Barcha yurtimiz posbonlarini chin qalbimizdan tabriklaymiz! 🛡",
        "03-08": f"💐 **8-mart – Xalqaro xotin-qizlar kuni muborak bo'lsin!** Guruhimizdagi barcha ayol va qizlarni tabriklaymiz, doimo yashnab yuringlar! 🌷",
        "03-21": f" 🌱 **21-mart – Navro'z ayyomi muborak bo'lsin!** Yurtimizga bahor nafasi, xonadonimizga qut-baraka kirib kelsin! ☀️",
        "05-09": f" 🕊 **9-may – Xotira va qadrlash kuni muborak bo'lsin!** Tinchligimiz abadiy bo'lsin, o'tganlar xotirasi hamisha dillarimizda! 🇺🇿",
        "06-01": f"🎈 **1-iyun – Xalqaro bolalarni himoya qilish kuni muborak bo'lsin!** Barcha jajji bolajonlarga baxt va porloq kelajak tilaymiz! 🌟",
        "09-01": f"🇺🇿 **O'zbekiston Respublikasi Mustaqillik kuni muborak bo'lsin!** Yurtimiz tinch, osmonimiz musaffo bo'lsin! 🎆",
        "10-01": f"📚 **1-oktabr – O'qituvchi va murabbiylar kuni muborak bo'lsin!** Barcha ustozlarni chin qalbimizdan tabriklaymiz! 🍎",
        "12-08": f"📜 **8-dekabr – O'zbekiston Respublikasi Konstitutsiyasi kuni muborak bo'lsin!** 📘"
    }

# Splash textlar ro'yxati
SPLASH_TEXTS = [
    "💻 Kod yozish — bu san'at, uni mukammal darajaga olib chiqing!",
    "🚀 Har bir kichik qadam sizni katta maqsadlarga yaqinlashtiradi.",
    "💡 Yangi g'oyalarni sinab ko'rishdan qo'rqmang!",
    "⚡ Xatolar — bu tajriba, ulardan dars oling va davom eting.",
    "☕ Qahva va kod: mukammal kun uchun asosiy formula.",
    "🔧 Bugun qanday ajoyib loyihaga asos solamiz?",
    "🌐 Internetdagi o'z olamingizni yarating!",
    "🧠 Miya faoliyati 100% quvvatda: kodlashni boshlaymiz!",
    "⌨️ Klaviaturadagi har bir bosish — kelajak sari tashlangan qadam.",
    "🛠️ O'z operatsion tizimingizni yoki ilovangizni yaratishga tayyormisiz?",
    "🎮 Bugun Minecraft'da nima quramiz?",
    "⛏️ Olmos qazish vaqti keldi, ketdik!",
    "🧱 Har bir mukammal imorat bitta blokdan boshlanadi.",
    "🟩 Blok ustiga blok qo'yib, o'z imperiyangizni quring!",
    "🧱 Dirt block ham o'z o'rnida buyuk san'at asari bo'la oladi!",
    "🐉 Ender Dragon'ni yengishga tayyormisiz?",
    "🌲 Yangi biomni kashf qilish — har safar yangi sarguzasht.",
    "🔥 Redstone sxemalari yordamida hammasini avtomatlashtiring!",
    "🎯 O'yin o'ynash ham, uni yaratish ham birdek zavqli.",
    "🏆 Bugungi reja: o'yinlardagi rekordlarni yangilash!",
    "🗺️ O'z olamingizni o'zingiz loyihalashtiring.",
    "🔥 Bugungi kuningiz samarali va qiziqarli o'tsin!",
    "⭐ Maqsad sari olg'a, to'xtash yo'q!",
    "🌟 Bugun boshqalar qila olmagan ishni qiling.",
    "🎯 Rejalarni tuzing va ularni birma-bir bajarib chiqing.",
    "🎨 O'z hayotingiz rassomi bo'ling.",
    "🔋 Ichki batareyangizni 100% ga to'ldiring va ishga kirishing!",
    "📈 Hari kuni oz-ozdan o'rganing — natijasi hayratda qoldiradi.",
    "🌊 To'siqlardan qo'rqmang, ular faqat tajriba beradi.",
    "✨ Bugungi kun — yangi g'alabalar uchun eng yaxshi fursat.",
    "🤖 Bot ishlayapti, demak hammasi nazorat ostida!",
    "🕶️ Haqiqiy dasturchilar yorug' mavzuni (Light Theme) yoqtirishmaydi.",
    "🍕 Pitsa va kod - eng yaxshi dasturlash muhiti.",
    "🚀 Serverlar qiziyapti, kayfiyat esa a'lo darajada!",
    "🐱 Mushukingiz klaviaturaga chiqib ketishidan ehtiyot bo'ling!",
    "criperman sizni doim eshitadi bemalol gapiroring"
]

# Taqiqlangan so'zlar ro'yxati (Block Words)
BAD_WORDS = [
    "ahmoq", "axmoq", "d_a_l_b_a_y_o_b", "d.a.l.b.a.y.o.b", "dalbayob", "dapa", "dappa", 
    "dinnaxuy", "dnx", "fock", "j a l a b", "j_a_l_a_b", "j.a.l.a.b", "j*a*l*a*b", "jalab", 
    "jinni", "k o t", "k_o_t", "k.o.t", "k.o'.t", "k.ot", "k*o*t", "kanalimga kiring", "ko't", 
    "konkurs", "kuzu", "like bosing", "lox", "mol", "obuna bo'ling", "odam bo'lmaysan", 
    "podpiska", "pul yutish", "qanjiq", "salov", "tentak", "vzaim", "yban", "yiban", 
    "yordam bering obuna bo'lishga", "админлик беринг", "ам", "б*ять", "бля", "блять", 
    "ботсан", "взаимка", "взаимно", "гaндон", "гандон", "гей", "далбаеб", "далбаёб", "даун", 
    "ебан", "ебать", "жалаб", "ибан", "йуқол", "йўқол", "каналга ўтинг", "ко'т", "конкурс качон", 
    "конкурс қачон", "котингга", "кут", "кутингга", "кутунгga", "лашара", "лохсан", "майнкрафт текин", 
    "мараз", "модер бер", "модерлик беринг", "нооб", "нуб", "пидараз", "пидр", "подписался", 
    "подпишись", "pul yutish", "pul беринг", "репорт", "с*ка", "сикай", "сиқий", "спам", "сука", "сур", 
    "сутак", "сўтак", "ташқи", "ташландик", "ташландиқ", "тупая", "тупой", "уйнашни билмайсан", "ўйнашни билмайсан", 
    "хакерлик", "харами", "хароми", "чит борми", "чит код", "ширинхур",
    ".onion", "18+", "porno", "sex"
]

# 1. Har kuni ishlaydigan fon vazifasi (Splash text + Bayramlar + Avto Reklama)
async def daily_scheduler(chat_id: int):
    while True:
        now = datetime.now()
        current_date = now.strftime("%m-%d") 
        holidays = get_holidays() 
        
        # Bayram tekshiruvi
        if current_date in holidays:
            try:
                await bot.send_message(chat_id, holidays[current_date])
            except Exception as e:
                logging.error(f"Bayram tabrigida xatolik: {e}")
        
        # Tasodifiy splash text yuborish
        text = random.choice(SPLASH_TEXTS)
        try:
            await bot.send_message(chat_id, f"🌟 **Kunlik Splash:**\n{text}")
        except Exception as e:
            logging.error(f"Splash yuborishda xatolik: {e}")
            
        # Kanallarni avtomatik reklama qilish (Har 24 soatda bir marta)
        try:
            ad_text = "🔥 **Kunlik tavsiya etilgan kanallarimizga obuna bo'ling!**\n\n" + "\n".join(MY_CHANNELS)
            await bot.send_message(chat_id, ad_text, disable_web_page_preview=True)
        except Exception as e:
            logging.error(f"Reklama yuborishda xatolik: {e}")
            
        await asyncio.sleep(86400) # 24 soat

@dp.startup()
async def on_startup(bot: Bot):
    GROUP_ID = "@criperman_chat"  # Matn ko'rinishida qo'shtirnoq ichida yoziladi
    asyncio.create_task(daily_scheduler(GROUP_ID))

# 2. /info buyrug'i (Bot haqida ma'lumot)
@dp.message(Command("info"))
async def cmd_info(message: types.Message):
    info_text = (
        "🤖 **Bot haqida ma'lumot:**\n\n"
        "✨ Bu bot guruhni tozalash, 18+ va taqiqlangan so'zlardan himoya qilish, begona botlarni haydash hamda guruhda ko'ngilochar kayfiyat ulashish uchun yaratilgan!\n\n"
        "👑 **Guruh asoschisi va bot egasi:** Criperman\n"
        "💻 **Loyiha:** CripOS va shaxsiy botlar\n"
        "👀 *Criperman sizni doim eshitadi, bemalol gapiravering!*"
    )
    await message.reply(info_text)

# 3. Guruhga bot qo'shilsa avtomatik haydash
@dp.message(F.new_chat_members)
async def anti_bot(message: types.Message):
    for member in message.new_chat_members:
        if member.is_bot and member.id != bot.id:
            try:
                await message.chat.ban(member.id)
                await message.answer(f"⚠️ <b>{member.full_name}</b> nomli bot guruhga qo'shildi va avtomatik chiqarib yuborildi!")
                await message.delete()
            except Exception as e:
                logging.error(f"Botni haydashda xatolik: {e}")

# 4. "Salom" reaksiyasi, /info va Blok so'zlar filtri
@dp.message(F.text)
async def chat_listener(message: types.Message):
    text = message.text.lower()
    
    # "Salom" so'zi yozilsa javob berish
    if "salom" in text:
        await message.reply("👀 **Criperman sizni doim eshitadi, bemalol gapiravering!** 💻😎 @criperman_uz")
        return

    # Adminlarni tekshirish (Blok so'zlar uchun)
    try:
        member = await message.chat.get_member(message.from_user.id)
        if member.status in ("administrator", "creator"):
            return
    except Exception:
        pass

    # Blok so'zlar, havolalar va 18+ ni tozalash filtri
    for word in BAD_WORDS:
        clean_word = word.replace(" ", "").replace("*", "").replace("_", "").replace(".", "")
        clean_text = text.replace(" ", "").replace("*", "").replace("_", "").replace(".", "")
        
        if word in text or clean_word in clean_text:
            try:
                await message.delete()
                await message.answer(f"🚫 {message.from_user.mention_parsed}, bu guruhda taqiqlangan so'z, havola yoki kontent yozish taqiqlangan!")
                return
            except Exception:
                pass

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())