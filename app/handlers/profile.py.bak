from aiogram import Router
from aiogram.types import CallbackQuery, InputFile
from ..db import load_character
from ..visuals import generate_hero_card
from ..keyboards import profile_kb
from ..utils import add_xp, add_gold

router = Router()

@router.callback_query(lambda c: c.data == "my_char")
async def cb_my_char(callback: CallbackQuery):
    await callback.answer()
    uid = callback.from_user.id
    char = await load_character(uid)
    if not char:
        await callback.message.edit_text("Персонаж не найден. Создайте персонажа.")
        return
    img = generate_hero_card(char)
    await callback.message.answer_photo(photo=InputFile(io.BytesIO(img), filename="hero.png"), caption=f"Профиль {char.get('nickname')}", reply_markup=profile_kb())

@router.callback_query(lambda c: c.data == "farm")
async def cb_farm(callback: CallbackQuery):
    await callback.answer()
    uid = callback.from_user.id
    # demo: base xp 100, base gold 20
    total_xp, levels = await add_xp(uid, 100, reason="farm")
    total_gold = await add_gold(uid, 20, reason="farm")
    text = f"Вы получили {total_xp} XP и {total_gold} золота."
    if levels>0:
        text += f"\nПовышены уровни: {levels} (получено +{5*levels} очков навыков)."
    await callback.message.answer(text)