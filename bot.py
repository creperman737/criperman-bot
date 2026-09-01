import asyncio
import logging
import os
import random
import re
import sqlite3
from datetime import datetime
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiohttp import web
from aiogram.types import FSInputFile, URLInputFile
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
DONATE_LINK = "https://idonate.uz/d/deeKARL"

BLOCKED_LINK_NAMES = [
    "iplogger",
    "grabify",
    "2no.co",
    "blasze",
    "ipgrabber",
]

BLOCKED_STICKER_PACKS = {
    "xaastikers",
    "lidreron",
    "My_stickers1230",
    "Webp_18",
    "Delete_zapal",
    "BanaAit_by_TgEmojis_bot",
    "AliJanes00",
    "uspeh7",
    "luvkyses",
    "nevsinka_by_fStikBot",
    "drctvtbukok9_by_TgEmojiBot",
    "MiSideT_by_TgEmodziBot",
    "plsmykiss",
    "hentsbor_by_fStikBot",
    "HANGSEED_Emoji2",
    "MurodjongaTegishliNothing035",
}


def normalize(text: str) -> str:
    if text is None:
        return ""

    text = str(text).lower()
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("'", "").replace("`", "")
    text = re.sub(r"[^a-z0-9а-яё]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def normalize_url_fragment(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def extract_urls(text: str):
    if not text:
        return []

    return re.findall(r"https?://[^\s<>'\"`]+", text, flags=re.IGNORECASE)


def is_blocked_link(url: str) -> bool:
    try:
        parsed = urlsplit(url)
    except ValueError:
        return False

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False

    host = (parsed.hostname or "").lower().replace("www.", "")
    path = (parsed.path or "").lower()
    query = (parsed.query or "").lower()
    fragment = (parsed.fragment or "").lower()
    url_text = f"{host} {path} {query} {fragment}"

    for blocked_name in BLOCKED_LINK_NAMES:
        blocked_key = normalize_url_fragment(blocked_name)

        if not blocked_key:
            continue

        if (
            blocked_key in normalize_url_fragment(host)
            or blocked_key in normalize_url_fragment(path)
            or blocked_key in normalize_url_fragment(url_text)
        ):
            return True

    return False


def has_blocked_link(text: str) -> bool:
    if not text:
        return False

    for url in extract_urls(text):
        if is_blocked_link(url):
            return True

    return False

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

cursor.execute("""
CREATE TABLE IF NOT EXISTS link_blocks (
    chat_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (chat_id, user_id)
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

GROUP_CHANNELS = {
    # Har bir guruhning public username'iga qarab kanal ro'yxatini yuboradi.
    # Siz berilgan 3 ta guruh uchun quyidagicha sozlaysiz.

    "@dee_KARLUZ_GROUP": [
        "assosy kanalim https://www.youtube.com/@deeKARL",
        "qosimcha kanalim https://www.youtube.com/@deeKARL_story-games",
    ],

    "@criperman_chat": [
        "💻 Dasturlash: https://www.youtube.com/@criperman_coding",
        "👨‍👩‍👧‍👦 Asosiy kanal: https://www.youtube.com/@criperman_family",
        "🎮 O'yinlar: https://www.youtube.com/@criperman_games",
        "🔥 Minecraft: https://www.youtube.com/@Crimson_criperman",
    ],

    "@verstak_uz": [
        "minecraft serverlar vazisida videolar topasiz: https://www.youtube.com/@Verstak_server_uz",
        "assoy kanalim https://www.youtube.com/@MCRetro_08",
    ]
}


# =========================================================
# SPLASH TEXTS
# =========================================================

SPLASH_TEXTS = [
    "🧠 Miyangizga bugun yangi g'oya kelmadimi?",
    "🔧 Har bir muammo — yangi tajriba.",
    "💾 Ishingizni saqlashni unutmayapsizmi?",
    "⌨️ Klaviatura bugun ham jangga tayyor.",
    "🖥️ Kompyuter jim, lekin ishlar davom etmoqda.",
    "🌐 Internet bor ekan, imkoniyatlar ham bor.",
    "🚀 Sekin bo'lsa ham oldinga yurish — yurish.",
    "🎯 Maqsadni bilsangiz, yo'l topiladi.",
    "🧩 Ba'zan javob bitta kichik detalda yashiringan.",
    "🔍 Bugun nimanidir boshqacha ko'rishga harakat qiling.",
    "📚 Biror yangi narsa o'rganib qo'ying.",
    "☕ Kod yozishda choy ham sherik.",
    "😂 Bug ham ba'zida dasturchining do'sti.",
    "🐛 Bug topildi. Endi u sizniki.",
    "🛠️ Ishlamasa, yana bir marta tekshiring.",
    "💡 G'oya kichik bo'lishi mumkin, natijasi katta bo'ladi.",
    "🌱 Har bir loyiha kichik qadamdan boshlanadi.",
    "🔥 Bugun ham taslim bo'lmaymiz.",
    "🏆 Natija emas, jarayon ham muhim.",
    "🎮 Bir blokdan butun shahar qurish mumkin.",
    "⛏️ Minecraft kutmoqda.",
    "🧱 Bitta blok qo'ying. Keyin yana bittasini.",
    "🌳 Daraxtni kesishdan oldin ko'chat ekishni unutmang.",
    "🐄 Minecraftdagi sigirlar ham sizni kutyapti.",
    "💎 Olmos topishdan oldin tosh qaziladi.",
    "🌋 Lava bilan hazillashmang.",
    "🐷 Piglinlar bilan ehtiyot bo'ling.",
    "👾 Creeper orqangizda bo'lishi mumkin. 👀",
    "🏠 Uy qurish — sarguzashtning boshlanishi.",
    "🌙 Kechasi Minecraftda hamma narsa boshqacha.",
    "☀️ Yangi kun — yangi imkoniyat.",
    "🌌 Osmonga qarash ham ba'zan foydali.",
    "⭐ Kichik yutuqlarni ham qadrlang.",
    "💚 O'zingizga ham vaqt ajrating.",
    "👀 O'zingizga oxirgi marta qachon e'tibor berdingiz?",
    "🫡 Bugungi vazifa: taslim bo'lmaslik.",
    "🧭 Yo'l yo'q bo'lsa, o'zingiz yo'l oching.",
    "🏃 Oldinga qarang, lekin xatolardan saboq oling.",
    "🕒 Vaqt o'tmoqda. Uni bekorga sarflamang.",
    "📈 Bugun kechagidan bir qadam oldinda bo'ling.",
    "📉 Hammasi pasayishi mumkin, lekin yana ko'tariladi.",
    "🎲 Hayotda hamma narsa oldindan rejalashtirilmaydi.",
    "🧪 Sinab ko'rmasangiz, natijani bilmaysiz.",
    "🔬 Qiziqish — bilimning boshlanishi.",
    "📖 Bir sahifa ham bir qadam.",
    "✏️ Xatoni o'chirish oson, undan saboq olish qiyin.",
    "🧠 Bilmagan narsangizni so'rashdan uyalmang.",
    "🤖 Bot ishlayapti. Siz-chi? 😏",
    "⚙️ Tizim ishlashi uchun kichik detallar ham kerak.",
    "🔌 Tok bor ekan, kompyuter ham bor.",
    "💻 Kompyuterga buyruq bering, lekin aniq bering.",
    "⌛ Kutish ham ba'zan jarayonning bir qismi.",
    "🔄 Qayta urinib ko'rish — mag'lubiyat emas.",
    "🗃️ Fayllaringizni tartibga solib qo'ydingizmi?",
    "🧹 Desktopingizda nechta keraksiz fayl bor? 😂",
    "📂 `final_final_2_REAL.py` degan fayl bo'lmasin.",
    "🐍 Python ham bugun ishlashga tayyor.",
    "🌐 Saytingiz bugun internetga chiqishga tayyormi?",
    "💻 Kod ishlasa — tegmang. 😂",
    "🧑‍💻 Dasturchining eng katta dushmani: bitta nuqta.",
    "🔴 Qizil xato chiqsa, vahima qilmang.",
    "🟢 Yashil bo'lsa, demak yaxshi ketmoqda.",
    "🟡 Sariq ogohlantirishni ham e'tiborsiz qoldirmang.",
    "🐞 Bug yashirinadi, lekin baribir topiladi.",
    "🧩 Kod ham puzzle'ga o'xshaydi.",
    "📦 Har bir package o'z vazifasini bajaradi.",
    "🚪 Ba'zi xatolar eshikni yopadi, boshqalari yangi eshik ochadi.",
    "🔐 Parollaringizni ehtiyot qiling.",
    "🛡️ Xavfsizlikni keyinga qoldirmang.",
    "🌍 Internet kichkina ekran ichidagi katta dunyo.",
    "📡 Signal bor. G'oya ham bor.",
    "📱 Telefonni bir daqiqaga chetga qo'yib ko'ring.",
    "🎧 Musiqa + kod = fokus rejimi.",
    "🎵 Bugun qaysi qo'shiq miyangizda aylanmoqda?",
    "🎨 Kod ham ijodning bir turi.",
    "🖌️ Dizayn chiroyli bo'lsa, foydalanuvchi xursand.",
    "🧱 Har bir katta loyiha minglab kichik qismlardan iborat.",
    "🏗️ Qurayotgan narsangizga poydevor qo'ying.",
    "🚧 Hali tugamagan loyiha — muvaffaqiyatsizlik emas.",
    "🔨 Ishni boshlash — eng qiyin qism.",
    "🏁 Boshlagan narsangizni tugatishga harakat qiling.",
    "🌟 Bugun sizda ham yangi rekord bo'lishi mumkin.",
    "🔥 Energiya bor ekan, foydalaning.",
    "💪 Kuch kichik harakatlardan yig'iladi.",
    "🫶 O'zingizga qattiq tanqidchi bo'lmang.",
    "🙂 Bir oz dam olish ham kerak.",
    "😴 Uyquni ham unutib qo'ymang.",
    "🍕 Pitsa kodni kompilyatsiya qilmaydi, afsus. 😂",
    "🍔 Burger ham bugni tuzatmaydi.",
    "☕ Choy sovib qolmasin.",
    "🐱 Mushuk yana klaviaturaga chiqmasin.",
    "🐶 It ham bugun yaxshi kayfiyatda.",
    "😂 Agar ishlamasa, kompyuterni ayblashdan oldin kodni tekshiring.",
    "👀 Hech kim ko'rmayapti deb o'ylamang, bot ko'rib turibdi.",
    "🤖 Men hammasini ko'rmayman, lekin loglar ko'radi. 😂",
    "📜 Eski kodni o'qish — tarixiy tadqiqot.",
    "🏛️ Eski kod ba'zan yangi muammolarning ajdodi bo'ladi.",
    "🧙 Bir kuni yozgan kodingiz o'zingizga sehrdek tuyuladi.",
    "⚡ Tezlik yaxshi, to'g'rilik undan yaxshi.",
    "🎯 Avval ishlasin, keyin mukammallashtiring.",
    "🔧 Mukammallikni kutib o'tirmang.",
    "🌱 Bugun ekilgan g'oya ertaga loyiha bo'lishi mumkin.",
    "🚀 Never Give Up — eski, lekin hali ham ishlaydigan qoida."

    # =========================================================
    # 😂 MEME — 84
    # =========================================================

    "😂 Bug chiqdi. Men esa bugni kutmagandim.",
    "🤣 Kompyuter ishlamayapti. Restart — qadimiy sehr.",
    "😎 Bugun ham hech narsa buzmaslikka harakat qilamiz.",
    "🍕 Pitsa kodni tuzatmaydi, lekin kayfiyatni tuzatadi.",
    "☕ Choy bor. Demak, loyiha yashaydi.",
    "🐱 Mushuk klaviaturaga tegmasa, hammasi yaxshi.",
    "💀 `final_final_REAL_v7.py` hali ham mavjud.",
    "😂 Kod ishlayaptimi? Tegmang.",
    "🤣 Biror narsa ishlasa, nima sababdanligini so'ramang.",
    "🧠 Miya: dam olaylik. Kompyuter: yana bir bug.",
    "💻 Men kod yozdim. Kompyuter esa fikrimga qo'shilmadi.",
    "😭 Birgina nuqta butun dasturni yiqitdi.",
    "😂 Ctrl+Z — dasturchining vaqt mashinasi.",
    "🤣 Ctrl+S — eng muhim diniy marosim.",
    "🫠 'Faqat bitta kichik o'zgarish qilaman' degan odam.",
    "💀 Bir qator kod o'zgardi. 47 ta xato paydo bo'ldi.",
    "😂 Internet sekinlashsa, hamma birdan texnik mutaxassis.",
    "🐛 Bug topildi. U ham meni topibdi.",
    "🤣 Kompyuter qiziyapti, demak u ham ishlayapti.",
    "😎 RAM 99%. Hali ham yashayapmiz.",
    "💾 Fayl saqlandi. Yurak ham tinchidi.",
    "😂 Wi-Fi ketdi. Hayot ham ketgandek.",
    "🤣 Parolni eslash uchun parol kerak.",
    "🧑‍💻 Dasturchi: '5 daqiqada tugaydi.'",
    "⏳ 5 daqiqa o'tdi. Uch soatlik sarguzasht boshlandi.",
    "😂 Men xatoni tuzatdim. Endi boshqa xato ishlamayapti.",
    "🤨 Bu xato kecha yo'q edi.",
    "🤣 Kecha ishlagan kod bugun ta'tilda.",
    "💀 Server: 'Men charchadim.'",
    "😂 Monitor qarab turibdi. Men ham qarab turibman.",
    "🍜 Noodles + coding = klassik kombinatsiya.",
    "🤣 Dokumentatsiya: 'Meni o'qi.' Dasturchi: 'Keyin.'",
    "😂 Google ochildi. Demak, muammo jiddiy.",
    "🔍 Stack Overflow ruhi yana chaqirilmoqda.",
    "🤣 Bitta typo butun kunni yedi.",
    "💀 Deadline yaqinlashmoqda.",
    "😂 Deadline — motivatsiyaning eng qadimgi shakli.",
    "😎 Bugun ham 'temporary fix' qilamiz.",
    "🤣 Temporary fix 3 yildan beri ishlayapti.",
    "😂 Developer mode: ON. Sleep mode: OFF.",
    "😴 Uyqu kelmoqda. Bug esa ketmayapti.",
    "🍔 Burger yeyib bug tuzatilmaydi. Lekin urinib ko'ramiz.",
    "😂 Printer yana o'zini muhim deb o'ylayapti.",
    "🤣 Bluetooth ulanmayapti. Klassika.",
    "📶 Signal bir chiziq. Umid esa nol.",
    "😂 1% battery — haqiqiy boss fight.",
    "🔋 Zaryadlovchi topildi. Hayot saqlandi.",
    "🤣 Sichqoncha yo'qolsa, hamma stol ostiga qaraydi.",
    "😂 Klaviaturadagi eng ko'p ishlatiladigan tugma: Enter.",
    "🤔 Nega ishlamayapti? Chunki.",
    "🤣 'Bu safar backup qilaman.'",
    "💀 Backup yo'q edi.",
    "😂 Kompyuter: error. Men: qaysi biri?",
    "🤣 Har bir dasturchining bir kuni 'nega?' kuni.",
    "😎 Debugging — detektivlikning zamonaviy turi.",
    "😂 Monitor qora. Yurak ham qora.",
    "🤣 Internet bor, lekin sayt ochilmayapti.",
    "🫡 Bugun ham texnologiyaga xizmat qilamiz.",
    "😂 Reja bor edi. Kompyuter boshqa reja tuzdi.",
    "🤣 Fayl nomi 'newnew2' bo'lib ketdi.",
    "💀 Desktopda 800 ta ikonka — bu tartib.",
    "😂 Papka ichida papka. Ichida yana papka.",
    "🤣 Downloads papkasi — arxeologik qazilma.",
    "😂 'Later' papkasi hech qachon ochilmaydi.",
    "😎 Biror narsa yuklanayotgan bo'lsa, kutamiz.",
    "🤣 Loading 99% — eng uzun foiz.",
    "😂 Update 1% dan 2% ga o'tdi. Bayram.",
    "🎉 Reboot qildik. Sehrli ravishda tuzaldi.",
    "🤣 ITning 50%: o'chirib yoqib ko'ring.",
    "😂 Qolgan 50%: yana o'chirib yoqib ko'ring.",
    "🤖 Robot ham ba'zan restart xohlaydi.",
    "🤣 Bugun ham odamlar parolini unutadi.",
    "😂 Kompyuterga qarab o'tirish ham sport.",
    "😎 Keyboard warrior navbatchilikda.",
    "🤣 Mouse click qildi. Dunyo o'zgardi.",
    "😂 'Men buni bilaman' — mashhur oxirgi so'z.",
    "💀 Error message'ni o'qimay yopish — klassika.",
    "🤣 Bugun ham loglar gapiradi.",


    # =========================================================
    # 💻 CODING — 84
    # =========================================================

    "💻 Kod yozish — bu muammoni satrlarga bo'lish san'ati.",
    "🚀 Har bir loyiha birinchi qator koddan boshlanadi.",
    "🧠 Algoritm yaxshi bo'lsa, kod ham nafas oladi.",
    "🔧 Debugging — muammoni tushunish san'ati.",
    "🐛 Har bir bug biror narsani o'rgatadi.",
    "📚 Dokumentatsiya sizning yashirin ustozingiz.",
    "⌨️ Bugun yangi funksiya yozib ko'ring.",
    "🧩 Kod — kichik qismlardan qurilgan katta fikr.",
    "⚙️ Toza kod kelajakdagi o'zingizga sovg'a.",
    "🔍 Muammoni kichik qismlarga ajrating.",
    "💡 Eng yaxshi kod — tushunarli kod.",
    "📦 Har bir modulning o'z vazifasi bor.",
    "🌐 Web dasturlash — g'oyani ekranga chiqarish.",
    "🛠️ Xatoni tuzatishdan oldin uni tushuning.",
    "🔄 Refactor — eski kodga yangi hayot berish.",
    "🎯 Kod yozishda maqsadni unutmang.",
    "🧪 Test yozish — kelajakdagi muammolarni kamaytirish.",
    "🔐 Xavfsizlikni koddan keyin emas, kod bilan birga o'ylang.",
    "📊 Ma'lumotlar yaxshi boshqarilsa, tizim ham yaxshi ishlaydi.",
    "🗃️ Database — loyihaning xotirasi.",
    "🐍 Python bugun ham tayyor.",
    "🟨 JavaScript yana bir sir saqlayapti.",
    "🌊 Async kod sabrni ham o'rgatadi.",
    "🚦 Exception'larni to'g'ri boshqaring.",
    "📝 Yaxshi nomlangan o'zgaruvchi yarim tushuntirishdir.",
    "💾 Backup — dasturchining sug'urtasi.",
    "🔗 API'lar tizimlarni bir-biri bilan gaplashtiradi.",
    "📡 Server ham odam kabi to'g'ri buyruq kutadi.",
    "🖥️ Terminal — oddiy ko'rinadigan kuchli vosita.",
    "⚡ Tez kod yaxshi, ishonchli kod undan yaxshi.",
    "📈 Performance ham feature.",
    "🧹 Keraksiz kodni tozalashdan qo'rqmang.",
    "🧠 Murakkab muammo oddiy qismlarga bo'linadi.",
    "🔬 Kodni tekshirish sifatni oshiradi.",
    "🚧 Prototype mukammal bo'lishi shart emas.",
    "🏗️ Avval poydevor, keyin bezak.",
    "🎨 UI ham kodning bir qismi.",
    "👨‍💻 Har bir developer bir payt beginner bo'lgan.",
    "📖 Tutorial ko'rish yaxshi, o'zingiz yozish undan yaxshi.",
    "💡 G'oyani kodga aylantirish — haqiqiy sehr.",
    "🔎 Error message sizga dushman emas.",
    "🛡️ Input validation'ni unutmang.",
    "📂 Fayl tuzilishi ham arxitekturaning bir qismi.",
    "🔌 Plugin tizimni kengaytiradi.",
    "⚙️ Config'ni koddan ajratish foydali.",
    "🌱 Kichik loyiha katta tajriba beradi.",
    "🚀 Deploy — kodning real dunyoga chiqishi.",
    "☁️ Cloud qulay, lekin konfiguratsiyani biling.",
    "🔑 Secretlarni kod ichiga yozmang.",
    "📜 Git commit — loyihaning tarixidir.",
    "🌳 Branchlar tajribalar uchun maydon.",
    "🔀 Merge qilishdan oldin kodni tekshiring.",
    "🧑‍💻 Code review yangi ko'zlar olib keladi.",
    "🧪 Testlar sizga ishonch beradi.",
    "📦 Dependency'larni nazorat qiling.",
    "🔄 Update qilishdan oldin backup qiling.",
    "🐞 Buglar ko'pincha kutilmagan joydan chiqadi.",
    "🧭 Arxitektura loyiha yo'nalishini belgilaydi.",
    "📐 Soddalik ko'pincha eng yaxshi dizayn.",
    "⚡ Optimallashtirishdan oldin o'lchang.",
    "🧠 Kod emas, yechim muhim.",
    "🔨 Ishlamayotgan kodni yashirmang, tushuning.",
    "📋 TODO ro'yxati ba'zan roman uzunligida bo'ladi.",
    "💻 Terminalda bitta buyruq katta ish qilishi mumkin.",
    "🌐 Frontend va backend — ikki xil dunyo, bitta loyiha.",
    "🗄️ Database schema'ni oldindan o'ylash foydali.",
    "🔒 Authentication va authorization bir xil narsa emas.",
    "📨 Message queue katta tizimlarda juda foydali.",
    "🛰️ Monitoring muammo chiqqandan keyin ham kerak.",
    "📈 Loglar tizimning kundaligi.",
    "🚀 CI/CD takroriy ishlarni avtomatlashtiradi.",
    "🤖 Automation vaqtni qaytarib beradi.",
    "🧩 Reusable code kelajakdagi ishni kamaytiradi.",
    "📚 Har kuni bitta yangi API o'rganish ham yutuq.",
    "⌛ Kod yozish tezlik emas, izchillik poygasi.",
    "🎯 Bugungi bitta commit ertangi katta release bo'lishi mumkin.",
    "🛠️ Dasturlashda sabr ham dependency.",
    "🌟 Yaxshi developer savol berishdan qo'rqmaydi.",
    "💚 Never Give Up — debuggingda ayniqsa kerak.",


    # =========================================================
    # ⛏️ MINECRAFT — 83
    # =========================================================

    "⛏️ Bugun yangi kon ochamizmi?",
    "💎 Olmos qidirish yana boshlandi.",
    "🧱 Har bir qurilish bitta blokdan boshlanadi.",
    "🌳 Daraxtni kesdik. Endi uy quramiz.",
    "🏠 Spawn yonida chiroyli uy kerak.",
    "🔥 Furnace yana ishlayapti.",
    "🐄 Ferma qurish vaqti.",
    "🌾 Bugun bug'doy yetishtiramiz.",
    "🎣 Baliq ovlash ham sarguzasht.",
    "🗺️ Xarita hali ham katta.",
    "🌌 Ender olami kutmoqda.",
    "🐉 Dragon bilan uchrashuv yaqin.",
    "👾 Creeperlar yana reja tuzmoqda.",
    "🧟 Kechasi tashqarida ehtiyot bo'ling.",
    "🕷️ O'rgimchaklar ham mehmon bo'lishni yaxshi ko'radi.",
    "💀 Skeletonlar nishonga olishni yaxshi biladi.",
    "🧱 Redstone bilan hamma narsa mumkin.",
    "🔴 Redstone laboratoriyasi ochildi.",
    "⚙️ Avtomatik ferma qilish vaqti.",
    "🚂 Minecart yo'li quramizmi?",
    "🚪 Yangi baza uchun eshik tayyor.",
    "🛏️ Spawn pointni unutmaylik.",
    "🕯️ G'orlarni yoritishni unutmang.",
    "🌋 Lava yonida ehtiyotkorlik kerak.",
    "💧 Suv chelakni olib yuring.",
    "🪣 Bitta chelak juda ko'p muammoni hal qiladi.",
    "🪨 Tosh oddiy, lekin foydali.",
    "🪵 Yog'och — Minecraftdagi klassik boshlanish.",
    "🌲 Taiga biomida sarguzasht boshlanadi.",
    "🏜️ Cho'l ibodatxonasi topilarmikan?",
    "🌴 Jungle hali ham sirli.",
    "❄️ Snow biome bugun sovuq.",
    "🌊 Okean tubida nimalar bor?",
    "🐠 Dengiz ham o'z xazinasini yashiradi.",
    "🪸 Coral reef juda chiroyli.",
    "🏔️ Tog' cho'qqisiga chiqamiz.",
    "☁️ Bulutlardan yuqorida baza qurish mumkin.",
    "🌙 Minecraft kechasi boshqacha ko'rinadi.",
    "☀️ Quyosh chiqdi. Moblar yashirinadi.",
    "🔥 Nether portal tayyor.",
    "👹 Netherda ehtiyot bo'ling.",
    "🟪 Portalning narigi tomonida nima bor?",
    "💀 Wither chaqirishga tayyormisiz?",
    "⭐ Nether Star hali ham qimmat.",
    "🛡️ Shield tayyor bo'lsin.",
    "⚔️ Sword durability'ni tekshiring.",
    "🏹 Kamon o'qlar bilan to'la bo'lsin.",
    "⛑️ Armor kiyishni unutmang.",
    "🪖 Diamond armor bugun porlaydi.",
    "💚 Emerald savdogarlar uchun kerak.",
    "🏘️ Villagerlar yana savdo kutmoqda.",
    "🛒 Trading hall qurish mumkin.",
    "📚 Enchantment table tayyor.",
    "✨ XP yig'ish boshlandi.",
    "📖 Mending kitobini topish — omad.",
    "🔨 Anvil yana ishlayapti.",
    "💰 Villager iqtisodiyoti qiziq.",
    "🐑 Qo'ylar junini kutmoqda.",
    "🐔 Tovuqlar tuxum bermoqda.",
    "🐷 Cho'chqalar o'z ishida.",
    "🐴 Ot bilan uzoq yo'lga chiqamiz.",
    "🐺 Bo'ri yangi do'st bo'lishi mumkin.",
    "🐈 Mushuklar creeperlardan himoya qiladi.",
    "🐝 Asalarilar ham ekotizimning bir qismi.",
    "🍯 Asal yig'ish vaqti.",
    "🎃 Pumpkin topildimi?",
    "🍎 Oltin olma juda qimmat.",
    "🥔 Kartoshka ham foydali.",
    "🍞 Non hech qachon yomon tanlov emas.",
    "🥕 Sabzi fermasi rivojlanmoqda.",
    "🍉 Qovun ham kerak bo'ladi.",
    "🎒 Inventory yana to'lib qoldimi?",
    "📦 Chestlar tartibni kutmoqda.",
    "🧹 Inventoryni tozalash vaqti.",
    "🧭 Compass yo'l ko'rsatadi.",
    "🕰️ Minecraftda vaqt tez o'tadi.",
    "🧪 Potion tayyorlash boshlanadi.",
    "🫧 Water breathing bugun kerak bo'lishi mumkin.",
    "🌟 End city topish vaqti.",
    "🪽 Elytra olish — katta maqsad.",
    "🚀 Elytra bilan osmonga!",
    "🏆 Achievementlar hali ko'p.",
    "💚 Minecraftda ham Never Give Up.",


    # =========================================================
    # 🧠 DEEP — 83
    # =========================================================

    "🧠 Ba'zan jimlik eng baland javob bo'ladi.",
    "🌌 Katta savollar kichik fikrlardan boshlanadi.",
    "👀 O'zingizga oxirgi marta qachon e'tibor berdingiz?",
    "🌱 O'sish doim ham ko'rinib turmaydi.",
    "🕊️ Tinchlik ham yutuq.",
    "⌛ Vaqt qaytmaydi, lekin undan saboq qoladi.",
    "🌙 Har bir tunning o'z hikoyasi bor.",
    "☀️ Ertalab yana bir imkoniyat keladi.",
    "🪞 O'zingizni boshqalar bilan emas, kechagi o'zingiz bilan solishtiring.",
    "🧭 Yo'nalish ba'zan tezlikdan muhimroq.",
    "🌊 Hayot ham to'lqinlarga o'xshaydi.",
    "🍂 Ba'zi narsalarni qo'yib yuborish ham kuch.",
    "🌳 Kuchli daraxt shamolda egiladi, lekin sinmaydi.",
    "🕯️ Kichik nur ham qorong'ulikni o'zgartiradi.",
    "📖 Har kimning ko'rinmaydigan hikoyasi bor.",
    "🤫 Hamma narsaga javob berish shart emas.",
    "💭 O'ylash ham harakatning bir turi.",
    "🧩 O'zingizni tushunish uzoq yo'l.",
    "🌍 Dunyo katta, fikrlar undan ham katta.",
    "⭐ Oddiy kunlar ham qadrli.",
    "🫶 O'zingizga ham mehr bilan qarang.",
    "🌿 Tinchlikni doim tashqaridan qidirmang.",
    "🔭 Uzoqqa qaragan odam yo'lni boshqacha ko'radi.",
    "🕰️ Ba'zi javoblar vaqt bilan keladi.",
    "🌧️ Yomg'ir ham osmonning bir hikoyasi.",
    "🌤️ Bulut ortida osmon baribir bor.",
    "🪶 Yengil fikr ba'zan og'ir yukni ko'taradi.",
    "🧘 Shoshilmaslik ham tanlov.",
    "🔎 Savol berish bilimning boshlanishi.",
    "📚 Bilim ko'paygani sari savollar ham ko'payadi.",
    "🌌 Biz bilgan narsalar bilmaganlarimizdan kichikroq.",
    "🧠 Fikrlar yo'nalishni o'zgartirishi mumkin.",
    "💬 So'zlar qisqa, ta'siri uzoq bo'lishi mumkin.",
    "🤝 Bir yaxshi so'z kimningdir kunini o'zgartiradi.",
    "❤️ Mehr hech qachon ortiqcha emas.",
    "🌱 Bugungi kichik qaror ertangi hayotni o'zgartirishi mumkin.",
    "🛤️ Har bir yo'lning o'z darsi bor.",
    "🏔️ Cho'qqiga chiqishdan oldin vodiydan o'tiladi.",
    "🌊 Chuqurlik har doim tashqaridan ko'rinmaydi.",
    "🪨 Sabr ham kuchning bir ko'rinishi.",
    "🕊️ Erkinlik mas'uliyat bilan birga keladi.",
    "🧭 O'zingizni yo'qotmasdan yo'nalishni o'zgartirish mumkin.",
    "🌿 Odam o'zgaradi, qadriyatlar esa yo'l ko'rsatadi.",
    "⌛ Kecha dars, bugun imkoniyat, ertaga noma'lum.",
    "🌅 Har tong kichik restartga o'xshaydi.",
    "🌄 Uzoq yo'l ham bir qadamdan boshlanadi.",
    "🔐 Ishonch sekin quriladi.",
    "🏛️ Kuchli poydevor ko'rinmaydi, lekin hammasini ushlab turadi.",
    "💡 Ba'zan javob emas, to'g'ri savol muhim.",
    "🧩 Har bir tajriba hayotning bir bo'lagi.",
    "🌍 Odamlar siz ko'rmagan janglarni boshdan kechirishi mumkin.",
    "🤫 Sukut ham tanlov.",
    "🕯️ Qorong'ulik nur borligini yanada sezdiradi.",
    "🍃 O'tmishni o'zgartirib bo'lmaydi, lekin uni tushunish mumkin.",
    "📜 Tarix takrorlanmasligi uchun uni eslash kerak.",
    "🪵 Eski yo'llarning ham o'z hikmati bor.",
    "🏺 Ba'zi qadriyatlar vaqt o'tsa ham qadrsizlanmaydi.",
    "🌳 Ildizlar ko'rinmaydi, lekin daraxtni ushlab turadi.",
    "🌊 Sokin suv ham chuqur bo'lishi mumkin.",
    "👁️ Ko'rish va tushunish bir xil narsa emas.",
    "🧠 Bilish va anglash orasida katta masofa bor.",
    "⏳ Sabrning natijasi darhol ko'rinmasligi mumkin.",
    "🌟 O'zligingizni saqlash ham katta g'alaba.",
    "🛡️ Chegara qo'yish ba'zan o'zingizni asrashdir.",
    "🧭 To'g'ri yo'l har doim eng oson yo'l emas.",
    "🏹 Maqsad aniq bo'lsa, ortiqcha yo'llar kamayadi.",
    "🌱 Har kuni ozgina o'sish ham o'sish.",
    "🌙 Tun fikrlarni balandroq eshittiradi.",
    "☀️ Yorug' kunlar qadrlanishi uchun qorong'u kunlar ham bo'ladi.",
    "🪞 O'zingizdan qochib uzoqqa borolmaysiz.",
    "📖 Hayotingizning keyingi bobini hali yozmagansiz.",
    "✍️ Ba'zi sahifalarni yangidan boshlash mumkin.",
    "🎭 Tashqi ko'rinish ichki hikoyani to'liq aytmaydi.",
    "🌍 Har bir odam o'z dunyosini olib yuradi.",
    "💚 O'zingizni yo'qotmaslik eng muhim yo'llardan biri.",
    "🌌 Savollar tugamasa ham, izlanish davom etadi.",


    # =========================================================
    # 🚀 MOTIVATION — 83
    # =========================================================

    "🚀 Bugun boshlash uchun mukammal vaqt shart emas.",
    "💪 Bir qadam ham oldinga hisoblanadi.",
    "🔥 Taslim bo'lmaslik — kuchli odat.",
    "🎯 Maqsadingizni eslang va davom eting.",
    "🏆 Katta natijalar kichik odatlardan keladi.",
    "🌱 Har kuni ozgina yaxshiroq bo'ling.",
    "⚡ Harakat qilmasangiz, natija ham bo'lmaydi.",
    "🧗 Cho'qqiga yo'l doim tekis emas.",
    "🚶 Sekin yurish ham oldinga yurish.",
    "💚 Never Give Up!",
    "🌟 Bugun kechagidan kuchliroq bo'ling.",
    "🔥 Qiyinchilik — to'xtash belgisi emas.",
    "🎯 Diqqatni maqsadga qaytaring.",
    "🏹 Nishonni bilgan odam yo'l topadi.",
    "💡 O'zingizga imkon bering.",
    "🚀 G'oyani harakatga aylantiring.",
    "🛠️ Orzu rejasiz qolmasin.",
    "📈 Kichik progress ham progress.",
    "⏳ Natija vaqt talab qiladi.",
    "🌱 Bugun eking, ertaga natijasini ko'rasiz.",
    "💪 Qiyin bo'lsa, sabrni oshiring.",
    "🏆 G'alaba ko'pincha davom etgan odamga keladi.",
    "🔥 Oson yo'l har doim eng yaxshi yo'l emas.",
    "🎯 Bir vaqtning o'zida bitta vazifa.",
    "🚀 Qo'rquvga qaramay boshlash — jasorat.",
    "🧠 O'rganishdan to'xtamang.",
    "📚 Bilimni amalda sinang.",
    "⚙️ Intizom motivatsiyadan uzoqroq yuradi.",
    "🕒 Vaqtingizni qadrlang.",
    "🌅 Har kun yangi imkoniyat.",
    "☀️ Bugun hali tugamadi.",
    "💥 O'zingiz kutgan o'zgarishni boshlang.",
    "🧭 Yo'nalishni yo'qotsangiz, maqsadni qayta ko'ring.",
    "🏗️ Poydevorni mustahkam quring.",
    "🚧 To'siq — boshqa yo'l topish uchun signal.",
    "🔨 Ishni kichik qismlarga bo'ling.",
    "🎮 Hayotdagi questni ham bosqichma-bosqich bajaring.",
    "⭐ O'zingizning rekordlaringizni yangilang.",
    "🏃 Harakatni to'xtatmang.",
    "💎 Bosim ostida ham qimmatli narsalar yaratiladi.",
    "🔥 Bugungi mehnat ertangi natijaga aylanadi.",
    "🌟 O'zingizga bergan va'dangizni unutmang.",
    "🛡️ Maqsadingizni keraksiz shovqindan himoya qiling.",
    "🎯 Diqqat — kuch.",
    "🧠 Sabr — strategiya.",
    "💪 Intizom — tayanch.",
    "🚀 Harakat — boshlanish.",
    "🏆 Natija — davomiylik.",
    "🌱 O'sish — jarayon.",
    "🔥 Qayta urinish — imkoniyat.",
    "⚡ Bir qaror butun yo'nalishni o'zgartirishi mumkin.",
    "🛤️ Yo'l uzoq bo'lsa ham davom eting.",
    "🏔️ Tog' uzoqdan katta ko'rinadi, yaqinlashgan sari qadamlar ko'rinadi.",
    "🚪 Bir eshik yopilsa, boshqa imkoniyat qidiring.",
    "💡 G'oyangizni kichik deb hisoblamang.",
    "🧩 Har bir qadam umumiy rasmni to'ldiradi.",
    "🌍 Katta maqsadlar katta sabr talab qiladi.",
    "🕰️ Vaqt o'tadi. Uni nimaga sarflash sizga bog'liq.",
    "🎯 Bugungi eng muhim ishni tanlang.",
    "📈 Kechagi xatodan bugungi dars yarating.",
    "💪 Kuchli bo'lish — hech qachon qiynalmaslik emas.",
    "🔥 Qiyinchilikdan keyin tajriba qoladi.",
    "🚀 Harakat qilgan odam yangi imkoniyatlarni ko'radi.",
    "🌟 O'zingizni kichraytirmang.",
    "🧠 O'rganishning oxiri yo'q.",
    "🏆 Natijani kutmang, jarayonni boshlang.",
    "🔧 O'zingizni ham loyiha kabi rivojlantiring.",
    "🌱 Har bir kun yangi commit.",
    "💻 Hayotingizning kodini o'zingiz yozing.",
    "🎮 Quest tugamadi.",
    "⚔️ Bugungi boss — kechagi o'zingiz.",
    "🛡️ Maqsadni himoya qiling.",
    "🏹 Birinchi o'q nishonga tegmasa, ikkinchisini yaxshiroq nishonlang.",
    "🔥 Energiya kam bo'lsa ham, kichik qadam qiling.",
    "🚶 To'xtab qolmaslikning o'zi yutuq.",
    "💚 O'zingizga ishoning, keyin ishingiz bilan isbotlang.",
    "🌅 Ertangi kun bugungi qarorlardan boshlanadi.",
    "🚀 Never Give Up — yo'l davom etadi.",


    # =========================================================
    # 🤖 BOT — 83
    # =========================================================

    "🤖 Bot ishga tushdi. Hamma narsa nazorat ostida.",
    "⚡ Criperman Bot navbatchilikda.",
    "👀 Bot hammasini ko'rib turibdi.",
    "🛡️ Guruh himoyasi faol.",
    "📡 Signal qabul qilindi.",
    "💻 Serverlar ishlayapti.",
    "🔧 Bot bugun ham xizmatda.",
    "🚀 Criperman Bot yana online.",
    "🤖 Men botman, lekin zerikmayman.",
    "📊 Statistikalar yig'ilmoqda.",
    "🎂 Tug'ilgan kunlar nazoratda.",
    "🏆 TOP ro'yxati yangilanmoqda.",
    "👥 Yangi odamlar kutib olinmoqda.",
    "🛡️ Spamga qarshi qalqon tayyor.",
    "🚫 Taqiqlangan kontentga joy yo'q.",
    "🤖 Begona botlar ehtiyot bo'lsin.",
    "📺 Kanallar tayyor.",
    "🎁 Donate havolasi ham tayyor.",
    "📖 /help sizni kutmoqda.",
    "🆔 /id hammasini aniqlaydi.",
    "📡 Telegram bilan aloqa barqaror.",
    "⚙️ Bot sozlamalari ishlayapti.",
    "💾 Ma'lumotlar bazasi xotirada.",
    "🗃️ Database bugun ham ishlayapti.",
    "🔄 Bot harakatda.",
    "🧠 Algoritmlar uyg'oq.",
    "👁️ Har bir xabar nazoratdan o'tmoqda.",
    "🛡️ Himoya tizimi faol.",
    "🚨 Shubhali xabar ko'rinsa, bot tayyor.",
    "💬 Chat jim bo'lsa ham bot online.",
    "🌐 Bot internet bilan bog'langan.",
    "⚡ Javob berish tizimi tayyor.",
    "🔍 Qidiruv rejimi emas, kuzatuv rejimi.",
    "📋 Buyruqlar ro'yxati tayyor.",
    "🎯 Buyruq bering, bot bajarishga harakat qiladi.",
    "🤖 Botda ham ish vaqti yo'q.",
    "🌙 Kechasi ham navbatchilik davom etadi.",
    "☀️ Ertalab ham bot online.",
    "🕒 Vaqt o'tadi, bot ishlaydi.",
    "🎂 Birthday checker uyg'oq.",
    "📢 Reklama scheduler ishga tayyor.",
    "🌟 Splash text generator ishlayapti.",
    "🎲 Random tanlov amalga oshmoqda.",
    "📊 Statistikalar jim turmaydi.",
    "👥 Invite counter sanamoqda.",
    "🏆 Bugun kim TOPga chiqadi?",
    "🛡️ Adminlar tinch, bot ishlayapti.",
    "🔐 Maxfiy ma'lumotlar kodga yozilmagan.",
    "⚙️ Har bir handler o'z vazifasida.",
    "📦 Dependency'lar joyida.",
    "🐍 Python dvigateli ishlayapti.",
    "🟢 Polling faol.",
    "📡 Update qabul qilindi.",
    "🔄 Telegramdan yangi xabar keldi.",
    "💻 Terminal jim, bot esa ishlayapti.",
    "📜 Loglar hammasini yozib bormoqda.",
    "🐛 Bug topilsa, tuzatishga harakat qilamiz.",
    "🚧 Ba'zi funksiyalar hali qurilmoqda.",
    "🔨 Bot asta-sekin kuchaymoqda.",
    "🌱 Har bir update yangi tajriba.",
    "🚀 Yangi feature yo'lda.",
    "🧩 Handlerlar bir-biri bilan ishlamoqda.",
    "🎯 Buyruq to'g'ri bo'lsa, javob ham tayyor.",
    "📨 Xabar yetib keldi.",
    "💬 Chat listener uyg'oq.",
    "🛡️ Filter tekshiruvi bajarilmoqda.",
    "🤖 Bot o'zini yaxshi his qilmoqda.",
    "🔋 Server energiyasi yetarli.",
    "☁️ Cloud ichida yashayotgan bot.",
    "🌍 Bir bot, ko'plab guruhlar.",
    "📡 Har bir guruh o'z sozlamasiga ega.",
    "📺 Har bir guruhga o'z kanallari.",
    "👑 Owner aniqlash tizimi faol.",
    "👋 Salomlarga javob berish tayyor.",
    "🎂 Birthday tizimi bugun ham eslab qoladi.",
    "🏆 Invite tizimi hisoblaydi.",
    "📈 Statistikalar ortib bormoqda.",
    "🔧 Criperman Bot yangilanmoqda.",
    "💚 Never Give Up — bot ham shuni biladi.",
    "🤖 Criperman Bot: online, alert, ready.",
    "🧠 Miya ishlayapti... 3%...",
"💻 Kod ishladi. Nega ishlaganini so'ramang.",
"🐛 Bug topildi. Bug: men.",
"🚀 Deploy qilindi. Endi duo qilamiz.",
"☕ Kod yozish uchun kofe emas, sabr kerak.",
"⌨️ Klaviatura: men aybdor emasman.",
"💀 Error 404: miyam topilmadi.",
"🤖 Bot ham bugun dam olmoqchi.",
"🎮 Minecraft ochildi — reja bekor qilindi.",
"⛏️ Olmos topilmadi. Lekin umid bor.",
"🧱 Bitta blok qo'yaman degandim... 3 soat o'tdi.",
"🐄 Minecraftdagi sigir ham mendan ko'proq dam oladi.",
"🌳 Daraxtni kesdim. Endi ekologlar kelmasin.",
"🔥 Creeper: men shunchaki salom bermoqchi edim.",
"🐉 Ender Dragon kutyapti, men esa ovqat izlayapman.",
"🗿 Steve hech qachon 'men charchadim' demaydi.",
"😂 Reja zo'r edi. Faqat ishlamadi.",
"💀 Men: hammasi nazorat ostida. Hayot: yo'q.",
"🗣️ NIIIMAGAAAAP?!",
"🗣️ SIX SEVEN!",
"Mam: Men senga necha marta aytdim?",
"Mam: sen odam bo'laysan kuchuk",
"Mam: sendan kora it baqsam yaxshi edi",
"Mam: Qachon odam bo'lasan?",
"Mam: Telefonni qo'y!",
"Mam: Telefoningdan bosh ko'tarmaysan.",
"Mam: Kompyuterni o'chir!",
"Mam: Yana kompyuterda o'tiribsanmi?",
"Mam: Avval darsingni qil, keyin o'yna.",
"Mam: Qara, qo'shnining bolasi nima qilyapti.",
"Mam: Qara, qo'shnining bolasi IELTS'dan 9 olibdi.",
"Mam: Men sening yoshingda...",
"Mam: Bizning paytimizda bunaqa narsalar yo'q edi.",
"Mam: Uyda hech narsa qilmay o'tiribsan.",
"Mam: Xonangni yig'ishtir!",
"Mam: Uyingni uy qil!",
"Mam: Eshikni yop!",
"Mam: Chiroqni o'chir, elektr tekin emas.",
"Mam: Suvni bekorga oqizma!",
"Mam: Kranni yop!",
"Mam: Ovqat tayyor, kel!",
"Mam: Ovqating sovib qoldi!",
"Mam: Ovqatni tashlab ketma!",
"Mam: Qorning och bo'lmasa ham ovqat ye.",
"Mam: Choy ichib ol.",
"Mam: Nonni uvol qilma!",
"Mam: Nonni yerga tashlama!",
"Mam: Sovuq, ustingga biror narsa kiy!",
"Mam: Kurtkangni kiyib ol!",
"Mam: Paypoq kiy!",
"Mam: Kasal bo'lib qolasan!",
"Mam: Ko'chada ko'p yurmagin.",
"Mam: Qayerga ketyapsan?",
"Mam: Kim bilan ketyapsan?",
"Mam: Qachon qaytasan?",
"Mam: Telefoningni zaryadga qo'y.",
"Mam: Telefoning o'chib qolmasin.",
"Mam: Internetni kim to'layapti o'zi?",
"Mam: Pul daraxtda o'smaydi.",
"Mam: Pulni supurib olyapmanmi?!",
"Mam: Do'konga borib kel.",
"Mam: Yo'lda non olib kel.",
"Mam: Axlatni chiqarib qo'y.",
"Mam: Mehmon keladi, uyni yig'ishtir!",
"Mam: Mehmonlar oldida bunaqa gapirma.",
"Mam: Salom berishni o'rgan.",
"Mam: Kattalarga hurmat bilan gapir.",
"Mam: Men aytmasam o'zing qilolmaysanmi?",
"Mam: Bitta ishni ham vaqtida qilmaysan.",
"Mam: Hozir qilaman deganing qachon keladi?",
"Mam: Keyin qilaman deganing — hech qachonmi?",
"Mam: Ertaga qilaman demagin.",
"Mam: Tur, tush bo'lib ketdi!",
"Mam: Yana uxlayapsanmi?",
"Mam: Kechasi vaqtida uxla!",
"Mam: Ertalab turish qiyin bo'ladi.",
"Mam: Ko'zing buziladi, telefonga kamroq qara.",
"Mam: Quloqchin bilan yuraverma!",
"Mam: Ovozni pasaytir!",
"Mam: Nima eshityapsan o'zi?",
"Mam: Kim bilan gaplashyapsan?",
"Mam: Nima kulasan?",
"Mam: Nima bo'ldi?",
"Mam: Tinch o'tir.",
"Mam: O'zingni bos.",
"Mam: Odamlar nima deydi?",
"Mam: Boshqalarga qarab ish qilma.",
"Mam: Odamlar tomdan tashlasa, sen ham tashla!",
"Mam: Boshing toshdan bo'lsin.",
"Mam: Yaxshi o'qi, kelajakda o'zingga kerak bo'ladi.",
"Mam: O'qish kerak, bolam.",
"Mam: Bir kun kelib o'zing tushunasan.",
"Mam: Men sen uchun aytyapman.",
"Mam: Men senga yomonlik tilamayman.",
"Mam: Gapimni bir marta eshit.",
"Mam: Necha marta takrorlayman?",
"Mam: Yana aytib o'tirmayman.",
"Mam: Hozir borib qil!",
"Mam: Hozir deganim — hozir!",
"Mam: Besh daqiqang bir soat bo'ldi.",
"Mam: Bo'ldi, yetadi.",
"Mam: Qani, tur!",
"Mam: Qo'y, o'zim qilaman.",
"Mam: Kel, yordam ber.",
"Mam: Buni qayerdan o'rganding?",
"Mam: Kim o'rgatdi senga?",
"Mam: O'zing o'ylab ko'r.",
"Mam: Meni ham bir marta tingla.",
"Mam: Onangning gapini eshit.",
"Mam: Boshimga qo'y!",
"💸 Pul topish uchun ishlash kerak, bomj.",
"🥤 Bir og'iz Cola so'radi — olib keldim.",
"🍊 Mandarinni ochadi.",
"🗿 Boshing toshdan bo'lsin.",
"🔥 Yigit kishining omadi bilan o'ynashma.",
"🤨 Bu qanaqa mantiq o'zi?",
"📡 Internet bor. Fikr yo'q.",
"🔋 Batareya 1%. Motivatsiya 100%.",
"🌙 Kechasi kelgan g'oya ertalab yo'qoladi.",
"🧠 Bugun o'rgangan narsang ertaga foyda beradi.",
"🚶 Kichik qadam ham qadam.",
"🏆 Rekord hali buzilmagan bo'lsa, demak imkon bor.",
"💚 Never Give Up!",
"🌟 Bugun kechagidan yaxshiroq bo'lishga harakat qil.",
"🔥 Xato qildingmi? Demak, tajriba olding.",
"🎯 Maqsad aniq. Yo'l biroz chalkash.",
"🚀 Sekin bo'lsa ham oldinga.",
"🛠️ Tuzatishdan qo'rqma, buzilgan narsa ham tuzaladi.",
"👀 Bot sizni kuzatmayapti... shunchaki online.",
"🤖 Men botman, lekin bugun kayfiyatim bor.",
"📊 Statistika yolg'on gapirmaydi. Ba'zida odamlar gapiradi.",
"⚡ Server tirik. Hozircha.",
"🧑‍💻 Ctrl+Z hayotda ham bo'lsa edi.",
"🐷👑 Technoblade never dies. NEVER DIES!",
"java.py java dasturlash tili men bu yerda nima qilyapman o'zi... java:mani java.py deb chaqirmanglar, iltimos"
]


# =========================================================
# BAD WORDS
# =========================================================

SAVOLLAR = [
    "⚖️ Adolat hamma uchun bir xil bo'lishi kerakmi yoki har bir odamning holatiga qarab o'zgarishi kerakmi?",
    "🕵️ Haqiqatni bilish biror odamga zarar yetkazsa ham, uni aytish kerakmi?",
    "🧠 Agar sening barcha xotiralaring o'chirilib, aynan sening tanangga boshqa xotiralar yozilsa — u odam hali ham senmisan?",
    "🔄 Kecha qilgan xatongni o'zgartirsang, bugungi 'sen' ham o'zgaradimi?",
    "⚖️ Bir begunoh odamni jazolab, minglab odamni qutqarish mumkin bo'lsa, bu adolatmi?",
    "🗿 Hech kim bilmaydigan yaxshilikni qilishning qiymati bormi?",
    "🎭 Odam yaxshi ishni faqat boshqalar uni yaxshi deb o'ylashi uchun qilsa, u baribir yaxshi odammi?",
    "🧩 Qonun adolatsiz bo'lsa, qonunni buzish jinoyatmi yoki adolatmi?",
    "👁️ Hamma odam bir xil voqeani ko'rib, har xil xulosa chiqarsa, 'haqiqat' qaysi biri?",
    "🕰️ Agar kelajakdagi sen bugungi qaroring noto'g'ri ekanini bilsa, bugungi sen o'z qarorini o'zgartirishi kerakmi?",
    "🧠 Agar yolg'on bir insonni baxtli qilsa, haqiqat esa uni sindirsa — qaysi birini tanlaysan?",
    "⚔️ Yomon odamni to'xtatish uchun o'zing ham yomon ish qilishga majbur bo'lsang, chegarani qayerda qo'yasan?",
    "👤 Agar hech kim seni eslamasa, hayotingdagi qilgan yaxshi ishlaring baribir ma'nolimi?",
    "♾️ Abadiy yashash imkoniyati berilsa, lekin sevganlaringning hammasi seni tark etib boraversa, uni tanlaysanmi?",
    "🪞 Odam o'zini boshqalarning ko'zi orqali ko'rmasa, o'zining qanday inson ekanini qayerdan biladi?",
    "💭 Fikringni o'zing tanlaysanmi yoki seni tarbiyalagan muhit tanlaydimi?",
    "⚖️ Do'sting nohaq bo'lsa, uni himoya qilish do'stlikmi yoki unga xiyonatmi?",
    "🔥 Maqsad yaxshi bo'lsa, unga erishish uchun har qanday vositadan foydalanish mumkinmi?",
    "🧠 Agar barcha qarorlaring miyangdagi jarayonlarning natijasi bo'lsa, 'erkin tanlov' aslida bormi?",
    "🌌 Agar koinotda insoniyatdan boshqa hech kim bo'lmasa, insoniyatning mavjudligi nimaga kerak?",
    "🧩 Nega ko'p odamlar yaxshilikni xohlaydi, lekin yomonlikka tezroq yo'l oladi?",
    "💬 Nega odam ba'zan o'zi bilmagan narsani juda qattiq himoya qiladi?",
    "🕳️ Agar sening ichki dunyoing bo'sh bo'lsa, nima to'ldiradi?",
    "🎭 Odamlar o'zlarini 'haqiqiy' deb o'ylashlari uchun qanday narsalarni o'ylashlari kerak?",
    "🌊 Odamlar bir-birini tushunish uchun nima bilan boshlashlari kerak?",
    "⚙️ Agar dunyo sizga noto'g'ri bo'lsa, kimning xatosi ko'proq — sizningmi yoki dunyoningmi?",
    "🧠 Agar miyang sizga yolg'on aytsa, uni qayerdan bilsangiz bo'ladi?",
    "🔒 Agar sirni saqlash uchun unga hech kimga bildirmaslik kerak bo'lsa, bu o'zingga qanchalik zarar yetkazadi?",
    "💊 Ba'zan eng kuchli odamlar eng ko'p og'riqni yashiradimi?",
    "🧬 Agar insoniyat hayotining ma'nosi bo'lsa, kim uni ta'riflaydi?",
    "📚 Nega ba'zi bilimlar ko'pchilikka ma'lum bo'lsa-da, odamlar ularni ishlatmaydi?",
    "🕊️ Odam o'zini boshqalar kamsitishini istamaydi, lekin ba'zan qadr-qimmatni ham kamsitadi. Nega?",
    "🧭 Agar yo'l xato bo'lsa, uni o'zgartirish qanchalik jasorat kerak?",
    "🪐 Odamlar nega doim kosmosni kuzatishadi, lekin o'zlarining ichki dunyosini unutasalar?",
    "🌌 Agar koinotning ma'nosi bo'lsa, uni odam yaratadimi yoki topadi?",
    "⚖️ Odamning adolati uning kuchiga emas, uning imtihonlariga bog'liqmi?",
    "🧠 Agar o'zingni haqiqiy deb his qilmasang, senga kim haqiqiyatni aytadi?",
    "🧩 Nega ba'zi odamlar kelajak haqida ko'p gapiradi, lekin hozirgi lahzani yashamaydi?",
    "🛡️ Bosqinchi biror narsaga tahdid solganda, kimni himoya qilish yaxshiroq: himoyachini mi yoki zaifni mi?",
    "🎲 Hayotda tasodif nima? Odamning tanlovi bilan chiziqlanganmi yoki mustaqilmi?",
    "💬 Agar o'zingga haqiqat yoqmasa, uni e'tirof qilishning o'zi halokatmi?",
    "🌧️ Qanday qilib insonlar duygularini yashiradi, lekin ularning ta'siri davom etaveradi?",
    "🕯️ Agar imon yo'q bo'lsa, yaxshi niyatlar qayerga boradi?",
    "🧠 Odamni o'zgartiradigan narsa uning xatosi emas, uning o'zi ko'rgan haqiqatmi?",
    "🏔️ Katta yutuq ba'zan kichik qarordan boshlanadimi?",
    "🌞 Nega ba'zi odamlar bir marta yaxshi ish qilgach, uni butun hayot uchun mukofot deb qarashadi?",
    "🧵 Odam o'zini tasvir qilishda qanchalik so'zlardan foydalanadi?"
]

# ==========================================
# BAD WORDS SOZLAMALARI VA FAYLLAR
# ==========================================

BAD_WORDS_FILE = os.path.join(os.path.dirname(__file__), "bad_words.txt")
WARNING_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "warning_word.jpg") # Taqiqlangan so'z uchun rasm

DEFAULT_BAD_WORDS = [
    "ahmoq", "zb", "axmoq", "dalbayob", "poxoy", "dnx", "ph", "dapa", "dappa", 
    "jinni", "jalab", "lox", "tentak", "yban", "yiban", "gandon", "гандон", 
    "гей", "далбаеб", "далбаёб", "ебан", "ебать", "жалаб", "лохсан", "пидр", 
    "спам", "сука", "сикай", "тупой", "хакерлик", "хароми", "чит борми", 
    ".onion", "18+", "porno", "sex", "fock", "f*ck", "f u c k", "kot", "ko't", 
    "neger", "시발", "https://youtube.com/@artijon", "https://t.me/artijonuzb", "porn.hub"
]

MANUAL_LINK_BLOCKED_USERS = {
    "5144283333",
}

def is_manual_link_blocked_user(message: types.Message) -> bool:
    if not message.from_user:
        return False

    username = (message.from_user.username or "").strip().lower()
    user_id = str(message.from_user.id)
    candidates = {user_id, username, f"@{username}"}

    normalized = {
        item.strip().lower()
        for item in MANUAL_LINK_BLOCKED_USERS
        if item and item.strip()
    }
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

def save_bad_words(words):
    try:
        with open(BAD_WORDS_FILE, "w", encoding="utf-8") as f:
            for w in words:
                f.write(w.strip() + "\n")
    except Exception as e:
        logging.error(f"bad_words: error saving file: {e}")

BAD_WORDS = load_bad_words()

# ==========================================
# TAQIQLANGAN SO'ZLARNI USHLASH VA RASM YUBORISH (HANDLER)
# ==========================================

@dp.message(F.text & F.chat.type.in_({"group", "supergroup"}))
async def check_bad_words_handler(message: types.Message):
    if not message.text:
        return

    text_lower = message.text.lower()
    
    # Matn ichida taqiqlangan so'zlardan biri bor-yo'qligini tekshirish
    has_bad_word = any(bad_word.lower() in text_lower for bad_word in BAD_WORDS)
    
    if has_bad_word:
        try:
            # 1. Haqoratomuz yoki taqiqlangan so'zli xabarni o'chirish
            await message.delete()
        except Exception as e:
            logging.error(f"Xabarni o'chirishda xato (Bot administrator emasmi?): {e}")

        # 2. Foydalanuvchini ogohlantirish uchun rasm va caption tayyorlash
        user_mention = message.from_user.get_mention(as_html=True)
        caption_text = (
            f"⚠️ {user_mention}, iltimos, guruhda taqiqlangan soʻz ishlatmang!\n"
            f"<i>Madaniyatli boʻling va qoidalarga rioya qiling.</i>"
        )

        try:
            # Rasm faylini tekshirish va yuborish
            if os.path.exists(WARNING_IMAGE_PATH):
                photo = FSInputFile(WARNING_IMAGE_PATH)
                await message.answer_photo(
                    photo=photo,
                    caption=caption_text,
                    parse_mode="HTML"
                )
            else:
                # Agar rasm fayli topilmasa, shunchaki tekstini yuborish
                await message.answer(
                    text=caption_text,
                    parse_mode="HTML"
                )
        except Exception as e:
            logging.error(f"Ogohlantirish rasmini yuborishda xato: {e}")


# ==========================================
# HTTP ADMIN SERVER (WEBSITE INTEGRATION)
# ==========================================

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "change-me")
BAD_WORDS_HOST = os.getenv("BAD_WORDS_HOST", "127.0.0.1")
BAD_WORDS_PORT = int(os.getenv("BAD_WORDS_PORT", "8080"))

async def _require_auth(data: dict):
    token = data.get("token") if isinstance(data, dict) else None
    return token == ADMIN_TOKEN

async def handle_list_bad_words(request):
    return web.json_response({"words": load_bad_words()})

async def handle_add_bad_word(request):
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "invalid json"}, status=400)

    if not await _require_auth(data):
        return web.json_response({"error": "unauthorized"}, status=401)

    word = (data.get("word") or "").strip()
    if not word:
        return web.json_response({"error": "missing word"}, status=400)

    current = load_bad_words()
    if word.lower() in (w.lower() for w in current):
        return web.json_response({"status": "exists"})

    current.append(word)
    save_bad_words(current)

    global BAD_WORDS
    BAD_WORDS = current

    return web.json_response({"status": "ok", "added": word})

async def handle_remove_bad_word(request):
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "invalid json"}, status=400)

    if not await _require_auth(data):
        return web.json_response({"error": "unauthorized"}, status=401)

    word = (data.get("word") or "").strip()
    if not word:
        return web.json_response({"error": "missing word"}, status=400)

    current = load_bad_words()
    new = [w for w in current if w.lower() != word.lower()]

    if len(new) == len(current):
        return web.json_response({"status": "not_found"})

    save_bad_words(new)
    global BAD_WORDS
    BAD_WORDS = new

    return web.json_response({"status": "ok", "removed": word})

@web.middleware
async def cors_middleware(request, handler):
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        }
        return web.Response(status=200, headers=headers)

    resp = await handler(request)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

async def start_bad_words_server():
    app = web.Application(middlewares=[cors_middleware])
    app.router.add_get('/badwords', handle_list_bad_words)
    app.router.add_get('/badwords/list', handle_list_bad_words)
    app.router.add_post('/badwords/add', handle_add_bad_word)
    app.router.add_post('/badwords/remove', handle_remove_bad_word)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, BAD_WORDS_HOST, BAD_WORDS_PORT)
    await site.start()

    logging.info(f"Bad words admin HTTP server started on {BAD_WORDS_HOST}:{BAD_WORDS_PORT}")
# =========================================================
# HELPERS
# =========================================================

def save_group(chat_id):
    cursor.execute(
        "INSERT OR IGNORE INTO groups(chat_id) VALUES (?)",
        (str(chat_id),)
    )
    db.commit()



def get_saved_groups():
    cursor.execute("SELECT chat_id FROM groups")
    return [row[0] for row in cursor.fetchall()]


async def is_group_admin(message: types.Message) -> bool:
    if message.chat.type not in ("group", "supergroup"):
        return False

    try:
        member = await message.bot.get_chat_member(
            message.chat.id,
            message.from_user.id
        )
    except Exception:
        return False

    return member.status in ("administrator", "creator")


def has_link(text: str) -> bool:
    if not text:
        return False

    pattern = r"""
        (?:
            https?://
            |
            www\.
            |
            t\.me/
            |
            telegram\.me/
            |
            [a-zA-Z0-9-]+\.(?:com|net|org|uz|ru|io|me|xyz|site|online)
        )
    """

    return bool(re.search(pattern, text, re.IGNORECASE | re.VERBOSE))


async def get_link_target_user(message: types.Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user

    args = (message.text or "").split()
    if len(args) < 2:
        return None

    username_or_id = args[1]

    if username_or_id.startswith("@"):
        try:
            return await message.bot.get_chat(username_or_id)
        except Exception:
            return None

    if username_or_id.isdigit():
        try:
            return await message.bot.get_chat(int(username_or_id))
        except Exception:
            return None

    return None


def is_user_link_blocked(chat_id: int, user_id: int) -> bool:
    cursor.execute(
        "SELECT 1 FROM link_blocks WHERE chat_id=? AND user_id=?",
        (chat_id, user_id),
    )
    return cursor.fetchone() is not None


def set_user_link_block(chat_id: int, user_id: int, blocked: bool):
    if blocked:
        cursor.execute(
            "INSERT OR IGNORE INTO link_blocks (chat_id, user_id) VALUES (?, ?)",
            (chat_id, user_id),
        )
    else:
        cursor.execute(
            "DELETE FROM link_blocks WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
    db.commit()


# =========================================================
# ELEMENT BATTLE GAME
# =========================================================

# Balanced element system - each element beats 3 and loses to 3
ELEMENTS = {
    "🔥 Olov": {
        "beats": ["🌳 Daraxt", "🧊 Muz", "🍃 Bargli"]
    },
    "💧 Suv": {
        "beats": ["🔥 Olov", "⏳ Lava", "🪵 Loy"]
    },
    "⚡ Chaqmoq": {
        "beats": ["💧 Suv", "⚙️ Metall", "🌩️ Firtina"]
    },
    "🌪️ Shamol": {
        "beats": ["🌫️ Tutun", "🔥 Olov", "🍃 Bargli"]
    },
    "⏳ Lava": {
        "beats": ["🪨 Tosh", "🧊 Muz", "⚙️ Metall"]
    },
    "🪨 Tosh": {
        "beats": ["🔥 Olov", "⚡ Chaqmoq", "🧊 Muz"]
    },
    "⚙️ Metall": {
        "beats": ["🪨 Tosh", "🌳 Daraxt", "💎 Kristall"]
    },
    "💡 Nur": {
        "beats": ["🌑 Soya", "🌫️ Tutun", "🧊 Muz"]
    },
    "🌑 Soya": {
        "beats": ["🌙 Oy", "💎 Kristall", "🧠 Savol"] # Qorong'ulik va sirli elementlar
    },
    "🧊 Muz": {
        "beats": ["💧 Suv", "🍃 Bargli", "🌳 Daraxt"]
    },
    "🌙 Oy": {
        "beats": ["💡 Nur", "☀️ Quyosh", "🌟 Yulduz"] # Tungi osmon ustunligi
    },
    "☀️ Quyosh": {
        "beats": ["🌑 Soya", "🧊 Muz", "🌙 Oy"]
    },
    "📦 Qum": {
        "beats": ["🔥 Olov", "💧 Suv", "⚡ Chaqmoq"] # Qum olov va suvni ko'madi, tokni o'tkazmaydi
    },
    "🍃 Bargli": {
        "beats": ["📦 Qum", "💧 Suv", "🪵 Loy"]
    },
    "🌳 Daraxt": {
        "beats": ["📦 Qum", "🪨 Tosh", "🪵 Loy"] # Ildizlari bilan tuproq/toshni yoradi
    },
    "🌫️ Tutun": {
        "beats": ["💡 Nur", "☀️ Quyosh", "🍃 Bargli"] # Quyosh nurini to'sadi, o'simlikni bo'g'adi
    },
    "💎 Kristall": {
        "beats": ["💡 Nur", "⚡ Chaqmoq", "🔥 Olov"] # Nurni qaytaradi, tok va issiqqa chidamli
    },
    "🪵 Loy": {
        "beats": ["🔥 Olov", "📦 Qum", "💎 Kristall"]
    },
    "🌩️ Firtina": {
        "beats": ["🌳 Daraxt", "🌪️ Shamol", "📦 Qum"]
    },
    "🌟 Yulduz": {
        "beats": ["🌑 Soya", "🌫️ Tutun", "🌩️ Firtina"]
    }
}

# Game sessions storage
game_sessions = {}


def create_element_buttons():
    """Create inline keyboard buttons for all elements"""
    buttons = []
    elements_list = list(ELEMENTS.keys())
    
    # Create 4 rows with 5 buttons each (20 total)
    for i in range(0, len(elements_list), 5):
        row = []
        for j in range(5):
            if i + j < len(elements_list):
                element = elements_list[i + j]
                row.append(
                    types.InlineKeyboardButton(
                        text=element,
                        callback_data=f"battle_{element.split()[1]}"
                    )
                )
        buttons.append(row)
    
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.message(Command("battle"))
async def battle_command(message: types.Message):
    """Start an Element Battle game"""
    user_id = message.from_user.id
    
    # Create game session
    game_sessions[user_id] = {
        "status": "waiting_for_choice",
        "message_id": None
    }
    
    keyboard = create_element_buttons()
    
    sent_message = await message.answer(
        "🔥 <b>ELEMENT BATTLE</b> 🔥\n\n"
        "🎮 O'z unsuringizni tanlang:\n\n"
        "<i>Har bir unsur boshqasindan quvvatli, boshqasidan zaif.</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    game_sessions[user_id]["message_id"] = sent_message.message_id


@dp.callback_query(lambda query: query.data.startswith("battle_"))
async def process_battle(query: types.CallbackQuery):
    """Process element selection and determine winner"""
    user_id = query.from_user.id
    
    # Get the element code (last part of callback data)
    element_name_part = query.data.replace("battle_", "")
    
    # Find the full element name
    user_element = None
    for elem in ELEMENTS.keys():
        if elem.split()[1] == element_name_part:
            user_element = elem
            break
    
    if not user_element:
        await query.answer("❌ Unsur topilmadi!", show_alert=True)
        return
    
    # Bot chooses random element
    bot_element = random.choice(list(ELEMENTS.keys()))
    
    # Determine result
    if user_element == bot_element:
        result = "🤝 DURANG!"
        result_emoji = "🤝"
        result_text = "Ikkalangiz ham bir xil unsur tanladingiz!"
    elif bot_element in ELEMENTS[user_element]["beats"]:
        result = "🏆 SIZNING G'ALIBI!"
        result_emoji = "🏆"
        result_text = f"{user_element} {bot_element}ni yutdi!"
    else:
        result = "💀 SIZNING MAGLUBIYTINGIZ!"
        result_emoji = "💀"
        result_text = f"{bot_element} {user_element}ni yutdi!"
    
    # Build result message
    result_message = (
        f"⚔️ <b>JANG BOSHLANDI!</b>\n\n"
        f"👤 <b>Siz:</b> {user_element}\n"
        f"🤖 <b>Curina Bot:</b> {bot_element}\n\n"
        f"<b>{user_element} 🆚 {bot_element}</b>\n\n"
        f"<b>{result}</b>\n"
        f"<i>{result_text}</i>\n\n"
        f"<code>/battle</code> - yana o'ynash uchun"
    )
    
    # Edit the original message with result
    try:
        await query.message.edit_text(
            result_message,
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Error editing message: {e}")
        await query.message.answer(result_message, parse_mode="HTML")
    
    # Clean up session
    if user_id in game_sessions:
        del game_sessions[user_id]
    
    await query.answer()


# =========================================================
# START
# =========================================================

@dp.message(Command("start"))
async def start_command(message: types.Message):

    save_group(message.chat.id)

    await message.answer(
        "🤖 <b>curinasan bot</b>ga xush kelibsiz!\n\n"
        "👋guruhizga qoshsayiz odamlar qoshilsa Welcome matnini chiqaradi\n"
        "🎮/battle tosh qaychi qogoz oyinini antiqa va ajoyib qolingani o'ynab ko'ring\n"
        "🎂 /birthday kk.oo buyrugi bilanguruhdagi odam tugulgan kuni eslab qolib oshakuni tabrikladi \n"
        "🏆 /top kim ko'p odam qoshganini top 10taligini qiladiz\n"
        "👥 /count siz nechta odam qoshganizni aytadi\n"
        "🎁 /danat bot qolab quvatlash uchun danat qilsayiz bo'ladi\n"
        "ℹ️ /info bot haqida qisqa malumat\n"
        "📖 /help barcha buyruqlar qanday ishlashini ko'rsatadi\n\n"
        "💚 Never Give Up! hech qachon tashlim bolmang",
        parse_mode="HTML"
    )


# =========================================================
# HELP
# =========================================================

@dp.message(Command("help"))
async def help_command(message: types.Message):

    await message.answer(
        "📖 <b>curinasan Boti buyruqlari nimalar qila oladi</b>\n\n"
        "🎂 /birthday 15.08 — tug'ilgan kunni saqlash\n"
        "🎈 /mybirthday — tug'ilgan kuningizni ko'rish\n"
        "🗑️ /delbirthday — tug'ilgan kunni o'chirish\n"
        "🏆 /top — TOP 10 odam qo'shganlarni korsatadi\n"
        "👥 /count — nechta odam qo'shganingizni ko'rish\n"
        "🎁 /danat — donate bilan qolab quvatlagiz kelsa botni shu buyruqni ishlating\n"
        "🌟 /text — bu buyruq bilan antiqa gaplar va hazil uchun yozilgan so'zlarni chiqar tirsayiz bo'ladi faqat random\n"
        "🧠 /savol — random hayot savoli\n"
        "📊 /stats — guruh statistikasi\n"
        "ℹ️ /info — bot haqida qisqacha\n"
        "🎮 /battle bu byruq bilan tosh qaychi qogoz oyinini yangicha versionnini oynay qolasiz sinab ko'ring\n"
        "📖 /help — buyruqlar ro'yxati",
        parse_mode="HTML"
    )


# =========================================================
# LINK BLOCK
# =========================================================

@dp.message(Command("link"))
async def link_command(message: types.Message):

    if not await is_group_admin(message):
        return

    target = await get_link_target_user(message)

    if not target:
        await message.answer(
            "❌ Foydalanuvchini ko'rsating.\n\n"
            "Misol:\n"
            "<code>/link @username</code>\n\n"
            "Yoki odamning xabariga Reply qilib:\n"
            "<code>/link</code>",
            parse_mode="HTML"
        )
        return

    set_user_link_block(message.chat.id, target.id, True)

    await message.answer(
        f"🔗 Link yuborish taqiqlandi.\n"
        f"👤 {target.full_name}"
    )


@dp.message(Command("unlink"))
async def unlink_command(message: types.Message):

    if not await is_group_admin(message):
        return

    target = await get_link_target_user(message)

    if not target:
        await message.answer(
            "❌ Foydalanuvchini ko'rsating.\n\n"
            "Misol:\n"
            "<code>/unlink @username</code>\n\n"
            "Yoki xabariga Reply qilib:\n"
            "<code>/unlink</code>",
            parse_mode="HTML"
        )
        return

    if is_user_link_blocked(message.chat.id, target.id):
        set_user_link_block(message.chat.id, target.id, False)
        await message.answer(
            f"✅ Link taqiqi olib tashlandi.\n"
            f"👤 {target.full_name}"
        )
        return

    await message.answer("ℹ️ Bu foydalanuvchiga link taqiqi berilmagan.")


# =========================================================
# RANDOM TEXT
# =========================================================

@dp.message(Command("text"))
async def text_command(message: types.Message):

    text = random.choice(SPLASH_TEXTS)

    await message.answer(
        f"🌟 <b>Random Splash Text:</b>\n\n{text}",
        parse_mode="HTML"
    )


# =========================================================
# RANDOM QUESTION
# =========================================================

@dp.message(Command("savol"))
async def savol_command(message: types.Message):

    question = random.choice(SAVOLLAR)

    await message.answer(
        "🧠 <b>savol:</b>\n\n"
        + question,
        parse_mode="HTML"
    )


# =========================================================
# ID
# =========================================================

@dp.message(Command("id"))
async def id_command(message: types.Message):

    answer_text = (
        "🆔 Sizning Telegram ID'ingiz:\n"
        f"<code>{message.from_user.id}</code>"
    )

    if message.chat.type in ("group", "supergroup", "channel"):
        answer_text += (
            "\n\n💬 Guruh/kanal ID:\n"
            f"<code>{message.chat.id}</code>"
        )

    await message.answer(
        answer_text,
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

    username = message.chat.username

    if not username:
        await message.answer(
            "❌ Bu guruhda public username mavjud emas."
        )
        return

    chat_username = f"@{username}"
    channels = GROUP_CHANNELS.get(chat_username)

    if not channels:
        await message.answer(
            "📺 Bu guruh uchun hali kanallar sozlanmagan. agar sozlashni hoxlasayiz @criperman_admin shu odamga kanaliz guruhizni linkini va kanallarizni lekinkini yozib qoldring"
        )
        return

    await message.answer(
        "📺 <b>Bizning kanallarimiz:</b>\n\n"
        + "\n".join(channels),
        parse_mode="HTML",
        disable_web_page_preview=True
    )


# =========================================================
# WELCOME
# =========================================================

WELCOME_IMAGE_PATH = "welcome.jpg"  # loyihangiz papkasidagi rasm fayli

@dp.message(F.new_chat_members)
async def welcome_new_members(message: types.Message):
    save_group(message.chat.id)

    for member in message.new_chat_members:

        # 1. Begona botlarni avtomatik ban qilish
        if member.is_bot:
            if member.id != bot.id:
                try:
                    await bot.ban_chat_member(
                        chat_id=message.chat.id,
                        user_id=member.id
                    )
                    await message.answer(
                        f"🤖 {member.full_name} bot edi.\n"
                        f"🛡 Guruhga begona bot kiritilmaydi."
                    )
                except Exception as e:
                    logging.error(f"Botni chiqarishda xato: {e}")
            continue

        # 2. Foydalanuvchi nomini shakllantirish
        username = (
            f"@{member.username}"
            if member.username
            else member.full_name
        )

        # 3. Kengaytirilgan tasodifiy xabarlar ro'yxati
        welcome_messages = [
            f"👋 Xush kelibsiz, {username}!",
            f"🎉 {username} guruhimizga qo'shildi!",
            f"💚 Xush kelibsiz, {username}! Never Give Up!",
            f"🎮 {username}, gaming chatimizga xush kelibsiz!",
            f"🔥 {username} ham bizga qo'shildi!",
            f"✨ Ooo, tarkibimizga yangi a'zo: {username}! Xush kelibsiz!",
            f"🚀 {username} saflarimizga qo'shildi. Chat endi yanada faolroq bo'ladi!",
            f"👑 {username}, chatimizga xush kelibsiz! O'zingizni uyingizdagidek his qiling.",
            f"👾 Yangi o'yinchi paydo bo'ldi: {username}! Tayyormisiz?",
            f"🌟 {username} keldi! Guruhimizga xush kelibsiz!",
            f"🎯 {username}, jamoadoshlar safiga xush kelibsiz!",
            f"💬 {username}, do'stlar davrasiga xush kelibsiz! Faol bo'ling va suhbatga qo'shiling!"
        ]

        caption_text = random.choice(welcome_messages)

        # 4. Rasm va matnni birga yuborish
        try:
            # Agar rasm fayli mavjud bo'lsa, rasmli yuboradi
            photo = FSInputFile(WELCOME_IMAGE_PATH)
            await message.answer_photo(
                photo=photo,
                caption=caption_text
            )
        except Exception as e:
            # Rasm yuklashda muammo bo'lsa, oddiy matnning o'zini yuboradi
            logging.error(f"Welcome rasmini yuborishda xato: {e}")
            await message.answer(caption_text)

        # 5. Odam qo'shgan foydalanuvchini hisoblash (Invites DB)
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
                        f"🇰🇷 생일 축하합니다!\n"
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
# BLOCKED STICKER PACKS
# =========================================================

import os
import logging
from aiogram import types, F
from aiogram.types import FSInputFile

# Taqiqlangan stikerlar uchun ogohlantirish rasmi
STICKER_WARNING_IMAGE = os.path.join(os.path.dirname(__file__), "warning_sticker.jpg")

@dp.message(F.sticker)
async def blocked_sticker_listener(message: types.Message):
    set_name = (message.sticker.set_name or "").lower().strip()

    if set_name in BLOCKED_STICKER_PACKS:
        try:
            # 1. Taqiqlangan stikerni o'chirish
            await message.delete()
        except Exception as e:
            logging.error(f"Blocked sticker delete xatosi: {e}")

        # 2. Foydalanuvchini tagging qilib matn tayyorlash
        user_mention = message.from_user.get_mention(as_html=True)
        caption_text = (
            f"🚫 {user_mention}, iltimos, taqiqlangan stiker pack ishlatmang!\n"
            f"<i>Guruh qoidalariga rioya qiling.</i>"
        )

        # 3. Rasmli ogohlantirish yuborish
        try:
            if os.path.exists(STICKER_WARNING_IMAGE):
                photo = FSInputFile(STICKER_WARNING_IMAGE)
                await message.answer_photo(
                    photo=photo,
                    caption=caption_text,
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    text=caption_text,
                    parse_mode="HTML"
                )
        except Exception as e:
            logging.error(f"Stiker ogohlantirishini yuborishda xato: {e}")

        return


# =========================================================
# SALOM
# =========================================================

@dp.message(F.text)
async def chat_listener(message: types.Message):

    if message.chat.type not in ("group", "supergroup"):
        return

    if message.from_user and is_user_link_blocked(message.chat.id, message.from_user.id):
        if has_link(message.text):
            try:
                await message.delete()
            except Exception:
                pass
        return

    if is_manual_link_blocked_user(message):
        if has_link(message.text):
            try:
                await message.delete()
            except Exception:
                pass
        return

    text = message.text.lower()

    # Taqiqlangan linklarni tekshirish
    if has_blocked_link(message.text):

        try:
            await message.delete()

            await message.answer(
                "🚫 Bu guruhda taqiqlangan link mavjud!"
            )

        except Exception as e:
            logging.error(
                f"Blocked link delete xatosi: {e}"
            )

        return

    # Taqiqlangan so'zlarni tekshirish
    clean_text = normalize(text)

    for word in BAD_WORDS:

        clean_word = normalize(word)

        if not clean_word:
            continue

        pattern = r"(?<![a-z0-9])" + re.escape(clean_word) + r"(?![a-z0-9])"

        if re.search(pattern, clean_text):

            try:
                await message.delete()

                await message.answer(
                    "🚫 Bu guruhda bunday kontent taqiqlangan!"
                )

            except Exception as e:
                logging.error(
                    f"Message delete xatosi: {e}"
                )

            return

    # =====================================================
    # SALOM → GURUH OWNER
    # =====================================================

HELLO_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "hello.jpg")

@dp.message(F.text & F.chat.type.in_({"group", "supergroup"}))
async def hello_listener(message: types.Message):
    text = message.text.lower().strip()

    # Text ichida salomlashuv so'zlarini aniqlash
    hello_keywords = ["salom", "assalomu alaykum", "salom alaykum", "privet", "hello"]
    
    if any(keyword in text for keyword in hello_keywords):
        owner_name = "Guruh egasi"

        # Guruh egasini (creator) topish
        try:
            admins = await message.chat.get_administrators()
            for admin in admins:
                if admin.status == "creator":
                    if admin.user.username:
                        owner_name = f"@{admin.user.username}"
                    else:
                        owner_name = admin.user.full_name
                    break
        except Exception as e:
            logging.error(f"Ownerni aniqlashda xato: {e}")

        # Har safar tasodifiy chiqadigan boyitilgan matnlar ro'yxati
        user_name = message.from_user.first_name
        hello_responses = [
            f"👀 <b>{owner_name} sizni doim eshitadi, bemalol gapiravering!</b> 💻😎",
            f"👋 Assalomu alaykum, {user_name}! {owner_name} bilan birga sizga ajoyib kayfiyat tilaymiz! ✨",
            f"🎧 {owner_name} quloqda, chatni kuzatib bormoqda... Nima gaplar, {user_name}? 🎮",
            f"🤖 Salom, {user_name}! Men <b>Curina</b>man, {owner_name}ning sodiq yordamchisiman. Xush kelibsiz! ⚡",
            f"🔥 Ooo salom, {user_name}! {owner_name} va men xizmatingizdamiz, bemalol yozing! 🚀"
        ]

        selected_caption = random.choice(hello_responses)

        # Rasm bilan javob berish (fayl mavjud bo'lsa)
        try:
            if os.path.exists(HELLO_IMAGE_PATH):
                photo = FSInputFile(HELLO_IMAGE_PATH)
                await message.reply_photo(
                    photo=photo,
                    caption=selected_caption,
                    parse_mode="HTML"
                )
            else:
                await message.reply(
                    text=selected_caption,
                    parse_mode="HTML"
                )
        except Exception as e:
            logging.error(f"Salomlashish javobida xato: {e}")
            await message.reply(selected_caption, parse_mode="HTML")

        return


# =========================================================
# DAILY SPLASH + AD
# =========================================================

async def daily_scheduler():

    last_sent_date = None

    while True:

        now = datetime.now(UZ_TZ)

        # Har kuni soat 07:00
        if now.hour == 7 and now.minute == 0:

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

                        try:
                            chat = await bot.get_chat(chat_id)
                            username = chat.username
                        except Exception as e:
                            username = None
                            logging.warning(
                                f"Guruh ma'lumotini olishda xato: {group_id} - {e}"
                            )

                        if username:
                            channels = GROUP_CHANNELS.get(f"@{username}")
                        else:
                            channels = None

                        if channels:
                            await bot.send_message(
                                chat_id,
                                "📺 <b>Bizning kanallarimiz:</b>\n\n"
                                + "\n".join(channels),
                                parse_mode="HTML",
                                disable_web_page_preview=True
                            )
                        else:
                            logging.warning(
                                f"Reklama uchun kanal konfiguratsiyasi topilmadi: {group_id}"
                            )

                    except Exception as e:

                        logging.error(
                            f"Daily scheduler {group_id} xatosi: {e}"
                        )

                last_sent_date = current_date

        await asyncio.sleep(30)


# =========================================================
# DAILY WEEKLY MESSAGE
# =========================================================

async def weekly_day_scheduler():
    last_sent = None

    while True:
        now = datetime.now(UZ_TZ)

        if now.hour == 8 and now.minute == 0:
            weekday_names = {
                0: (
                    "Dushanba",
                    "🌅 <b>BUGUN DUSHANBA — YANGI HAFTA, YANGI IMKONIYATLAR!</b>\n\n"
                    "📅 Yangi ish haftasi boshlandi! O'z maqsadlaringiz sari dadil qadam tashlang.\n"
                    "✨ Qiyinchiliklardan qochmang, har bir yangi kun — yangi g'alaba demakdir.\n"
                    "💡 Siz bugun rejalashtirgan har bir ishingizni a'lo darajada bajara olasiz!\n"
                    "💚 Bugungi kuningiz omadli va unumli o'tsin!\n\n"
                    "🔥 <i>Never Give Up! Olg'a!</i>"
                ),
                1: (
                    "Seshanba",
                    "🔥 <b>BUGUN SESHANBA — SUR'ATNI OSHIRAMIZ!</b>\n\n"
                    "💪 Haftaning ikkinchi kuni! Hafta sur'atini pasaytirmasdan ilgariroq harakat qiling.\n"
                    "📈 Kichik bo'lsa ham, har kuni qo'yilgan qadam sizni buyuk natijaga yaqinlashtiradi.\n"
                    "🚀 Rejalashtirilgan ishlaringizni birma-bir va sifatli yakunlang.\n"
                    "🎯 O'zingizga bo'lgan ishonchni aslo yo'qotmang!\n\n"
                    "💚 <i>Never Give Up! G'alaba siz tomonda!</i>"
                ),
                2: (
                    "Chorshanba",
                    "💻 <b>BUGUN CHORSHANBA — HAFTANING SHIRIN O'RTASI!</b>\n\n"
                    "⚡ Marra sari yarim yo'l bosib o'tildi! Energiyangizni to'g'ri taqsimlang.\n"
                    "📌 Har bir kichik muvaffaqiyat buyuk marralarning poydevoridir.\n"
                    "⚙️ Ish yoki o'qishda bugun yangi g'oyalarni sinab ko'rish uchun ajoyib imkoniyat.\n"
                    "🌟 Kayfiyatingizni a'lo darajada tuting va boshqalarga ham ulashing!\n\n"
                    "💚 <i>Never Give Up! Harakatdan to'xtamang!</i>"
                ),
                3: (
                    "Payshanba",
                    "⚡ <b>BUGUN PAYSHANBA — MARRAGA OZ QOLDI!</b>\n\n"
                    "🔥 Ish haftasining oxirgi bosqichi yaqinlashmoqda, kuchingizni to'plang!\n"
                    "📈 To'siqlar sizni to'xtatib qolishiga yo'l qo'ymang. Intilishda davom eting.\n"
                    "💪 Kunning har bir daqiqasidan maksimal darajada unumli foydalaning.\n"
                    "🚀 Yaxshi natijalar va sabr siz kutgan omadni keltiradi!\n\n"
                    "💚 <i>Never Give Up! Oz qoldi, olg'a!</i>"
                ),
                4: (
                    "Juma",
                    "🎉 <b>BUGUN JUMA — HAFTANING ENG BARAQALI KUNI!</b>\n\n"
                    "✨ Haftaning eng fayzli va ajoyib kuni muborak bo'lsin!\n"
                    "💚 Barcha qilingan mehnatlar va harakatlaringiz rohatini ko'radigan kun.\n"
                    "🚀 Haftalik vazifalaringizni chiroyli yakunlang va o'zingizga yaxshi hislar ulashing.\n"
                    "🌟 Atrofdagilarga samimiyat ko'rsating va ijobiy energiya bering!\n\n"
                    "🔥 <i>Never Give Up! Ajoyib kun tilaymiz!</i>"
                ),
                5: (
                    "Shanba",
                    "😎 <b>BUGUN SHANBA — DAM OLISH VA RECHARGE VAQTI!</b>\n\n"
                    "💤 Og'ir haftadan so'ng nihoyat miya va tanaga dam berish vaqti keldi.\n"
                    "🌿 O'zingiz yoqtirgan hobbi, o'yinlar yoki yaqinlaringiz davrasida vaqt o'tkazing.\n"
                    "🧠 Qilgan ishlaringizni sarhisob qiling va o'zingiz bilan faxrlaning!\n"
                    "🎮 Maroqli dam oling va yangi kuch to'plang!\n\n"
                    "💚 <i>Never Give Up! Bugun faqat hordiq!</i>"
                ),
                6: (
                    "Yakshanba",
                    "🌙 <b>BUGUN YAKSHANBA — YANGI ZAFARLARGA TAYYORGARLIK!</b>\n\n"
                    "🧠 Yana bir ajoyib dam olish kuni. Kelasi hafta uchun rejalarni tartiblang.\n"
                    "📅 O'zingizni ruhiy va jismoniy tomondan yangi haftaga sozlang.\n"
                    "💚 O'zingiz va oilangiz uchun vaqt ajrating, quvvatlanib oling!\n"
                    "🔥 Yangi haftada sizni bundan ham katta g'alabalar kutmoqda!\n\n"
                    "🔥 <i>Never Give Up! Yangi haftada ko'rishguncha!</i>"
                ),
            }

            today_name, message_text = weekday_names.get(now.weekday(), ("Kun", "💚 Never Give Up!"))
            current = now.strftime("%Y-%m-%d")

            if current != last_sent:
                groups = get_saved_groups()

                for group_id in groups:
                    try:
                        await bot.send_message(
                            int(group_id),
                            message_text,
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        logging.error(f"Weekly message {group_id} xatosi: {e}")

                last_sent = current

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

    asyncio.create_task(
        weekly_day_scheduler()
    )

    # Start HTTP admin server for bad words management
    try:
        asyncio.create_task(start_bad_words_server())
    except Exception as e:
        logging.error(f"Failed to start bad words admin server: {e}")

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
