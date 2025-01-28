# handlers/user_handlers.py
import asyncio, os, ebooklib, html2text
from ebooklib import epub

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from loader import bot, dp
from filters.filters import IsDelBookmarkCallbackData, IsDigitCallbackData
from keyboards.bookmarks_kb import (create_bookmarks_keyboard,create_edit_keyboard)
from keyboards.pagination_kb import create_pagination_keyboard
from lexicon.lexicon import LEXICON
from services.file_handling import prepare_book, cache_manager




router = Router()
dp.include_router(router)

USER_DATA_KEY = 'user_data_{}'  # Формат ключа для данных пользователя


class UserStates(StatesGroup):
    add_book = State()


# Этот хэндлер будет срабатывать на команду "/start" -
# добавлять пользователя в базу данных, если его там еще не было
# и отправлять ему приветственное сообщение
@router.message(Command('start'))
async def process_start_command(message: Message):
    user_id = message.from_user.id
    user_data = await cache_manager.get_user_data(user_id)
    if user_data is None:
        user_data = {'page': 1, 'bookmarks': []}
        await cache_manager.set_user_data(user_id, user_data)
    await message.answer(LEXICON['start'])



# хендлер на добавление книги
@router.message(Command('add_book'))
async def process_add_book_command(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.set_state(UserStates.add_book)
    await message.answer(LEXICON['add_book'])



# хендлер на добавление книги
@router.message(F.document, UserStates.add_book)
async def process_add_book_save(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # Получаем информацию о файле
    file_info = await bot.get_file(file_id=message.document.file_id)

    # Создаем директорию для пользователя, если она не существует
    user_directory = f'book/{user_id}'
    os.makedirs(user_directory, exist_ok=True)

    # Определяем путь сохранения файла
    file_path = os.path.join(user_directory, message.document.file_name)

    # Проверяем, что это текстовый или ePub файл
    if message.document.mime_type in ['text/plain', 'application/epub+zip']:
        # Скачиваем файл
        await bot.download_file(file_path=file_info.file_path, destination=file_path)

        # Если файл ePub, конвертируем его в txt
        if message.document.mime_type == 'application/epub+zip':
            book = epub.read_epub(file_path)
            text = ""

            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    text += html2text.html2text(item.get_body_content().decode('utf-8'))

            # Сохраняем преобразованный текст в .txt файл
            txt_file_path = file_path.replace('.epub', '.txt')
            with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write(text)

            # Удаляем исходный ePub файл
            os.remove(file_path)

        await message.answer(LEXICON['add_book_ok'])

    else:
        await message.answer(LEXICON['add_book_false'])

    await state.clear()

        


# Этот хэндлер будет срабатывать на команду "/help"
# и отправлять пользователю сообщение со списком доступных команд в боте
@router.message(Command('help'))
async def process_help_command(message: Message):
    await message.answer(LEXICON[message.text])


# Этот хэндлер будет срабатывать на команду "/beginning"
# и отправлять пользователю первую страницу книги с кнопками пагинации
@router.message(Command(commands='beginning'))
async def process_beginning_command(message: Message):
    user_id = message.from_user.id
    if not await prepare_book(user_id):
        await message.answer("Извините, книга не найдена.")
        return
    
    await cache_manager.update_user_page(user_id, 1)
    user_data = await cache_manager.get_user_data(user_id)
    book_key = f'book_{user_id}'
    book_data = await cache_manager.get(book_key)

    text = book_data.get(str(user_data['page']), "Страница не найдена.")
    total_pages = len(book_data)
    await message.answer(
        text=text,
        reply_markup=create_pagination_keyboard(
            'backward',
            f'{user_data["page"]}/{total_pages}',
            'forward'
        )
    )



# Этот хэндлер будет срабатывать на команду "/continue"
# и отправлять пользователю страницу книги, на которой пользователь
# остановился в процессе взаимодействия с ботом
@router.message(Command('continue'))
async def process_continue_command(message: Message):
    user_id = message.from_user.id
    user_data = await cache_manager.get_user_data(user_id)
    book_key = f'book_{user_id}'
    book_data = await cache_manager.get(book_key)

    if user_data and book_data and str(user_data['page']) in book_data:
        text = book_data[str(user_data['page'])]
        total_pages = len(book_data)
        await message.answer(
            text=text,
            reply_markup=create_pagination_keyboard(
                'backward',
                f"{user_data['page']}/{total_pages}",
                'forward'
            )
        )
    else:
        await message.answer("Страница не найдена или книга не загружена.")




# Этот хэндлер будет срабатывать на команду "/bookmarks"
# и отправлять пользователю список сохраненных закладок,
# если они есть или сообщение о том, что закладок нет
@router.message(Command('bookmarks'))
async def process_bookmarks_command(message: Message):
    user_id = message.from_user.id
    user_data = await cache_manager.get_user_data(user_id)
    book_key = f'book_{user_id}'
    book_data = await cache_manager.get(book_key)

    if user_data and user_data.get('bookmarks'):
        bookmarks = user_data['bookmarks']
        await message.answer(
            text=LEXICON['bookmarks'],  # Предполагается, что в LEXICON есть ключ 'bookmarks'
            reply_markup=create_bookmarks_keyboard(book_data, bookmarks)
        )
    else:
        await message.answer(text=LEXICON['no_bookmarks'])




# Этот хэндлер будет срабатывать на нажатие инлайн-кнопки "вперед"
# во время взаимодействия пользователя с сообщением-книгой
@router.callback_query(F.data == 'forward')
async def process_forward_press(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await cache_manager.get_user_data(user_id)
    book_key = f'book_{user_id}'
    book_data = await cache_manager.get(book_key)

    if user_data and book_data and user_data['page'] < len(book_data):
        user_data['page'] += 1
        await cache_manager.set_user_data(user_id, user_data)

        text = book_data[str(user_data['page'])]
        total_pages = len(book_data)
        await callback.message.edit_text(
            text=text,
            reply_markup=create_pagination_keyboard(
                'backward',
                f"{user_data['page']}/{total_pages}",
                'forward'
            )
        )
    await callback.answer()



# Этот хэндлер будет срабатывать на нажатие инлайн-кнопки "назад"
# во время взаимодействия пользователя с сообщением-книгой
@router.callback_query(F.data == 'backward')
async def process_backward_press(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await cache_manager.get_user_data(user_id)
    book_key = f'book_{user_id}'
    book_data = await cache_manager.get(book_key)

    if user_data and book_data and user_data['page'] < len(book_data):
        user_data['page'] -= 1
        await cache_manager.set_user_data(user_id, user_data)

        text = book_data[str(user_data['page'])]
        total_pages = len(book_data)
        await callback.message.edit_text(
            text=text,
            reply_markup=create_pagination_keyboard(
                'backward',
                f"{user_data['page']}/{total_pages}",
                'forward'
            )
        )
    await callback.answer()


# Этот хэндлер будет срабатывать на нажатие инлайн-кнопки
# с номером текущей страницы и добавлять текущую страницу в закладки
@router.callback_query(lambda x: '/' in x.data and x.data.replace('/', '').isdigit())
async def process_page_press(callback: CallbackQuery):
    user_id = callback.from_user.id
    page = callback.data.split('/')[0]

    await cache_manager.add_user_bookmark(user_id, page)    
    await callback.answer('Страница добавлена в закладки!')



# Этот хэндлер будет срабатывать на нажатие инлайн-кнопки
# с закладкой из списка закладок
@router.callback_query(IsDigitCallbackData())
async def process_bookmark_press(callback: CallbackQuery):
    user_id = callback.from_user.id
    page = int(callback.data)
    user_data = await cache_manager.get_user_data(user_id)
    book_key = f'book_{user_id}'
    book_data = await cache_manager.get(book_key)

    if book_data and str(page) in book_data:
        user_data['page'] = page
        await cache_manager.set_user_data(user_id, user_data)
        text = book_data[str(page)]
        total_pages = len(book_data)
        await callback.message.edit_text(
            text=text,
            reply_markup=create_pagination_keyboard(
                'backward',
                f"{page}/{total_pages}",
                'forward'
            )
        )
    else:
        await callback.answer('Страница не найдена.')



# Этот хэндлер будет срабатывать на нажатие инлайн-кнопки
# "редактировать" под списком закладок
@router.callback_query(F.data == 'edit_bookmarks')
async def process_edit_press(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await cache_manager.get_user_data(user_id)
    book_key = f'book_{user_id}'
    book_data = await cache_manager.get(book_key)
    
    if user_data and user_data.get('bookmarks'):
        await callback.message.edit_text(
            text=LEXICON['edit_bookmarks'],
            reply_markup=create_edit_keyboard(
                book_data,
                user_data['bookmarks']
            )
        )
    else:
        await callback.message.edit_text(text=LEXICON['no_bookmarks'])
    await callback.answer()



# Этот хэндлер будет срабатывать на нажатие инлайн-кнопки
# "отменить" во время работы со списком закладок (просмотр и редактирование)
@router.callback_query(F.data == 'cancel')
async def process_cancel_press(callback: CallbackQuery):
    await callback.message.edit_text(text=LEXICON['cancel_text'])
    await callback.answer()



# Этот хэндлер будет срабатывать на нажатие инлайн-кнопки
# с закладкой из списка закладок к удалению
@router.callback_query(IsDelBookmarkCallbackData())
async def process_del_bookmark_press(callback: CallbackQuery):
    user_id = callback.from_user.id
    page = int(callback.data[:-3])

    # Удаляем закладку
    await cache_manager.remove_user_bookmark(user_id, page)
    await asyncio.sleep(0.5)  # Даем время на обновление кеша

    # Получаем обновленные данные пользователя из кеша
    user_data = await cache_manager.get_user_data(user_id)
    book_key = f'book_{user_id}'
    book_data = await cache_manager.get(book_key)

    if user_data and user_data.get('bookmarks'):
        new_markup = create_edit_keyboard(book_data, user_data['bookmarks'])
        # Проверяем, изменилась ли клавиатура
        if callback.message.reply_markup != new_markup:
            await callback.message.edit_reply_markup(reply_markup=new_markup)
            await callback.answer('Закладка удалена.')
        else:
            # Если клавиатура не изменилась, просто отправляем уведомление
            await callback.answer('Нет изменений.')
    else:
        # Если закладок нет, отправляем сообщение об этом
        await callback.message.edit_text(text=LEXICON['no_bookmarks'])
        await callback.answer('Закладки удалены.')


