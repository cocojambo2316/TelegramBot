from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove

from handlers.user_group import get_admins

from sqlalchemy import select
from database.models import Product

from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import (
    orm_change_banner_image,
    orm_get_categories,
    orm_add_product,
    orm_delete_product,
    orm_get_info_pages,
    orm_get_product,
    orm_get_products,
    orm_update_product,
    orm_add_category,
    orm_add_teacher,
    orm_get_teachers_by_product,
    orm_update_teacher,
    orm_update_category,
    orm_add_to_whitelist,
    orm_remove_from_whitelist
)

from filters.chat_types import ChatTypeFilter, IsAdmin
from handlers.menu_processing import products

from kbds.inline import get_callback_btns
from kbds.reply import get_keyboard

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


ADMIN_KB = get_keyboard(
    "Add product",
    "Assortment",
    "Add/Change banner",
    "Add Category",
    "Add Teacher",
    "Change teacher",
    "Edit Category",
    "Add user",
    "Remove user",
    placeholder="Choose wat you want to do",
    sizes=(2,),
)

@admin_router.message(Command("admin"))
async def admin_features(message: types.Message):
    await message.answer("What do you what to do??", reply_markup=ADMIN_KB)


@admin_router.message(F.text == 'Assortment')
async def admin_features(message: types.Message, session: AsyncSession):
    categories = await orm_get_categories(session)
    btns = {category.name : f'category_{category.id}' for category in categories}
    await message.answer("Choose the categoty", reply_markup=get_callback_btns(btns=btns))


@admin_router.callback_query(F.data.startswith('category_'))
async def starring_at_product(callback: types.CallbackQuery, session: AsyncSession):
    category_id = callback.data.split('_')[-1]
    for product in await orm_get_products(session, int(category_id)):
        await callback.message.answer_photo(
            product.image,
            caption=f"{product.name}\
                    \n{product.description}",
            reply_markup=get_callback_btns(
                btns={
                    "Delete": f"delete_{product.id}",
                    "Change": f"change_{product.id}",
                },
                sizes=(2,)
            ),
        )
    await callback.answer()
    await callback.message.answer("Here is the list of subjects ⏫")


@admin_router.callback_query(F.data.startswith("delete_"))
async def delete_product_callback(callback: types.CallbackQuery, session: AsyncSession):
    product_id = callback.data.split("_")[-1]
    await orm_delete_product(session, int(product_id))

    await callback.answer("Subject is added")
    await callback.message.answer("Subject is deleted!")


################# Micro FSM for loading/changing banners ############################

class AddBanner(StatesGroup):
    image = State()

# We send a list of information pages to the bot and enter the photo sending state.
@admin_router.message(StateFilter(None), F.text == 'Add/Change banner')
async def add_image2(message: types.Message, state: FSMContext, session: AsyncSession):
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    await message.answer(f"Send photo of the banner.\nWhite the category this banner is for\
                         \n{', '.join(pages_names)}")
    await state.set_state(AddBanner.image)

# Add/change the image in the table (there are already pages recorded by name:
# main, catalog, about
@admin_router.message(AddBanner.image, F.photo)
async def add_banner(message: types.Message, state: FSMContext, session: AsyncSession):
    image_id = message.photo[-1].file_id
    for_page = message.caption.strip()
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    if for_page not in pages_names:
        await message.answer(f"Please enter a normal page title, for example:\
                         \n{', '.join(pages_names)}")
        return
    await orm_change_banner_image(session, for_page, image_id,)
    await message.answer("Banner is added/changed")
    await state.clear()

# catching incorrect input
@admin_router.message(AddBanner.image)
async def add_banner2(message: types.Message, state: FSMContext):
    await message.answer("Send a photo of the banner or cancel")

#########################################################################################



######################## FSM for adding/changing products by the admin ###################

class AddProduct(StatesGroup):
    # State steps
    name = State()
    description = State()
    category = State()
    image = State()
    product_for_change = None

    texts = {
        "AddProduct:name": "Re-enter the name:",
        "AddProduct:description": "Re-enter the description:",
        "AddProduct:category": "Please select a category again ⬆️",
        "AddProduct:image": "This state is the last one, so...",
    }


# We enter the state of waiting for the name input
@admin_router.callback_query(StateFilter(None), F.data.startswith("change_"))
async def change_product_callback(
    callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
):
    product_id = callback.data.split("_")[-1]

    product_for_change = await orm_get_product(session, int(product_id))

    AddProduct.product_for_change = product_for_change

    await callback.answer()
    await callback.message.answer(
        "Enter product name", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddProduct.name)


