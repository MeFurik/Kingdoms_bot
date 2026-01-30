import time
import json
import aiosqlite
from typing import Optional
from .config import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS characters (
            user_id INTEGER PRIMARY KEY,
            nickname TEXT,
            username TEXT,
            class TEXT,
            level INTEGER,
            xp INTEGER,
            xp_to_next INTEGER,
            available_points INTEGER,
            stats_json TEXT,
            premium_until INTEGER DEFAULT 0,
            platinum INTEGER DEFAULT 0,
            gold INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS creation_sessions (
            user_id INTEGER PRIMARY KEY,
            step TEXT,
            class TEXT,
            nickname TEXT,
            stats_json TEXT,
            points_left INTEGER,
            ui_chat_id INTEGER,
            ui_message_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            kind TEXT,
            amount INTEGER,
            created_at INTEGER
        );CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            action TEXT,
            target_user INTEGER,
            meta_json TEXT,
            created_at INTEGER
        );
        CREATE TABLE IF NOT EXISTS xp_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            base_xp INTEGER,
            bonus_xp INTEGER,
            total_xp INTEGER,
            reason TEXT,
            created_at INTEGER
        );
        CREATE TABLE IF NOT EXISTS gold_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            base_gold INTEGER,
            bonus_gold INTEGER,
            total_gold INTEGER,
            reason TEXT,
            created_at INTEGER
        );
        """)
        await db.commit()

# Character persistence functions
async def save_character(user_id: int, char: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT OR REPLACE INTO characters (user_id,nickname,username,class,level,xp,xp_to_next,available_points,stats_json,premium_until,platinum,gold,is_admin)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            user_id,
            char.get("nickname"),
            char.get("username",""),
            char["class"],
            char.get("level",1),
            char.get("xp",0),
            char.get("xp_to_next",1000),
            char.get("available_points",0),
            json.dumps(char["stats"], ensure_ascii=False),
            char.get("premium_until",0),
            char.get("platinum",0),
            char.get("gold",0),
            1 if char.get("is_admin") else 0
        ))
        await db.commit()

async def load_character(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT nickname,username,class,level,xp,xp_to_next,available_points,stats_json,premium_until,platinum,gold,is_admin FROM characters WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        await cur.close()
        if not row:
            return None
        return {
            "nickname": row[0],
            "username": row[1],
            "class": row[2],
            "level": row[3],
            "xp": row[4],
            "xp_to_next": row[5],
            "available_points": row[6],
            "stats": json.loads(row[7]),
            "premium_until": row[8] or 0,
            "platinum": row[9] or 0,
            "gold": row[10] or 0,
            "is_admin": bool(row[11])
        }

# Creation session functions (persistent)
async def save_creation_session(user_id: int, session: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT OR REPLACE INTO creation_sessions (user_id,step,class,nickname,stats_json,points_left,ui_chat_id,ui_message_id)
        VALUES (?,?,?,?,?,?,?,?)
        """, (
            user_id,
            session.get("step"),
            session.get("class"),
            session.get("nickname"),
            json.dumps(session.get("stats", {}), ensure_ascii=False),
            session.get("points_left"),
            session.get("ui_chat_id"),
            session.get("ui_message_id")
        ))
        await db.commit()

async def load_creation_session(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT step,class,nickname,stats_json,points_left,ui_chat_id,ui_message_id FROM creation_sessions WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        await cur.close()
        if not row:
            return None
        return {
            "step": row[0],
            "class": row[1],
            "nickname": row[2],
            "stats": json.loads(row[3]),
            "points_left": row[4],
            "ui_chat_id": row[5],
            "ui_message_id": row[6]
        }

async def delete_creation_session(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:await db.execute("DELETE FROM creationsessions WHERE userid = ?", (userid,))
        await db.commit()

# purchases/admin logs/xp/gold logs
async def addpurchase(userid: int, kind: str, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO purchases (userid,kind,amount,createdat) VALUES (?,?,?,?)", (userid, kind, amount, int(time.time())))
        await db.commit()

async def addadminlog(adminid: int, action: str, targetuser: Optional[int], meta: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO adminlogs (adminid,action,targetuser,metajson,createdat) VALUES (?,?,?,?,?)",
                         (adminid, action, targetuser, json.dumps(meta, ensureascii=False), int(time.time())))
        await db.commit()

async def addxplog(userid:int, basexp:int, bonusxp:int, total:int, reason:str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO xplogs (userid,basexp,bonusxp,totalxp,reason,createdat) VALUES (?,?,?,?,?,?)",
                         (userid, basexp, bonusxp, total, reason, int(time.time())))
        await db.commit()

async def addgoldlog(userid:int, basegold:int, bonusgold:int, total:int, reason:str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO goldlogs (userid,basegold,bonusgold,totalgold,reason,createdat) VALUES (?,?,?,?,?,?)",
                         (userid, basegold, bonusgold, total, reason, int(time.time())))
        await db.commit()