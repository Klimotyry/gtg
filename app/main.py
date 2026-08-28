import asyncio
import re
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import load_config
from app.db import get_user, init_db, set_card, set_sbp, upsert_user

router = Router()
config = load_config()


class Form(StatesGroup):
    buy_amount = State()
    sell_amount = State()
    sbp_phone = State()
    sbp_bank = State()
    card = State()


def kb(rows):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=x) for x in row] for row in rows],
        resize_keyboard=True,
    )


MAIN_KB = kb([
    ["📈 Купить", "📉 Продать"],
    ["📊 Информация"],
    ["🧾 Профиль"],
])

BACK_KB = kb([["⬅️ Назад"]])
BUY_PRESETS = kb([["500₽", "1000₽", "5000₽"], ["10k", "12k"], ["⬅️ Назад"]])
SELL_PRESETS = kb([["500₽", "1000₽", "5000₽"], ["10k", "25k", "99k"], ["⬅️ Назад"]])


def parse_rubles(text: str) -> int | None:
    raw = text.lower().replace("₽", "").replace("р", "").replace(" ", "").strip()
    m = re.fullmatch(r"(\d+(?:[.,]\d+)?)(k|к)?", raw)
    if not m:
        return None
    value = float(m.group(1).replace(",", "."))
    if m.group(2):
        value *= 1000
    return int(value)


def money(value: float) -> str:
    return f"{value:,.0f}".replace(",", " ")


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    u = message.from_user
    upsert_user(u.id, u.username, u.first_name)
    await message.answer(
        "🔥 <b>Byte Shop</b>\n\n"
        "💎 Удобный шаблон маркета Byte Coin\n"
        "🌿 Покупка и продажа BC\n"
        "🚀 Платёжные и coin API подключим следующим этапом.\n\n"
        "Меню снизу 👇",
        reply_markup=MAIN_KB,
        parse_mode="HTML",
    )


@router.message(F.text == "⬅️ Назад")
async def go_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню 👇", reply_markup=MAIN_KB)


@router.message(F.text == "📈 Купить")
async def buy(message: Message, state: FSMContext):
    await state.set_state(Form.buy_amount)
    max_rub = int(config.buy_reserve_bc / 1000 * config.buy_rate)
    await message.answer(
        "📈 <b>Купить</b>\n\n"
        f"🔥 Курс: <b>{config.buy_rate:g}₽ за 1000 BC</b>\n"
        f"💰 Резерв: <b>{money(config.buy_reserve_bc)} BC</b>\n\n"
        f"✏️ Введите сумму покупки (макс {money(max_rub)}₽)\n"
        "Пример: 500, 10k, 15000р",
        reply_markup=BUY_PRESETS,
        parse_mode="HTML",
    )


@router.message(Form.buy_amount)
async def buy_amount(message: Message, state: FSMContext):
    rub = parse_rubles(message.text or "")
    if not rub or rub <= 0:
        await message.answer("Введите сумму, например 500 или 10k.")
        return
    max_rub = int(config.buy_reserve_bc / 1000 * config.buy_rate)
    if rub > max_rub:
        await message.answer(f"Сейчас максимум {money(max_rub)}₽.")
        return
    bc = int(rub / config.buy_rate * 1000)
    await state.clear()
    await message.answer(
        f"💎 Вы покупаете: <b>{money(bc)} BC</b>\n"
        f"💵 К оплате: <b>{money(rub)} ₽</b>\n\n"
        "🏁 Выберите способ оплаты 👇\n\n"
        "❤️ <b>СБП</b> — шаблон, API пока не подключён\n"
        "🤖 <b>CryptoBot</b> — подключим через API\n"
        "⭐ <b>Telegram Stars</b> — подключим позже",
        reply_markup=kb([["❤️ СБП"], ["🤖 CryptoBot"], ["⭐ Telegram Stars"], ["⬅️ Назад"]]),
        parse_mode="HTML",
    )


@router.message(F.text.in_({"❤️ СБП", "🤖 CryptoBot", "⭐ Telegram Stars"}))
async def payment_stub(message: Message):
    await message.answer(
        "🧩 Платёжный модуль пока в режиме шаблона.\n"
        "Здесь будет создание счёта, проверка оплаты и автоматическая выдача BC через API.",
        reply_markup=MAIN_KB,
    )


@router.message(F.text == "📉 Продать")
async def sell(message: Message, state: FSMContext):
    await state.set_state(Form.sell_amount)
    await message.answer(
        "📉 <b>Продать</b>\n\n"
        f"🔥 Курс: <b>{config.sell_rate:g}₽ за 1000 BC</b>\n"
        f"💵 Резерв: <b>{money(config.sell_reserve_rub)}₽</b>\n\n"
        f"✏️ Введите сумму продажи (макс {money(config.sell_reserve_rub)}₽)\n"
        "Пример: 500, 25k, 15000р",
        reply_markup=SELL_PRESETS,
        parse_mode="HTML",
    )


