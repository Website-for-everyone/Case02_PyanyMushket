import os
import io
import asyncio
import logging
import uuid
from typing import Optional
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile,
)
from PIL import Image, ImageDraw

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8217851677:AAHN34TMuC1P4e6SppuazFN8BIiLHa_RyIc")
OWNER_HANDLE = os.getenv("OWNER_HANDLE", "@Idrisov_prod")

class TavernFSM(StatesGroup):
    choosing_table = State()
    entering_name = State()
    entering_guests = State()
    entering_phone = State()

TABLES = {
    "hearth": {"title": "🔥 У пылающего камина", "cap": "до 4 персон"},
    "standard": {"title": "🛡 Под королевским штандартом", "cap": "до 6 персон"},
    "cellar": {"title": "🍷 В прохладном винном погребе", "cap": "до 8 персон (VIP)"}
}

def generate_wax_seal_image(guest_name: str, table_title: str, cert_id: str) -> bytes:
    img = Image.new("RGB", (650, 420), color="#E2D1B3")
    draw = ImageDraw.Draw(img)

    # Burnt edges border
    draw.rectangle([10, 10, 640, 410], outline="#3E2718", width=5)
    draw.rectangle([18, 18, 632, 402], outline="#8B5A2B", width=2)
    draw.rectangle([22, 22, 628, 398], outline="#C89B3C", width=1)

    draw.text((325, 45), "ГРАМОТА НА ВХОДЪ И ТРАПЕЗУ", fill="#1F140E", anchor="mm")
    draw.text((325, 75), "ТАВЕРНА «ПЬЯНЫЙ МУШКЕТЪ» ЛѢТА 1584", fill="#8B1E1E", anchor="mm")
    draw.line([(80, 95), (570, 95)], fill="#3E2718", width=2)

    body_text = (
        f"Симъ подлинно утверждается, что бояринъ\n"
        f"«{guest_name}»\n"
        f"со товарищи изволилъ занять въ трактире:\n"
        f"«{table_title}»\n"
        f"на великую вечерю и вкушеніе хмельныхъ напитковъ."
    )
    draw.text((325, 175), body_text, fill="#2A1B0E", anchor="mm", align="center")

    seal_center = (520, 310)
    seal_radius = 50
    draw.ellipse([seal_center[0]-seal_radius, seal_center[1]-seal_radius,
                  seal_center[0]+seal_radius, seal_center[1]+seal_radius],
                 fill="#8B1E1E", outline="#590D22", width=3)
    draw.ellipse([seal_center[0]-seal_radius+8, seal_center[1]-seal_radius+8,
                  seal_center[0]+seal_radius-8, seal_center[1]+seal_radius-8],
                 outline="#FFD700", width=2)
    draw.text(seal_center, "ПМ\n1584", fill="#FFE5A3", anchor="mm", align="center")

    draw.text((80, 310), f"Печать и соизволеніе Трактирщика\nГрамота № {cert_id}\nУведомленъ: {OWNER_HANDLE}", fill="#3E2718")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Подать челобитную на столъ", callback_data="tavern_reserve")],
        [InlineKeyboardButton(text="🍗 Яства и хмельные взвары (Меню)", callback_data="tavern_menu")],
        [InlineKeyboardButton(text="👑 Доска королевского розыска", callback_data="tavern_bounties")],
        [InlineKeyboardButton(text="✉️ Отправить весть хозяину (@Idrisov_prod)", url=f"https://t.me/Idrisov_prod")]
    ])

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "🍗 *Миръ дому твоему, путникъ!*\n\n"
        "Ты ступилъ подъ своды славной таверны *«Пьяный Мушкетъ»*!\n"
        "Очагъ нашъ жарокъ, въ погребахъ зреетъ медовуха да темный монастырскій эль, "
        "а на вертеле подрумянивается дикій вепрь.\n\n"
        "Какое дѣло привело тебя къ трактирщику?"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@router.callback_query(F.data == "tavern_menu")
async def cb_tavern_menu(call: CallbackQuery):
    text = (
        "📜 *Трапезное меню таверны «Пьяный Мушкетъ»:*\n\n"
        "• *Запеченный вепрь съ брусникой:* 1 Дукатъ 2 Талера (~4 200 ₽)\n"
        "• *Тушеная оленина въ горшочке:* 8 Талеровъ (~2 800 ₽)\n"
        "• *Копченый фазанъ съ травами:* 6 Талеровъ (~2 100 ₽)\n"
        "• *Кружка монастырскаго эля:* 12 Грошей (~420 ₽)\n"
        "• *Кубокъ ставленой медовухи:* 18 Грошей (~630 ₽)\n"
        "• *Подовый каравай съ чеснокомъ:* 8 Грошей (~280 ₽)\n\n"
        "_Изволишь ли занять дубовый столъ для сытнаго пира?_"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Занять столъ у трактирщика", callback_data="tavern_reserve")],
        [InlineKeyboardButton(text="⬅️ Назадъ въ залу", callback_data="tavern_back")]
    ])
    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data == "tavern_bounties")
