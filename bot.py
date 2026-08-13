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
DONATE_LINK = "https://idonate.uz/d/deeKARL"

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
]


# =========================================================
# BAD WORDS
# =========================================================

BAD_WORDS = [
    "ahmoq",
    "zb",
    "axmoq",
    "dalbayob",
    "poxoy",
    "dnx",
    "ph",
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
    "neger",
    "시발",
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
        "📺 /channels — guruhga mos kanallar\n"
        "🌟 /text — random splash text\n"
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
            "📺 Bu guruh uchun hali kanallar sozlanmagan."
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
# SALOM
# =========================================================

@dp.message(F.text)
async def chat_listener(message: types.Message):

    text = message.text.lower()

    # Taqiqlangan so'zlarni tekshirish
    clean_text = normalize(text)

    for word in BAD_WORDS:

        clean_word = normalize(word)

        if word in text or clean_word in clean_text:

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

    if "salom" in text:

        owner_name = "Owner"

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
            logging.error(
                f"Ownerni aniqlashda xato: {e}"
            )

        await message.reply(
            f"👀 <b>{owner_name} sizni doim eshitadi, "
            f"bemalol gapiravering!</b> 💻😎",
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