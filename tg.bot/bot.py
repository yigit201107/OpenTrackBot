import asyncio
import re
from urllib.parse import quote_plus

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties


# =====================
# НАСТРОЙКИ
# =====================
TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"

# =====================
# ИНИЦИАЛИЗАЦИЯ
# =====================
router = Router()


# =====================
# КЛАВИАТУРА (ВЕРТИКАЛЬНАЯ)
# =====================
menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Поиск по нику")],
        [KeyboardButton(text="👤 Поиск по ФИО")],
        [KeyboardButton(text="🏠 В меню")]
    ],
    resize_keyboard=True
)


# =====================
# /start
# =====================
@router.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "🔎 <b>OpenTrackBot</b>\n\n"
        "Помогаю находить открытую информацию по запросу.\n\n"
        "📌 <b>Выберите тип поиска ниже</b>",
        reply_markup=menu_kb
    )


# =====================
# ПОИСК ПО НИКУ
# =====================
@router.message(F.text == "🔍 Поиск по нику")
async def search_nick_hint(message: Message):
    await message.answer(
        "🪪 <b>Введите ник (без @)</b>\n\n"
        "📌 <i>Пример:</i>\n"
        "<code>example_user</code>"
    )


# =====================
# ПОИСК ПО ФИО
# =====================
@router.message(F.text == "👤 Поиск по ФИО")
async def search_fio_hint(message: Message):
    await message.answer(
        "👤 <b>Введите ФИО и город</b>\n\n"
        "📌 <i>Пример:</i>\n"
        "<code>Иван Иванов Москва</code>"
    )


# =====================
# В МЕНЮ
# =====================
@router.message(F.text == "🏠 В меню")
async def back_to_menu(message: Message):
    await message.answer(
        "🏠 <b>Главное меню</b>",
        reply_markup=menu_kb
    )


# =====================
# ОБРАБОТКА ЗАПРОСА
# =====================
@router.message()
async def handle_query(message: Message):
    text = message.text.strip()

    # защита от кнопок
    if text in (
        "🔍 Поиск по нику",
        "👤 Поиск по ФИО",
        "🏠 В меню"
    ):
        return

    query = quote_plus(text)

    results = [
        ("Telegram", f"https://t.me/{text}" if re.match(r"^[a-zA-Z0-9_]{3,}$", text) else None),
        ("Google", f"https://www.google.com/search?q={query}"),
        ("VK", f"https://vk.com/search?c[q]={query}"),
        ("Yandex", f"https://yandex.ru/search/?text={query}")
    ]

    response = "🔗 <b>Найденные ссылки:</b>\n\n"

    for name, link in results:
        if link:
            response += f"• <b>{name}:</b> {link}\n"

    await message.answer(response)


# =====================
# ЗАПУСК
# =====================
async def main():
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )

    dp = Dispatcher()
    dp.include_router(router)

    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())