async def cb_tavern_bounties(call: CallbackQuery):
    text = (
        "👑 *Королевская Доска Розыска и Грамотъ:*\n\n"
        "1. ⚔️ *Черный Баронъ:* Розыскъ живымъ или мертвымъ. Награда: 500 золотыхъ дукатовъ!\n"
        "2. 📜 *Похвальная грамота короны:* Выдана нашему трактиру за лучшую медовуху въ королевстве!\n"
        "3. ⚗️ *Беглый Алхимикъ Магнусъ:* Укралъ гримуаръ архиепископа. Награда: 300 талеровъ серебромъ."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назадъ въ залу", callback_data="tavern_back")]
    ])
    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data == "tavern_back")
async def cb_tavern_back(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "🍗 *Главная зала таверны «Пьяный Мушкетъ»*\nЧего изволишь, путникъ?",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    await call.answer()

@router.callback_query(F.data == "tavern_reserve")
async def cb_tavern_reserve(call: CallbackQuery, state: FSMContext):
    await state.set_state(TavernFSM.choosing_table)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Столъ у камина (до 4)", callback_data="table_hearth")],
        [InlineKeyboardButton(text="🛡 Подъ штандартомъ (до 6)", callback_data="table_standard")],
        [InlineKeyboardButton(text="🍷 Винный погребъ VIP (до 8)", callback_data="table_cellar")],
        [InlineKeyboardButton(text="⬅️ Назадъ", callback_data="tavern_back")]
    ])
    await call.message.edit_text(
        "🪵 *Который дубовый столъ изволишь занять подле очага?*",
        parse_mode="Markdown",
        reply_markup=kb
    )
    await call.answer()

@router.callback_query(TavernFSM.choosing_table, F.data.startswith("table_"))
async def cb_chosen_table(call: CallbackQuery, state: FSMContext):
    table_key = call.data.replace("table_", "")
    table_data = TABLES.get(table_key, TABLES["hearth"])
    await state.update_data(table_key=table_key, table_title=table_data["title"])
    await state.set_state(TavernFSM.entering_name)

    await call.message.edit_text(
        f"Выбранъ: *{table_data['title']}* ({table_data['cap']}).\n\n"
        "📜 *Какимъ именемъ или родомъ величать тебя въ грамоте?*\n"
        "_(Напиши въ отвѣте, напримѣръ: Бояринъ Даниэль):_",
        parse_mode="Markdown"
    )
    await call.answer()

@router.message(TavernFSM.entering_name)
async def msg_guest_name(message: Message, state: FSMContext):
    await state.update_data(guest_name=message.text.strip())
    await state.set_state(TavernFSM.entering_guests)
    await message.answer(
        "👥 *Сколько душъ прибудетъ съ тобою на вечерю?* (Число отъ 1 до 12):",
        parse_mode="Markdown"
    )

@router.message(TavernFSM.entering_guests)
async def msg_guest_count(message: Message, state: FSMContext):
    count_str = message.text.strip()
    await state.update_data(guest_count=count_str)
    await state.set_state(TavernFSM.entering_phone)
    await message.answer(
        "📱 *Назови номеръ (телефонъ) для отправки голубиной весточки:*",
        parse_mode="Markdown"
    )

@router.message(TavernFSM.entering_phone)
async def msg_guest_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    data = await state.get_data()
    cert_id = f"MUSH-{uuid.uuid4().hex[:6].upper()}"

    guest_name = data.get("guest_name", "Благородный Гость")
    table_title = data.get("table_title", "Дубовый стол у камина")

    # Generate certificate image with wax seal
    cert_bytes = generate_wax_seal_image(guest_name, table_title, cert_id)

    input_file = BufferedInputFile(cert_bytes, filename=f"gramota_{cert_id}.png")

    caption = (
        f"👑 *Сургучная Грамота № `{cert_id}` составлена!*\n\n"
        f"Благородный бояринъ *{guest_name}*, твой столъ *{table_title}* закрѣпленъ!\n"
        f"Число гостей: {data.get('guest_count')}\n"
        f"Контактная весть: `{phone}`\n\n"
        f"Сургучъ остылъ. Весть о брони отправлена хозяину таверны: {OWNER_HANDLE}."
    )

    lead_payload = {
        "event": "TAVERN_TABLE_RESERVED",
        "certificate_id": cert_id,
        "guest_name": guest_name,
        "table": table_title,
        "phone": phone,
        "forwarded_to": OWNER_HANDLE
    }
    logger.info(f"DISPATCH TAVERN LEAD: {lead_payload}")

    await message.answer_photo(photo=input_file, caption=caption, parse_mode="Markdown", reply_markup=get_main_keyboard())
    await state.clear()

def create_tavern_bot() -> tuple[Bot, Dispatcher]:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    return bot, dp

async def main():
    bot, dp = create_tavern_bot()
    logger.info("Pyany Mushket Tavern Bot is listening for guests...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
