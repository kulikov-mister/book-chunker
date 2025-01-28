# services/file_handling.py
from services.cache_utils import CacheManager

import os

cache_manager = CacheManager()

PAGE_SIZE = 750


# Функция, возвращающая строку с текстом страницы и ее размер
def _get_part_text(text: str, start: int, size: int) -> tuple[str, int]:
    end_signs = ',.!:;?'
    counter = 0
    if len(text) < start + size:
        size = len(text) - start
        text = text[start:start + size]
    else:
        if text[start + size] == '.' and text[start + size - 1] in end_signs:
            text = text[start:start + size - 2]
            size -= 2
        else:
            text = text[start:start + size]
        for i in range(size - 1, 0, -1):
            if text[i] in end_signs:
                break
            counter = size - i
    page_text = text[:size - counter]
    page_size = size - counter
    return page_text, page_size


async def prepare_book(user_id: int) -> bool:
    book_key = f'book_{user_id}'
    book_exists = await cache_manager.get(book_key)
    if book_exists is not None:
        return True  # Книга уже в кэше

    path = f'book/{user_id}/Vern_Harnish_Razvitie_biznesa.txt'
    if not os.path.exists(path):
        return False  # Книга не найдена

    with open(file=path, mode='r', encoding='utf-8') as file:
        text = file.read()

    # Разбиение текста на страницы и сохранение в кэше
    book_data = {}
    start, page_number = 0, 1
    while start < len(text):
        page_text, page_size = _get_part_text(text, start, PAGE_SIZE)
        start += page_size
        book_data[page_number] = page_text.strip()
        page_number += 1

    await cache_manager.set(book_key, book_data)
    return True