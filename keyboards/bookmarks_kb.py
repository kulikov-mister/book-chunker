# keyboards/bookmarks_kb.py
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from lexicon.lexicon import LEXICON


def create_bookmarks_keyboard(book_data: dict, bookmarks: list) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    for button in sorted(bookmarks, key=int):
        page_text = book_data.get(str(button), "")[:100]
        kb_builder.row(InlineKeyboardButton(
            text=f'{button} - {page_text}',
            callback_data=str(button)))
    kb_builder.row(
        InlineKeyboardButton(
            text=LEXICON['edit_bookmarks_button'],
            callback_data='edit_bookmarks'
        ),
        InlineKeyboardButton(
            text=LEXICON['cancel'],
            callback_data='cancel'
        ),
        width=2
    )
    return kb_builder.as_markup()



def create_edit_keyboard(book_data: dict, bookmarks: list) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    for button in sorted(bookmarks, key=int):
        page_text = book_data.get(str(button), "")[:100]
        kb_builder.row(InlineKeyboardButton(
            text=f'{LEXICON["del"]} {button} - {page_text}',
            callback_data=f'{button}del'
        ))
    kb_builder.row(InlineKeyboardButton(
        text=LEXICON['cancel'],
        callback_data='cancel'
    ))
    return kb_builder.as_markup()
