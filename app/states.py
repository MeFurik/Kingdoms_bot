from aiogram.fsm.state import StatesGroup, State

class CreateStates(StatesGroup):
    waiting_nick = State()
    allocating = State()

class ShopStates(StatesGroup):
    waiting_nick = State()

class AdminStates(StatesGroup):
    waiting_amount = State()
    waiting_days = State()
    waiting_nick = State()