@router.message(Form.sell_amount)
async def sell_amount(message: Message, state: FSMContext):
    rub = parse_rubles(message.text or "")
    if not rub or rub <= 0:
        await message.answer("Введите сумму, например 500 или 25k.")
        return
    if rub > config.sell_reserve_rub:
        await message.answer(f"Максимум по резерву: {money(config.sell_reserve_rub)}₽.")
        return
    bc = int(rub / config.sell_rate * 1000)
    await state.clear()
    await message.answer(
        f"💎 Для продажи потребуется: <b>{money(bc)} BC</b>\n"
        f"💵 К выплате: <b>{money(rub)} ₽</b>\n\n"
        "🏁 Выберите способ выплаты",
        reply_markup=kb([["💳 СБП (₽)"], ["💳 Карта (₽)"], ["🤖 CryptoBot (крипто)"], ["⬅️ Назад"]]),
        parse_mode="HTML",
    )


@router.message(F.text == "💳 СБП (₽)")
async def payout_sbp(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if user and user["sbp_phone"] and user["sbp_bank"]:
        await message.answer(
            f"✅ СБП сохранён: {user['sbp_phone']} / {user['sbp_bank']}\n\n"
            "🧩 На следующем этапе здесь будет заявка на вывод и перевод BC через API.",
            reply_markup=MAIN_KB,
        )
        return
    await state.set_state(Form.sbp_phone)
    await message.answer("📱 Введите номер телефона для СБП:", reply_markup=BACK_KB)


@router.message(Form.sbp_phone)
async def save_sbp_phone(message: Message, state: FSMContext):
    phone = (message.text or "").strip()
    if len(phone) < 7:
        await message.answer("Номер выглядит слишком коротким. Попробуйте ещё раз.")
        return
    await state.update_data(sbp_phone=phone)
    await state.set_state(Form.sbp_bank)
    await message.answer("🏦 Введите название банка, например OZON:")


@router.message(Form.sbp_bank)
async def save_sbp_bank(message: Message, state: FSMContext):
    data = await state.get_data()
    bank = (message.text or "").strip()
    set_sbp(message.from_user.id, data["sbp_phone"], bank)
    await state.clear()
    await message.answer("✅ Реквизиты СБП сохранены локально.", reply_markup=MAIN_KB)


@router.message(F.text == "💳 Карта (₽)")
async def payout_card(message: Message, state: FSMContext):
    await state.set_state(Form.card)
    await message.answer("💳 Введите номер карты:", reply_markup=BACK_KB)


@router.message(Form.card)
async def save_card(message: Message, state: FSMContext):
    card = re.sub(r"\s+", "", message.text or "")
    if not card.isdigit() or not 12 <= len(card) <= 19:
        await message.answer("Проверьте номер карты и введите его ещё раз.")
        return
    set_card(message.from_user.id, card)
    await state.clear()
    await message.answer("✅ Карта сохранена локально.", reply_markup=MAIN_KB)


@router.message(F.text == "🤖 CryptoBot (крипто)")
async def payout_crypto_stub(message: Message):
    await message.answer("🤖 CryptoBot API пока не подключён. Место под интеграцию уже предусмотрено.", reply_markup=MAIN_KB)


@router.message(F.text == "📊 Информация")
async def info(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Поддержка", url=config.support_url)
    builder.button(text="📣 Канал", url=config.channel_url)
    builder.adjust(1)
    await message.answer(
        "📊 <b>Информация</b>\n\n"
        f"📈 Купить: <b>{config.buy_rate:g}₽ / 1000 BC</b>\n"
        f"📉 Продать: <b>{config.sell_rate:g}₽ / 1000 BC</b>\n\n"
        f"📦 Продадим: <b>{money(config.buy_reserve_bc)} BC</b>\n"
        f"💸 Резерв выплат: <b>{money(config.sell_reserve_rub)}₽</b>\n\n"
        "🤖 CryptoBot: интеграция будет добавлена позже.",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


@router.message(F.text == "🧾 Профиль")
async def profile(message: Message):
    user = get_user(message.from_user.id)
    if not user:
        upsert_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        user = get_user(message.from_user.id)
    card = user["card_number"] or "Не добавлено"
    if card != "Не добавлено" and len(card) > 4:
        card = "•••• " + card[-4:]
    await message.answer(
        "🧾 <b>Ваш профиль</b>\n\n"
        f"✅ Успешных сделок: <b>{user['successful_deals']}</b>\n"
        f"📈 Купили успешно: <b>{money(user['bought_bc'])} BC</b>\n"
        f"📉 Продали успешно: <b>{money(user['sold_bc'])} BC</b>\n\n"
        f"💳 СБП: <b>{user['sbp_phone'] or 'Не добавлено'}</b>\n"
        f"🏦 Банк: <b>{user['sbp_bank'] or 'Не добавлено'}</b>\n"
        f"💳 Карта: <b>{card}</b>\n\n"
        "Реквизиты сохраняются только в локальной базе на сервере, не в GitHub.",
        reply_markup=MAIN_KB,
        parse_mode="HTML",
    )


async def main():
    init_db()
    bot = Bot(config.bot_token)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
