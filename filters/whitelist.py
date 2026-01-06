from aiogram.filters import BaseFilter
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from database.orm_query import orm_is_user_whitelisted

class WhiteListFilter(BaseFilter):
    async def __call__(self, message: Message, session: AsyncSession) -> bool:
        return await orm_is_user_whitelisted(session, message.from_user.id)