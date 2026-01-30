from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputFile
from aiogram.fsm.context import FSMContext
from ..keyboards import start_kb, classes_kb, stats_kb
from ..db import save_creation_session, load_creation_session, delete_creation_session, save_character
from ..visuals import generate_hero_card
from ..config import WELCOME_IMG
from .. import utils
from .. import db as _db

router = Router()

STATS = ["Strength","Dexterity","Endurance","Luck","Intelligence"]
STAT_RU = {"Strength":"Сила","Dexterity":"Ловкость","Endurance":"Выносливость","Luck":"Удача","Intelligence":"Разум"}

def build_creation_text(session):
    lines = [f"Распределение для класса: {session['class']}", f"Ник: {session.get('nickname')}", f"Осталось очков: {session['points_left']}", ""]
    for st in STATS:
        lines.append(f"{STAT_RU[st]}: {session['stats'][st]}")
    lines.append("")
    lines.append("Нажимайте + / - для изменения. После заполнения нажмите Подтвердить.")
    return "\n".join(lines)

@router.message(F.text, F.chat.type == "private", commands=["start"])
async def cmd_start(message: Message):
    caption = "Привет! Нажми Создать персонажа чтобы начать."
    if WELCOME_IMG:
        try:
            await message.answer_photo(photo=InputFile(WELCOME_IMG), caption=caption, reply_markup=start_kb())
            return
        except Exception:
            pass
    await message.answer(caption, reply_markup=start_kb())

@router.callback_query(lambda c: c.data=="create")
async def cb_create(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Выберите класс героя:", reply_markup=classes_kb())

@router.callback_query(lambda c: c.data and c.data.startswith("class:"))
async def cb_class(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    _, cls = callback.data.split(":",1)
    uid = callback.from_user.id
    session = {"step":"waiting_nick","class":cls,"nickname":None,"stats":{st:0 for st in STATS},"points_left":10,"ui_chat_id":None,"ui_message_id":None}
    await save_creation_session(uid, session)
    await callback.message.edit_text(f"Выбрано: {cls}\nВведите ник (до 32 символов):")
    await state.set_state("waiting_nick")

@router.message(F.chat.type=="private", state="waiting_nick")
async def process_nick(message: Message, state: FSMContext):
    uid = message.from_user.id
    nick = (message.text or "").strip()[:32]
    if not nick:
        await message.reply("Неверный ник.")
        return
    session = await load_creation_session(uid)
    if not session:
        await message.reply("Сессия не найдена.")
        await state.clear()
        return
    session["nickname"] = nick
    session["step"] = "allocating"
    session["stats"] = {st:0 for st in STATS}
    session["points_left"] = 10
    text = build_creation_text(session)
    sent = await message.reply(text, reply_markup=stats_kb())
    session["ui_chat_id"] = sent.chat.id
    session["ui_message_id"] = sent.message_id
    await save_creation_session(uid, session)
    await state.set_state("allocating")

@router.callback_query(lambda c: c.data and c.data.startswith("stat:"))
async def cb_stat_change(callback: CallbackQuery):
    await callback.answer()
    uid = callback.from_user.id
    session = await load_creation_session(uid)
    if not session or session.get("step")!="allocating":
        await callback.message.answer("Сессия не найдена.")
        return
    _, stat, action = callback.data.split(":")
    if action=="inc":
        if session["points_left"]<=0:
            await callback.answer("Очки закончились", show_alert=True); return
        session["stats"][stat]+=1; session["points_left"]-=1
    else:
        if session["stats"][stat]<=0:
            await callback.answer("Нельзя уменьшить ниже 0", show_alert=True); return
        session["stats"][stat]-=1; session["points_left"]+=1
    await save_creation_session(uid, session)
    text = build_creation_text(session)
    try:await callback.bot.edit_message_text(text, chat_id=session["ui_chat_id"], message_id=session["ui_message_id"], reply_markup=stats_kb())
    except:
        await callback.message.edit_text(text, reply_markup=stats_kb())

@router.callback_query(lambda c: c.data=="confirm")
async def cb_confirm(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    session = await load_creation_session(uid)
    if not session:
        await callback.message.answer("Сессия не найдена.")
        return
    if session.get("points_left",0)!=0:
        await callback.answer("Нужно потратить все очки", show_alert=True); return
    char = {"nickname":session.get("nickname"),"username":callback.from_user.username or "","class":session.get("class"),
            "level":1,"xp":0,"xp_to_next":1000,"available_points":0,"stats":session.get("stats"),
            "premium_until":0,"platinum":0,"gold":0,"is_admin":0}
    await save_character(uid, char)
    await delete_creation_session(uid)
    img = generate_hero_card(char)
    await callback.message.answer_photo(photo=InputFile(io.BytesIO(img), filename="hero.png"), caption=f"Добро пожаловать, {char['nickname']}!", reply_markup=None)
    await state.clear()