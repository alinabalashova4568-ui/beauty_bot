import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- НАСТРОЙКИ ---
# Сюда мы вставим токен чуть позже, пока оставь как есть
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_НОВЫЙ_ТОКЕН")
ADMIN_ID = 8553406744  # Твой ID

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- СОСТОЯНИЯ ---
class OrderForm(StatesGroup):
    name = State()
    phone = State()
    date = State()
    time = State()

# --- КЛАВИАТУРЫ ---
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💅 Услуги и цены", callback_data="services"))
    builder.row(InlineKeyboardButton(text="📅 Записаться", callback_data="book"))
    builder.row(InlineKeyboardButton(text="📍 Контакты", callback_data="contacts"))
    return builder.as_markup()

def get_back_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu"))
    return builder.as_markup()

# --- ОБРАБОТЧИКИ МЕНЮ ---
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n"
        "Добро пожаловать в Beauty Studio.\n"
        "Выберите действие:",
        reply_markup=get_main_menu()
    )

@dp.callback_query(F.data == "services")
async def show_services(callback: types.CallbackQuery):
    text = (
        "💅 *Наши услуги:*\n\n"
        "1. Маникюр с покрытием — 2500 руб.\n"
        "2. Педикюр — 3000 руб.\n"
        "3. Наращивание ресниц — 3500 руб.\n\n"
        "Для записи нажмите кнопку ниже."
    )
    await callback.message.edit_text(text, reply_markup=get_back_menu(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "contacts")
async def show_contacts(callback: types.CallbackQuery):
    text = (
        "📍 *Наши контакты:*\n\n"
        "Адрес: г. Егорьевск, ул. Ленина, д. 10\n"
        "Телефон: +7 (999) 123-45-67\n"
        "Instagram: @beauty_studio_eg\n\n"
        "Ждем вас!"
    )
    await callback.message.edit_text(text, reply_markup=get_back_menu(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("Главное меню:", reply_markup=get_main_menu())
    await callback.answer()

# --- ОБРАБОТЧИКИ ЗАПИСИ ---
@dp.callback_query(F.data == "book")
async def book_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Отлично! Как вас зовут?")
    await state.set_state(OrderForm.name)
    await callback.answer()

@dp.message(OrderForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Напишите ваш номер телефона:")
    await state.set_state(OrderForm.phone)

@dp.message(OrderForm.phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("На какую дату вас записать? (например, 25 мая)")
    await state.set_state(OrderForm.date)

@dp.message(OrderForm.date)
async def process_date(message: types.Message, state: FSMContext):
    await state.update_data(date=message.text)
    await message.answer("На какое время? (например, 14:00)")
    await state.set_state(OrderForm.time)

@dp.message(OrderForm.time)
async def process_time(message: types.Message, state: FSMContext):
    await state.update_data(time=message.text)
    data = await state.get_data()

    # Отправляем заявку админу
    text_to_admin = (
        f"🔥 *Новая запись!*\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"📅 Дата: {data['date']}\n"
        f"⏰ Время: {data['time']}\n"
        f"💬 От: @{message.from_user.username or message.from_user.id}"
    )
    await bot.send_message(ADMIN_ID, text_to_admin, parse_mode="Markdown")

    await message.answer(
        f"Спасибо, {data['name']}! Вы записаны на {data['date']} в {data['time']}.\n"
        "Мы свяжемся с вами для подтверждения. ✅",
        reply_markup=get_main_menu()
    )
    await state.clear()

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle(request):
    return web.Response(text="Beauty Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Web server started on port {port}")

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())