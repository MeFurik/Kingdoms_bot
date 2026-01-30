import io
import time
from PIL import Image, ImageDraw, ImageFont
from .config import FONT_PATH, ASSETS_DIR
from .utils import premiummultiplier

STATRU = {"Strength":"Сила","Dexterity":"Ловкость","Endurance":"Выносливость","Luck":"Удача","Intelligence":"Разум"}

def buildxpbar(xp, xptonext, length=24):
    if xptonext <= 0:
        return "█"length
    filled = int(xp/xp_to_next  length)filled = max(0, min(length, filled))
    return "█"*filled + "░"*(length-filled)

def generate_hero_card(char):
    width, height = 900, 320
    bg = (18,18,25)
    img = Image.new("RGB", (width,height), color=bg)
    draw = ImageDraw.Draw(img)
    try:
        font_h = ImageFont.truetype(FONT_PATH, 28)
        font_m = ImageFont.truetype(FONT_PATH, 18)
        font_s = ImageFont.truetype(FONT_PATH, 14)
    except Exception:
        font_h = ImageFont.load_default()
        font_m = ImageFont.load_default()
        font_s = ImageFont.load_default()

    nickname = char.get("nickname") or char.get("username") or "Герой"
    draw.text((20,20), nickname, font=font_h, fill=(230,200,100))
    draw.text((20,60), f"Класс: {char['class']}  |  Уровень: {char['level']}", font=font_m, fill=(220,220,220))
    xpbar = build_xp_bar(char.get("xp",0), char.get("xp_to_next",1000))
    draw.text((20,90), f"XP: {xpbar} {char.get('xp',0)}/{char.get('xp_to_next',1000)}", font=font_m, fill=(200,200,200))

    sx = 420
    sy = 20
    draw.text((sx,sy), "Характеристики:", font=font_h, fill=(200,160,60))
    sy += 36
    for st, label in STAT_RU.items():
        draw.text((sx, sy), f"{label}: {char['stats'][st]}", font=font_m, fill=(230,230,230))
        sy += 26

    # bottom status
    is_premium = (char.get("premium_until",0) or 0) > int(time.time())
    status = "Премиум" if is_premium else "Обычный"
    gold = char.get("gold",0) or 0
    platinum = char.get("platinum",0) or 0
    bottom = f"HP: ?  Mana: ?   Платина: {platinum}♢   Золото: {gold}  Статус: {status}"
    draw.text((20, height-40), bottom, font=font_s, fill=(200,200,200))

    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio.getvalue()