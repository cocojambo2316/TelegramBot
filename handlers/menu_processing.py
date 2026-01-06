from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_banner
from kbds.inline import get_user_catalog_btns

from database.orm_query import (
    orm_get_banner,
    orm_get_categories,
    orm_get_products,
    orm_get_teachers_by_product
)
from kbds.inline import (
    get_products_btns,
    get_user_catalog_btns,
    get_user_main_btns,
    get_single_teacher_btns
)

from utils.paginator import Paginator

async def main_menu(session, level, menu_name):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    kbds = get_user_main_btns(level=level)

    return image, kbds


async def catalog(session, level, menu_name):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    categories = await orm_get_categories(session)
    kbds = get_user_catalog_btns(level=level, categories=categories)

    return image, kbds


def pages(paginator: Paginator):
    btns = dict()
    if paginator.has_previous():
        btns["◀Przesz "] = "previous"

    if paginator.has_next():
        btns[" Nast▶"] = "next"

    return btns


async def products(session, level, category, page):
    products = await orm_get_products(session, category_id=category)

    paginator = Paginator(products, page=page)
    product = paginator.get_page()[0]    # ← A TRULY RELEVANT ITEM

    # caption
    caption = (
        f"{product.name}\n"
        f"{product.description}\n\n"
        f"Przedmiot {paginator.page} z {paginator.pages}"
    )

    # BUTTONS - we transfer EXACTLY product.id
    pagination_btns = pages(paginator)
    kbds = get_products_btns(
        level=level,
        category=category,
        page=page,
        pagination_btns=pagination_btns,
        product_id=product.id     # ← THE MOST IMPORTANT POINT
    )

    image = InputMediaPhoto(media=product.image, caption=caption)

    return image, kbds


async def get_menu_content(
        session: AsyncSession,
        level: int,
        menu_name:str,
        category: int | None = None,
        page: int | None = None,
        product_id: int | None = None,
        user_id: int | None = None,
):

        if level ==0:
            return await main_menu(session, level, menu_name)
        elif level ==1:
            return await catalog(session, level, menu_name)
        elif level ==2:
            return await products(session, level, category, page)
        elif level ==3:
            return await carts(session, level, menu_name, page, user_id, product_id)



async def build_teachers_text(session: AsyncSession, product_id: int) -> str:
    teachers = await orm_get_teachers_by_product(session, product_id)

    if not teachers:
        return "\n\nWykładowcy: na razie brak."

    text = "\n\nWykładowcy:\n"
    for t in teachers:
        text += f"👩‍🏫 {t.name}\n🔗 {t.url_link}\n"
        if t.description:
            text += f"📌 {t.description}\n"
        text += "\n"

    return text