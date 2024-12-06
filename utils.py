from aiogram.types import Message

from bot import bot
from config import TOKEN
from imgbb import get_client


def difficulty_symbol(difficulty: int) -> str:
    if difficulty < 3:
        difficulty_symbol = '📗'
    elif 3 <= difficulty < 4.5:
        difficulty_symbol = '📙'
    elif difficulty >= 4.5:
        difficulty_symbol = '📕'
    else:
        difficulty_symbol = '💀'
    return difficulty_symbol


def get_item_color(difficulty: str) -> int:
    if difficulty == '📗':
        return 9367192
    elif difficulty == '📙':
        return 16766590
    elif difficulty == '📕':
        return 16478047
    return 13338331


async def get_preview_url(message: Message) -> str:
    file = await bot.get_file(file_id=message.photo[-1].file_id)
    telegram_file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
    imgbb_client = await get_client()
    imgg_reponse = await imgbb_client.upload(url=telegram_file_url)
    await imgbb_client.close()
    return imgg_reponse.url
