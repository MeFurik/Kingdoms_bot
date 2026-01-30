import time
from typing import Tuple
from . import db

# Premium multiplier: 1.5 for premium, else 1.0
def premiummultiplier(ispremium: bool) -> float:
    return 1.5 if ispremium else 1.0

async def ispremiumuser(char: dict) -> bool:
    return (char.get("premium_until",0) or 0) > int(time.time())

# Add XP: applies multiplier, writes xp log, handles level up, returns tuple (gainedtotalxp, levelsgained)
async def add_xp(userid: int, basexp: int, reason: str=""):
    char = await db.load_character(userid)
    if not char:
        return (0,0)
    ispremiumflag = await ispremiumuser(char)
    mult = premiummultiplier(ispremiumflag)
    total = int(base_xp * mult)
    bonus = total - base_xp
    # update character xp
    new_xp = (char.get("xp",0) or 0) + total
    levels_gained = 0
    xp_to_next = char.get("xp_to_next", 1000)
    while new_xp >= xp_to_next:
        new_xp -= xp_to_next
        char["level"] = char.get("level",1) + 1
        char["available_points"] = (char.get("available_points",0) or 0) + 5
        levels_gained += 1
        # optionally scale xp_to_next per level (here keep constant 1000)
        # xp_to_next could be char['xp_to_next'] = int(xp_to_next  1.1)
    char["xp"] = new_xp
    char["xp_to_next"] = xp_to_next
    await db.save_character(userid, char)
    await db.addxplog(userid, basexp, bonus, total, reason or "auto")
    return (total, levels_gained)

# Add gold: applies multiplier and writes gold log; gold stored in char'gold'
async def add_gold(userid: int, basegold: int, reason: str=""):
    char = await db.load_character(userid)
    if not char:
        return 0
    ispremiumflag = await ispremiumuser(char)
    mult = premiummultiplier(ispremiumflag)
    total = int(basegold * mult)
    bonus = total - basegold
    char["gold"] = (char.get("gold",0) or 0) + total
    await db.save_character(userid, char)
    await db.addgoldlog(userid, basegold, bonus, total, reason or "auto")
    return total