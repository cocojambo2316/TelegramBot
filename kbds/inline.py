from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import Teacher


class MenuCallBack(CallbackData, prefix="menu"):
    level: int
    menu_name: str
    category: int | None = None
    page: int = 1
    product_id: int | None = None


def get_user_main_btns(*, level: int, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    btns = {
        "Kierunki i przedmioty": "catalog",
        "Co robi ten bot?": "about",
        "Wsparcie techniczne": "payment",
        "Dodatkowe materiały": "shipping",
    }
    for text, menu_name in btns.items():
        if menu_name == 'catalog':
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBack(level=level + 1, menu_name=menu_name).pack()))
        else:
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBack(level=level, menu_name=menu_name).pack()))

    return keyboard.adjust(*sizes).as_markup()


def get_user_catalog_btns(*, level: int, categories: list, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='wstecz',
                                      callback_data=MenuCallBack(level=level - 1, menu_name='main').pack()))
    for c in categories:
        keyboard.add(InlineKeyboardButton(text=c.name,
                                          callback_data=MenuCallBack(level=level + 1, menu_name=c.name,
                                                                     category=c.id).pack()))

    return keyboard.adjust(*sizes).as_markup()


def get_products_btns(
        *,
        level: int,
        category: int,
        page: int,
        pagination_btns: dict,
        product_id: int,
        sizes: tuple[int] = (2, 1)
):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='Wstecz',
                                      callback_data=MenuCallBack(level=level - 1, menu_name='catalog').pack()))

    keyboard.adjust(*sizes)

    row = []
    for text, menu_name in pagination_btns.items():
        if menu_name == "next":
            row.append(InlineKeyboardButton(text=text,
                                            callback_data=MenuCallBack(
                                                level=level,
                                                menu_name=menu_name,
                                                category=category,
                                                page=page + 1).pack()))

        elif menu_name == "previous":
            row.append(InlineKeyboardButton(text=text,
                                            callback_data=MenuCallBack(
                                                level=level,
                                                menu_name=menu_name,
                                                category=category,
                                                page=page - 1).pack()))

        # кнопка ПРЕПОДАВАТЕЛИ
    keyboard.add(InlineKeyboardButton(
        text="Wykładowcy",
        callback_data=MenuCallBack(
            level=level + 1,
            menu_name="teachers",
            product_id=product_id,
            category=category,
            page=page,
        ).pack()
    ))

    keyboard.adjust(*sizes)

    return keyboard.row(*row).as_markup()


def get_callback_btns(*, btns: dict[str, str], sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()


def get_products_btns(
        *,
        level: int,
        category: int,
        page: int,
        pagination_btns: dict,
        product_id: int,
        sizes: tuple[int] = (1,)
):
    keyboard = InlineKeyboardBuilder()

    # Back
    keyboard.add(InlineKeyboardButton(
        text='⬅ Wstecz',
        callback_data=MenuCallBack(
            level=level - 1,
            menu_name='catalog'
        ).pack()
    ))

    # Teachers
    keyboard.add(InlineKeyboardButton(
        text='👩‍🏫 Wykładowcy',
        callback_data=f"teachers_list_{product_id}"   # ← new format
    ))

    keyboard.adjust(*sizes)

    # paginacja
    row = []
    for text, menu_name in pagination_btns.items():

        new_page = page + 1 if menu_name == "next" else page - 1

        row.append(InlineKeyboardButton(
            text=text,
            callback_data=MenuCallBack(
                level=level,
                menu_name="product",
                category=category,
                page=new_page
            ).pack()
        ))

    keyboard.row(*row)

    return keyboard.as_markup()

def get_single_teacher_btns(teachers: list[Teacher]):
    keyboard = InlineKeyboardBuilder()

    for t in teachers:
        keyboard.add(InlineKeyboardButton(
            text=t.name,
            callback_data=f"teacher_{t.id}"
        ))

    keyboard.adjust(1)
    return keyboard.as_markup()