from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .config import ADMIN_IDS
from .db import load_character

def start_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Создать персонажа", callback_data="create")],
        [InlineKeyboardButton("Мой персонаж", callback_data="my_char")]
    ])

def classes_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Воин", callback_data="class:Воин"),
           InlineKeyboardButton("Лучник", callback_data="class:Лучник"))
    kb.add(InlineKeyboardButton("Маг", callback_data="class:Маг"),
           InlineKeyboardButton("Друид", callback_data="class:Друид"))
    kb.add(InlineKeyboardButton("Отмена", callback_data="cancel"))
    return kb

def stats_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    stats = ["Strength","Dexterity","Endurance","Luck","Intelligence"]
    for st in stats:
        kb.row(InlineKeyboardButton(f"+ {st}", callback_data=f"stat:{st}:inc"),
               InlineKeyboardButton(f"- {st}", callback_data=f"stat:{st}:dec"))
    kb.row(InlineKeyboardButton("Подтвердить", callback_data="confirm"),
           InlineKeyboardButton("Отменить", callback_data="cancel"))
    return kb

def profile_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Фарм (тест) +100XP +20 золота", callback_data="farm"))
    kb.add(InlineKeyboardButton("Магазин", callback_data="shop"))
    kb.add(InlineKeyboardButton("Статус", callback_data="show_status"))
    kb.add(InlineKeyboardButton("Назад", callback_data="back_to_menu"))
    return kb

def shop_kb(costs):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(f"Premium 1 день — {costs['premium_1']}♢", callback_data="buy:premium_1"))
    kb.add(InlineKeyboardButton(f"Premium 7 дней — {costs['premium_7']}♢", callback_data="buy:premium_7"))
    kb.add(InlineKeyboardButton(f"Сменить ник — {costs['change_nick']}♢", callback_data="buy:change_nick"))
    kb.add(InlineKeyboardButton("Назад", callback_data="back_to_menu"))
    return kb

def admin_panel_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Список персонажей", callback_data="admin_list"))
    kb.add(InlineKeyboardButton("Назад", callback_data="back_to_menu"))
    return kb