# We enter the state of waiting for the name input
@admin_router.message(StateFilter(None), F.text == "Add product")
async def add_product(message: types.Message, state: FSMContext):
    await message.answer(
        "Enter product name", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddProduct.name)


# The handler for canceling and resetting the state should always be here,
# after we have just reached state number 1 (elementary sequence of filters)
@admin_router.message(StateFilter("*"), Command("stop"))
@admin_router.message(StateFilter("*"), F.text.casefold() == "stop")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    if AddProduct.product_for_change:
        AddProduct.product_for_change = None
    await state.clear()
    await message.answer("Actions canceled", reply_markup=ADMIN_KB)


# Go back a step (to the previous state)
@admin_router.message(StateFilter("*"), Command("back"))
@admin_router.message(StateFilter("*"), F.text.casefold() == "back")
async def back_step_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()

    if current_state == AddProduct.name:
        await message.answer(
            'There is no previous step, or enter the name of the product or write "cancel"'
        )
        return

    previous = None
    for step in AddProduct.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(
                f"Ok, you're back to the previous step. \n {AddProduct.texts[previous.state]}"
            )
            return
        previous = step






######################################### FSM FOR CATEGORIES ########################################

class AddCategory(StatesGroup):
    name = State()

@admin_router.message(StateFilter(None), F.text == "Add Category")
async def add_category_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Enter category name",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(AddCategory.name)

@admin_router.message(AddCategory.name, F.text)
async def add_category_name(
        message = types.Message,
        state = FSMContext,
        session = AsyncSession
):

    name = message.text.strip()
    if not name:
        await message.answer("Category name cannot be empty, please enter again")
        return

    await orm_add_category(session, name)

    await message.answer(
        f"Category «{name}» added.",
        reply_markup=ADMIN_KB,
    )
    await state.clear()


@admin_router.message(AddCategory.name)
async def add_category_name_invalid(message: types.Message, state: FSMContext):
    await message.answer("Enter the category name in text")


#################################################################################################



# We catch the data for the name state and then change the state to description
@admin_router.message(AddProduct.name, F.text)
async def add_name(message: types.Message, state: FSMContext):
    if message.text == "." and AddProduct.product_for_change:
        await state.update_data(name=AddProduct.product_for_change.name)
    else:
        # Here you can do any additional checking.
        # and exit the handler without changing the state by sending the corresponding message
        # for example:
        if 4 >= len(message.text) >= 150:
            await message.answer(
                "The product name must not exceed 150 characters or be less than 5 characters. Re-enter"
            )
            return

        await state.update_data(name=message.text)
    await message.answer("Enter product description")
    await state.set_state(AddProduct.description)

# Handler for catching invalid inputs for the name state
@admin_router.message(AddProduct.name)
async def add_name2(message: types.Message, state: FSMContext):
    await message.answer("You have entered invalid data. Please enter the text of the product name.")


