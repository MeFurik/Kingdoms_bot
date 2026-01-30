from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
import io
import time
import aiosqlite

from ..db import load_character, save_character, add_admin_log, add_purchase
from ..visuals import generate_hero_card
from ..keyboards import admin_panel_kb
from ..states import AdminStates
from ..config import ADMIN_IDS, DB_PATH

router = Router()

# admin panel entrance
@router.callback_query(F.data == "admin_panel")
async def cb_admin_panel(callback: CallbackQuery):
    await callback.answer()
    uid = callback.from_user.id
    char = await load_character(uid)
    if not (uid in (ADMIN_IDS or []) or (char and char.get("is_admin"))):
        await callback.answer("Только администратор.", show_alert=True)
        return
    await callback.message.edit_text("Админ-панель:", reply_markup=admin_panel_kb())

# list characters
@router.callback_query(F.data == "admin_list")
async def cb_admin_list(callback: CallbackQuery):
    await callback.answer()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT userid,nickname,username,class,level,platinum FROM characters ORDER BY level DESC LIMIT 50")
        rows = await cur.fetchall()
        await cur.close()
    if not rows:
        await callback.message.edit_text("Список пуст.", reply_markup=admin_panel_kb())
        return
    kb = InlineKeyboardMarkup()
    for r in rows:
        userid, nick, username, cls, lvl, plat = r
        label = f"{nick or username or userid} ({cls}, lvl {lvl}) ♢{plat}"
        kb.add(InlineKeyboardButton(label, callback_data=f"adminview:{userid}"))
    kb.add(InlineKeyboardButton("Назад", callback_data="admin_panel"))
    await callback.message.edit_text("Список персонажей:", reply_markup=kb)

# view character
@router.callback_query(F.data.startswith("adminview:"))
async def cb_admin_view(callback: CallbackQuery):
    await callback.answer()
    _, tid = callback.data.split(":", 1)
    targetid = int(tid)
    tchar = await load_character(targetid)
    if not tchar:
        await callback.message.edit_text("Персонаж не найден.", reply_markup=admin_panel_kb())
        return
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Добавить платину", callback_data=f"adminaddplatinum:{targetid}"))
    kb.add(InlineKeyboardButton("Выдать Premium (дни)", callback_data=f"admingivepremium:{targetid}"))
    kb.add(InlineKeyboardButton("Сделать/снять админа", callback_data=f"admintoggleadmin:{targetid}"))
    kb.add(InlineKeyboardButton("Установить ник", callback_data=f"adminsetnick:{targetid}"))
    kb.add(InlineKeyboardButton("Установить класс", callback_data=f"adminsetclass:{targetid}"))
    kb.add(InlineKeyboardButton("Назад", callback_data="admin_list"))
    img = generate_hero_card(tchar)
    await callback.message.answer_photo(photo=InputFile(io.BytesIO(img), filename="hero.png"),
                                        caption=f"Персонаж {targetid}: {tchar.get('nickname')}",
                                        reply_markup=kb)

# add platinum -> ask for amount@router.callback_query(F.data.startswith("adminaddplatinum:"))
async def cb_admin_add_platinum(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    _, tid = callback.data.split(":", 1)
    targetid = int(tid)
    await state.update_data(admintarget=targetid)
    await callback.message.edit_text("Введите количество платин (целое число):")
    await state.set_state(AdminStates.waitingamount)

# process amount (from state)
@router.message(F.chat.type == "private", state=AdminStates.waitingamount)
async def process_admin_amount(message: Message, state: FSMContext):
    data = await state.get_data()
    target = data.get("admintarget")
    try:
        amount = int(message.text.strip())
    except Exception:
        await message.reply("Введите целое число.")
        return
    tchar = await load_character(target)
    if not tchar:
        await message.reply("Целевой персонаж не найден.")
        await state.clear()
        return
    tchar["platinum"] = tchar.get("platinum", 0) + amount
    await save_character(target, tchar)
    await add_admin_log(message.from_user.id, "addplatinum", target, {"amount": amount})
    await message.reply(f"Добавлено {amount}♢ пользователю {target}.")
    try:
        await message.bot.send_message(target, f"Вам начислено {amount}♢ администратором.")
    except Exception:
        pass
    await state.clear()

# give premium -> ask days
@router.callback_query(F.data.startswith("admingivepremium:"))
async def cb_admin_give_premium(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    _, tid = callback.data.split(":", 1)
    targetid = int(tid)
    await state.update_data(admintarget=targetid)
    await callback.message.edit_text("Введите количество дней Premium (целое число):")
    await state.set_state(AdminStates.waitingdays)

@router.message(F.chat.type == "private", state=AdminStates.waitingdays)
async def process_admin_days(message: Message, state: FSMContext):
    data = await state.get_data()
    target = data.get("admintarget")
    try:
        days = int(message.text.strip())
    except Exception:
        await message.reply("Введите целое число.")
        return
    tchar = await load_character(target)
    if not tchar:
        await message.reply("Целевой персонаж не найден.")
        await state.clear()
        return
    addsec = days * 24 * 3600
    curuntil = tchar.get("premium_until", 0) or 0
    tchar["premium_until"] = max(curuntil, int(time.time())) + addsec
    await save_character(target, tchar)
    await add_admin_log(message.from_user.id, "givepremium", target, {"days": days})
    await message.reply(f"Выдан Premium на {days} дней пользователю {target}.")
    try:
        await message.bot.send_message(target, f"Вам выдан Premium на {days} дней администратором.")
    except Exception:
        pass
    await state.clear()

# toggle admin
@router.callback_query(F.data.startswith("admintoggleadmin:"))
async def cb_admin_toggle(callback: CallbackQuery):
    await callback.answer()
    _, tid = callback.data.split(":", 1)
    targetid = int(tid)
    tchar = await load_character(targetid)
    if not tchar:
        await callback.message.edit_text("Пользователь не найден.", reply_markup=admin_panel_kb())
        return
    tchar["is_admin"] = not tchar.get("is_admin", False)
    await save_character(targetid, tchar)
    await add_admin_log(callback.from_user.id, "toggleadmin", targetid, {"is_admin": tchar["is_admin"]})
    await callback.message.edit_text(f"Флаг админа для {targetid} установлен в {tchar['is_admin']}.", reply_markup=admin_panel_kb())

# set nick
@router.callback_query(F.data.startswith("adminsetnick:"))
async def cb_admin_set_nick(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    _, tid = callback.data.split(":", 1)
    targetid = int(tid)
    await state.update_data(admintarget=targetid)
    await callback.message.edit_text("Введите новый ник (текст):")
    await state.set_state(AdminStates.waitingnick)

# process nick@router.message(F.chat.type == "private", state=AdminStates.waitingnick)
async def processadminsetnick(message: Message, state: FSMContext):
    data = await state.getdata()
    target = data.get("admintarget")
    newnick = (message.text or "").strip():32
    tchar = await loadcharacter(target)
    if not tchar:
        await message.reply("Пользователь не найден.")
        await state.clear()
        return
    tchar["nickname"] = newnick
    await savecharacter(target, tchar)
    await addadminlog(message.fromuser.id, "setnick", target, {"nick": newnick})
    await message.reply(f"Ник для {target} установлен: {newnick}")
    await state.clear()