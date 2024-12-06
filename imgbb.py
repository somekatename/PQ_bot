from imgbbpy import AsyncClient

from config import IMGBB_API_KEY


async def get_client():
    return AsyncClient(key=IMGBB_API_KEY)
