from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InputFile
from aiogram.fsm.context import FSMContext
import io
import time

from ..db import load_character, save_character, save_creation_session, delete_creation_session, add_purchase
from ..visuals import generate_hero_card
from ..keyboards import shop_kb, stats_kb, profile_kb
from ..config import SHOP_COSTS, PREMIUM_DAYS
from ..states import ShopStates, CreateStates
from ..utils import add_xp, add_gold

router = Router()

# Show shop
@router.callback_query(lambda c: c.data == "shop")
async def cb_shop(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Магазин:", reply_markup=shop_kb(SHOP_COSTS))

# Buy handlers
@router.callback_query(lambda c: c.data and c.data.startswith("buy:"))
async def cb_buy(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    kind = callback.data.split(":",1)[1]
    char = await load_character(uid)
    if not char:
        await callback.message.edit_text("Персонаж не найден. Создайте персонажа.", reply_markup=None)
        return

    # Premium purchases
    if kind in PREMIUM_DAYS:
        cost = SHOP_COSTS.get(kind)
        if char.get("platinum",0) < cost:
            await callback.answer("Недостаточно платин.", show_alert=True); return
        char["platinum"] -= cost
        days = PREMIUM_DAYS[kind]
        add_sec = days * 24 * 3600
        cur_until = char.get("premium_until",0) or 0
        char["premium_until"] = max(cur_until, int(time.time())) + add_sec
        await save_character(uid, char)
        await add_purchase(uid, kind, cost)
        await callback.message.edit_text(f"Куплено Premium на {days} дней.", reply_markup=profile_kb())
        return

    # change nick
    if kind == "change_nick":
        cost = SHOP_COSTS.get("change_nick", 0)
        if char.get("platinum",0) < cost:
            await callback.answer("Недостаточно платин.", show_alert=True); return
        char["platinum"] -= cost
        await save_character(uid, char)
        await callback.message.edit_text("Напишите новый ник (текстом):")
        await state.set_state(ShopStates.waiting_nick)
        return

    # change class
    if kind == "change_class":
        cost = SHOP_COSTS.get("change_class", 0)
        if char.get("platinum",0) < cost:
            await callback.answer("Недостаточно платин.", show_alert=True); return
        char["platinum"] -= cost
        await save_character(uid, char)
        # show class buttons (simple callbacks buyclass:<class>)
        kb = []
        for c in ["Воин","Лучник","Маг","Друид"]:kb.append([{"text": c, "callback_data": f"buyclass:{c}"}])
        # we'll use reply_markup built manually to keep simple
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        markup = InlineKeyboardMarkup()
        for c in ["Воин","Лучник","Маг","Друид"]:
            markup.add(InlineKeyboardButton(c, callback_data=f"buyclass:{c}"))
        markup.add(InlineKeyboardButton("Отмена", callback_data="back_to_menu"))
        await callback.message.edit_text("Выберите новый класс:", reply_markup=markup)
        return

    # respec
    if kind == "respec":
        cost = SHOP_COSTS.get("respec",0)
        if char.get("platinum",0) < cost:
            await callback.answer("Недостаточно платин.", show_alert=True); return
        char["platinum"] -= cost
        await save_character(uid, char)
        # initialize creation session for reallocation
        session = {
            "step": "allocating",
            "class": char["class"],
            "nickname": char.get("nickname"),
            "stats": {st: 0 for st in char["stats"].keys()},
            "points_left": 10,
            "ui_chat_id": None,
            "ui_message_id": None
        }
        text = "Полная перераспределка: распределите 10 очков заново."
        sent = await callback.message.answer(text, reply_markup=stats_kb())
        session["ui_chat_id"] = sent.chat.id
        session["ui_message_id"] = sent.message_id
        await save_creation_session(uid, session)
        await state.set_state(CreateStates.allocating)
        return

# buyclass callbacks
@router.callback_query(lambda c: c.data and c.data.startswith("buyclass:"))
async def cb_buyclass(callback: CallbackQuery):
    await callback.answer()
    uid = callback.from_user.id
    new_class = callback.data.split(":",1)[1]
    char = await load_character(uid)
    if not char:
        await callback.message.edit_text("Персонаж не найден.", reply_markup=None)
        return
    char["class"] = new_class
    await save_character(uid, char)
    await callback.message.edit_text(f"Класс успешно изменён на {new_class}.", reply_markup=profile_kb())

# state handler for change nick
@router.message(F.chat.type == "private", state=ShopStates.waiting_nick)
async def shop_change_nick(message: Message, state: FSMContext):
    uid = message.from_user.id
    newnick = (message.text or "").strip()[:32]
    if not newnick:
        await message.reply("Неверный ник. Попробуйте снова.")
        return
    char = await load_character(uid)
    if not char:
        await message.reply("Персонаж не найден.")
        await state.clear()
        return
    char["nickname"] = newnick
    await save_character(uid, char)
    await add_purchase(uid, "change_nick", SHOP_COSTS.get("change_nick",0))
    await message.reply(f"Ник успешно изменён на: {newnick}", reply_markup=profile_kb())
    await state.clear()