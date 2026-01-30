import os

TG_BOT_TOKEN = os.getenv("8562623985:AAGo7JxepGoTNqreJCiCwi6xRSMyxwf914Q")
REDIS_DSN = os.getenv("REDIS_DSN", "redis://localhost:6379/0")
DB_PATH = os.getenv("DB_PATH", "game.db")
ADMIN_IDS = [int(i) for i in os.getenv("1291693026", "").split(",") if i.strip().isdigit()]
ASSETS_DIR = os.getenv("ASSETS_DIR", "assets")
WELCOME_IMG = os.path.join(ASSETS_DIR, "welcome.jpg")
FONT_PATH = os.path.join(ASSETS_DIR, "fonts", "DejaVuSans-Bold.ttf")