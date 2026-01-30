from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
import io
import time

from ..db import load_character, save_character, add_admin_log
from ..db import add_purchase
from ..visuals import generate_hero_card
from ..keyboards import admin_panel_kb
from ..states import AdminStates

router = Router()

# admin panel entrance
@router.callback_query(lambda c: c.data == "admin_panel")
async def cb_admin_panel(callback: CallbackQuery):
    await callback.answer()
    uid = callback.from_user.id
    char = await load_character(uid)
    if not (uid in callback.bot.get('ADMIN_IDS') or (char and char.get("is_admin"))):
        # safer check: we'll treat ADMIN_IDS in config; here we simply deny if not admin
        await callback.answer("Только администратор.", show_alert=True); return
    await callback.message.edit_text("Админ-панель:", reply_markup=admin_panel_kb())

# list characters
@router.callback_query(lambda c: c.data == "admin_list")
async def cb_admin_list(callback: CallbackQuery):
    await callback.answer()# fetch up to 50 characters
    import aiosqlite
    from ..config import DBPATH
    async with aiosqlite.connect(DBPATH) as db:
        cur = await db.execute("SELECT userid,nickname,username,class,level,platinum FROM characters ORDER BY level DESC LIMIT 50")
        rows = await cur.fetchall()
        await cur.close()
    if not rows:
        await callback.message.edittext("Список пуст.", replymarkup=adminpanelkb()); return
    kb = InlineKeyboardMarkup()
    for r in rows:
        userid, nick, username, cls, lvl, plat = r
        label = f"{nick or username or userid} ({cls}, lvl {lvl}) ♢{plat}"
        kb.add(InlineKeyboardButton(label, callbackdata=f"adminview:{userid}"))
    kb.add(InlineKeyboardButton("Назад", callbackdata="adminpanel"))
    await callback.message.edittext("Список персонажей:", replymarkup=kb)

# view character
@router.callbackquery(lambda c: c.data and c.data.startswith("adminview:"))
async def cbadminview(callback: CallbackQuery):
    await callback.answer()
    , tid = callback.data.split(":",1)
    targetid = int(tid)
    tchar = await loadcharacter(targetid)
    if not tchar:
        await callback.message.edittext("Персонаж не найден.", replymarkup=adminpanelkb()); return
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Добавить платину", callbackdata=f"adminaddplatinum:{targetid}"))
    kb.add(InlineKeyboardButton("Выдать Premium (дни)", callbackdata=f"admingivepremium:{targetid}"))
    kb.add(InlineKeyboardButton("Сделать/снять админа", callbackdata=f"admintoggleadmin:{targetid}"))
    kb.add(InlineKeyboardButton("Установить ник", callbackdata=f"adminsetnick:{targetid}"))
    kb.add(InlineKeyboardButton("Установить класс", callbackdata=f"adminsetclass:{targetid}"))
    kb.add(InlineKeyboardButton("Назад", callbackdata="adminlist"))
    img = generateherocard(tchar)
    await callback.message.answerphoto(photo=InputFile(io.BytesIO(img), filename="hero.png"), caption=f"Персонаж {targetid}: {tchar.get('nickname')}", replymarkup=kb)