# We catch data for the description state and then change the state to price
@admin_router.message(AddProduct.description, F.text)
async def add_description(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text == "." and AddProduct.product_for_change:
        await state.update_data(description=AddProduct.product_for_change.description)
    else:
        if 4 >= len(message.text):
            await message.answer(
                "The description is too short. \n Please re-enter"
            )
            return
        await state.update_data(description=message.text)

    categories = await orm_get_categories(session)
    btns = {category.name : str(category.id) for category in categories}
    await message.answer("Select category", reply_markup=get_callback_btns(btns=btns))
    await state.set_state(AddProduct.category)

# Handler for catching invalid inputs for the description state
@admin_router.message(AddProduct.description)
async def add_description2(message: types.Message, state: FSMContext):
    await message.answer("You have entered invalid data. Please enter the product description text.")


# Catching the category selection callback
@admin_router.callback_query(AddProduct.category)
async def category_choice(callback: types.CallbackQuery, state: FSMContext , session: AsyncSession):
    categories = await orm_get_categories(session)
    valid_ids = [category.id for category in categories]

    try:
        cat_id = int(callback.data)
    except ValueError:
        await callback.message.answer('Select a category from the buttons.')
        await callback.answer()
        return

    if cat_id in valid_ids:
        await callback.answer()
        await state.update_data(category=cat_id)
        await callback.message.answer('Now upload the product image.')
        await state.set_state(AddProduct.image)
    else:
        await callback.message.answer('Select a category from the buttons.')
        await callback.answer()

#We catch any incorrect actions except clicking on the category selection button
@admin_router.message(AddProduct.category)
async def category_choice2(message: types.Message, state: FSMContext):
    await message.answer("'Select a category from the buttons.'")


# We catch data for the image state and then exit the states
@admin_router.message(AddProduct.image, or_f(F.photo, F.text == "."))
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text and message.text == "." and AddProduct.product_for_change:
        await state.update_data(image=AddProduct.product_for_change.image)

    elif message.photo:
        await state.update_data(image=message.photo[-1].file_id)
    else:
        await message.answer("Send a photo")
        return
    data = await state.get_data()
    try:
        if AddProduct.product_for_change:
            await orm_update_product(session, AddProduct.product_for_change.id, data)
        else:
            await orm_add_product(session, data)
        await message.answer("Product added/changed", reply_markup=ADMIN_KB)
        await state.clear()

    except Exception as e:
        await message.answer(
            f"Error: \n{str(e)}\nReport a bug",
            reply_markup=ADMIN_KB,
        )
        await state.clear()

    AddProduct.product_for_change = None

# We catch all other incorrect behavior for this state
@admin_router.message(AddProduct.image)
async def add_image2(message: types.Message, state: FSMContext):
    await message.answer("Send a photo")


#

class AddTeacher(StatesGroup):
    product_id = State()
    name = State()
    url_link = State()
    description = State()


@admin_router.message(StateFilter(None), F.text == "Add Teacher")
async def add_teachers(message: types.Message, state: FSMContext, session: AsyncSession):

    result = await session.execute(select(Product))
    products = result.scalars().all()

    if not products:
        await message.answer("No items. Please add an item first.")
        return

    # buttons: item name → item ID
    btns = {p.name: str(p.id) for p in products}

    await message.answer(
        "Select the subject to which you want to add a teacher:",
        reply_markup=get_callback_btns(btns=btns),
    )

    await state.set_state(AddTeacher.product_id)


@admin_router.callback_query(AddTeacher.product_id)
async def teacher_product_chosen(callback: types.CallbackQuery, state: FSMContext):
    try:
        product_id = int(callback.data)
    except ValueError:
        await callback.answer()
        await callback.message.answer("Select an item from the buttons.")
        return

    await state.update_data(product_id=product_id)
    await callback.answer()
    await callback.message.answer(
        "Enter the teacher's name:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(AddTeacher.name)


@admin_router.message(AddTeacher.name, F.text)
async def teacher_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("Name cannot be empty, please enter again.")
        return

    await state.update_data(name=name)
    await message.answer("Send a link to the teacher (tg/site, etc.):")
    await state.set_state(AddTeacher.url_link)


@admin_router.message(AddTeacher.url_link, F.text)
async def teacher_url(message: types.Message, state: FSMContext):
    url = message.text.strip()
    if not url:
        await message.answer("The link cannot be empty, please enter it again.")
        return

    await state.update_data(url_link=url)
    await message.answer(
        "Optional: Write a short description of the teacher.\n"
        "If not needed, send '-'.",
    )
    await state.set_state(AddTeacher.description)


@admin_router.message(AddTeacher.description, F.text)
async def teacher_finish(message: types.Message, state: FSMContext, session: AsyncSession):
    desc_raw = message.text.strip()
    description = None if desc_raw == "-" else desc_raw

    data = await state.get_data()

    await orm_add_teacher(
        session=session,
        name=data["name"],
        url_link=data["url_link"],
        description=description,
        product_id=data["product_id"],
    )

    await message.answer("The teacher has been added ✅", reply_markup=ADMIN_KB)
    await state.clear()


class EditTeacher(StatesGroup):
    choose_product = State()
    choose_teacher = State()
    choose_field = State()
    new_value = State()

    teacher_id = None
    field = None


@admin_router.message(StateFilter(None), F.text == "Change teacher")
async def edit_teacher_start(message: types.Message, state: FSMContext, session: AsyncSession):
    products = await orm_get_products(session, category_id=None)  # if necessary, we will adapt
    if not products:
        await message.answer("No items.")
        return

    btns = {p.name: f"edit_teacher_product_{p.id}" for p in products}

    await message.answer("Select item:", reply_markup=get_callback_btns(btns=btns))
    await state.set_state(EditTeacher.choose_product)


@admin_router.callback_query(EditTeacher.choose_product, F.data.startswith("edit_teacher_product_"))
async def edit_teacher_choose_teacher(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    product_id = int(callback.data.split("_")[-1])
    teachers = await orm_get_teachers_by_product(session, product_id)

    if not teachers:
        await callback.message.answer("This subject has no teachers.")
        await state.clear()
        return

    btns = {t.name: f"edit_teacher_{t.id}" for t in teachers}

    await callback.message.answer("Select a teacher:", reply_markup=get_callback_btns(btns=btns))

    await state.set_state(EditTeacher.choose_teacher)


@admin_router.callback_query(EditTeacher.choose_teacher, F.data.startswith("edit_teacher_"))
async def edit_teacher_choose_field(callback: types.CallbackQuery, state: FSMContext):
    teacher_id = int(callback.data.split("_")[-1])
    EditTeacher.teacher_id = teacher_id

    btns = {
        "Name": "field_name",
        "Link": "field_url_link",
        "Description": "field_description",
    }

    await callback.message.answer("What do you want to change?", reply_markup=get_callback_btns(btns=btns))
    await state.set_state(EditTeacher.choose_field)


@admin_router.callback_query(EditTeacher.choose_field, F.data.startswith("field_"))
async def edit_teacher_enter_value(callback: types.CallbackQuery, state: FSMContext):
    field = callback.data.split("_", 1)[1]
    EditTeacher.field = field

    await callback.message.answer(f"Enter a new value for the field: {field}")
    await state.set_state(EditTeacher.new_value)


@admin_router.message(EditTeacher.new_value, F.text)
async def edit_teacher_finish(message: types.Message, state: FSMContext, session: AsyncSession):
    teacher_id = EditTeacher.teacher_id
    field = EditTeacher.field
    value = message.text.strip()

    await orm_update_teacher(session, teacher_id, {field: value})

    await message.answer("Changes saved!", reply_markup=ADMIN_KB)
    await state.clear()


class SupportFSM(StatesGroup):
    waiting_for_message = State()


@admin_router.message(F.text == "Wsparcie techniczne")
async def support_start(message: types.Message, state: FSMContext):
    # Ask user to describe the issue
    await message.answer(
        "Opisz swój problem lub napisz, czego potrzebujesz.\n"
        "Aby anulować, wpisz: /stop",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(SupportFSM.waiting_for_message)


class EditCategory(StatesGroup):
    choose_category = State()
    new_name = State()

@admin_router.message(StateFilter(None), F.text == "Edit Category")
async def edit_category_start(message: types.Message, state: FSMContext, session: AsyncSession):
    categories = await orm_get_categories(session)

    if not categories:
        await message.answer("No categories found.")
        return

    btns = {c.name: f"edit_cat_{c.id}" for c in categories}
    await message.answer("Choose category to edit:", reply_markup=get_callback_btns(btns))

    await state.set_state(EditCategory.choose_category)

@admin_router.callback_query(EditCategory.choose_category, F.data.startswith("edit_cat_"))
async def choose_category_for_edit(callback: types.CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split("_")[-1])

    await state.update_data(category_id=cat_id)
    await callback.answer()

    await callback.message.answer(
        "Enter new name for this category:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(EditCategory.new_name)

@admin_router.message(EditCategory.new_name, F.text)
async def change_category_name(message: types.Message, state: FSMContext, session: AsyncSession):
    new_name = message.text.strip()
    if not new_name:
        await message.answer("Name cannot be empty.")
        return

    data = await state.get_data()
    category_id = data["category_id"]

    await orm_update_category(session, category_id, new_name)

    await message.answer("Category renamed successfully ✅", reply_markup=ADMIN_KB)
    await state.clear()


class AddWhitelistUser(StatesGroup):
    user_id = State()


@admin_router.message(F.text == "Add user")
async def add_whitelist_start(message: types.Message, state: FSMContext):
    await message.answer("Enter Telegram user_id:")
    await state.set_state(AddWhitelistUser.user_id)


@admin_router.message(AddWhitelistUser.user_id, F.text)
async def add_whitelist_finish(message: types.Message, state: FSMContext, session: AsyncSession):
    user_id = int(message.text.strip())

    await orm_add_to_whitelist(session, user_id)

    await message.answer("✅ User added to whitelist", reply_markup=ADMIN_KB)
    await state.clear()


class RemoveWhitelistUser(StatesGroup):
    user_id = State()


@admin_router.message(F.text == "Remove user")
async def remove_whitelist_start(message: types.Message, state: FSMContext):
    await message.answer("Enter Telegram user_id to remove:")
    await state.set_state(RemoveWhitelistUser.user_id)


@admin_router.message(RemoveWhitelistUser.user_id, F.text)
async def remove_whitelist_finish(message: types.Message, state: FSMContext, session: AsyncSession):
    user_id = int(message.text.strip())

    await orm_remove_from_whitelist(session, user_id)

    await message.answer("🗑 User removed from whitelist", reply_markup=ADMIN_KB)
    await state.clear()
