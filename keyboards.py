from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def choosing_tournament() -> InlineKeyboardMarkup:
    tournament_keyboard = InlineKeyboardBuilder()
    tournament_buttons = [
        InlineKeyboardButton(text="ШРеК или МКМ", callback_data='shrek_mkm'),
        InlineKeyboardButton(text="Другой турнир", callback_data='another_tournament')
    ]
    tournament_keyboard.row(*tournament_buttons, width=1)
    return tournament_keyboard.as_markup()

def build_reg_markup(chat_username: str, topic_id: int) -> InlineKeyboardMarkup:
    reg_link = f"https://t.me/{chat_username}/{topic_id}"
    builder = InlineKeyboardBuilder()
    button = InlineKeyboardButton(text='Регистрация', url=reg_link)
    builder.row(button, width=1)
    return builder.as_markup()


def get_checking_keyboard() -> InlineKeyboardMarkup:
    checking_keyboard = InlineKeyboardBuilder()
    checking_buttons = [
        # TODO: check
        # InlineKeyboardButton(text="Да, пост готов к публикации", callback_data='yes'),
        InlineKeyboardButton(text="Да, создать комнату для регистрации", callback_data='theme_poll'),
        InlineKeyboardButton(text="Нет, нужны исправления", callback_data='no')
    ]
    checking_keyboard.row(*checking_buttons, width=1)
    return checking_keyboard.as_markup()


def build_create_theme_markup() -> InlineKeyboardMarkup:
    builder_create_theme = InlineKeyboardBuilder()
    btn = InlineKeyboardButton(text="Создать тему и опрос для регистрации", callback_data='theme_poll')
    builder_create_theme.row(btn, width=1)
    return builder_create_theme.as_markup()