# add platinum -> ask for amount
@router.callbackquery(lambda c: c.data and c.data.startswith("adminaddplatinum:"))
async def cbadminaddplatinum(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    , tid = callback.data.split(":",1)
    targetid = int(tid)
    await state.updatedata(admintarget=targetid)
    await callback.message.edittext("Введите количество платин (целое число):")
    await state.setstate(AdminStates.waitingamount)

@router.message(F.chat.type == "private", state=AdminStates.waitingamount)
async def processadminamount(message: Message, state: FSMContext):
    data = await state.getdata()
    target = data.get("admintarget")
    try:
        amount = int(message.text.strip())
    except:
        await message.reply("Введите целое число."); return
    tchar = await loadcharacter(target)
    if not tchar:
        await message.reply("Целевой персонаж не найден."); await state.clear(); return
    tchar["platinum"] = tchar.get("platinum",0) + amount
    await savecharacter(target, tchar)
    await addadminlog(message.fromuser.id, "addplatinum", target, {"amount": amount})
    await message.reply(f"Добавлено {amount}♢ пользователю {target}.")
    try:
        await message.bot.sendmessage(target, f"Вам начислено {amount}♢ администратором.")
    except:
        pass
    await state.clear()

# give premium -> ask days
@router.callbackquery(lambda c: c.data and c.data.startswith("admingivepremium:"))
async def cbadmingivepremium(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    , tid = callback.data.split(":",1)
    targetid = int(tid)
    await state.updatedata(admintarget=targetid)
    await callback.message.edittext("Введите количество дней Premium (целое число):")
    await state.setstate(AdminStates.waitingdays)

@router.message(F.chat.type == "private", state=AdminStates.waitingdays)
async def processadmindays(message: Message, state: FSMContext):data = await state.getdata()
    target = data.get("admintarget")
    try:
        days = int(message.text.strip())
    except:
        await message.reply("Введите целое число."); return
    tchar = await loadcharacter(target)
    if not tchar:
        await message.reply("Целевой персонаж не найден."); await state.clear(); return
    addsec = days243600
    curuntil = tchar.get("premiumuntil",0) or 0
    tchar"premium_until" = max(curuntil, int(time.time())) + addsec
    await savecharacter(target, tchar)
    await addadminlog(message.fromuser.id, "givepremium", target, {"days": days})
    await message.reply(f"Выдан Premium на {days} дней пользователю {target}.")
    try:
        await message.bot.sendmessage(target, f"Вам выдан Premium на {days} дней администратором.")
    except:
        pass
    await state.clear()

# toggle admin
@router.callbackquery(lambda c: c.data and c.data.startswith("admintoggleadmin:"))
async def cbadmintoggle(callback: CallbackQuery):
    await callback.answer()
    , tid = callback.data.split(":",1)
    targetid = int(tid)
    tchar = await loadcharacter(targetid)
    if not tchar:
        await callback.message.edittext("Пользователь не найден.", replymarkup=adminpanelkb()); return
    tchar["isadmin"] = not tchar.get("isadmin", False)
    await savecharacter(targetid, tchar)
    await addadminlog(callback.fromuser.id, "toggleadmin", targetid, {"isadmin": tchar["isadmin"]})
    await callback.message.edittext(f"Флаг админа для {targetid} установлен в {tchar'is_admin'}.", replymarkup=adminpanelkb())

# set nick
@router.callbackquery(lambda c: c.data and c.data.startswith("adminsetnick:"))
async def cbadminsetnick(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    , tid = callback.data.split(":",1)
    targetid = int(tid)
    await state.updatedata(admintarget=targetid)
    await callback.message.edittext("Введите новый ник (текст):")
    await state.setstate(AdminStates.waitingnick)

@router.message(F.chat.type == "private", state=AdminStates.waitingnick)
async def processadminsetnick(message: Message, state: FSMContext):
    data = await state.getdata()
    target = data.get("admintarget")
    newnick = (message.text or "").strip()[:32]
    tchar = await loadcharacter(target)
    if not tchar:
        await message.reply("Пользователь не найден."); await state.clear(); return
    tchar"nickname" = newnick
    await savecharacter(target, tchar)
    await addadminlog(message.fromuser.id, "setnick", target, {"nick": newnick})
    await message.reply(f"Ник для {target} установлен: {newnick}")
    await state.clear()

# set class (show choices and accept)
@router.callbackquery(lambda c: c.data and c.data.startswith("adminsetclass:"))
async def cbadminsetclass(callback: CallbackQuery):
    await callback.answer()
    , tid = callback.data.split(":",1)
    targetid = int(tid)
    kb = InlineKeyboardMarkup()
    for c in ["Воин","Лучник","Маг","Друид"]:
        kb.add(InlineKeyboardButton(c, callbackdata=f"adminsetclassdo:{targetid}:{c}"))
    kb.add(InlineKeyboardButton("Отмена", callbackdata="adminpanel"))
    await callback.message.edittext("Выберите класс:", replymarkup=kb)

@router.callbackquery(lambda c: c.data and c.data.startswith("adminsetclassdo:"))
async def cbadminsetclassdo(callback: CallbackQuery):
    await callback.answer()
    , tid, newclass = callback.data.split(":",2)
    targetid = int(tid)
    tchar = await loadcharacter(targetid)
    if not tchar:
        await callback.message.edittext("Пользователь не найден.", replymarkup=adminpanelkb()); return
    tchar["class"] = newclass
    await savecharacter(targetid, tchar)
    await addadminlog(callback.fromuser.id, "setclass", targetid, {"class": newclass})
    await callback.message.edittext(f"Класс для {targetid} установлен: {newclass}", replymarkup=adminpanelkb())