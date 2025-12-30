import os
import time
import asyncio
import logging
import sqlite3
import urllib.parse

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# =======================
# ENV
# =======================
load_dotenv()
TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
FREE_REQUESTS = 3

if not TOKEN:
    raise RuntimeError("TOKEN not found in .env")

# =======================
# DB
# =======================
db = sqlite3.connect("bot.db", check_same_thread=False)
db.row_factory = sqlite3.Row
cur = db.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    stars INTEGER DEFAULT 3,
    last_free INTEGER DEFAULT 0
)
""")
db.commit()

# =======================
# FSM
# =======================
class SearchFIO(StatesGroup):
    waiting = State()

class SearchNick(StatesGroup):
    waiting = State()

class SearchPhone(StatesGroup):
    waiting = State()

class SearchEmail(StatesGroup):
    waiting = State()

# =======================
# HELPERS
# =======================
def get_user(uid: int):
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    u = cur.fetchone()
    if not u:
        now = int(time.time())
        cur.execute(
            "INSERT INTO users (user_id, stars, last_free) VALUES (?,?,?)",
            (uid, FREE_REQUESTS, now)
        )
        db.commit()
        return get_user(uid)
    return u

def has_access(uid: int) -> bool:
    if uid == ADMIN_ID:
        return True
    u = get_user(uid)
    return u["stars"] > 0

def use_request(uid: int):
    if uid == ADMIN_ID:
        return
    u = get_user(uid)
    if u["stars"] > 0:
        cur.execute(
            "UPDATE users SET stars = stars - 1 WHERE user_id=? AND stars>0",
            (uid,),
        )
        db.commit()

def progress(uid: int) -> str:
    if uid == ADMIN_ID:
        return "∞"
    u = get_user(uid)
    return str(u["stars"])

# =======================
# KEYBOARDS
# =======================
def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [{"text": "👤 Поиск по ФИО"}],
            [{"text": "🔍 Поиск по нику"}],
            [{"text": "📞 Поиск по телефону"}],
            [{"text": "📧 Проверка email"}]
        ],
        resize_keyboard=True
    )

def back_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 В меню", callback_data="back_home")]]
    )

# =======================
# BOT
# =======================
logging.basicConfig(level=logging.INFO)
bot = Bot(TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# =======================
# START
# =======================
@dp.message(Command("start"))
async def start_cmd(m: Message):
    get_user(m.from_user.id)
    await m.answer(
        f"👋 <b>Добро пожаловать в SpyFinder</b>\n\n"
        f"Я — OSINT-бот для поиска информации по открытым источникам 🌐\n\n"
        f"🔎 Что умею:\n"
        f"• поиск по ФИО\n"
        f"• поиск по нику\n"
        f"• поиск по телефону\n"
        f"• проверка email\n\n"
        f"🎁 У тебя {FREE_REQUESTS} бесплатных запроса в день\n\n"
        f"⚡ Примеры ввода:\n"
        f"ФИО: Иванов Иван Иванович Москва\n"
        f"Ник: example_user\n"
        f"Телефон: +79991234567\n"
        f"Email: example@mail.com\n\n"
        f"🏠 Выбери действие ниже",
        reply_markup=main_kb()
    )

# =======================
# MENU BUTTONS
# =======================
@dp.message(F.text == "👤 Поиск по ФИО")
async def btn_fio(m: Message, state: FSMContext):
    if not has_access(m.from_user.id):
        await m.answer("❌ Нет запросов на сегодня", reply_markup=main_kb())
        return
    await state.set_state(SearchFIO.waiting)
    await m.answer("✍️ Введите ФИО и город\nПример: Иванов Иван Иванович Москва", reply_markup=back_kb())

@dp.message(F.text == "🔍 Поиск по нику")
async def btn_nick(m: Message, state: FSMContext):
    if not has_access(m.from_user.id):
        await m.answer("❌ Нет запросов на сегодня", reply_markup=main_kb())
        return
    await state.set_state(SearchNick.waiting)
    await m.answer("✍️ Введите ник (без @)\nПример: example_user", reply_markup=back_kb())

@dp.message(F.text == "📞 Поиск по телефону")
async def btn_phone(m: Message, state: FSMContext):
    if not has_access(m.from_user.id):
        await m.answer("❌ Нет запросов на сегодня", reply_markup=main_kb())
        return
    await state.set_state(SearchPhone.waiting)
    await m.answer("✍️ Введите номер телефона\nПример: +79991234567", reply_markup=back_kb())

@dp.message(F.text == "📧 Проверка email")
async def btn_email(m: Message, state: FSMContext):
    if not has_access(m.from_user.id):
        await m.answer("❌ Нет запросов на сегодня", reply_markup=main_kb())
        return
    await state.set_state(SearchEmail.waiting)
    await m.answer("✍️ Введите email\nПример: example@mail.com", reply_markup=back_kb())

# =======================
# SEARCH HANDLERS
# =======================
@dp.message(SearchFIO.waiting)
async def do_fio(m: Message, state: FSMContext):
    query = m.text.strip()
    use_request(m.from_user.id)
    await state.clear()
    q = urllib.parse.quote_plus(query)
    await m.answer(
        f"🔎 <b>Поиск по ФИО</b>\n\n"
        f"👤 {query}\n\n"
        f"🌐 Google: https://www.google.com/search?q={q}\n"
        f"👥 VK: https://vk.com/search?c%5Bq%5D={q}&c%5Bsection%5D=people\n"
        f"📱 Telegram: https://t.me/s/{q.replace(' ', '')}\n\n"
        f"💎 Осталось: {progress(m.from_user.id)}",
        reply_markup=main_kb()
    )

@dp.message(SearchNick.waiting)
async def do_nick(m: Message, state: FSMContext):
    nick = m.text.strip().lstrip("@")
    use_request(m.from_user.id)
    await state.clear()
    await m.answer(
        f"🔎 <b>Поиск по нику</b>\n\n"
        f"@{nick}\n\n"
        f"📱 Telegram: https://t.me/{nick}\n"
        f"🌐 VK: https://vk.com/{nick}\n"
        f"📸 Instagram: https://instagram.com/{nick}\n"
        f"🎵 TikTok: https://www.tiktok.com/@{nick}\n\n"
        f"💎 Осталось: {progress(m.from_user.id)}",
        reply_markup=main_kb()
    )

@dp.message(SearchPhone.waiting)
async def do_phone(m: Message, state: FSMContext):
    phone = m.text.strip()
    use_request(m.from_user.id)
    await state.clear()
    q = urllib.parse.quote_plus(phone)
    await m.answer(
        f"🔎 <b>Поиск по телефону</b>\n\n"
        f"{phone}\n\n"
        f"🌐 Google: https://www.google.com/search?q={q}\n"
        f"📱 Telegram: https://t.me/s/{q}\n"
        f"👥 VK: https://vk.com/search?c%5Bq%5D={q}&c%5Bsection%5D=people\n\n"
        f"💎 Осталось: {progress(m.from_user.id)}",
        reply_markup=main_kb()
    )

@dp.message(SearchEmail.waiting)
async def do_email(m: Message, state: FSMContext):
    email = m.text.strip()
    use_request(m.from_user.id)
    await state.clear()
    q = urllib.parse.quote_plus(email)
    await m.answer(
        f"🔎 <b>Email OSINT</b>\n\n"
        f"{email}\n\n"
        f"🌐 Google: https://www.google.com/search?q={q}\n"
        f"📧 HaveIBeenPwned: https://haveibeenpwned.com/unifiedsearch/{q}\n\n"
        f"💎 Осталось: {progress(m.from_user.id)}",
        reply_markup=main_kb()
    )

# =======================
# BACK HOME
# =======================
@dp.callback_query(F.data == "back_home")
async def back_home(c, state: FSMContext):
    await state.clear()
    await c.message.answer(
        f"🏠 Меню\n💎 Запросов: {progress(c.from_user.id)}",
        reply_markup=main_kb()
    )
    await c.answer()

# =======================
# FREE REQUESTS WATCHER
# =======================
async def free_requests_watcher():
    while True:
        now = int(time.time())
        cur.execute("SELECT user_id, stars, last_free FROM users")
        users = cur.fetchall()
        for u in users:
            if u["stars"] < FREE_REQUESTS and now - u["last_free"] >= 86400:
                cur.execute(
                    "UPDATE users SET stars = ?, last_free = ? WHERE user_id=?",
                    (FREE_REQUESTS, now, u["user_id"])
                )
                db.commit()
        await asyncio.sleep(3600)

# =======================
# MAIN
# =======================
async def main():
    print("✅ Бот запущен")
    asyncio.create_task(free_requests_watcher())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())