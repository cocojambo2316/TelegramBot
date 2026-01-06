from aiogram import F, types, Router, Bot
from aiogram.filters import CommandStart
from filters.whitelist import Message
from handlers.config import ADMINS

from sqlalchemy.ext.asyncio import AsyncSession
from database.orm_query import (
    orm_add_user,
    orm_get_teachers_by_product,
    orm_is_user_whitelisted
)

from database.models import Teacher

from filters.chat_types import ChatTypeFilter
from handlers.menu_processing import get_menu_content
from kbds.inline import (MenuCallBack, get_callback_btns, get_single_teacher_btns,
                         get_products_btns, get_user_main_btns, get_user_catalog_btns)

from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from handlers.admin_private import SupportFSM

user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(["private"]))


@user_private_router.message(CommandStart())
async def start_cmd(message: Message, session: AsyncSession):

    # ✅ Админ всегда имеет доступ
    if message.from_user.id not in ADMINS:
        is_allowed = await orm_is_user_whitelisted(session, message.from_user.id)

        if not is_allowed:
            await message.answer(
                "⛔ Brak dostępu.\n\n"
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ\n"
                "Skontaktuj się z administratorem."
            )
            return

    media, reply_markup = await get_menu_content(session, level=0, menu_name="main")

    await message.answer_photo(
        media.media,
        caption=media.caption or "",
        reply_markup=reply_markup
    )

@user_private_router.callback_query(MenuCallBack.filter())
async def user_menu(callback: types.CallbackQuery, callback_data: MenuCallBack, session: AsyncSession):

    media, reply_markup = await get_menu_content(
        session,
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        category=callback_data.category,
        page = callback_data.page,
        product_id=callback_data.product_id,
        user_id = callback.from_user.id,
    )
    await callback.message.edit_media(media=media, reply_markup=reply_markup)
    await callback.answer()


@user_private_router.callback_query(F.data.startswith("teachers_list_"))
async def show_teachers(callback: types.CallbackQuery, session: AsyncSession):
    product_id = int(callback.data.split("_")[-1])

    teachers = await orm_get_teachers_by_product(session, product_id)

    if not teachers:
        await callback.answer("W tej chwili nie ma żadnych wykładowców..", show_alert=True)
        return

    await callback.message.answer(
        "Wybierz wykładowcę:",
        reply_markup=get_single_teacher_btns(teachers)
    )

    await callback.answer()


@user_private_router.callback_query(F.data.startswith("teacher_"))
async def show_single_teacher(callback: types.CallbackQuery, session: AsyncSession):
    teacher_id = int(callback.data.split("_")[-1])

    teacher = await session.get(Teacher, teacher_id)

    text = (
        f"👩‍🏫 {teacher.name}\n"
        f"🔗 {teacher.url_link}\n"
        f"{teacher.description or ''}"
    )

    await callback.message.answer(text)
    await callback.answer()


@user_private_router.message(SupportFSM.waiting_for_message, F.text)
async def support_receive(message: types.Message, state: FSMContext, bot: Bot):
    user = message.from_user

    # Forward user's request to the admin
    text = (
        f"📩 Nowa wiadomość od użytkownika:\n"
        f"👤 {user.full_name} (ID: {user.id})\n\n"
        f"💬 Treść:\n{message.text}"
    )

    await bot.send_message(chat_id=820001842, text=text)

    # Confirm to user
    await message.answer(
        "Dziękujemy! Twoje zgłoszenie zostało wysłane do administracji 👌",
        reply_markup=get_user_main_btns()
    )

    await state.clear()


