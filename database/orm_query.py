import math
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import Banner, Category, Product, User, Teacher, Whitelist




############### Banners (info pages) ###############

async def orm_add_banner_description(session: AsyncSession, data: dict):
    #Add a new one or change an existing one by name
    #menu items: main, about, cart, shipping, payment, catalog
    query = select(Banner)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([Banner(name=name, description=description) for name, description in data.items()])
    await session.commit()


async def orm_change_banner_image(session: AsyncSession, name: str, image: str):
    query = update(Banner).where(Banner.name == name).values(image=image)
    await session.execute(query)
    await session.commit()


async def orm_get_banner(session: AsyncSession, page: str):
    query = select(Banner).where(Banner.name == page)
    result = await session.execute(query)
    return result.scalar()


async def orm_get_info_pages(session: AsyncSession):
    query = select(Banner)
    result = await session.execute(query)
    return result.scalars().all()


############################ Categories ######################################

async def orm_get_categories(session: AsyncSession):
    query = select(Category)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_create_categories(session: AsyncSession, categories: list):
    query = select(Category)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([Category(name=name) for name in categories])
    await session.commit()

############ Admin: add/edit/delete product ########################

async def orm_add_product(session: AsyncSession, data: dict):
    obj = Product(
        name=data["name"],
        description=data["description"],
        image=data["image"],
        category_id=int(data["category"]),
    )
    session.add(obj)
    await session.commit()


async def orm_get_products(session: AsyncSession, category_id: int | None = None):
    if category_id is None:
        # Return all the subjects back
        query = select(Product)
    else:
        # Return subjects from exact category
        query = select(Product).where(Product.category_id == int(category_id))

    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_product(session: AsyncSession, product_id: int):
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_update_product(session: AsyncSession, product_id: int, data):
    query = (
        update(Product)
        .where(Product.id == product_id)
        .values(
            name=data["name"],
            description=data["description"],
            image=data["image"],
            category_id=int(data["category"]),
        )
    )
    await session.execute(query)
    await session.commit()


async def orm_delete_product(session: AsyncSession, product_id: int):
    query = delete(Product).where(Product.id == product_id)
    await session.execute(query)
    await session.commit()

async def orm_add_category(session: AsyncSession, name: str):
    """Add one category by name"""
    # Cheching if it is already exists
    query = select(Category).where(Category.name == name)
    result = await session.execute(query)
    if result.scalar():
        return  #Alredy exists, you can leave or take smth

    session.add(Category(name=name))
    await session.commit()

##################### Add user to DB #####################################

async def orm_add_user(
    session: AsyncSession,
    user_id: int,
    first_name: str | None = None,
    last_name: str | None = None,
    phone: str | None = None,
):
    query = select(User).where(User.user_id == user_id)
    result = await session.execute(query)
    if result.first() is None:
        session.add(
            User(user_id=user_id, first_name=first_name, last_name=last_name, phone=phone)
        )
        await session.commit()

#teachers

async def orm_add_teacher(
    session: AsyncSession,
    name: str,
    url_link: str,
    description: str | None,
    product_id: int,
):
    teacher = Teacher(
        name=name,
        url_link=url_link,
        description=description,
        product_id=product_id
    )
    session.add(teacher)
    await session.commit()

async def orm_get_teachers_by_product(session: AsyncSession, product_id: int):
    result = await session.execute(
        select(Teacher).where(Teacher.product_id == product_id)
    )
    return result.scalars().all()


async def orm_update_teacher(session: AsyncSession, teacher_id: int, data: dict):
    query = (
        update(Teacher)
        .where(Teacher.id == teacher_id)
        .values(**data)
    )
    await session.execute(query)
    await session.commit()


async def orm_update_category(session: AsyncSession, category_id: int, new_name: str):
    query = (
        update(Category)
        .where(Category.id == category_id)
        .values(name=new_name)
    )
    await session.execute(query)
    await session.commit()


async def orm_delete_category(session: AsyncSession, category_id: int):
    query = delete(Category).where(Category.id == category_id)
    await session.execute(query)
    await session.commit()

async def orm_is_user_whitelisted(session: AsyncSession, user_id: int) -> bool:
    result = await session.execute(
        select(Whitelist).where(Whitelist.user_id == user_id)
    )
    return result.scalar() is not None


async def orm_add_to_whitelist(session: AsyncSession, user_id: int) -> bool:
    result = await session.execute(
        select(Whitelist).where(Whitelist.user_id == user_id)
    )

    if result.scalar():
        return False   # уже есть

    session.add(Whitelist(user_id=user_id))
    await session.commit()
    return True

async def orm_remove_from_whitelist(session: AsyncSession, user_id: int):
    await session.execute(
        delete(Whitelist).where(Whitelist.user_id == user_id)
    )
    await session.commit()
