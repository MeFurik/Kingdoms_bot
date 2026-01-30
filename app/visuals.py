import io
import time
from PIL import Image, ImageDraw, ImageFont
from .config import FONT_PATH, ASSETS_DIR
from .utils import premiummultiplier

STAT_RU = {
    "Strength": "Сила",
    "Dexterity": "Ловкость",
    "Endurance": "Выносливость",
    "Luck": "Удача",
    "Intelligence": "Разум",
}

def build_xp_bar(xp, xp_to_next, length=24):
    try:
        xp = int(xp or 0)
        xp_to_next = int(xp_to_next or 0)
        length = int(length)
    except (TypeError, ValueError):
        return "░" * max(0, int(length))

    if length <= 0:
        return ""

    if xp_to_next <= 0:
        # если цель не задана, считаем шкалу полной
        return "█" * length

    ratio = max(0.0, min(1.0, xp / xp_to_next))
    filled = int(round(ratio * length))
    filled = max(0, min(length, filled))
    return "█" * filled + "░" * (length - filled)

def generate_hero_card(char):
    width, height = 900, 320
    bg = (18, 18, 25)
    img = Image.new("RGB", (width, height), color=bg)
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
    draw.text((20, 20), nickname, font=font_h, fill=(230, 200, 100))

    cls = char.get("class", "-")
    level = char.get("level", 0)
    draw.text((20, 60), f"Класс: {cls}  |  Уровень: {level}", font=font_m, fill=(220, 220, 220))

    xp = char.get("xp", 0) or 0
    xp_to_next = char.get("xp_to_next", 1000) or 1000
    xpbar = build_xp_bar(xp, xp_to_next, length=24)
    draw.text((20, 90), f"XP: {xpbar} {xp}/{xp_to_next}", font=font_m, fill=(200, 200, 200))

    sx = 420
    sy = 20
    draw.text((sx, sy), "Характеристики:", font=font_h, fill=(200, 160, 60))
    sy += 36

    stats = char.get("stats", {}) or {}
    for st_key, label in STAT_RU.items():
        val = stats.get(st_key, 0)
        draw.text((sx, sy), f"{label}: {val}", font=font_m, fill=(230, 230, 230))
        sy += 26

    # bottom status
    is_premium = (char.get("premium_until", 0) or 0) > int(time.time())
    status = "Премиум" if is_premium else "Обычный"
    gold = char.get("gold", 0) or 0
    platinum = char.get("platinum", 0) or 0
    bottom = f"HP: ?  Mana: ?   Платина: {platinum}♢   Золото: {gold}  Статус: {status}"
    draw.text((20, height - 40), bottom, font=font_s, fill=(200, 200, 200))

    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio.getvalue()